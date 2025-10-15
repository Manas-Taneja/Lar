# check_audio_devices.py
import sounddevice as sd

print("Querying audio devices...")
print(sd.query_devices())