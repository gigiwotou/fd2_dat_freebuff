#!/usr/bin/env python
"""
调试LMI1 tile大小计算
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

# 检查LMI1头部
if res_data[0:4] == b'LMI1':
    tile_count = struct.unpack('<H', res_data[4:6])[0]
    print(f"  LMI1 magic: {res_data[0:4]}")
    print(f"  Tile count: {tile_count}")

    # 解析前10个偏移
    print("\n  前10个偏移:")
    for i in range(min(11, tile_count + 1)):
        off_pos = 6 + i * 4
        if off_pos + 4 <= res_size:
            off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
            print(f"    [{i:2d}] offset={off:6d} (0x{off:04X})")

    # 计算tile大小
    if tile_count >= 1:
        off0 = struct.unpack('<I', res_data[6:10])[0]
        if tile_count >= 2:
            off1 = struct.unpack('<I', res_data[10:14])[0]
        else:
            off1 = res_size
        tile_size = off1 - off0
        print(f"\n  Tile 0 起始: {off0}")
        print(f"  Tile 1 起始: {off1}")
        print(f"  Tile大小: {tile_size}")

        # 可能的尺寸
        print("\n  可能的尺寸组合:")
        for i in range(1, min(64, tile_size) + 1):
            if tile_size % i == 0:
                j = tile_size // i
                if j <= 64 and i <= 64:
                    print(f"    {i}x{j}")

# 检查索引6
print("\n" + "=" * 60)
idx = 6
start = offsets[idx]
end = offsets[idx + 1]
res_data = data[start:end]
res_size = end - start

print(f"索引 {idx}: {res_size} bytes")

if res_data[0:4] == b'LMI1':
    tile_count = struct.unpack('<H', res_data[4:6])[0]
    print(f"  LMI1 magic: {res_data[0:4]}")
    print(f"  Tile count: {tile_count}")

    print("\n  前5个偏移:")
    for i in range(min(6, tile_count + 1)):
        off_pos = 6 + i * 4
        if off_pos + 4 <= res_size:
            off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
            print(f"    [{i:2d}] offset={off:6d} (0x{off:04X})")

    if tile_count >= 2:
        off0 = struct.unpack('<I', res_data[6:10])[0]
        off1 = struct.unpack('<I', res_data[10:14])[0]
        tile_size = off1 - off0
        print(f"\n  Tile大小: {tile_size}")

        print("\n  可能的尺寸组合:")
        for i in range(1, min(64, tile_size) + 1):
            if tile_size % i == 0:
                j = tile_size // i
                if j <= 64 and i <= 64:
                    print(f"    {i}x{j}")
