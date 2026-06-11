#!/usr/bin/env python
"""
完整测试所有FDOTHER资源解码
"""
import os
import struct
import zlib
from PIL import Image

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
output_dir = r"d:\workspace\fd2_dat_freebuff\output\all_resources_test"
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
palette_rgb = []
for i in range(256):
    r = palette[i*3]
    g = palette[i*3+1]
    b = palette[i*3+2]
    r8 = (r << 2) | (r >> 4)
    g8 = (g << 2) | (g >> 4)
    b8 = (b << 2) | (b >> 4)
    palette_rgb.append((r8, g8, b8))

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

def decode_sub_4E22A(src_data, w, h, pitch):
    """sub_4E22A解码"""
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

def get_all_divisors(n):
    pairs = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            pairs.append((i, n // i))
            if i != n // i:
                pairs.append((n // i, i))
    return sorted(pairs, key=lambda x: abs(x[0] - x[1]))

def save_image(filename, width, height, pixels, window=0):
    """保存为PNG"""
    img = Image.new('RGB', (width, height), (128, 128, 128))
    for y in range(height):
        for x in range(width):
            idx = pixels[y * width + x]
            if window:
                idx = (idx + window) & 0xFF
            if idx < 256:
                img.putpixel((x, y), palette_rgb[idx])
    img.save(filename)

# 测试每个索引
results = []
for idx in range(min(103, len(offsets) - 1)):
    start = offsets[idx]
    end = offsets[idx + 1]
    res_data = data[start:end]
    res_size = end - start

    result = {
        'index': idx,
        'size': res_size,
        'type': 'UNKNOWN'
    }

    # 检查是否是LMI1
    if res_size >= 6 and res_data[0:4] == b'LMI1':
        tile_count = struct.unpack('<H', res_data[4:6])[0]
        result['type'] = f'LMI1 ({tile_count} tiles)'

        # 解析偏移
        lmi1_offsets = []
        for i in range(tile_count + 1):
            off_pos = 6 + i * 4
            if off_pos + 4 > res_size:
                break
            off = struct.unpack('<I', res_data[off_pos:off_pos+4])[0]
            lmi1_offsets.append(off)

        if len(lmi1_offsets) >= 2:
            tile_size = lmi1_offsets[1] - lmi1_offsets[0]

            # 尝试最佳尺寸
            best_w, best_h = 16, tile_size // 16
            best_diff = abs(16 - tile_size // 16)
            for w, h in get_all_divisors(tile_size):
                if w <= 64 and h <= 64:
                    diff = abs(w - h)
                    if diff < best_diff or (diff == best_diff and w % 16 == 0):
                        best_w, best_h = w, h
                        best_diff = diff

            result['tile_size'] = f'{best_w}x{best_h}'

            # 只导出第一个tile
            if tile_count > 0 and lmi1_offsets[0] < res_size:
                off = lmi1_offsets[0]
                tile_data = res_data[off:off+tile_size]
                decoded = decode_sub_4EC66(tile_data, len(tile_data), best_w*best_h)
                while len(decoded) < best_w*best_h:
                    decoded.append(0)

                filename = os.path.join(output_dir, f"index{idx:03d}_lmi1.png")
                save_image(filename, best_w, best_h, decoded)

    # 检查是否是嵌套DAT
    elif res_size >= 6 and res_data[0:6] == b'LLLLLL':
        sub_count = struct.unpack('<I', res_data[6:10])[0]
        result['type'] = f'Nested DAT ({sub_count} resources)'

    # 检查是否是普通TILE
    elif res_size >= 4:
        w = struct.unpack('<H', res_data[0:2])[0]
        h = struct.unpack('<H', res_data[2:4])[0]
        if 0 < w <= 640 and 0 < h <= 480:
            result['type'] = f'TILE {w}x{h}'

            # 检查palette_window
            if res_size >= 8 and res_data[5] != 0:
                pw = res_data[4] | (res_data[5] << 8)
                header_size = 8
            else:
                pw = res_data[4] if res_size >= 5 else 0
                header_size = 5

            result['palette_window'] = pw

            # RLE数据
            rle_data = res_data[header_size:]
            rle_size = res_size - header_size

            # 解码
            decoded = decode_sub_4EC66(rle_data, rle_size, w*h)
            while len(decoded) < w*h:
                decoded.append(0)

            # 导出
            filename = os.path.join(output_dir, f"index{idx:03d}_tile.png")
            save_image(filename, w, h, decoded, pw)

    # 检查是否是索引1（24x24图标集）
    elif idx == 1:
        result['type'] = '24x24 Icons (20 icons)'

        # 解析偏移表
        icon_offsets = []
        pos = 6
        while pos + 4 <= res_size:
            off = struct.unpack('<I', res_data[pos:pos+4])[0]
            if off == 0 or off > res_size:
                break
            icon_offsets.append(off)
            pos += 4

        if icon_offsets:
            w, h = 24, 24
            # 创建组合图
            cols = 5
            rows = (len(icon_offsets) + cols - 1) // cols
            margin = 2
            img_w = cols * w + (cols + 1) * margin
            img_h = rows * h + (rows + 1) * margin

            img = Image.new('RGB', (img_w, img_h), (128, 128, 128))
            pw = res_data[4]

            for icon_idx, icon_off in enumerate(icon_offsets):
                icon_end = icon_offsets[icon_idx+1] if icon_idx+1 < len(icon_offsets) else res_size
                icon_data = res_data[icon_off:icon_end]
                decoded = decode_sub_4E22A(icon_data, w, h, w)

                row = icon_idx // cols
                col = icon_idx % cols
                x = margin + col * (w + margin)
                y = margin + row * (h + margin)

                for py in range(h):
                    for px in range(w):
                        idx = decoded[py * w + px]
                        idx = (idx + pw) & 0xFF
                        if idx < 256:
                            img.putpixel((x + px, y + py), palette_rgb[idx])

            filename = os.path.join(output_dir, f"index{idx:03d}_icons.png")
            img.save(filename)

    # 索引4是字体
    elif idx == 4:
        result['type'] = 'Font (1824 chars, 16x16)'

    results.append(result)

# 输出摘要
print("=" * 70)
print("FDOTHER资源解码测试结果")
print("=" * 70)

for r in results:
    if r['type'] != 'UNKNOWN':
        info = f"索引{r['index']:3d}: {r['type']}"
        if 'tile_size' in r:
            info += f" [{r['tile_size']}]"
        if 'palette_window' in r:
            info += f" [pw={r['palette_window']}]"
        print(info)

print("\n" + "=" * 70)
print(f"测试输出目录: {output_dir}")
print(f"共 {len([r for r in results if r['type'] != 'UNKNOWN'])} 个已识别资源")
