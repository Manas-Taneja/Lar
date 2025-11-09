import sounddevice as sd
import numpy as np
import sys
import time

# --- SETTINGS ---
# Using YOUR settings that stopped the crashing:
MIC_DEVICE_INDEX = 8     
SAMPLE_RATE = 16000      
CHANNELS = 2             
BUFFER_DURATION_MS = 100 # We'll read 100ms of audio at a time
# ---

print("--- Starting Microphone Test (v5 - Readable) ---")
print(f"Using Device {MIC_DEVICE_INDEX} with {CHANNELS} channels at {SAMPLE_RATE}Hz")
print("\nBe silent to measure your 'noise floor'...")
print("Then, speak normally to measure your 'speaking volume'...")
print("\nPress Ctrl+C to stop.")

# Calculate number of frames for our buffer
frames_per_buffer = int((SAMPLE_RATE / 1000) * BUFFER_DURATION_MS)

try:
    with sd.InputStream(
        device=MIC_DEVICE_INDEX,
        channels=CHANNELS, 
        samplerate=SAMPLE_RATE, 
        dtype='int16'
    ) as stream:
        
        while True:
            # Read a chunk of audio
            indata, overflowed = stream.read(frames_per_buffer) 
            if overflowed:
                print("Warning: Audio buffer overflowed", file=sys.stderr)
            
            # This is the raw volume calculation
            volume_norm = np.linalg.norm(indata) * 10
            
            # --- Bar Graph Logic ---
            # You set this to 100, which is great.
            # I'll use a larger number just to keep the bar small.
            scaling_factor = 500 # Adjust this if the bar is too big/small
            max_bar_width = 50
            
            bar_length = int((volume_norm / scaling_factor) * max_bar_width)
            bar_length = min(bar_length, max_bar_width) # Clamp the bar
            
            bar = '#' * bar_length
            # --- End Bar Graph ---
            
            # Print the stable volume level
            print(f"Volume: {volume_norm:<10.2f} [{bar:<50}]", end='\r')
            
except KeyboardInterrupt:
    print("\nTest stopped.")
except Exception as e:
    print(f"\nAn error occurred on Device {MIC_DEVICE_INDEX}: {e}")