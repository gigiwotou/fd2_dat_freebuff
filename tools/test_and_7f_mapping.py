#!/usr/bin/env python3
import struct
from PIL import Image

fdfield = open("game/FDFIELD.DAT", "rb").read()
fdshap = open("game/FDSHAP.DAT", "rb").read()

# 解析FDFIELD
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from("<I", fdfield, pos)[0]
    if o > pos and o < len(fdfield):
        fdfield_offsets.append(o)
    else:
        break
    pos += 4

layout_data = fdfield[fdfield_offsets[0]:fdfield_offsets[1]]
w = struct.unpack_from("<H", layout_data, 0)[0]
h = struct.unpack_from("<H", layout_data, 2)[0]

terrain_ids = []
for i in range(w * h):
    pos = 4 + 4 * i
    tid = struct.unpack_from("<H", layout_data, pos)[0]
    terrain_ids.append(tid)

# 解析FDSHAP
fdshap_count = struct.unpack_from("<I", fdshap, 6)[0]
fdshap_offsets = [struct.unpack_from("<I", fdshap, 10 + i * 4)[0] for i in range(fdshap_count)]
tile_set_data = fdshap[fdshap_offsets[1]:fdshap_offsets[2]]
palette_data = fdshap[fdshap_offsets[0]:fdshap_offsets[1]]

tile_w = struct.unpack_from("<H", tile_set_data, 0)[0]
tile_h = struct.unpack_from("<H", tile_set_data, 2)[0]
tile_count = struct.unpack_from("<H", tile_set_data, 4)[0]

tile_offsets = []
pos = 6
for i in range(tile_count):
    off = struct.unpack_from("<I", tile_set_data, pos)[0]
    tile_offsets.append(off)
    pos += 4

# 简化：直接使用调色板数据（如果大小是768的倍数，直接使用）
palette = []
if len(palette_data) >= 768:
    # 6-bit to 8-bit conversion
    pal_data = palette_data[:768]
    for i in range(256):
        r = (pal_data[i*3] << 2) | (pal_data[i*3] >> 4)
        g = (pal_data[i*3+1] << 2) | (pal_data[i*3+1] >> 4)
        b = (pal_data[i*3+2] << 2) | (pal_data[i*3+2] >> 4)
        palette.extend([min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))])
else:
    palette = [i for i in range(256) for _ in range(3)]  # fallback

# RLE解压缩
def rle_decompress(src, width, height):
    dst = bytearray(width * height)
    p = 0
    src_end = len(src)
    for row in range(height):
        row_dst = row * width
        count = width
        while count > 0 and p < src_end:
            value = src[p]
            p += 1
            count_1 = (value & 0x3F) + 1
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            if bit7 and bit6:
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count >= 2:
                            if row_dst + 1 < len(dst):
                                dst[row_dst + 1] = fill
                            row_dst += 2
                            count -= 2
                        else:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
            else:
                if p < src_end:
                    fill = src[p]
                    p += 1
                    for i in range(count_1):
                        if count > 0:
                            if row_dst < len(dst):
                                dst[row_dst] = fill
                            row_dst += 1
                            count -= 1
    return bytes(dst)

# 生成地图
map_img = Image.new("RGB", (w * tile_w, h * tile_h), (0, 0, 0))
rendered = 0
for i, tid in enumerate(terrain_ids):
    tile_idx = tid & 0x7F  # 使用 & 0x7F
    if 0 <= tile_idx < len(tile_offsets):
        offset = tile_offsets[tile_idx]
        next_offset = tile_offsets[tile_idx + 1] if tile_idx + 1 < len(tile_offsets) else len(tile_set_data)
        compressed = tile_set_data[offset:next_offset]
        pixels = rle_decompress(compressed, tile_w, tile_h)
        if len(pixels) == tile_w * tile_h:
            y = i // w
            x = i % w
            tile_img = Image.new("P", (tile_w, tile_h))
            tile_img.putdata(pixels)
            tile_img.putpalette(palette[:768])
            map_img.paste(tile_img, (x * tile_w, y * tile_h))
            rendered += 1

map_img.save("output/map_0_and_7f.png")
print(f"渲染了 {rendered}/{w*h}")
