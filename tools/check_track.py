#!/usr/bin/env python3
import struct
data=open('output/fdmus_tracks/track_000.bin','rb').read()
print(f'File size: {len(data)} bytes')
print(f'FORM at: {data.find(b"FORM")}')
print(f'XMID at: {data.find(b"XMID")}')
print(f'EVNT at: {data.find(b"EVNT")}')
print()
print('First 100 bytes hex:')
for i in range(0, 100, 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'  {i:04X}: {hex_str:<48} {ascii_str}')
