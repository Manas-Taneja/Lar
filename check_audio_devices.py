import sounddevice as sd
import sys

print("--- Querying Audio Devices ---")

try:
    devices = sd.query_devices()
    print(devices)
    
    print("\n--- Specific Device Details ---")
    device_index = 8 # The device we care about
    
    if device_index >= len(devices):
        print(f"Error: Device index {device_index} is out of range.")
        print(f"Your system only has {len(devices)} devices (indexed 0 to {len(devices)-1}).")
    else:
        device = devices[device_index]
        print(f"\nDetails for Device #{device_index}:")
        print(f"  Name: {device['name']}")
        print(f"  Host API: {device['hostapi']}")
        print(f"  Max Input Channels: {device['max_input_channels']}")
        print(f"  Max Output Channels: {device['max_output_channels']}")
        print(f"  Default Sample Rate: {device['default_samplerate']}")

except Exception as e:
    print(f"An error occurred while querying devices: {e}")