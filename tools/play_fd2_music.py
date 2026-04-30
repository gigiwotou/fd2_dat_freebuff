#!/usr/bin/env python3
"""
FD2 FDMUS.DAT MIDI Player
Play extracted music tracks using pygame
"""

import pygame
import sys
from pathlib import Path

def play_track(track_file, track_name):
    """Play a single track"""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(str(track_file))
        pygame.mixer.music.play()
        
        print(f"\n{'='*60}")
        print(f"Now playing: {track_name}")
        print(f"File: {track_file}")
        print(f"{'='*60}")
        print("\nControls:")
        print("  Press Ctrl+C to stop and return to menu")
        print()
        
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)
        
        pygame.mixer.quit()
        return True
    except KeyboardInterrupt:
        print("\n\nPlayback stopped")
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        return False
    except Exception as e:
        print(f"Error playing track: {e}")
        return False

def show_menu(tracks):
    """Show track selection menu"""
    print("\n" + "="*60)
    print("FD2 FDMUS.DAT MIDI Player")
    print("="*60)
    print(f"\nAvailable tracks ({len(tracks)}):")
    print(f"  {'ID':<5} {'Size':<10} {'File':<30}")
    print(f"  {'-'*45}")
    
    for i, track in enumerate(tracks):
        size = track.stat().st_size
        print(f"  [{i:<3}] {size:<10,} {track.name}")
    
    print(f"\nCommands:")
    print(f"  <number>  - Play track (e.g., 0, 1, 2)")
    print(f"  a         - Play all tracks")
    print(f"  q         - Quit")
    
    return input("\nSelect track: ")

def play_all(tracks):
    """Play all tracks"""
    for i, track in enumerate(tracks):
        try:
            print(f"\n[{i}/{len(tracks)}] Playing: {track.name}")
            play_track(track, track.name)
        except KeyboardInterrupt:
            print("\nPlayback stopped")
            break

def main():
    midi_dir = Path("output/fdmus_midi")
    
    if not midi_dir.exists():
        print("Error: MIDI directory not found")
        print("Run convert_midi_to_midi.py first")
        return
    
    tracks = sorted(midi_dir.glob("track_*.mid"))
    
    if not tracks:
        print("No tracks found in output/fdmus_midi")
        return
    
    print(f"Found {len(tracks)} MIDI tracks")
    
    while True:
        try:
            cmd = show_menu(tracks)
            
            if cmd.lower() == 'q':
                print("Goodbye!")
                break
            elif cmd.lower() == 'a':
                play_all(tracks)
            elif cmd.isdigit():
                track_idx = int(cmd)
                if 0 <= track_idx < len(tracks):
                    play_track(tracks[track_idx], tracks[track_idx].name)
                else:
                    print(f"Invalid track ID: {track_idx}")
            else:
                print(f"Unknown command: {cmd}")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
    
    pygame.quit()

if __name__ == "__main__":
    main()
