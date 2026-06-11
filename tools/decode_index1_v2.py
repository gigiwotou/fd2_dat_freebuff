#!/usr/bin/env python
"""
严格按照汇编1:1实现sub_4E22A解码，并导出所有图标为PNG
"""
import os
import struct
import zlib

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
output_dir = r"d:\workspace\fd2_dat_freebuff\output\index1_icons"
os.makedirs(output_dir, exist_ok=True)

with open(fdother_path, 'rb') as f:
    data = f.read()

file_size = len(data)

# 解析FDOTHER偏移表
offsets = []
pos = 6
while pos + 4 <= file_size:
    off = struct.unpack('<I', data[pos:pos+4])[0]
    if off == 0 or off > file_size:
        break
    offsets.append(off)
    pos += 4
offsets.append(file_size)

# 索引0：调色板
idx0_start = offsets[0]
palette = data[idx0_start:idx0_start+768]

# 索引1：图标集
idx1_start = offsets[1]
idx1_end = offsets[2]
idx1_data = data[idx1_start:idx1_end]
idx1_size = idx1_end - idx1_start

print(f"Index 1 size: {idx1_size} bytes")

# 解析头部
width = struct.unpack('<H', idx1_data[0:2])[0]
height = struct.unpack('<H', idx1_data[2:4])[0]
palette_window = idx1_data[4]
icon_count_in_header = struct.unpack('<H', idx1_data[4:6])[0]

print(f"Header: width={width}, height={height}, palette_window={palette_window}, icon_count={icon_count_in_header}")

# 解析图标偏移表
icon_offsets = []
pos = 6
while pos + 4 <= len(idx1_data):
    off = struct.unpack('<I', idx1_data[pos:pos+4])[0]
    if off == 0 or off > len(idx1_data):
        break
    icon_offsets.append(off)
    pos += 4

print(f"Number of icons from offset table: {len(icon_offsets)}")

# 严格按汇编1:1实现sub_4E22A
def decode_sub_4E22A(src_data, w, h, pitch):
    """严格按照汇编1:1实现
    - 外层循环 n24 = h
    - 内层循环 n24_1 = w
    - count = ((value << 2) & 0xFF) >> 2 + 1 = (value & 0x3F) + 1
    """
    dst = bytearray(w * h)  # 注意：dst大小是w*h，不是pitch*h
    src_idx = 0
    dst_idx = 0  # 注意：汇编是直接操作dst指针

    n24 = h
    while n24 != 0:
        n24_1 = w

        while True:
            if src_idx >= len(src_data):
                # 数据不足，返回部分解码的结果
                return bytes(dst)

            value = src_data[src_idx]
            src_idx += 1

            v9 = (value << 1) & 0xFF

            # 汇编: __CFSHL__(value, 1) - 检查bit7
            if value & 0x80:
                # bit7=1
                # 汇编: __CFSHL__(v9, 1) - 检查bit6
                count = (value << 2) & 0xFF  # LOBYTE(count) = 4 * value

                if v9 & 0x80:
                    # bit6=1: SKIP模式
                    count = (count >> 2) + 1
                    dst_idx += count
                    n24_1 = (n24_1 - count) & 0xFF
                else:
                    # bit6=0: COPY模式
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    # qmemcpy(dst, src, count)
                    for i in range(count):
                        if dst_idx < len(dst) and src_idx + i < len(src_data):
                            dst[dst_idx] = src_data[src_idx + i]
                        dst_idx += 1
                    src_idx += count
            else:
                # bit7=0
                # 汇编: __CFSHL__(v9, 1) - 检查bit6
                if v9 & 0x80:
                    # bit6=1: ALTERNATE模式
                    count = (value << 2) & 0xFF
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    n24_1 = (n24_1 - count) & 0xFF  # 减了两次
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    # 汇编: do { v11 = dst + 1; *v11 = value; dst = v11 + 1; --count; } while (count);
                    for i in range(count):
                        dst_idx += 1  # inc edi
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1  # stosb
                else:
                    # bit6=0: FILL模式
                    count = (value << 2) & 0xFF
                    count = (count >> 2) + 1
                    n24_1 = (n24_1 - count) & 0xFF
                    pixel_value = src_data[src_idx]
                    src_idx += 1
                    # memset(dst, value, count)
                    for i in range(count):
                        if dst_idx < len(dst):
                            dst[dst_idx] = pixel_value
                        dst_idx += 1

            if (n24_1 & 0xFF) == 0:
                break

        # 行结束
        dst_idx += pitch - w
        n24 = (n24 - 1) & 0xFF

    return bytes(dst)

# PNG编码（简单实现）
def write_png(filename, width, height, pixels, palette_data, window=0):
    """写入8位调色板PNG"""
    def chunk(typ, data):
        crc = zlib.crc32(typ + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', crc)

    # 应用调色板窗口
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # filter byte
        for x in range(width):
            idx = pixels[y * width + x]
            if window:
                idx = (idx + window) & 0xFF
            raw_data.append(idx)

    # 调色板
    pal_data = bytearray()
    for i in range(256):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        # 6bit -> 8bit
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        pal_data.extend([r8, g8, b8])

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 3, 0, 0, 0)  # 8bit, palette
    plte = chunk(b'PLTE', pal_data)
    idat = chunk(b'IDAT', zlib.compress(bytes(raw_data)))
    iend = chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(sig + chunk(b'IHDR', ihdr) + plte + idat + iend)

# 解码并导出所有图标
print(f"\n=== 解码所有图标 ===")
results = []
for i in range(len(icon_offsets)):
    icon_start = icon_offsets[i]
    icon_end = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(idx1_data)
    icon_data = idx1_data[icon_start:icon_end]

    # 调用sub_4E22A - width=24, height=24, pitch=24
    decoded = decode_sub_4E22A(icon_data, 24, 24, 24)

    non_zero = sum(1 for v in decoded if v != 0)
    results.append((i, non_zero, decoded))
    print(f"图标{i}: size={len(icon_data)}, 非0像素={non_zero}/576")

    # 写入PNG
    png_file = os.path.join(output_dir, f"icon_{i:02d}.png")
    write_png(png_file, 24, 24, decoded, palette, palette_window)

# 写入组合图（大图，所有图标排列）
cols = 5
rows = (len(icon_offsets) + cols - 1) // cols
margin = 4
combo_w = cols * 24 + (cols + 1) * margin
combo_h = rows * 24 + (rows + 1) * margin
combo = bytearray(combo_w * combo_h)

for idx, (_, _, decoded) in enumerate(results):
    r = idx // cols
    c = idx % cols
    x0 = margin + c * (24 + margin)
    y0 = margin + r * (24 + margin)
    for y in range(24):
        for x in range(24):
            combo[(y0 + y) * combo_w + (x0 + x)] = decoded[y * 24 + x]

combo_file = os.path.join(output_dir, "all_icons.png")
write_png(combo_file, combo_w, combo_h, combo, palette, palette_window)
print(f"\n组合图: {combo_file}")
print(f"图标目录: {output_dir}")
