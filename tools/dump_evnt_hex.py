#!/usr/bin/env python3
"""
Dump raw EVNT bytes to understand format
"""

import struct
from pathlib import Path

fdmus_path = Path("game/FDMUS.DAT")
with open(fdmus_path, 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
offsets = [struct.unpack('<I', data[10 + i*4:14 + i*4])[0] for i in range(count)]

for track_idx in [0, 11]:
    start = offsets[track_idx]
    end = offsets[track_idx+1] if track_idx+1 < count else len(data)
    track_data = data[start:end]
    
    evnt_pos = track_data.find(b'EVNT')
    if evnt_pos < 0:
        continue
    
    chunk_size = struct.unpack('>I', track_data[evnt_pos+4:evnt_pos+8])[0]
    evnt_data = track_data[evnt_pos+8:evnt_pos+8+chunk_size]
    
    print(f"\nTrack {track_idx}: {chunk_size} bytes EVNT")
    print("="*60)
    
    # Show first 100 bytes as hex
    for i in range(0, min(200, len(evnt_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in evnt_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in evnt_data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
