#!/usr/bin/env python3
"""Debug: Why are most tracks showing as EMPTY?"""

import struct
from pathlib import Path

track_dir = Path("output/fdmus_tracks")

# Test a few tracks
for idx in [0, 2, 5, 17]:
    track_file = track_dir / f"track_{idx:03d}.bin"
    with open(track_file, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    if evnt_pos < 0:
        print(f"track_{idx:03d}: No EVNT")
        continue
    
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    pos = evnt_pos + 8
    end = pos + chunk_size
    
    # Count events
    note_on = 0
    note_off = 0
    other = 0
    total = 0
    
    while pos < end and total < 100:
        # Parse delta
        delta = 0
        while pos < end:
            byte = data[pos]
            if byte >= 0x80:
                break
            pos += 1
            delta = (delta << 7) | byte
        
        if pos >= end:
            break
        
        status = data[pos]
        pos += 1
        total += 1
        
        if status == 0xFF:
            other += 1
            # Skip meta
            if pos < end:
                pos += 1  # type
                length = 0
                while pos < end:
                    byte = data[pos]
                    pos += 1
                    length = (length << 7) | byte
                    if not (byte & 0x80):
                        break
                pos += length
        elif status >= 0x80:
            cmd = status & 0xF0
            if cmd == 0x90:
                if pos + 1 < end:
                    vel = data[pos+1]
                    if vel > 0:
                        note_on += 1
                    else:
                        note_off += 1
                    pos += 2
            elif cmd == 0x80:
                note_off += 1
                pos += 2
            elif cmd in (0xA0, 0xB0, 0xE0):
                other += 1
                pos += 2
            elif cmd in (0xC0, 0xD0):
                other += 1
                pos += 1
        else:
            break
    
    print(f"track_{idx:03d}: {total} events, note_on={note_on}, note_off={note_off}, other={other}")
