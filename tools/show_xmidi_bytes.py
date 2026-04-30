#!/usr/bin/env python3
"""
查看EVNT开始的原始字节，分析delta时间解析问题
"""

import struct
from pathlib import Path

def show_raw_bytes(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    evnt_pos = data.find(b'EVNT')
    chunk_size = struct.unpack('>I', data[evnt_pos+4:evnt_pos+8])[0]
    
    print(f"\n{filepath.name}")
    print(f"EVNT at: {evnt_pos:#x}, chunk_size: {chunk_size}")
    print(f"\nFirst 80 bytes of EVNT data:")
    
    evnt_data = data[evnt_pos+8:evnt_pos+8+min(80, chunk_size)]
    for i in range(0, len(evnt_data), 16):
        chunk = evnt_data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {evnt_pos+8+i:04X}: {hex_str:<48} {ascii_str}")
    
    print(f"\nByte-by-byte analysis:")
    for i, byte in enumerate(evnt_data[:40]):
        print(f"  [{i}] 0x{byte:02X} = {byte:3d}  {'delta' if byte < 0x80 else 'status/data'}")

def main():
    track_dir = Path("output/fdmus_tracks")
    for idx in [0, 2, 5, 11]:
        track_file = track_dir / f"track_{idx:03d}.bin"
        if track_file.exists():
            show_raw_bytes(track_file)

if __name__ == "__main__":
    main()
