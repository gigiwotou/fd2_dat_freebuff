#!/usr/bin/env python3
"""
Test MIDI playback for tracks 10, 11, 12
"""

import subprocess
import pygame
import time
from pathlib import Path

def test_midi_playback():
    pygame.mixer.init()
    pygame.init()
    
    midi_dir = Path('output/fdmus_midi_final')
    
    for track_num in [10, 11, 12]:
        midi_file = midi_dir / f'track_{track_num:03d}.mid'
        if not midi_file.exists():
            print(f"Track {track_num}: File not found")
            continue
        
        print(f"\n{'='*60}")
        print(f"Testing Track {track_num}")
        print(f"{'='*60}")
        print(f"File: {midi_file}")
        print(f"Size: {midi_file.stat().st_size} bytes")
        
        try:
            pygame.mixer.music.load(str(midi_file))
            pygame.mixer.music.play()
            print(f"Started playback...")
            
            # Play for 5 seconds then stop
            time.sleep(5)
            pygame.mixer.music.stop()
            print(f"Stopped after 5 seconds")
            
        except Exception as e:
            print(f"Error: {e}")
    
    pygame.quit()

if __name__ == '__main__':
    test_midi_playback()
