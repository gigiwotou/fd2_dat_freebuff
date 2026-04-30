#!/usr/bin/env python3
"""
Create a definitive test MIDI with known-good notes
C4 (60), E4 (64), G4 (67) with proper velocity
"""

import struct
from pathlib import Path

def create_definitive_test():
    """Create MIDI with guaranteed playable notes"""
    
    # Header
    header = struct.pack('>4sIHHH', b'MThd', 6, 0, 1, 120)
    
    events = []
    
    # Tempo: 120 BPM
    events.append((0, 0xFF, 0x51, bytes([0x07, 0xA1, 0x20])))
    
    # Instrument: Piano on channel 0
    events.append((0, 0xC0, 0, 0))
    
    # Standard notes in MIDI range
    # C4 (60), D4 (62), E4 (64), F4 (65), G4 (67)
    notes = [60, 62, 64, 65, 67]
    
    for note in notes:
        # Note On (channel 0, velocity 80)
        events.append((0, 0x90, note, 80))
        # Note Off after 1 beat
        events.append((120, 0x90, note, 0))
    
    # End of Track
    events.append((0, 0xFF, 0x2F, b''))
    
    # Convert to binary
    track_data = b''
    for delta, status, b1, b2 in events:
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
    
    test_file = Path("output/definitive_test.mid")
    test_file.write_bytes(midi_data)
    
    print(f"Created: {test_file}")
    print(f"Size: {len(midi_data)} bytes")
    print(f"Notes: C4(60) D4(62) E4(64) F4(65) G4(67)")
    print(f"Velocity: 80")
    print(f"Channel: 0")
    print(f"Instrument: Piano")
    print(f"\nThis should DEFINITELY play if MIDI works at all")
    print(f"Test: vlc output/definitive_test.mid")

if __name__ == "__main__":
    create_definitive_test()
