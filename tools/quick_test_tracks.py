#!/usr/bin/env python3
"""
Quick test: Check FDMUS.DAT track format details
"""

import struct
from pathlib import Path

def analyze_track(filepath):
    """Detailed analysis of a track file"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*60}")
    print(f"File: {filepath.name}")
    print(f"Size: {len(data)} bytes")
    print(f"{'='*60}")
    
    # Show first 128 bytes in hex
    print("First 128 bytes:")
    for i in range(0, min(128, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48}  {ascii_str}")
    
    # Look for MThd anywhere in file
    midi_start = data.find(b'MThd')
    if midi_start >= 0:
        print(f"\n** Found 'MThd' at offset 0x{midi_start:X} **")
        # Parse MIDI header
        if midi_start + 14 <= len(data):
            hdr_size = struct.unpack('>I', data[midi_start+4:midi_start+8])[0]
            fmt = struct.unpack('>H', data[midi_start+8:midi_start+10])[0]
            ntrks = struct.unpack('>H', data[midi_start+10:midi_start+12])[0]
            division = struct.unpack('>H', data[midi_start+12:midi_start+14])[0]
            print(f"  Header size: {hdr_size}")
            print(f"  Format: {fmt}")
            print(f"  Tracks: {ntrks}")
            print(f"  Division: {division}")
    else:
        print("\nNo 'MThd' signature found")
    
    # Look for MTrk
    mtrk_pos = data.find(b'MTrk')
    if mtrk_pos >= 0:
        print(f"** Found 'MTrk' at offset 0x{mtrk_pos:X} **")

def main():
    track_dir = Path("output/fdmus_tracks")
    
    # Test a few representative tracks
    test_tracks = [
        "track_000.bin",  # XMIDI (FORM)
        "track_001.bin",  # Small (25 bytes)
        "track_005.bin",  # Medium XMIDI
        "track_033.bin",  # Largest (80KB)
    ]
    
    for track_name in test_tracks:
        track_file = track_dir / track_name
        if track_file.exists():
            analyze_track(track_file)
        else:
            print(f"Not found: {track_name}")

if __name__ == "__main__":
    main()
