#!/usr/bin/env python3
"""
Create a minimal test MIDI file to verify playback works
Then compare with our converted files
"""

import struct
from pathlib import Path

def create_test_midi():
    """Create a simple, known-good MIDI file"""
    
    # Header
    header = struct.pack('>4sIHHH',
                        b'MThd',
                        6,
                        0,  # Format 0
                        1,  # 1 track
                        120 # Division
                        )
    
    # Simple melody: C4, E4, G4, C5
    track_data = bytes([
        # Tempo: 120 BPM
        0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20,
        
        # Program Change: Acoustic Grand Piano
        0x00, 0xC0, 0x00,
        
        # C4 (note 60) on
        0x00, 0x90, 60, 80,
        0x3C, 0x90, 60, 0,  # Note off after 60 ticks
        0x00, 0x90, 64, 80,  # E4 on
        0x3C, 0x90, 64, 0,   # E4 off
        0x00, 0x90, 67, 80,  # G4 on
        0x3C, 0x90, 67, 0,   # G4 off
        0x00, 0x90, 72, 80,  # C5 on
        0x78, 0x90, 72, 0,   # C5 off
        
        # End of track
        0x00, 0xFF, 0x2F, 0x00
    ])
    
    track_header = struct.pack('>4sI', b'MTrk', len(track_data))
    
    midi_data = header + track_header + track_data
    
    test_file = Path("output/test_midi.mid")
    test_file.write_bytes(midi_data)
    print(f"Created test MIDI: {test_file}")
    print(f"Size: {len(midi_data)} bytes")
    
    return test_file

def compare_with_converted():
    """Compare our converted file with expected format"""
    converted = Path("output/fdmus_midi_v2/track_000.mid")
    
    if not converted.exists():
        return
    
    with open(converted, 'rb') as f:
        data = f.read()
    
    print(f"\nConverted file: {converted}")
    print(f"First 100 bytes:")
    for i in range(0, min(100, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    # Check for non-standard meta events
    print(f"\nLooking for meta events (FF XX)...")
    pos = 0
    while pos < len(data) - 2:
        if data[pos] == 0xFF or (pos > 0 and data[pos-1] == 0xFF):
            if pos + 2 < len(data):
                if data[pos] == 0xFF:
                    meta_type = data[pos+1]
                    print(f"  Offset {pos:04X}: Meta 0x{meta_type:02X}")
                    pos += 2
        pos += 1

def main():
    test_file = create_test_midi()
    compare_with_converted()
    
    print(f"\n{'='*60}")
    print("Test the minimal MIDI file first:")
    print(f"  vlc output/test_midi.mid")
    print(f"\nIf test_midi.mid plays but track_000.mid doesn't,")
    print(f"then the converted MIDI has incompatible events")

if __name__ == "__main__":
    main()
