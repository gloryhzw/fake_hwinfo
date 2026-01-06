import mmap
import ctypes
import sys
import time
from hwinfo_common import (
    HWiNFOHeader, HWiNFOSensor, HWiNFOEntry,
    HWiNFO_SHARED_MEM_PATH, HWiNFO_HEADER_MAGIC, HWiNFO_MEM_SIZE
)

def read_shared_memory():
    try:
        shm = mmap.mmap(-1, HWiNFO_MEM_SIZE, tagname=HWiNFO_SHARED_MEM_PATH)
        
    except FileNotFoundError:
        print(f"Error: Shared memory '{HWiNFO_SHARED_MEM_PATH}' not found.")
        print("Make sure 'fake_hwinfo.py' is running!")
        return

    header = HWiNFOHeader.from_buffer(shm, 0)
    
    if header.magic != HWiNFO_HEADER_MAGIC:
        print(f"Invalid Magic: 0x{header.magic:08X}! Expected: 0x{HWiNFO_HEADER_MAGIC:08X}")
        return

    print("Found HWiNFO Shared Memory!")
    print(f"Sensors: {header.sensor_element_count}, Entries: {header.entry_element_count}")

    try:
        while True:
            # Move cursor to start of loop
            print("\033[H\033[J", end="") # Clear screen (ANSI)
            print(f"Last Update: {header.last_update}")
            print("-" * 40)
            
            for i in range(header.entry_element_count):
                offset = header.entry_section_offset + (i * header.entry_element_size)
                entry = HWiNFOEntry.from_buffer(shm, offset)
                
                s_name = "Unknown"
                s_idx = entry.sensor_index
                if s_idx < header.sensor_element_count:
                    s_offset = header.sensor_section_offset + (s_idx * header.sensor_element_size)
                    s = HWiNFOSensor.from_buffer(shm, s_offset)
                    s_name = s.name_unicode.decode('utf-8', 'ignore').rstrip('\x00')
                
                e_name = entry.name_unicode.decode('utf-8', 'ignore').rstrip('\x00')
                e_unit = entry.reading_units.decode('utf-8', 'ignore').rstrip('\x00')
                
                print(f"[{s_name}] {e_name}: {entry.value:.2f} {e_unit}")

            print("-" * 40)
            print("Press Ctrl+C to exit.")
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        # Avoid BufferError: cannot close exported pointers exist
        # We need to delete the references to the buffer before closing shm
        del header
        shm.close()

if __name__ == "__main__":
    read_shared_memory()