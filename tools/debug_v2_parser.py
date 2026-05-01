#!/usr/bin/env python3
"""Debug V2 parser step by step for track 11"""
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

print(f"Track {track_idx}: {chunk_size} bytes EVNT")
print(f"\nFirst 50 bytes hex:")
hex_str = ' '.join(f'{b:02X}' for b in evnt_data[:50])
print(f"  {hex_str}")

# Simulate V2 parser behavior
print(f"\nV2 Parser simulation:")
pos = 0
end = len(evnt_data)

# Step 1: Header meta events (no delta)
print("\nStep 1: Header meta parsing (no delta)")
while pos < end:
    byte = evnt_data[pos]
    print(f"  pos={pos}: byte=0x{byte:02X}")
    
    if byte != 0xFF:
        print(f"  -> Not FF, breaking header loop")
        break
    
    pos += 1
    meta_type = evnt_data[pos]
    pos += 1
    
    length = 0
    while pos < end:
        b = evnt_data[pos]
        pos += 1
        length = (length << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    
    if pos + length > end:
        print(f"  -> Length {length} exceeds end!")
        break
    
    pos += length
    
    print(f"  -> FF {meta_type:02X} len={length}, now at pos={pos}")

print(f"\nAfter header: pos={pos}, evnt_data[pos]=0x{evnt_data[pos]:02X}")

# Step 2: Now delta parsing
print("\nStep 2: Delta parsing")
# V2 reads delta from current position
delta = 0
while pos < end:
    b = evnt_data[pos]
    pos += 1
    delta = (delta << 7) | (b & 0x7F)
    print(f"  delta byte: 0x{b:02X}, delta so far: {delta}")
    if not (b & 0x80):
        break

print(f"  After delta: pos={pos}")

# Step 3: Status byte
print("\nStep 3: Status byte")
if pos < end:
    byte = evnt_data[pos]
    print(f"  byte at pos {pos}: 0x{byte:02X}")
    
    if byte >= 0x80:
        status = byte
        pos += 1
        print(f"  -> New status: 0x{status:02X}")
    else:
        print(f"  -> Running status needed, but none exists!")

# The issue is that V2 treats 0xC3 as a delta byte, not a status byte!
print(f"\n\n*** ROOT CAUSE ***")
print(f"V2 reads 0xC3 (195) as delta time: delta = 195")
print(f"Then reads 0x39 (57) as delta: delta = 195*128 + 57 = {195*128 + 57}")
print(f"Then 0xC4 has MSB=1 so continues: delta = {195*128+57}*128 + (0xC4 & 0x7F)")
print(f"This causes the parser to skip all the actual MIDI events!")
