#!/usr/bin/env python3
"""Test pygame MIDI playback support"""

import pygame
import pygame.mixer

pygame.mixer.init()
pygame.init()

# Check what's available
print(f"mixer init: {pygame.mixer.get_init()}")
print(f"driver: {pygame.mixer.get_driver()}")
print(f"SDL version: {pygame.get_sdl_version()}")

# Try a simple wav first
print("\nTrying to play WAV (pygame supports this natively)...")

# Create a simple wav
import wave
import struct
import tempfile
import os

wav_path = os.path.join(tempfile.gettempdir(), "test.wav")
with wave.open(wav_path, 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(44100)
    # Create a simple beep
    for i in range(44100):
        value = int(32767 * 0.5 * ((i * 440 * 2 * 3.14159) % 44100 / 44100 - 0.5) * 2)
        wav_file.writeframes(struct.pack('<h', value))

print(f"Created test WAV: {wav_path}")

try:
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()
    import time
    time.sleep(0.5)
    if pygame.mixer.music.get_busy():
        print("WAV playback works!")
    else:
        print("WAV playback not working either")
    pygame.mixer.music.stop()
except Exception as e:
    print(f"WAV playback error: {e}")

pygame.quit()
os.unlink(wav_path)
