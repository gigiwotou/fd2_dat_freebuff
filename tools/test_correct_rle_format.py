#!/usr/bin/env python3
"""
测试正确的sub_4E98D RLE解码
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/test_correct_rle"
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
    """
    精确实现sub_4E98D的RLE解压缩逻辑

    参数:
    - src_data: RLE压缩数据 (不包含w,h头)
    - width: 图像宽度
    - height: 图像高度
    - stride: 行宽 (通常等于width)
    - value_1: 颜色模式 (-1=原始颜色, 0-255=固定颜色, >255=调色板偏移)
    """
    output_size = stride * height
    output = bytearray(output_size)

    src_pos = 0
    src_len = len(src_data)

    # 当前行起始位置（相对于输出缓冲区的绝对偏移）
    row_start = 0
    # 当前行已写入的像素数
    col_pos = 0
    # 当前处理的行号
    current_row = 0

    while current_row < height and src_pos < src_len:
        ctrl = src_data[src_pos]
        src_pos += 1

        count = (ctrl & 0x3F) + 1  # 低6位 + 1

        if ctrl & 0x80:  # Bit 7 = 1: 压缩命令
            if ctrl & 0x40:  # Bit 6 = 1: 跳过
                # 跳过count个像素
                col_pos += count
            else:  # Bit 6 = 0: 复制
                # 从源数据复制count个字节
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = src_data[src_pos]
                        src_pos += 1

                        # 计算输出位置
                        out_pos = row_start + col_pos

                        if value_1 == -1:
                            output[out_pos] = pixel
                        elif value_1 > 0xFF:
                            modified = value_1 + (((value_1 >> 8) + pixel) & 7)
                            output[out_pos] = modified & 0xFF
                        else:
                            output[out_pos] = value_1 & 0xFF

                        col_pos += 1
        else:  # Bit 7 = 0: 填充模式
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

        # 检查是否需要换行
        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0

    return bytes(output)


def apply_palette_window(pixels, window_offset):
    """应用调色板窗口技术

    根据sub_2EB9F函数分析:
    displayed_color = palette[(window_offset + pixel_value) % 256]
    """
    return [(window_offset + p) & 0xFF for p in pixels]


with open(dat_path, 'rb') as f:
    data = f.read()

# 加载主调色板
palette_data, _, _ = read_dat_resource(data, 0, 0)
if palette_data:
    # 转换为RGB
    palette_rgb = []
    for i in range(256):
        r = palette_data[i * 3]
        g = palette_data[i * 3 + 1]
        b = palette_data[i * 3 + 2]
        # 6位转8位
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        palette_rgb.append((r, g, b))
else:
    palette_rgb = [(i, i, i) for i in range(256)]

print("测试正确的RLE解码 (sub_4E98D)")
print("=" * 60)

# 测试索引11 (320x200全屏图像)
idx = 11
res_data, res_offset, res_size = read_dat_resource(data, 0, idx)
if res_data:
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    rle_data = res_data[4:]
    print(f"\n索引 {idx}: {w}x{h}, RLE数据大小: {len(rle_data)}")

    # 解码
    decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
    print(f"解码后大小: {len(decompressed)}, 预期: {w * h}")

    if len(decompressed) >= w * h:
        # 创建RGB图像
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                pal_idx = decompressed[px_idx]
                img.putpixel((x, y), palette_rgb[pal_idx])

        img_path = os.path.join(output_dir, f"index_{idx}_{w}x{h}.png")
        img.save(img_path)
        print(f"已保存: {img_path}")

# 测试嵌套DAT 7 的 tile 1
print("\n" + "=" * 60)
idx = 7
nested_data, _, _ = read_dat_resource(data, 0, idx)
if nested_data and len(nested_data) >= 10:
    # 解析嵌套DAT
    res_count = struct.unpack_from('<I', nested_data, 6)[0]
    print(f"\n嵌套DAT {idx}: 包含 {res_count} 个子资源")

    # 获取tile 1
    tile_offset_addr = 10 + 1 * 4
    tile_offset = struct.unpack_from('<I', nested_data, tile_offset_addr)[0]
    tile_data = nested_data[tile_offset:]

    if len(tile_data) >= 5:
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        window_offset = tile_data[4]  # 这是调色板窗口偏移
        rle_data = tile_data[5:]

        print(f"\n嵌套DAT {idx} tile 1: {w}x{h}")
        print(f"调色板窗口偏移: 0x{window_offset:02X}")

        # 解码（不应用窗口）
        decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)

        # 应用调色板窗口
        pixels_with_window = apply_palette_window(decompressed[:w*h], window_offset)

        # 创建RGB图像
        img = Image.new('RGB', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(pixels_with_window):
                    pal_idx = pixels_with_window[px_idx]
                    img.putpixel((x, y), palette_rgb[pal_idx])

        img_path = os.path.join(output_dir, f"nested_{idx}_tile1_{w}x{h}_window.png")
        img.save(img_path)
        print(f"已保存: {img_path}")

# 测试索引3 (LMI1 tile集)
print("\n" + "=" * 60)
idx = 3
res_data, res_offset, res_size = read_dat_resource(data, 0, idx)
if res_data and res_data[:4] == b'LMI1':
    tile_count = struct.unpack_from('<H', res_data, 4)[0]
    print(f"\nLMI1 索引 {idx}: 包含 {tile_count} 个tile")

    # 获取第一个tile的偏移
    first_tile_offset = struct.unpack_from('<I', res_data, 6)[0]
    second_tile_offset = struct.unpack_from('<I', res_data, 10)[0]
    tile_size = second_tile_offset - first_tile_offset
    print(f"第一个tile偏移: {first_tile_offset}, 大小: {tile_size}")

    # 尝试作为tile解析
    if len(res_data) > first_tile_offset + 4:
        tile_data = res_data[first_tile_offset:]
        w = struct.unpack_from('<H', tile_data, 0)[0]
        h = struct.unpack_from('<H', tile_data, 2)[0]
        print(f"第一个tile尺寸: {w}x{h}")

        if 0 < w <= 64 and 0 < h <= 64:
            rle_data = tile_data[4:]
            decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)

            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        pal_idx = decompressed[px_idx]
                        img.putpixel((x, y), palette_rgb[pal_idx])

            img_path = os.path.join(output_dir, f"lmi1_{idx}_tile0_{w}x{h}.png")
            img.save(img_path)
            print(f"已保存: {img_path}")

print("\n" + "=" * 60)
print("测试完成!")
