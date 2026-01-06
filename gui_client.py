import tkinter as tk
from tkinter import ttk
import mmap
import ctypes
import time
from hwinfo_common import (
    HWiNFOHeader, HWiNFOSensor, HWiNFOEntry,
    HWiNFO_SHARED_MEM_PATH, HWiNFO_HEADER_MAGIC, HWiNFO_MEM_SIZE
)

class HWiNFOViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fake HWiNFO64 Viewer")
        self.geometry("600x400")
        
        self.tree = ttk.Treeview(self, columns=("Sensor", "Value", "Unit"), show="headings")
        self.tree.heading("Sensor", text="Sensor / Entry Name")
        self.tree.heading("Value", text="Value")
        self.tree.heading("Unit", text="Unit")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.shm = None
        self.connect_shm()
        self.update_data()

    def connect_shm(self):
        try:
            self.shm = mmap.mmap(-1, HWiNFO_MEM_SIZE, tagname=HWiNFO_SHARED_MEM_PATH)
            self.header = HWiNFOHeader.from_buffer(self.shm, 0)
            if self.header.magic != HWiNFO_HEADER_MAGIC:
                print("Invalid Magic")
                self.shm = None
        except FileNotFoundError:
            print("Shared memory not found")
            self.shm = None

    def update_data(self):
        if not self.shm:
            self.connect_shm()
            if not self.shm:
                self.after(1000, self.update_data)
                return

        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            # Read Header
            num_sensors = self.header.sensor_element_count
            num_entries = self.header.entry_element_count
            
            # Map Sensors for lookup by index
            sensors = []
            for i in range(num_sensors):
                offset = self.header.sensor_section_offset + (i * self.header.sensor_element_size)
                s = HWiNFOSensor.from_buffer(self.shm, offset)
                # Decode and strip null bytes
                name = s.name_unicode.decode('utf-8', 'ignore').rstrip('\x00')
                sensors.append(name)

            # Read Entries
            for i in range(num_entries):
                offset = self.header.entry_section_offset + (i * self.header.entry_element_size)
                e = HWiNFOEntry.from_buffer(self.shm, offset)
                
                s_idx = e.sensor_index
                s_name = sensors[s_idx] if s_idx < len(sensors) else "Unknown"
                
                e_name = e.name_unicode.decode('utf-8', 'ignore').rstrip('\x00')
                e_unit = e.reading_units.decode('utf-8', 'ignore').rstrip('\x00')
                
                # Insert into tree
                self.tree.insert("", "end", values=(f"[{s_name}] {e_name}", f"{e.value:.2f}", e_unit))

        except Exception as e:
            print(f"Error reading shm: {e}")

        self.after(1000, self.update_data)

if __name__ == "__main__":
    app = HWiNFOViewer()
    app.mainloop()
