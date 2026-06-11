#!/usr/bin/env python
"""
读取调色板，查看索引20的颜色
并对比Python和C的解码结果
"""

import os
import struct

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read()

# 索引0是调色板
# 前6字节是头部，后跟调色板数据
# FDOTHER索引0: 768字节 = 256个RGB颜色

# 找到索引0的偏移
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4
offsets.append(len(data))

# 索引0
idx0_start = offsets[0]
idx0_size = offsets[1] - idx0_start
print(f"Index 0 (palette): offset=0x{idx0_start:X}, size={idx0_size}")
print(f"First 16 bytes: {' '.join(f'{b:02X}' for b in data[idx0_start:idx0_start+16])}")

# 调色板
palette_data = data[idx0_start:idx0_start+min(768, idx0_size)]
print(f"\nPalette index 20 (used for index 1):")
if len(palette_data) >= 21*3:
    r = palette_data[20*3]
    g = palette_data[20*3+1]
    b = palette_data[20*3+2]
    print(f"  R={r} G={g} B={b}")
    # 转换为8bit
    r8 = (r << 2) | (r >> 4)
    g8 = (g << 2) | (g >> 4)
    b8 = (b << 2) | (b >> 4)
    print(f"  8bit: R={r8} G={g8} B={b8} = #${r8:02X}{g8:02X}{b8:02X}")

# 索引1的解码
idx1_start = offsets[1]
idx1_end = offsets[2]
idx1_data = data[idx1_start:idx1_end]

# 头部
print(f"\nIndex 1 header:")
print(f"  width={idx1_data[0] | (idx1_data[1] << 8)}")
print(f"  height={idx1_data[2] | (idx1_data[3] << 8)}")
print(f"  palette_window={idx1_data[4]}")

# 解析图标偏移
icon_offsets = []
pos = 6
while pos + 4 <= len(idx1_data):
    off = struct.unpack('<I', idx1_data[pos:pos+4])[0]
    if off == 0 or off > len(idx1_data):
        break
    icon_offsets.append(off)
    pos += 4

print(f"\nNumber of icons: {len(icon_offsets)}")
print(f"All offsets: {[hex(o) for o in icon_offsets]}")

# 解码每个图标
def decode_sub_4E22A(src_data):
    """严格按照汇编1:1实现"""
    dst = bytearray(24 * 24)
    src_idx = 0
    dst_idx = 0

    n24 = 24
    while n24 != 0:
        n24_1 = 24
        while True:
            if src_idx >= len(src_data):
                return bytes(dst)
            value = src_data[src_idx]
            src_idx += 1

            cl = (value << 1) & 0xFF

            if value & 0x80:
                cl = (cl << 1) & 0xFF
                count_val = (value << 2) & 0xFF
                if cl & 0x100:
                    # 跳过
                    count = (count_val >> 2) + 1
                    dst_idx += count
                    n24_1 = (n24_1 - count) & 0xFF
                else:
                    # 复制
                    count = (count_val >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    for i in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = src_data[src_idx + i]
                        dst_idx += 1
                    src_idx += count
            else:
                cl = (cl << 1) & 0xFF
                count_val = (value << 2) & 0xFF
                if cl & 0x100:
                    # 交替
                    count = (count_val >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    n24_1 = (n24_1 - count) & 0xFF
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    for _ in range(count):
                        dst_idx += 1
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1
                else:
                    # 填充
                    count = (count_val >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    for _ in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1

            if n24_1 == 0:
                break

        # 行结束
        # pitch = 24, so dst_idx += 0
        n24 = (n24 - 1) & 0xFF

    return bytes(dst)

# 解码每个图标
print("\n=== 解码所有图标 ===")
for i in range(min(20, len(icon_offsets))):
    icon_start = icon_offsets[i]
    icon_end = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(idx1_data)
    icon_data = idx1_data[icon_start:icon_end]

    decoded = decode_sub_4E22A(icon_data)

    # 统计非0像素
    non_zero = sum(1 for v in decoded if v != 0)
    total = len(decoded)
    print(f"\n图标{i}: size={len(icon_data)}, 非0像素={non_zero}/{total}")

    if i < 3:
        print(f"  像素矩阵 (前8行):")
        for row in range(8):
            row_data = decoded[row*24:(row+1)*24]
            print(f"    {row:2d}: {' '.join(f'{v:02X}' for v in row_data)}")
