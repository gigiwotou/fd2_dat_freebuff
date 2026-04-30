#!/usr/bin/env python3
"""Dump FDOTHER.DAT header"""

import sys

def dump_fdother_header(filepath):
    with open(filepath, 'rb') as f:
        data = f.read(500)
    
    print(f"FDOTHER.DAT first 500 bytes:")
    for i in range(0, min(500, len(data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")

if __name__ == '__main__':
    dump_fdother_header(sys.argv[1] if len(sys.argv) > 1 else 'FDOTHER.DAT')
