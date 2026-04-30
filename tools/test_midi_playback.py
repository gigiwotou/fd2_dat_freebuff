#!/usr/bin/env python3
"""
Test play converted MIDI files with pygame
"""

import pygame
import pygame.mixer
from pathlib import Path
import sys

def test_play_midi(midi_file):
    """Try to play a MIDI file with pygame"""
    print(f"\nTesting: {midi_file.name} ({midi_file.stat().st_size:,} bytes)")
    
    try:
        pygame.mixer.init()
        
        # Check if pygame can load this file
        pygame.mixer.music.load(str(midi_file))
        pygame.mixer.music.play()
        
        print(f"  SUCCESS - Now playing...")
        print(f"  Press Ctrl+C to stop")
        
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)
        
        pygame.mixer.quit()
        return True
        
    except pygame.error as e:
        print(f"  FAILED - pygame error: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n  Stopped")
        pygame.mixer.quit()
        return True

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    if not midi_dir.exists():
        print("Error: MIDI directory not found")
        return
    
    midi_files = sorted(midi_dir.glob("track_*.mid"))
    
    print(f"Found {len(midi_files)} MIDI files")
    print(f"\nTesting playback with pygame {pygame.version.ver}")
    
    success_count = 0
    
    for i, midi_file in enumerate(midi_files):
        try:
            if test_play_midi(midi_file):
                success_count += 1
        except Exception as e:
            print(f"  Exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(midi_files)} tracks played successfully")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
