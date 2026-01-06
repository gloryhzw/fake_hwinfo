from fake_hwinfo_api import FakeHWiNFO
import time
import math

def create_fake_sensor():
    hwinfo = FakeHWiNFO()

    # Define Topology
    sensor = hwinfo.add_sensor(id=0xf000, name="Aquasuite Fake Sensor", sensor_type=5, instance=1)
    temp_entry = sensor.add_entry(id=0xf001, name="Fake Temp", units="°C", entry_type=1, value=45.0)
    fan_entry = sensor.add_entry(id=0xf002, name="Fake Fan", units="RPM", entry_type=3, value=1200.0)

    try:
        hwinfo.create()
        print("Fake HWiNFO sensor started. Press Ctrl+C to stop.", flush=True)
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            v1 = 45.0 + 10.0 * math.sin(elapsed)
            v2 = 1200.0 + 100.0 * math.cos(elapsed)

            temp_entry.set_value(v1)
            fan_entry.set_value(v2)

            hwinfo.update()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping fake sensor.")
    finally:
        hwinfo.close()

if __name__ == "__main__":
    create_fake_sensor()
