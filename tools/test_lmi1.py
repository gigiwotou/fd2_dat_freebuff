#!/usr/bin/env python
"""
测试LMI1 tile的解码，使用正确的尺寸计算
"""
import os
import struct
import zlib

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"
output_dir = r"d:\workspace\fd2_dat_freebuff\output\lmi1_test"
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
    """sub_4EC66解码 - RLE解码"""
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

def parse_lmi1_offsets(data, size):
    """解析LMI1的偏移表"""
    if size < 6 or data[0:4] != b'LMI1':
        return None

    tile_count = struct.unpack('<H', data[4:6])[0]

    offsets = []
    for i in range(tile_count + 1):
        off_pos = 6 + i * 4
        if off_pos + 4 > size:
            break
        off = struct.unpack('<I', data[off_pos:off_pos+4])[0]
        offsets.append(off)

    return {
        'tile_count': tile_count,
        'offsets': offsets
    }

def estimate_tile_dimensions(tile_size):
    """估算tile尺寸"""
    # 常见的tile尺寸组合
    candidates = []
    for h in range(1, 64):
        w = tile_size // h
        if w * h == tile_size and w <= 256 and h <= 256:
            candidates.append((w, h))
    return candidates[0] if candidates else (16, tile_size // 16)

def write_png(filename, width, height, pixels, palette_data, window=0):
    """写入8位调色板PNG"""
    def chunk(typ, data):
        crc = zlib.crc32(typ + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', crc)

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)
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

# 测试索引3 (LMI1, 23 tiles)
idx = 3
res_data = data[offsets[idx]:offsets[idx+1]]
res_size = offsets[idx+1] - offsets[idx]

print(f"索引 {idx}: {res_size} bytes")
lmi1 = parse_lmi1_offsets(res_data, res_size)
print(f"  Tile数量: {lmi1['tile_count']}")
print(f"  偏移: {lmi1['offsets'][:5]}...")

# 计算tile大小
if len(lmi1['offsets']) >= 2:
    tile_size = lmi1['offsets'][1] - lmi1['offsets'][0]
    print(f"  Tile大小: {tile_size}")

    w, h = estimate_tile_dimensions(tile_size)
    print(f"  估算尺寸: {w}x{h}")

    # 解码第一个tile
    off = lmi1['offsets'][0]
    tile_data = res_data[off:off+tile_size]
    decoded = decode_sub_4EC66(tile_data, len(tile_data), w*h)

    # 检查实际解码了多少
    print(f"  解码像素: {len(decoded)}/{w*h}")

    # 填充到目标大小
    while len(decoded) < w*h:
        decoded.append(0)

    # 写入PNG
    png_file = os.path.join(output_dir, f"index{idx}_lmi1_tile0.png")
    write_png(png_file, w, h, decoded, palette, 0)
    print(f"  已导出: {png_file}")

# 测试索引6 (LMI1, 230 tiles)
print()
idx = 6
res_data = data[offsets[idx]:offsets[idx+1]]
res_size = offsets[idx+1] - offsets[idx]

print(f"索引 {idx}: {res_size} bytes")
lmi1 = parse_lmi1_offsets(res_data, res_size)
print(f"  Tile数量: {lmi1['tile_count']}")

if len(lmi1['offsets']) >= 2:
    tile_size = lmi1['offsets'][1] - lmi1['offsets'][0]
    print(f"  Tile大小: {tile_size}")

    w, h = estimate_tile_dimensions(tile_size)
    print(f"  估算尺寸: {w}x{h}")

    # 解码前3个tile
    for t in range(min(3, lmi1['tile_count'])):
        off = lmi1['offsets'][t]
        next_off = lmi1['offsets'][t+1] if t+1 < len(lmi1['offsets']) else res_size
        tile_data = res_data[off:next_off]
        tile_size_actual = next_off - off

        decoded = decode_sub_4EC66(tile_data, len(tile_data), w*h)
        while len(decoded) < w*h:
            decoded.append(0)

        png_file = os.path.join(output_dir, f"index{idx}_lmi1_tile{t}.png")
        write_png(png_file, w, h, decoded, palette, 0)
        print(f"  已导出 tile{t}: {png_file}")

print(f"\n测试输出: {output_dir}")
