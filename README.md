# Fake HWiNFO Sensor SDK

A Python-based emulator for the HWiNFO64 Shared Memory interface. This project allows you to inject custom sensor data into applications that support HWiNFO (like **Aquasuite**, **Rainmeter**, **RTSS**, or **AIDA64**) without running the actual HWiNFO64 application.

It is particularly useful for:
*   Bridging data from unsupported devices (Arduino, ESP32, proprietary controllers) into Aquasuite/Rainmeter.
*   Testing themes/skins with predictable fake data.
*   Developing applications that consume HWiNFO data without needing the main app.

## ⚠️ Important Warning

**Conflict**: You **cannot** run the real HWiNFO64 and this Fake HWiNFO script simultaneously. They compete for the same Global Shared Memory block (`Global\HWiNFO_SENS_SM2`).
*   The script includes a safety check and will abort if it detects the real HWiNFO64 is running.
*   To use this, fully exit HWiNFO64 (including from the System Tray).

## Features

*   **Python API (`fake_hwinfo_api.py`)**: A clean, object-oriented API to define Sensors and Entries (Temp, Fan, Voltage, etc.) and update them programmatically.
*   **CLI Client (`read_hwinfo.py`)**: A simple tool to verify data is being exposed correctly.
*   **GUI Client (`gui_client.py`)**: A visual dashboard to see the values in real-time.
*   **Compatibility Tools**: Includes scripts to trick detection mechanisms (`fake_window.py`, `setup_registry.py`).

## Prerequisites

*   Windows OS (Shared Memory implementation is Windows-specific).
*   Python 3.x
*   Administrator Privileges (Required to create Global Shared Memory).
*   **Dependencies**:
    ```bash
    pip install pywin32
    ```

## Installation

1.  Clone this repository.
2.  Install dependencies: `pip install pywin32`.

## Quick Start (Demo)

To run the included demo which generates sine-wave temperature and fan speed data:

1.  **Registry Setup** (One-time, Admin required):
    ```powershell
    python setup_registry.py
    ```
    *This sets `SupportSharedMemory = 1` in the registry, which some apps check.*

2.  **Start the Fake Window** (Required for Aquasuite):
    ```powershell
    start /B python fake_window.py
    ```
    *Creates a hidden window with class `HWiNFO64`, satisfying `FindWindow` checks.*

3.  **Start the Fake Sensor**:
    ```powershell
    python fake_hwinfo.py
    ```

4.  **Verify**:
    *   Run `python gui_client.py` to see the data.
    *   Open your target app (e.g., Aquasuite). It should detect "Aquasuite Fake Sensor".

## Developer Guide: Creating Custom Sensors

You can use `fake_hwinfo_api.py` to bridge your own data sources.

### Example

```python
import time
from fake_hwinfo_api import FakeHWiNFO

# 1. Initialize
hwinfo = FakeHWiNFO()

# 2. Define Sensors & Entries
# Sensor Type 5 = Other/Custom
my_device = hwinfo.add_sensor(id=0xA000, name="My Custom Device", sensor_type=5)

# Entry Type 1 = Temperature
temp_sensor = my_device.add_entry(id=0xA001, name="Water Temp", units="°C", entry_type=1, value=25.0)

# Entry Type 3 = Fan
fan_sensor  = my_device.add_entry(id=0xA002, name="Pump Speed", units="RPM", entry_type=3, value=4500.0)

# 3. Create Shared Memory
# Must be done AFTER defining all sensors
hwinfo.create()

print("Broadcasting data...")

try:
    while True:
        # 4. Update Values
        # (Replace this with your actual data fetching logic)
        current_temp = get_temp_from_somewhere() 
        
        temp_sensor.set_value(current_temp)
        
        # 5. Flush to Shared Memory
        hwinfo.update()
        
        time.sleep(1)
finally:
    hwinfo.close()
```

### Sensor Types
| ID | Type |
| :--- | :--- |
| 1 | Temperature |
| 2 | Voltage |
| 3 | Fan |
| 4 | Current |
| 5 | Power |
| 6 | Clock |
| 7 | Usage |
| 8 | Other |

## Troubleshooting

*   **"Access Denied" or Error 5**: Run your terminal/IDE as **Administrator**.
*   **"Real HWiNFO64 detected"**: The script checks if the memory block already exists and has many sensors. Close the real HWiNFO64.
*   **Aquasuite doesn't see the sensor**:
    *   Ensure `fake_window.py` is running.
    *   Ensure a process named `HWiNFO64.exe` is running (you can rename `cmd.exe` to `HWiNFO64.exe` and leave it open if the fake window isn't enough).
    *   Restart the Aquasuite background service.

## Files

*   `fake_hwinfo_api.py`: **The Core Library**. Use this for your projects.
*   `fake_hwinfo.py`: A demo implementation using the library.
*   `read_hwinfo.py`: CLI reader for debugging.
*   `gui_client.py`: GUI reader for debugging.
*   `fake_window.py`: Window class emulator.
*   `setup_registry.py`: Registry helper.
*   `hwinfo_common.py`: C-struct definitions.

## License

MIT
