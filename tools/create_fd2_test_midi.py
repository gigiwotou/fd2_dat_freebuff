#!/usr/bin/env python3
"""
Create a test MIDI file using actual note data from track_000
This verifies if the player can handle multi-channel MIDI with real FD2 notes
"""

import struct
from pathlib import Path

def create_test_from_fd2():
    """Create MIDI with actual FD2 track notes"""
    
    # Header
    header = struct.pack('>4sIHHH', b'MThd', 6, 0, 1, 120)
    
    # Build track - use actual notes we found in track_000 analysis
    events = []
    
    # Tempo: 120 BPM
    events.append((0, 0xFF, 0x51, bytes([0x07, 0xA1, 0x20])))
    
    # Track name
    events.append((0, 0xFF, 0x03, b'FD2 Test'))
    
    # Program changes for different channels (from track_000)
    events.append((0, 0xC2, 50, 0))  # Ch 2: Orchestra Hit
    events.append((0, 0xC4, 57, 0))  # Ch 4: Trumpet
    
    # Simple melody using notes we found
    notes_data = [
        # (channel, note, velocity, duration)
        (9, 42, 105, 120),   # Drum
        (2, 74, 116, 120),   # Note D5
        (2, 72, 100, 120),   # Note C5
        (1, 40, 107, 120),   # Note E3
        (3, 69, 72, 120),    # Note A4
    ]
    
    # Play each note
    for ch, note, vel, dur in notes_data:
        # Note On
        events.append((0, 0x90 | ch, note, vel))
        # Note Off after duration
        events.append((dur, 0x90 | ch, note, 0))
    
    # End of Track
    events.append((0, 0xFF, 0x2F, b''))
    
    # Convert to binary
    track_data = b''
    for delta, status, b1, b2 in events:
        # Delta
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
    
    test_file = Path("output/fd2_test.mid")
    test_file.write_bytes(midi_data)
    
    print(f"Created: {test_file}")
    print(f"Size: {len(midi_data)} bytes")
    print(f"Content: 5 notes on channels 1,2,3,9")
    print(f"\nTest this file:")
    print(f"  vlc output/fd2_test.mid")

def main():
    create_test_from_fd2()
    
    print(f"\n{'='*60}")
    print(f"If this plays:")
    print(f"  -> Multi-channel MIDI works, problem is in full conversion")
    print(f"If this doesn't play:")
    print(f"  -> Problem might be with specific channels (ch 9 = drums)")

if __name__ == "__main__":
    main()
