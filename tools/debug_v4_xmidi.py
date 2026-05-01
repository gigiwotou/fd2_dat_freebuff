#!/usr/bin/env python3
"""Debug V4 XMIDI parsing"""
import struct
from pathlib import Path

def read_variable_length(data, pos):
    value = 0
    count = 0
    while count < 4 and pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        count += 1
        if not (byte & 0x80):
            break
    return value, pos

# Read XMIDI
fdmus_path = Path("game/FDMUS.DAT")
with open(fdmus_path, 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]

track_idx = 11
start = offsets[track_idx]
end = offsets[track_idx+1] if track_idx+1 < count else len(data)
track_data = data[start:end]

evnt_pos = track_data.find(b'EVNT')
chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]

print(f"XMIDI track {track_idx}: {chunk_size} bytes")
print(f"\nFirst 100 bytes:")
for i in range(0, min(100, len(evnt_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str}")

# Parse like V4
print(f"\nV4 parsing:")
pos = 0
end = len(evnt_data)
abs_tick = 0
running_status = None
event_count = 0

# Step 1: Header meta events
print("Headers (no delta):")
while pos < end and evnt_data[pos] == 0xFF:
    pos += 1
    meta_type = evnt_data[pos]
    pos += 1
    length, pos = read_variable_length(evnt_data, pos)
    pos += length
    print(f"  FF {meta_type:02X} len={length}")

print(f"\nAfter headers: pos={pos}")
print(f"Bytes: {' '.join(f'{b:02X}' for b in evnt_data[pos:pos+30])}")

# Step 2: Events
print(f"\nEvents:")
if pos < end and evnt_data[pos] >= 0x80:
    delta = 0
    print(f"First byte >= 0x80, delta=0")
else:
    delta, pos = read_variable_length(evnt_data, pos)
    print(f"Delta read: {delta}")

abs_tick = 0

while pos < end and event_count < 15:
    if delta is None:
        delta, pos = read_variable_length(evnt_data, pos)
        if pos >= end:
            break
    
    abs_tick += delta
    
    byte = evnt_data[pos]
    pos += 1
    
    if byte >= 0x80:
        status = byte
        running_status = status
        status_info = f"new 0x{status:02X}"
    else:
        if running_status is None:
            continue
        status = running_status
        status_info = f"running 0x{status:02X}"
    
    status_type = status & 0xF0
    
    if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        data1 = evnt_data[pos]
        pos += 1
        data2 = evnt_data[pos]
        pos += 1
        
        if status_type == 0x90:
            duration, pos = read_variable_length(evnt_data, pos)
            print(f"  [{event_count}] abs_tick={abs_tick} delta={delta} | {status_info} NoteOn Note={data1} Vel={data2} Dur={duration}")
        else:
            print(f"  [{event_count}] abs_tick={abs_tick} delta={delta} | {status_info} {status_type:02X} Data={data1} {data2}")
    
    elif status_type in (0xC0, 0xD0):
        data1 = evnt_data[pos]
        pos += 1
        print(f"  [{event_count}] abs_tick={abs_tick} delta={delta} | {status_info} {status_type:02X} Data={data1}")
    
    elif status == 0xFF:
        meta = evnt_data[pos]
        pos += 1
        length, pos = read_variable_length(evnt_data, pos)
        pos += length
        print(f"  [{event_count}] abs_tick={abs_tick} delta={delta} | {status_info} FF {meta:02X}")
    
    delta = None  # Reset for next iteration
    event_count += 1
