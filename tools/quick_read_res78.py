#!/usr/bin/env python3
"""
快速读取res78，检查格式
"""
import struct
import os

dat_path = os.path.join('game', 'FDOTHER.DAT')
with open(dat_path, 'rb') as f:
    data = f.read(100)
    print(f"FDOTHER.DAT前100字节:")
    for i in range(0, len(data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 尝试不同的头部解析
    print(f"\n头部解析尝试:")
    print(f"  *(0x0) [4B LE]: {struct.unpack_from('<I', data, 0)[0]}")
    print(f"  *(0x4) [4B LE]: {struct.unpack_from('<I', data, 4)[0]}")
    print(f"  *(0x8) [4B LE]: {struct.unpack_from('<I', data, 8)[0]}")
    print(f"  *(0xC) [4B LE]: {struct.unpack_from('<I', data, 12)[0]}")
    print(f"  *(0x10) [4B LE]: {struct.unpack_from('<I', data, 16)[0]}")
    
    # 文件大小
    f.seek(0, 2)
    file_size = f.tell()
    print(f"\n文件大小: {file_size} bytes (0x{file_size:x})")
