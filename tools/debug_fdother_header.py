#!/usr/bin/env python
"""
查看FDOTHER的头部结构
"""

import os
import struct

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read(500)

print("FDOTHER.DAT 头部分析:\n")
print("前200字节:")
for i in range(0, 200, 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")

# 尝试不同的头部解析方式
print("\n\n可能的头部结构:")
print(f"[0-3]: {data[0:4]}")
print(f"[4-7]: {struct.unpack('<I', data[4:8])[0]}")
print(f"[8-11]: {struct.unpack('<I', data[8:12])[0]}")
print(f"[12-15]: {struct.unpack('<I', data[12:16])[0]}")

# 如果是LLLL格式
if data[0:4] == b'LLLL':
    print("\nLLLI格式:")
    num_resources = struct.unpack('<I', data[4:8])[0]
    print(f"  资源数量: {num_resources}")
    
    # 每个资源可能是8字节 (offset + size)
    print(f"\n资源索引表:")
    for i in range(min(10, num_resources)):
        entry_offset = 8 + i * 8
        if entry_offset + 8 > len(data):
            break
        off, size = struct.unpack('<II', data[entry_offset:entry_offset+8])
        print(f"  索引{i}: offset=0x{off:X}, size=0x{size:X}")
        
        # 如果offset看起来合理，读取一些数据
        if off > 0 and off < 0x339CD1 and size < 1000000:
            print(f"    前10字节: {' '.join(f'{b:02X}' for b in data[off:off+10])}")
