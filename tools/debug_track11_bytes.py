#!/usr/bin/env python3
"""Compare XMIDI bytes with V3 output"""
import struct
from pathlib import Path

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

print("XMIDI bytes (pos 40-60):")
for i in range(40, 70):
    if i < len(evnt_data):
        print(f"  {i:3d}: 0x{evnt_data[i]:02X}")

# Manual parse
print("\nManual parse from pos 40:")
pos = 40

# Headers end at 40, next bytes are events
# First check if we need to read delta
byte = evnt_data[pos]
print(f"Byte at pos {pos}: 0x{byte:02X}")

if byte >= 0x80:
    print("  -> Status byte (no delta)")
    status = byte
    pos += 1
    
    if status == 0xC3:
        data1 = evnt_data[pos]
        pos += 1
        print(f"  -> Program Ch3, prog=0x{data1:02X} ({data1})")
    
    byte = evnt_data[pos]
    print(f"Byte at pos {pos}: 0x{byte:02X}")
    if byte >= 0x80:
        status = byte
        pos += 1
        if status == 0xC4:
            data1 = evnt_data[pos]
            pos += 1
            print(f"  -> Program Ch4, prog=0x{data1:02X} ({data1})")
        
        byte = evnt_data[pos]
        print(f"Byte at pos {pos}: 0x{byte:02X}")
        if byte >= 0x80:
            status = byte
            pos += 1
            if status == 0xC5:
                data1 = evnt_data[pos]
                pos += 1
                print(f"  -> Program Ch5, prog=0x{data1:02X} ({data1})")
            
            byte = evnt_data[pos]
            print(f"Byte at pos {pos}: 0x{byte:02X}")
            if byte == 0xFF:
                pos += 1
                meta = evnt_data[pos]
                pos += 1
                print(f"  -> Meta type 0x{meta:02X}")
                
                if meta == 0x51:
                    length = evnt_data[pos]
                    pos += 1
                    print(f"  -> Length: {length}")
                    
                    tempo_data = evnt_data[pos:pos+length]
                    pos += length
                    tempo = (tempo_data[0] << 16) | (tempo_data[1] << 8) | tempo_data[2]
                    print(f"  -> Tempo: {tempo} (0x{tempo:06X})")
