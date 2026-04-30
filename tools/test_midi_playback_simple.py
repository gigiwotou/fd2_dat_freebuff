#!/usr/bin/env python3
"""Test MIDI playback to diagnose audio issues"""

import pygame
import pygame.mixer
from pathlib import Path
import time

pygame.mixer.init()
pygame.init()

midi_dir = Path("output/fdmus_midi_v3")
midi_files = sorted(midi_dir.glob("track_*.mid"))

if not midi_files:
    print("No MIDI files found in output/fdmus_midi_v3")
    exit()

print(f"Testing playback of: {midi_files[0].name}")

# Try loading
try:
    pygame.mixer.music.load(str(midi_files[0]))
    print("MIDI file loaded successfully")
except Exception as e:
    print(f"Failed to load MIDI: {e}")
    exit()

# Try playing
try:
    pygame.mixer.music.play()
    print("Playback started")
    
    # Wait and check status
    for i in range(3):
        time.sleep(1)
        busy = pygame.mixer.music.get_busy()
        print(f"  After {i+1}s: busy={busy}")
    
    pygame.mixer.music.stop()
    print("Playback stopped")
    
except Exception as e:
    print(f"Playback error: {e}")

pygame.quit()
