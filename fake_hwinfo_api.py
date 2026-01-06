import ctypes
import time
from ctypes import wintypes
from hwinfo_common import (
    HWiNFOHeader, HWiNFOSensor, HWiNFOEntry,
    HWiNFO_SHARED_MEM_PATH, HWiNFO_HEADER_MAGIC, HWiNFO_MEM_SIZE
)

# Constants
PAGE_READWRITE = 0x04
FILE_MAP_ALL_ACCESS = 0xF001F
INVALID_HANDLE_VALUE = -1
SDDL_REVISION_1 = 1
HWiNFO_MUTEX_NAME = "Global\HWiNFO_SM2_MUTEX"
ERROR_ALREADY_EXISTS = 183

class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]

def _create_security_attributes():
    sd_string = "D:(A;;GA;;;WD)"
    sd = wintypes.LPVOID()
    advapi32 = ctypes.windll.advapi32
    ConvertStringSecurityDescriptorToSecurityDescriptorW = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.ULONG),
    ]
    
    if not ConvertStringSecurityDescriptorToSecurityDescriptorW(sd_string, SDDL_REVISION_1, ctypes.byref(sd), None):
        print(f"Failed to create security descriptor: {ctypes.GetLastError()}")
        return None

    sa = SECURITY_ATTRIBUTES()
    sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
    sa.lpSecurityDescriptor = sd
    sa.bInheritHandle = False
    return sa

class FakeEntry:
    def __init__(self, id, name, units, entry_type, value=0.0):
        self.id = id
        self.name = name
        self.units = units
        self.entry_type = entry_type
        self.value = value
        self.value_min = value
        self.value_max = value
        self.parent_sensor = None
        self._mapped_entry = None # Pointer to shared memory structure

    def set_value(self, val):
        """Updates the local value. Won't be visible in SHM until FakeHWiNFO.update() is called."""
        self.value = float(val)
        self.value_max = max(self.value_max, self.value)
        self.value_min = min(self.value_min, self.value)

    def get_value(self):
        return self.value

class FakeSensor:
    def __init__(self, id, name, sensor_type=5, instance=1):
        self.id = id
        self.name = name
        self.sensor_type = sensor_type
        self.instance = instance
        self.entries = []
        self._mapped_sensor = None

    def add_entry(self, name, units, entry_type, id, value=0.0):
        """
        entry_type: 1=Temp, 2=Volt, 3=Fan, 4=Current, 5=Power, 6=Clock, 7=Usage, 8=Other
        """
        entry = FakeEntry(id, name, units, entry_type, value)
        entry.parent_sensor = self
        self.entries.append(entry)
        return entry

class FakeHWiNFO:
    def __init__(self):
        self.sensors = []
        self.mapping_handle = None
        self.map_addr = None
        self.mutex_handle = None
        self.header = None
        self._kernel32 = ctypes.windll.kernel32
        self.is_active = False

    def add_sensor(self, id, name, sensor_type=5, instance=1):
        sensor = FakeSensor(id, name, sensor_type, instance)
        self.sensors.append(sensor)
        return sensor

    def create(self):
        """Creates the Shared Memory and populates the layout."""
        # 1. Calculate Layout
        num_sensors = len(self.sensors)
        all_entries = [e for s in self.sensors for e in s.entries]
        num_entries = len(all_entries)

        header_size = ctypes.sizeof(HWiNFOHeader)
        sensor_size = ctypes.sizeof(HWiNFOSensor)
        entry_size = ctypes.sizeof(HWiNFOEntry)

        sensor_section_offset = header_size
        entry_section_offset = sensor_section_offset + (num_sensors * sensor_size)
        total_size = entry_section_offset + (num_entries * entry_size)
        total_size = max(total_size, HWiNFO_MEM_SIZE) # Ensure at least default size

        print(f"Initializing Fake HWiNFO: {num_sensors} Sensors, {num_entries} Entries.")
        
        # 2. Prepare Handles
        sa = _create_security_attributes()
        sa_ptr = ctypes.byref(sa) if sa else None

        self.mutex_handle = self._kernel32.CreateMutexW(sa_ptr, False, HWiNFO_MUTEX_NAME)
        
        CreateFileMappingW = self._kernel32.CreateFileMappingW
        CreateFileMappingW.argtypes = [wintypes.HANDLE, ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR]
        CreateFileMappingW.restype = wintypes.HANDLE

        self.mapping_handle = CreateFileMappingW(
            wintypes.HANDLE(INVALID_HANDLE_VALUE), sa_ptr, PAGE_READWRITE, 0, total_size, HWiNFO_SHARED_MEM_PATH
        )
        
        creation_error = ctypes.GetLastError()

        if not self.mapping_handle:
            raise OSError(f"Failed to create file mapping: {creation_error}")

        MapViewOfFile = self._kernel32.MapViewOfFile
        MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
        MapViewOfFile.restype = wintypes.LPVOID

        self.map_addr = MapViewOfFile(self.mapping_handle, FILE_MAP_ALL_ACCESS, 0, 0, 0)
        if not self.map_addr:
            raise OSError("Failed to map view of file")

        # 3. Conflict Check
        if creation_error == ERROR_ALREADY_EXISTS:
            existing_header = HWiNFOHeader.from_address(self.map_addr)
            # Heuristic: Real HWiNFO usually has many sensors.
            if existing_header.magic == HWiNFO_HEADER_MAGIC and existing_header.sensor_element_count > 5:
                self.close()
                raise RuntimeError("Real HWiNFO64 detected! Close it before running this script.")
            else:
                print("Re-using existing shared memory block.")

        # 4. Map and Fill Data
        self.header = HWiNFOHeader.from_address(self.map_addr)
        self.header.magic = HWiNFO_HEADER_MAGIC
        self.header.version = 1
        self.header.version2 = 1
        self.header.sensor_section_offset = sensor_section_offset
        self.header.sensor_element_size = sensor_size
        self.header.sensor_element_count = num_sensors
        self.header.entry_section_offset = entry_section_offset
        self.header.entry_element_size = entry_size
        self.header.entry_element_count = num_entries

        # Fill Sensors
        for i, s_obj in enumerate(self.sensors):
            offset = self.map_addr + sensor_section_offset + (i * sensor_size)
            s_struct = HWiNFOSensor.from_address(offset)
            s_struct.id = s_obj.id
            s_struct.instance = s_obj.instance
            s_struct.name_original = s_obj.name.encode('utf-8')
            s_struct.name_user = s_obj.name.encode('utf-8')
            s_struct.name_unicode = s_obj.name.encode('utf-8')
            s_struct.sensor_type = s_obj.sensor_type
            s_obj._mapped_sensor = s_struct

        # Fill Entries
        current_entry_idx = 0
        for s_idx, s_obj in enumerate(self.sensors):
            for e_obj in s_obj.entries:
                offset = self.map_addr + entry_section_offset + (current_entry_idx * entry_size)
                e_struct = HWiNFOEntry.from_address(offset)
                e_struct.entry_type = e_obj.entry_type
                e_struct.sensor_index = s_idx
                e_struct.id = e_obj.id
                e_struct.name_original = e_obj.name.encode('utf-8')
                e_struct.name_user = e_obj.name.encode('utf-8')
                e_struct.name_unicode = e_obj.name.encode('utf-8')
                e_struct.reading_units = e_obj.units.encode('utf-8')
                e_struct.units_unicode = e_obj.units.encode('utf-8')
                # Initial Values
                e_struct.value = e_obj.value
                e_struct.value_min = e_obj.value_min
                e_struct.value_max = e_obj.value_max
                e_struct.value_avg = e_obj.value
                
                e_obj._mapped_entry = e_struct
                current_entry_idx += 1

        self.is_active = True
        self.update() # Initial flush
        print("Fake HWiNFO Interface Created successfully.")

    def update(self):
        """Flushes current python values to Shared Memory safely."""
        if not self.is_active:
            return

        self._kernel32.WaitForSingleObject(self.mutex_handle, 1000)
        try:
            self.header.last_update = int(time.time())
            
            # Efficiently update only values
            for s in self.sensors:
                for e in s.entries:
                    if e._mapped_entry:
                        e._mapped_entry.value = e.value
                        e._mapped_entry.value_min = e.value_min
                        e._mapped_entry.value_max = e.value_max
                        # We don't calc avg here to save CPU, but could if needed
        finally:
            self._kernel32.ReleaseMutex(self.mutex_handle)

    def close(self):
        self.is_active = False
        if self.map_addr:
            self._kernel32.UnmapViewOfFile(self.map_addr)
            self.map_addr = None
        if self.mapping_handle:
            self._kernel32.CloseHandle(self.mapping_handle)
            self.mapping_handle = None
        if self.mutex_handle:
            self._kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
