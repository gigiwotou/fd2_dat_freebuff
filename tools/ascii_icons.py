#!/usr/bin/env python
"""
ASCII可视化所有索引1的图标
"""
import os
import struct

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析FDOTHER偏移表
offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4
offsets.append(len(data))

idx1_start = offsets[1]
idx1_end = offsets[2]
idx1_data = data[idx1_start:idx1_end]

icon_offsets = []
pos = 6
while pos + 4 <= len(idx1_data):
    off = struct.unpack('<I', idx1_data[pos:pos+4])[0]
    if off == 0 or off > len(idx1_data):
        break
    icon_offsets.append(off)
    pos += 4

def decode_sub_4E22A(src_data, w, h, pitch):
    dst = bytearray(w * h)
    src_idx = 0
    dst_idx = 0

    n24 = h
    while n24 != 0:
        n24_1 = w

        while True:
            if src_idx >= len(src_data):
                return bytes(dst)

            value = src_data[src_idx]
            src_idx += 1

            v9 = (value << 1) & 0xFF

            if value & 0x80:
                count = (value << 2) & 0xFF

                if v9 & 0x80:
                    count = (count >> 2) + 1
                    dst_idx += count
                    n24_1 = (n24_1 - count) & 0xFF
                else:
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    for i in range(count):
                        if dst_idx < len(dst) and src_idx + i < len(src_data):
                            dst[dst_idx] = src_data[src_idx + i]
                        dst_idx += 1
                    src_idx += count
            else:
                if v9 & 0x80:
                    count = (value << 2) & 0xFF
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    n24_1 = (n24_1 - count) & 0xFF
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    for i in range(count):
                        dst_idx += 1
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1
                else:
                    count = (value << 2) & 0xFF
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    for i in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1

            if (n24_1 & 0xFF) == 0:
                break

        dst_idx += pitch - w
        n24 = (n24 - 1) & 0xFF

    return bytes(dst)

# 解码并显示所有图标
print("=" * 80)
print("索引1图标ASCII可视化 (24x24)")
print("=" * 80)

for i in range(len(icon_offsets)):
    icon_start = icon_offsets[i]
    icon_end = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(idx1_data)
    icon_data = idx1_data[icon_start:icon_end]
    decoded = decode_sub_4E22A(icon_data, 24, 24, 24)

    print(f"\n=== 图标 {i} (size={len(icon_data)} bytes) ===")
    for row in range(24):
        line = ""
        for col in range(24):
            v = decoded[row * 24 + col]
            if v == 0:
                line += " "
            elif v < 16:
                line += "."
            elif v < 32:
                line += ":"
            elif v < 64:
                line += "o"
            elif v < 128:
                line += "O"
            elif v < 192:
                line += "#"
            else:
                line += "@"
        print(f"  |{line}|")
