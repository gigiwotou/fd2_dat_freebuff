#!/usr/bin/env python3
"""Debug track 11 events"""
import struct
from pathlib import Path

def read_variable_length(data, pos):
    value = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos

v4_file = Path("output/fdmus_midi_v4/track_011.mid")
with open(v4_file, 'rb') as f:
    data = f.read()

# Skip headers
pos = 14 + 8
track_len = struct.unpack('>I', data[18:22])[0]
track_end = pos + track_len

print(f"Track length: {track_len}, Track data: pos {pos} to {track_end}")

events = []
abs_tick = 0
running_status = None

while pos < track_end:
    start_pos = pos
    delta, pos = read_variable_length(data, pos)
    abs_tick += delta
    
    if pos >= track_end:
        break
    
    byte = data[pos]
    pos += 1
    
    if byte >= 0x80:
        status = byte
        running_status = status
    else:
        status = running_status
    
    if status is None:
        continue
    
    status_type = status & 0xF0
    
    if status == 0xFF:
        meta = data[pos]
        pos += 1
        length, pos = read_variable_length(data, pos)
        pos += length
        if meta == 0x2F:
            print(f"End of Track at abs_tick={abs_tick}")
            break
    elif status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        data1 = data[pos]
        data2 = data[pos+1]
        pos += 2
        
        if status_type == 0x90:
            events.append((abs_tick, 'note_on', data1, data2))
        elif status_type == 0x80:
            events.append((abs_tick, 'note_off', data1, data2))
    elif status_type in (0xC0, 0xD0):
        data1 = data[pos]
        pos += 1
        events.append((abs_tick, 'program', data1, 0))

print(f"Total events: {len(events)}")
print(f"First 10 events:")
for i, (tick, etype, d1, d2) in enumerate(events[:10]):
    print(f"  [{i}] tick={tick}, type={etype}, data={d1}, {d2}")

print(f"\nLast 10 events:")
for i, (tick, etype, d1, d2) in enumerate(events[-10:]):
    print(f"  [{len(events)-10+i}] tick={tick}, type={etype}, data={d1}, {d2}")

print(f"\nMax tick: {max(t for t, _, _, _ in events)}")
print(f"Min tick: {min(t for t, _, _, _ in events)}")
