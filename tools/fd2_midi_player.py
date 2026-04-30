#!/usr/bin/env python3
"""
FD2 MIDI Player Test
Play converted MIDI files using pygame
"""

import pygame
import pygame.mixer
from pathlib import Path
import time

def play_midi(filepath, duration=10):
    print(f"\nPlaying: {filepath}")
    
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.init()
    
    try:
        pygame.mixer.music.load(str(filepath))
        pygame.mixer.music.play()
        
        print(f"Playing for {duration} seconds...")
        for i in range(duration):
            print(f"  {duration-i}s remaining...")
            time.sleep(1)
        
        pygame.mixer.music.stop()
        print("Playback complete")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pygame.quit()

def main():
    midi_dir = Path("output/fdmus_midi_v3")
    midi_files = sorted(midi_dir.glob("track_*.mid"))
    
    print(f"Found {len(midi_files)} MIDI files:")
    for i, f in enumerate(midi_files):
        size = f.stat().st_size
        print(f"  [{i}] {f.name} ({size} bytes)")
    
    if not midi_files:
        print("No MIDI files found")
        return
    
    try:
        cmd = input("\nSelect track to play (number), or 'a' for all: ").strip()
        
        if cmd.lower() == 'a':
            for i, midi in enumerate(midi_files):
                print(f"\n{'='*60}")
                print(f"Now playing: {midi.name}")
                play_midi(midi, duration=8)
        elif cmd.isdigit():
            idx = int(cmd)
            if 0 <= idx < len(midi_files):
                play_midi(midi_files[idx], duration=15)
            else:
                print(f"Invalid track number")
    except KeyboardInterrupt:
        print("\nStopped")

if __name__ == "__main__":
    main()
