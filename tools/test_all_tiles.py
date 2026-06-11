#!/usr/bin/env python
"""
测试所有FDOTHER tile资源的解码
"""
import os
import struct
import zlib

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
output_dir = r"d:\workspace\fd2_dat_freebuff\output\all_tiles_test"
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

def apply_palette(window, idx):
    """应用调色板窗口偏移"""
    if window >= 0:
        return (idx + window) & 0xFF
    return idx

def decode_sub_4EC66(src, src_size):
    """sub_4EC66解码 - RLE解码"""
    dst = []
    ah = 0  # 运行长度计数器
    al = 0  # 当前像素值
    src_idx = 0

    while len(dst) < 24*24:  # 假设最大24x24
        if ah > 0:
            # 重复之前的像素值
            ah -= 1
            dst.append(al)
        else:
            if src_idx >= src_size:
                break
            al = src[src_idx]
            src_idx += 1

            if al > 0xC0:
                # 运行长度编码
                ah = al - 0xC1
                if src_idx < src_size:
                    al = src[src_idx]
                    src_idx += 1
                dst.append(al)
            else:
                dst.append(al)
                ah = 0

        if len(dst) >= 24*24:
            break

    return dst

def parse_tile_header(data, size):
    """解析tile头部"""
    if size < 4:
        return None

    w = struct.unpack('<H', data[0:2])[0]
    h = struct.unpack('<H', data[2:4])[0]

    if w == 0 or w > 640 or h == 0 or h > 480:
        return None

    # 检查是否有palette_window
    if size >= 8 and data[5] != 0:
        palette_window = data[4] | (data[5] << 8)
        rle_data = data[8:]
        header_size = 8
    else:
        palette_window = data[4] if size >= 5 else 0
        rle_data = data[5:]
        header_size = 5

    return {
        'width': w,
        'height': h,
        'palette_window': palette_window,
        'rle_data': rle_data,
        'rle_size': size - header_size,
        'header_size': header_size
    }

def parse_lmi1(data, size):
    """解析LMI1格式"""
    if size < 6 or data[0:4] != b'LMI1':
        return None

    tile_count = struct.unpack('<H', data[4:6])[0]

    # 获取前两个tile的偏移来计算tile大小
    offsets = []
    for i in range(tile_count + 1):
        off = struct.unpack('<I', data[6 + i*4:10 + i*4])[0]
        offsets.append(off)

    tile_size = offsets[1] - offsets[0] if len(offsets) > 1 else 0

    # 估算宽高
    w = 16
    h = tile_size // 16 if tile_size >= 16 else 16

    return {
        'tile_count': tile_count,
        'tile_size': tile_size,
        'tile_width': w,
        'tile_height': h,
        'offsets': offsets
    }

def write_png(filename, width, height, pixels, palette_data, window=0):
    """写入8位调色板PNG"""
    def chunk(typ, data):
        crc = zlib.crc32(typ + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', crc)

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)  # filter byte
        for x in range(width):
            idx = pixels[y * width + x]
            if window:
                idx = (idx + window) & 0xFF
            raw_data.append(idx)

    pal_data = bytearray()
    for i in range(256):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        pal_data.extend([r8, g8, b8])

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 3, 0, 0, 0)
    plte = chunk(b'PLTE', pal_data)
    idat = chunk(b'IDAT', zlib.compress(bytes(raw_data)))
    iend = chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(sig + chunk(b'IHDR', ihdr) + plte + idat + iend)

# 测试关键索引
test_indices = [1, 3, 5, 6, 7, 9, 11, 12, 13, 14, 63, 96]

for idx in test_indices:
    if idx >= len(offsets) - 1:
        continue

    start = offsets[idx]
    end = offsets[idx + 1]
    res_data = data[start:end]
    res_size = end - start

    print(f"\n{'='*60}")
    print(f"索引 {idx}: {res_size} bytes")

    # 检查是否是LMI1
    if res_data[0:4] == b'LMI1':
        print("类型: LMI1")
        lmi1 = parse_lmi1(res_data, res_size)
        if lmi1:
            print(f"  Tile数量: {lmi1['tile_count']}, 大小: {lmi1['tile_size']}, 尺寸: {lmi1['tile_width']}x{lmi1['tile_height']}")

            # 解码第一个tile
            off = lmi1['offsets'][0]
            tile_data = res_data[off:off+lmi1['tile_size']]
            decoded = decode_sub_4EC66(tile_data, len(tile_data))

            if decoded:
                # 写入PNG
                png_file = os.path.join(output_dir, f"index{idx}_tile0.png")
                write_png(png_file, lmi1['tile_width'], lmi1['tile_height'], decoded[:lmi1['tile_width']*lmi1['tile_height']], palette, 0)
                print(f"  已导出: {png_file}")

    # 检查是否是嵌套DAT
    elif res_data[0:6] == b'LLLLLL':
        print("类型: 嵌套DAT")
        # 解析子资源
        sub_count = struct.unpack('<I', res_data[6:10])[0]
        print(f"  子资源数: {sub_count}")

    # 检查是否是普通TILE
    elif res_size >= 4:
        w = struct.unpack('<H', res_data[0:2])[0]
        h = struct.unpack('<H', res_data[2:4])[0]
        if 0 < w <= 640 and 0 < h <= 480:
            print(f"类型: TILE {w}x{h}")
            tile = parse_tile_header(res_data, res_size)
            if tile:
                decoded = decode_sub_4EC66(tile['rle_data'], tile['rle_size'])

                # 限制像素数量
                actual_count = min(len(decoded), tile['width'] * tile['height'])
                decoded = decoded[:actual_count]

                # 填充到目标大小
                while len(decoded) < tile['width'] * tile['height']:
                    decoded.append(0)

                print(f"  调色板窗口: {tile['palette_window']}, RLE大小: {tile['rle_size']}")
                print(f"  解码像素: {len(decoded)}/{tile['width']*tile['height']}")

                # 写入PNG
                png_file = os.path.join(output_dir, f"index{idx}_tile.png")
                write_png(png_file, tile['width'], tile['height'], decoded, palette, tile['palette_window'])
                print(f"  已导出: {png_file}")

    else:
        print("类型: 未知")

print(f"\n\n所有测试输出: {output_dir}")
