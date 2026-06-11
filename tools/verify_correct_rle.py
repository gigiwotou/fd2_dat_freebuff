#!/usr/bin/env python3
"""
验证正确的RLE解码与C代码实现
"""
import struct
from PIL import Image
import os
import ctypes

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/verify_correct_rle"
os.makedirs(output_dir, exist_ok=True)

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    if offset0 + size > len(file_data):
        size = len(file_data) - offset0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

def decompress_sub_4E98D(src_data, width, height, stride, value_1=-1):
    """精确实现sub_4E98D的RLE解压缩"""
    output_size = stride * height
    output = bytearray(output_size)

    src_pos = 0
    src_len = len(src_data)

    row_start = 0
    col_pos = 0
    current_row = 0

    while current_row < height and src_pos < src_len:
        ctrl = src_data[src_pos]
        src_pos += 1

        count = (ctrl & 0x3F) + 1

        if ctrl & 0x80:
            if ctrl & 0x40:
                col_pos += count
            else:
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = src_data[src_pos]
                        src_pos += 1
                        out_pos = row_start + col_pos

                        if value_1 == -1:
                            output[out_pos] = pixel
                        elif value_1 > 0xFF:
                            modified = value_1 + (((value_1 >> 8) + pixel) & 7)
                            output[out_pos] = modified & 0xFF
                        else:
                            output[out_pos] = value_1 & 0xFF

                        col_pos += 1
        else:
            if src_pos < src_len:
                fill_value = src_data[src_pos]
                src_pos += 1

                if value_1 == -1:
                    fill_byte = fill_value
                elif value_1 > 0xFF:
                    fill_byte = (value_1 + (((value_1 >> 8) + fill_value) & 7)) & 0xFF
                else:
                    fill_byte = value_1 & 0xFF

                for i in range(count):
                    if col_pos < width:
                        out_pos = row_start + col_pos
                        output[out_pos] = fill_byte
                        col_pos += 1

        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0

    return bytes(output)


def apply_palette_window(pixels, window_offset):
    """应用调色板窗口技术"""
    return [(window_offset + p) & 0xFF for p in pixels]


with open(dat_path, 'rb') as f:
    data = f.read()

# 加载主调色板
palette_data, _, _ = read_dat_resource(data, 0, 0)
if palette_data:
    palette_rgb = []
    for i in range(256):
        r = palette_data[i * 3]
        g = palette_data[i * 3 + 1]
        b = palette_data[i * 3 + 2]
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette_rgb.append((r, g, b))
else:
    palette_rgb = [(i, i, i) for i in range(256)]

print("验证正确的RLE解码")
print("=" * 70)

# 测试1: 索引11 (320x200全屏图像)
print("\n[测试1] 索引 11: 320x200 全屏图像")
idx = 11
res_data, _, res_size = read_dat_resource(data, 0, idx)
if res_data:
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    rle_data = res_data[4:]
    print(f"  尺寸: {w}x{h}, RLE大小: {len(rle_data)}")

    decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
    print(f"  解码: {len(decompressed)}/{w*h} 像素")

    if len(decompressed) >= w * h:
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                pal_idx = decompressed[px_idx]
                img.putpixel((x, y), palette_rgb[pal_idx])

        img_path = os.path.join(output_dir, f"test1_idx11_{w}x{h}.png")
        img.save(img_path)
        print(f"  保存: {img_path}")

        # 统计
        unique = len(set(decompressed[:w*h]))
        print(f"  唯一像素值: {unique}")

# 测试2: 嵌套DAT 7 的 tile 1
print("\n[测试2] 嵌套DAT 7, tile 1")
idx = 7
nested_data, _, _ = read_dat_resource(data, 0, idx)
if nested_data and len(nested_data) >= 10:
    res_count = struct.unpack_from('<I', nested_data, 6)[0]
    print(f"  子资源数: {res_count}")

    tile_offset_addr = 10 + 1 * 4
    tile_offset = struct.unpack_from('<I', nested_data, tile_offset_addr)[0]
    tile_data = nested_data[tile_offset:]

    if len(tile_data) >= 5:
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        window_offset = tile_data[4]
        rle_data = tile_data[5:]

        print(f"  tile尺寸: {w}x{h}")
        print(f"  调色板窗口偏移: 0x{window_offset:02X}")

        decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
        pixels_with_window = apply_palette_window(decompressed[:w*h], window_offset)

        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(pixels_with_window):
                    pal_idx = pixels_with_window[px_idx]
                    img.putpixel((x, y), palette_rgb[pal_idx])

        img_path = os.path.join(output_dir, f"test2_nested7_tile1_{w}x{h}_window.png")
        img.save(img_path)
        print(f"  保存: {img_path}")

        # 统计非零像素
        non_zero = sum(1 for p in pixels_with_window if p != 0)
        print(f"  非零像素: {non_zero}/{w*h} ({non_zero/(w*h)*100:.1f}%)")

# 测试3: LMI1 索引3
print("\n[测试3] LMI1 索引 3")
idx = 3
res_data, _, res_size = read_dat_resource(data, 0, idx)
if res_data and res_data[:4] == b'LMI1':
    tile_count = struct.unpack_from('<H', res_data, 4)[0]
    print(f"  tile数量: {tile_count}")

    # 获取前几个tile
    for tile_idx in range(min(3, tile_count)):
        tile_offset_addr = 6 + tile_idx * 4
        if tile_offset_addr + 4 > len(res_data):
            break
        tile_offset = struct.unpack_from('<I', res_data, tile_offset_addr)[0]

        if tile_offset >= len(res_data):
            continue

        # LMI1 tile数据从offset开始
        tile_data = res_data[tile_offset:]
        if len(tile_data) < 5:
            continue

        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]

        # 检查是否是有效的tile尺寸
        if w > 0 and w <= 64 and h > 0 and h <= 64:
            rle_data = tile_data[4:]
            decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)

            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        pal_idx = decompressed[px_idx]
                        img.putpixel((x, y), palette_rgb[pal_idx])

            img_path = os.path.join(output_dir, f"test3_lmi1_idx3_tile{tile_idx}_{w}x{h}.png")
            img.save(img_path)
            print(f"  tile{tile_idx}: {w}x{h} -> 已保存")

# 测试4: 直接Tile索引（如索引54）
print("\n[测试4] 直接Tile索引 54")
idx = 54
res_data, _, res_size = read_dat_resource(data, 0, idx)
if res_data:
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    window_offset = res_data[4] if len(res_data) > 4 else 0
    rle_data = res_data[5:]

    print(f"  尺寸: {w}x{h}, 调色板窗口: 0x{window_offset:02X}")

    if w > 0 and w <= 320 and h > 0 and h <= 200:
        decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
        pixels_with_window = apply_palette_window(decompressed[:w*h], window_offset)

        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(pixels_with_window):
                    pal_idx = pixels_with_window[px_idx]
                    img.putpixel((x, y), palette_rgb[pal_idx])

        img_path = os.path.join(output_dir, f"test4_idx54_{w}x{h}.png")
        img.save(img_path)
        print(f"  保存: {img_path}")

        non_zero = sum(1 for p in pixels_with_window if p != 0)
        print(f"  非零像素: {non_zero}/{w*h} ({non_zero/(w*h)*100:.1f}%)")

print("\n" + "=" * 70)
print("验证完成！检查output/verify_correct_rle目录中的图像。")
print("\n如果图像显示正确，说明RLE解码实现正确。")
