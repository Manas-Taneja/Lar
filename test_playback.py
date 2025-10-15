# test_playback.py
import sounddevice as sd
import soundfile as sf

TEST_FILE = 'test_sound.wav'
OUTPUT_DEVICE = 'pipewire' # Use the device name we identified

try:
    # Set the default output device
    sd.default.device = OUTPUT_DEVICE
    
    print(f"Attempting to play '{TEST_FILE}' on device '{OUTPUT_DEVICE}'...")

    # Load the audio file
    data, fs = sf.read(TEST_FILE, dtype='float32')
    
    # Play the audio
    sd.play(data, fs)
    
    print("Playing... (This should take about 2 seconds)")
    sd.wait() # Wait for the sound to finish
    
    print("Playback finished.")
    print("\nSUCCESS: If you heard a piano sound, your audio output is working correctly.")

except Exception as e:
    print(f"\nERROR: An error occurred during playback.")
    print(e)