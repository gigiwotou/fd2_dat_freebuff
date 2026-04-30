#!/usr/bin/env python3
"""
Create a known-good test MIDI file and compare with converted files
"""

import struct
from pathlib import Path

def create_test_midi():
    """Create a simple, standard MIDI file that should play on any player"""
    
    # Header: Format 0, 1 track, 120 ticks/quarter
    header = struct.pack('>4sIHHH', b'MThd', 6, 0, 1, 120)
    
    # Build track data
    events = []
    
    # Tempo: 120 BPM (500000 microseconds per quarter)
    events.append((0, 0xFF, 0x51, bytes([0x07, 0xA1, 0x20])))
    
    # Track name
    events.append((0, 0xFF, 0x03, b'Test MIDI'))
    
    # Instrument: Acoustic Grand Piano (program 0)
    events.append((0, 0xC0, 0, 0))
    
    # Notes: C4, E4, G4, C5 (each 1 beat)
    notes = [60, 64, 67, 72]  # C4, E4, G4, C5
    
    for note in notes:
        # Note On
        events.append((0, 0x90, note, 80))
        # Note Off after 1 beat (120 ticks)
        events.append((120, 0x90, note, 0))
    
    # End of Track
    events.append((0, 0xFF, 0x2F, b''))
    
    # Convert to binary
    track_data = b''
    for delta, status, b1, b2 in events:
        # Delta (variable length)
        if delta == 0:
            track_data += bytes([0])
        else:
            vl = []
            vl.append(delta & 0x7F)
            delta >>= 7
            while delta > 0:
                vl.append(0x80 | (delta & 0x7F))
                delta >>= 7
            track_data += bytes(reversed(vl))
        
        # Event
        if status == 0xFF:
            track_data += bytes([0xFF, b1])
            if isinstance(b2, bytes):
                track_data += bytes([len(b2)]) + b2
            else:
                track_data += bytes([0])
        else:
            command = status & 0xF0
            if command in (0xC0, 0xD0):
                track_data += bytes([status, b1])
            else:
                track_data += bytes([status, b1, b2])
    
    track_header = struct.pack('>4sI', b'MTrk', len(track_data))
    
    midi_data = header + track_header + track_data
    
    test_file = Path("output/known_good.mid")
    test_file.write_bytes(midi_data)
    print(f"Created: {test_file}")
    print(f"Size: {len(midi_data)} bytes")
    print(f"Format: MIDI 0, 1 track, 120 ticks/quarter")
    print(f"Content: Tempo 120 BPM, Piano, Notes: C4 E4 G4 C5")
    print(f"\nTest this file first:")
    print(f"  vlc output/known_good.mid")
    print(f"  If this plays, then MIDI playback works")

def compare_with_converted():
    """Compare structure of converted file with known-good"""
    print(f"\n{'='*60}")
    print("Comparing MIDI files...")
    print(f"{'='*60}")
    
    known_good = Path("output/known_good.mid")
    converted = Path("output/fdmus_midi_v3/track_000.mid")
    
    if not converted.exists():
        return
    
    for label, filepath in [("Known Good", known_good), ("Converted", converted)]:
        if not filepath.exists():
            continue
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        print(f"\n{label} ({filepath.name}):")
        print(f"  Size: {len(data)}")
        print(f"  Header: {data[:14].hex(' ')}")
        
        # Check format
        if data[:4] == b'MThd':
            fmt = struct.unpack('>H', data[8:10])[0]
            ntrks = struct.unpack('>H', data[10:12])[0]
            div = struct.unpack('>H', data[12:14])[0]
            print(f"  Format: {fmt}")
            print(f"  Tracks: {ntrks}")
            print(f"  Division: {div}")
        
        # Check for MTrk
        mtrk_pos = data.find(b'MTrk')
        if mtrk_pos >= 0:
            track_size = struct.unpack('>I', data[mtrk_pos+4:mtrk_pos+8])[0]
            print(f"  Track size: {track_size}")
        
        # First few bytes of track
        if mtrk_pos >= 0:
            track_start = mtrk_pos + 8
            print(f"  Track start: {data[track_start:track_start+16].hex(' ')}")

def main():
    create_test_midi()
    compare_with_converted()
    
    print(f"\n{'='*60}")
    print("Next steps:")
    print(f"{'='*60}")
    print(f"1. Test known_good.mid first")
    print(f"2. If it plays, your player works")
    print(f"3. Then try track_000.mid from fdmus_midi_v3")
    print(f"4. If known_good plays but track_000 doesn't,")
    print(f"   the conversion has issues with the event data")

if __name__ == "__main__":
    main()
