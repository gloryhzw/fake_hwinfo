import time
import math
import sys
from fake_hwinfo_api import FakeHWiNFO

def main():
    # 1. Initialize Manager
    hwinfo = FakeHWiNFO()

    # 2. Define Sensors
    # Sensor 1: Aquasuite Fake
    sensor1 = hwinfo.add_sensor(id=0xf000, name="Aquasuite Fake Sensor", sensor_type=5)
    
    # Add Entries to Sensor 1
    # Type 1=Temp, 3=Fan
    temp_entry = sensor1.add_entry(id=0xf001, name="Fake Temp", units="°C", entry_type=1, value=45.0)
    fan_entry = sensor1.add_entry(id=0xf002, name="Fake Fan", units="RPM", entry_type=3, value=1200.0)

    # 3. Create Interface
    try:
        hwinfo.create()
    except RuntimeError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Setup failed: {e}")
        return

    print("Fake Sensor Running. Press Ctrl+C to stop.")
    
    start_time = time.time()
    
    try:
        while True:
            # Generate fake data
            elapsed = time.time() - start_time
            
            # Sine wave 45 +/- 10
            new_temp = 45.0 + 10.0 * math.sin(elapsed)
            # Cosine wave 1200 +/- 100
            new_fan = 1200.0 + 100.0 * math.cos(elapsed)
            
            # Update Python objects
            temp_entry.set_value(new_temp)
            fan_entry.set_value(new_fan)
            
            # Flush to Shared Memory
            hwinfo.update()
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        hwinfo.close()

if __name__ == "__main__":
    main()