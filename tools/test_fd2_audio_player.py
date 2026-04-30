#!/usr/bin/env python3
"""
FD2 FDMUS.DAT Audio Player Test Tool
Extracts and plays music from FDMUS.DAT
Supports: pygame (preferred) or pygame.midi fallback
"""

import struct
import os
import sys
from pathlib import Path

# Try to import pygame
try:
    import pygame
    HAS_PYGAME = True
    print("pygame available")
except ImportError:
    HAS_PYGAME = False
    print("pygame not installed - install with: pip install pygame")

def parse_fdmus_dat(filepath):
    """Parse FDMUS.DAT and extract all music resources"""
    print(f"\nParsing {filepath}...")
    
    with open(filepath, 'rb') as f:
        file_data = f.read()
    
    file_size = len(file_data)
    
    magic = file_data[:6]
    if magic != b'LLLLLL':
        print(f"Error: Invalid magic {magic}")
        return None
    
    resource_count = struct.unpack('<I', file_data[6:10])[0]
    print(f"  Resources: {resource_count}")
    print(f"  File size: {file_size:,} bytes")
    
    # Parse offset table
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack('<I', file_data[10 + i*4:14 + i*4])[0]
        offsets.append(offset)
    
    # Extract resources
    resources = []
    for i in range(resource_count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < resource_count else file_size
        size = end - start
        
        if start < 0 or start >= file_size or size <= 0:
            resources.append(None)
            continue
        
        if start + size > file_size:
            size = file_size - start
        
        resources.append(file_data[start:start+size])
    
    valid = [r for r in resources if r is not None]
    print(f"  Valid resources: {len(valid)}/{resource_count}")
    
    return resources

def analyze_resource(data, index):
    """Analyze resource format"""
    if data is None:
        return "None"
    
    size = len(data)
    
    if size < 10:
        return f"Small({size}B)"
    
    # Check for MIDI/XMIDI signatures
    if data[:4] == b'MThd':
        return "Standard MIDI"
    
    if data[:4] == b'FORM' and b'XDIR' in data[:100]:
        return "XMIDI (EA)"
    
    # XMIDI usually has FORM header
    if data[:4] == b'FORM':
        return "RIFF/FORM"
    
    # MDI format detection
    if size > 100:
        # Check for MIDI-like patterns
        zero_count = data.count(0)
        zero_ratio = zero_count / size
        
        # MIDI files typically have moderate zero ratio
        if 0.05 < zero_ratio < 0.4:
            return "MIDI/MDI"
        elif zero_ratio > 0.7:
            return f"Sparse data"
        else:
            return f"Binary data"
    
    return f"Unknown({size}B)"

def extract_to_files(resources, output_dir):
    """Extract resources to individual files"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExtracting tracks to {output_dir}...")
    extracted = 0
    
    for i, res in enumerate(resources):
        if res is None:
            continue
        
        output_file = output_dir / f"track_{i:03d}.bin"
        output_file.write_bytes(res)
        
        fmt = analyze_resource(res, i)
        print(f"  [{i:3d}] {len(res):6,} bytes - {fmt}")
        extracted += 1
    
    print(f"\nExtracted {extracted} tracks")
    return output_dir

def play_with_pygame(filepath):
    """Try to play using pygame.mixer.music"""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(str(filepath))
        pygame.mixer.music.play()
        
        print(f"\nPlaying: {filepath.name}")
        print("Press Ctrl+C to stop...")
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"Cannot play: {e}")
        return False

def play_track(resources, track_id, output_dir):
    """Play a specific track"""
    track_dir = Path(output_dir)
    track_file = track_dir / f"track_{track_id:03d}.bin"
    
    if not track_file.exists():
        print(f"\nTrack {track_id} not found")
        return False
    
    if not HAS_PYGAME:
        print(f"\npygame not installed - cannot play")
        print(f"File saved to: {track_file}")
        print(f"Try playing with: vlc {track_file}")
        return False
    
    print(f"\nAttempting to play track {track_id}...")
    print(f"Format: {analyze_resource(resources[track_id], track_id)}")
    
    # Try direct playback
    if play_with_pygame(track_file):
        return True
    
    # If direct playback fails, suggest conversion
    print(f"\nTrack may need conversion:")
    print(f"  - timidity {track_file}")
    print(f"  - vlc {track_file}")
    print(f"  - ffmpeg -i {track_file} -f wav track_{track_id}.wav")
    
    return False

def show_menu(resources):
    """Show interactive menu"""
    print("\n" + "="*70)
    print("FD2 FDMUS.DAT Music Player - Interactive Menu")
    print("="*70)
    
    print(f"\n{'ID':>4} {'Size':>8} {'Format':<20}")
    print("-" * 70)
    
    for i, res in enumerate(resources):
        if res is None:
            continue
        
        fmt = analyze_resource(res, i)
        print(f"[{i:3d}] {len(res):6,}B  {fmt:<20}")
    
    print(f"\nCommands:")
    print(f"  <number> - Play track (e.g., 0, 2, 5)")
    print(f"  a        - Play all tracks sequentially")
    print(f"  q        - Quit")
    
    return input("\nEnter command: ")

def play_all(resources, output_dir):
    """Play all tracks sequentially"""
    for i, res in enumerate(resources):
        if res is None:
            continue
        
        try:
            play_track(resources, i, output_dir)
        except KeyboardInterrupt:
            print("\nPlayback stopped")
            break

def main():
    fdmus_path = Path("game/FDMUS.DAT")
    output_dir = Path("output/fdmus_tracks")
    
    if not fdmus_path.exists():
        print(f"Error: {fdmus_path} not found")
        return
    
    # Parse and extract
    resources = parse_fdmus_dat(fdmus_path)
    if resources is None:
        return
    
    extract_to_files(resources, output_dir)
    
    # Interactive playback
    if HAS_PYGAME:
        while True:
            try:
                cmd = show_menu(resources)
                
                if cmd.lower() == 'q':
                    break
                elif cmd.lower() == 'a':
                    play_all(resources, output_dir)
                elif cmd.isdigit():
                    track_id = int(cmd)
                    if 0 <= track_id < len(resources):
                        play_track(resources, track_id, output_dir)
                    else:
                        print(f"Invalid track ID: {track_id}")
                else:
                    print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                print("\n\nStopped.")
                continue
            except EOFError:
                break
    else:
        print(f"\nTracks extracted to: {output_dir}")
        print("\nTo play tracks, install pygame:")
        print("  pip install pygame")
        print("\nOr use external players:")
        print("  vlc output/fdmus_tracks/track_000.bin")
        print("  timidity output/fdmus_tracks/track_000.bin")

if __name__ == "__main__":
    main()
