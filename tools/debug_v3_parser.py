#!/usr/bin/env python3
"""Debug V3 parser"""
import struct
from pathlib import Path

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

print(f"Track {track_idx}: {chunk_size} bytes")
print(f"\nFirst 100 bytes:")
for i in range(0, min(100, len(evnt_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
    print(f"  {i:04X}: {hex_str}")

# Simulate V3 parser
pos = 0
end = len(evnt_data)

# Step 1: Header parsing
print(f"\nStep 1: Header parsing (while byte==0xFF)")
header_count = 0

while pos < end and evnt_data[pos] == 0xFF:
    header_count += 1
    print(f"  pos={pos}: byte=0x{evnt_data[pos]:02X}")
    pos += 1
    meta_type = evnt_data[pos]
    pos += 1
    print(f"    -> meta_type=0x{meta_type:02X}")
    
    length = 0
    while pos < end:
        b = evnt_data[pos]
        pos += 1
        length = (length << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    print(f"    -> length={length}")
    
    if pos + length > end:
        print(f"    -> ERROR: exceeds end!")
        break
    
    pos += length
    print(f"    -> now at pos={pos}, byte=0x{evnt_data[pos]:02X}")

print(f"\nParsed {header_count} headers, ending at pos={pos}")

# Now parse events
print(f"\nStep 2: Event parsing")
running_status = None
event_count = 0

while pos < end and event_count < 10:
    # Read delta
    delta = 0
    delta_start = pos
    while pos < end:
        b = evnt_data[pos]
        pos += 1
        delta = (delta << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    print(f"  Event {event_count}: delta_start={delta_start}, delta={delta}")
    
    if pos >= end:
        break
    
    byte = evnt_data[pos]
    print(f"    byte at pos {pos}: 0x{byte:02X}")
    
    if byte >= 0x80:
        status = byte
        pos += 1
        running_status = status
        print(f"    -> new status: 0x{status:02X}")
    else:
        if running_status is None:
            print(f"    -> No running status, skipping")
            event_count += 1
            continue
        status = running_status
        print(f"    -> running status: 0x{status:02X}")
    
    status_type = status & 0xF0
    print(f"    -> status_type: 0x{status_type:02X}")
    
    if status_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
        data1 = evnt_data[pos]
        pos += 1
        data2 = evnt_data[pos]
        pos += 1
        print(f"    -> data: 0x{data1:02X}, 0x{data2:02X}")
        
        if status_type == 0x90:
            duration = 0
            while pos < end:
                b = evnt_data[pos]
                pos += 1
                duration = (duration << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            print(f"    -> Note On: note={data1}, vel={data2}, dur={duration}")
    
    elif status_type in (0xC0, 0xD0):
        data1 = evnt_data[pos]
        pos += 1
        print(f"    -> data: 0x{data1:02X}")
    
    event_count += 1
