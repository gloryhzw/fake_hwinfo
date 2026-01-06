import winreg

def set_hwinfo_registry():
    keys_to_set = [
        (winreg.HKEY_CURRENT_USER, r"Software\HWiNFO64\Sensors"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\HWiNFO64\Sensors")
    ]
    
    for hkey, subkey in keys_to_set:
        try:
            # Create or Open Key
            key = winreg.CreateKey(hkey, subkey)
            # Set "SupportSharedMemory" to 1
            winreg.SetValueEx(key, "SupportSharedMemory", 0, winreg.REG_DWORD, 1)
            print(f"Successfully set {hkey}\\{subkey}\\SupportSharedMemory = 1")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to set registry key {subkey}: {e}")

if __name__ == "__main__":
    set_hwinfo_registry()