#!/usr/bin/env python3
"""
Quick comparison: known_good vs new track_000
"""

import struct
from pathlib import Path

def check_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{filepath.name} ({len(data)} bytes):")
    
    # Show first 32 bytes
    print(f"  First 32: {data[:32].hex(' ')}")
    
    # Check for tempo
    has_tempo = b'\xFF\x51\x03\x07\xA1\x20' in data
    print(f"  Has Tempo: {has_tempo}")
    
    # First event after MTrk
    mtrk_pos = data.find(b'MTrk')
    track_start = data[mtrk_pos+8:mtrk_pos+20]
    print(f"  First events: {track_start.hex(' ')}")

def main():
    check_file(Path("output/known_good.mid"))
    check_file(Path("output/fdmus_midi_final/track_000.mid"))
    check_file(Path("output/fdmus_midi_final/track_005.mid"))

if __name__ == "__main__":
    main()
