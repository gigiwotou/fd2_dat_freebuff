#!/usr/bin/env python
"""
深入分析LMI1格式
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

# 索引13详细分析
idx = 13
start = offsets[idx]
end = offsets[idx + 1]
res_data = data[start:end]
res_size = end - start

print(f"索引 {idx}: {res_size} bytes")
print(f"起始位置: 0x{start:X}")

# 检查前100字节的原始数据
print("\n前100字节:")
for i in range(0, min(100, res_size), 16):
    chunk = res_data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04X}: {hex_str}  {ascii_str}")

# 检查偏移表
print("\n偏移表（前10个dword）:")
for i in range(min(10, (res_size - 6) // 4 + 1)):
    off_pos = 6 + i * 4
    if off_pos + 4 <= res_size:
        off_le = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
        off_be = struct.unpack('>I', res_data[off_pos:off_pos+4])[0]
        print(f"  [{i:2d}] LE=0x{off_le:06X} ({off_le:7d}), BE=0x{off_be:06X}")

# 尝试另一种解释：偏移可能是相对于资源起始+偏移6的位置
print("\n重新解析（假设偏移是相对于数据区起始）:")
data_start = 6  # 偏移表从字节6开始
tile_count = struct.unpack('<H', res_data[4:6])[0]
print(f"Tile count: {tile_count}")

# 打印偏移表位置的内容
print("\n偏移表区域原始内容:")
for i in range(tile_count + 1):
    off_pos = 6 + i * 4
    if off_pos + 4 <= res_size:
        off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
        print(f"  [{i:2d}] @ 0x{off_pos:X}: 0x{off:06X}")

# 索引6分析
print("\n" + "=" * 60)
idx = 6
start = offsets[idx]
end = offsets[idx + 1]
res_data = data[start:end]
res_size = end - start

print(f"索引 {idx}: {res_size} bytes")

print("\n前100字节:")
for i in range(0, min(100, res_size), 16):
    chunk = res_data[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"  {i:04X}: {hex_str}  {ascii_str}")

print("\n偏移表:")
tile_count = struct.unpack('<H', res_data[4:6])[0]
print(f"Tile count: {tile_count}")
for i in range(min(10, tile_count + 1)):
    off_pos = 6 + i * 4
    if off_pos + 4 <= res_size:
        off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
        print(f"  [{i:2d}] @ 0x{off_pos:X}: 0x{off:06X}")
