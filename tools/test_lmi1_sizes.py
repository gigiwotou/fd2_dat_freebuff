#!/usr/bin/env python
"""
测试LMI1 tile的不同尺寸组合
"""
import os
import struct
import zlib
from PIL import Image

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
output_dir = r"d:\workspace\fd2_dat_freebuff\output\lmi1_sizes_test"
os.makedirs(output_dir, exist_ok=True)

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

# 调色板
palette = data[offsets[0]:offsets[0]+768]

def decode_sub_4EC66(src, src_size, expected_count):
    """sub_4EC66解码"""
    dst = []
    ah = 0
    al = 0
    src_idx = 0

    while len(dst) < expected_count:
        if ah > 0:
            ah -= 1
            dst.append(al)
        else:
            if src_idx >= src_size:
                break
            al = src[src_idx]
            src_idx += 1

            if al > 0xC0:
                ah = al - 0xC1
                if src_idx < src_size:
                    al = src[src_idx]
                    src_idx += 1
                dst.append(al)
            else:
                dst.append(al)
                ah = 0

        if len(dst) >= expected_count:
            break

    return dst

def get_all_divisors(n):
    """获取n的所有因数对"""
    pairs = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            pairs.append((i, n // i))
            if i != n // i:
                pairs.append((n // i, i))
    return sorted(pairs, key=lambda x: abs(x[0] - x[1]))  # 按接近正方形排序

def palette_to_rgb(palette_data, window=0):
    """将6bit调色板转换为8bit"""
    rgb = []
    for i in range(256):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        rgb.append((r8, g8, b8))
    return rgb

def decode_and_save_combined(filename, lmi1_data, offsets_list, tile_size, palette_data, window=0):
    """解码并保存所有tile的组合图"""
    cols = min(8, len(offsets_list))
    rows = (len(offsets_list) + cols - 1) // cols

    # 尝试不同的尺寸
    candidates = get_all_divisors(tile_size)
    if not candidates:
        return

    # 只测试前几个候选尺寸
    best_dims = candidates[:3]

    for w, h in best_dims:
        # 创建大图
        margin = 2
        img_w = cols * w + (cols + 1) * margin
        img_h = rows * h + (rows + 1) * margin

        img = Image.new('RGB', (img_w, img_h), (128, 128, 128))
        rgb = palette_to_rgb(palette_data, window)

        for tile_idx, off in enumerate(offsets_list):
            if tile_idx >= len(offsets_list) - 1:
                break

            next_off = offsets_list[tile_idx + 1]
            tile_data = lmi1_data[off:next_off]

            decoded = decode_sub_4EC66(tile_data, len(tile_data), w*h)

            # 填充到目标大小
            while len(decoded) < w*h:
                decoded.append(0)

            # 计算位置
            row = tile_idx // cols
            col = tile_idx % cols
            x = margin + col * (w + margin)
            y = margin + row * (h + margin)

            # 绘制tile
            for py in range(h):
                for px in range(w):
                    idx = decoded[py * w + px]
                    if window:
                        idx = (idx + window) & 0xFF
                    if idx < 256:
                        img.putpixel((x + px, y + py), rgb[idx])

        # 保存
        out_file = os.path.join(output_dir, f"{filename}_w{w}_h{h}.png")
        img.save(out_file)
        print(f"  尺寸 {w}x{h}: {out_file}")

# 测试索引3
idx = 3
res_data = data[offsets[idx]:offsets[idx+1]]
res_size = offsets[idx+1] - offsets[idx]

print(f"索引 {idx}: {res_size} bytes")

# 解析LMI1
tile_count = struct.unpack('<H', res_data[4:6])[0]
print(f"  Tile数量: {tile_count}")

# 解析偏移
lmi1_offsets = []
for i in range(tile_count + 1):
    off_pos = 6 + i * 4
    if off_pos + 4 > res_size:
        break
    off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
    lmi1_offsets.append(off)

print(f"  偏移: {lmi1_offsets[:5]}...")

# 计算tile大小
tile_size = lmi1_offsets[1] - lmi1_offsets[0]
print(f"  Tile大小: {tile_size}")

# 可能的尺寸组合
candidates = get_all_divisors(tile_size)
print(f"  可能的尺寸: {candidates[:5]}")

# 解码并测试不同尺寸
print(f"\n索引 {idx} 测试:")
decode_and_save_combined(f"index{idx}", res_data, lmi1_offsets, tile_size, palette)

print(f"\n测试输出: {output_dir}")
