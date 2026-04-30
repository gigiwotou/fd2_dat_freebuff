#!/usr/bin/env python3
"""
Quick check: Compare original XMIDI with standard MIDI
"""

from pathlib import Path

def check_track(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*60}")
    print(f"File: {filepath.name} ({len(data)} bytes)")
    print(f"{'='*60}")
    
    # Show first 64 bytes
    print("First 64 bytes:")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Check for key signatures
    has_mthd = data[:4] == b'MThd'
    has_mtrk = b'MTrk' in data
    has_ff2f = b'\xFF\x2F\x00' in data
    
    print(f"\n  Has MThd: {has_mthd}")
    print(f"  Has MTrk: {has_mtrk}")
    print(f"  Has EndOfTrack: {has_ff2f}")
    
    if has_mthd:
        import struct
        hdr_size = struct.unpack('>I', data[4:8])[0]
        fmt = struct.unpack('>H', data[8:10])[0]
        ntrks = struct.unpack('>H', data[10:12])[0]
        div = struct.unpack('>H', data[12:14])[0]
        print(f"  Header size: {hdr_size}")
        print(f"  Format: {fmt}")
        print(f"  Tracks: {ntrks}")
        print(f"  Division: {div}")

def main():
    midi_dir = Path("output/fdmus_midi_v2")
    
    test_tracks = ["track_000.mid", "track_002.mid", "track_018.mid"]
    
    for track in test_tracks:
        track_file = midi_dir / track
        if track_file.exists():
            check_track(track_file)

if __name__ == "__main__":
    main()
