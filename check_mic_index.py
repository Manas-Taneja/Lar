import pyaudio

pa = pyaudio.PyAudio()

print("--- PyAudio Input Devices ---")
print("Please find your microphone in this list and note its 'Index'.")

try:
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        # Check if it's an input device
        if dev.get('maxInputChannels') > 0:
            print(f"  Index {dev.get('index')}: {dev.get('name')} (Channels: {dev.get('maxInputChannels')})")
except Exception as e:
    print(f"An error occurred: {e}")
    print("This often happens if no microphones are connected.")
finally:
    print("-------------------------------")
    pa.terminate()

