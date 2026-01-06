import ctypes

# Constants
HWiNFO_SHARED_MEM_PATH = "Global\HWiNFO_SENS_SM2"
HWiNFO_HEADER_MAGIC = 0x48576953  # 'SiWH' (Classic)
# HWiNFO_HEADER_MAGIC = 0x53695748  # 'HWiS' (Newer)
HWiNFO_MEM_SIZE = 16 * 1024 * 1024 # 16MB Safe Size

# Corresponds to PACKED_STRUCT(struct HWiNFOHeader)
class HWiNFOHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("version2", ctypes.c_uint32),
        ("last_update", ctypes.c_int64),
        ("sensor_section_offset", ctypes.c_uint32),
        ("sensor_element_size", ctypes.c_uint32),
        ("sensor_element_count", ctypes.c_uint32),
        ("entry_section_offset", ctypes.c_uint32),
        ("entry_element_size", ctypes.c_uint32),
        ("entry_element_count", ctypes.c_uint32),
    ]

class HWiNFOSensor(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("instance", ctypes.c_uint32),
        ("name_original", ctypes.c_char * 128),
        ("name_user", ctypes.c_char * 128),
        ("name_unicode", ctypes.c_char * 128), # Observed 128 bytes here
    ]
    
class HWiNFOEntry(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("entry_type", ctypes.c_uint32),
        ("sensor_index", ctypes.c_uint32),
        ("id", ctypes.c_uint32),
        ("name_original", ctypes.c_char * 128),
        ("name_user", ctypes.c_char * 128),
        ("reading_units", ctypes.c_char * 16),
        ("value", ctypes.c_double),
        ("value_min", ctypes.c_double),
        ("value_max", ctypes.c_double),
        ("value_avg", ctypes.c_double),
        ("name_unicode", ctypes.c_char * 128),
        ("units_unicode", ctypes.c_char * 16),
    ]