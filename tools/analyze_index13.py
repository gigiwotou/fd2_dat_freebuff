#!/usr/bin/env python
"""
深入分析索引13、14、29的格式
"""
import struct

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析偏移表
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4
offsets.append(len(data))

# 检查索引13
idx = 13
start = offsets[idx]
end = offsets[idx + 1]
res_data = data[start:end]
res_size = end - start

print(f"索引 {idx}: {res_size} bytes")
print("\n前200字节:")
for i in range(0, min(200, res_size), 16):
    chunk = res_data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04X}: {hex_str}  {ascii_str}")

# 看看偏移122处是什么
print(f"\n偏移122处的内容（假设这是tile数据）:")
tile_start = 122
for i in range(0, min(100, res_size - tile_start), 16):
    chunk = res_data[tile_start + i:tile_start + i + 16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {tile_start + i:04X}: {hex_str}  {ascii_str}")

# 尝试另一种理解：跳过前122字节作为头部
print(f"\n前122字节作为头部后的数据:")
if res_size > 122:
    after_header = res_data[122:]
    for i in range(0, min(100, len(after_header)), 16):
        chunk = after_header[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {i:04X}: {hex_str}  {ascii_str}")

# 检查偏移44507（offset[1]）处
print(f"\n偏移44507处的内容:")
tile1_start = 44507
if res_size > tile1_start:
    for i in range(0, min(100, res_size - tile1_start), 16):
        chunk = res_data[tile1_start + i:tile1_start + i + 16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"  {tile1_start + i:04X}: {hex_str}  {ascii_str}")
