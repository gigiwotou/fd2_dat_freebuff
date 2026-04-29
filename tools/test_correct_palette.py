#!/usr/bin/env python3
"""使用FDOTHER.DAT的正确调色板生成地图"""
import struct
from PIL import Image

# 加载正确的调色板（FDOTHER.DAT 资源7）
fdother = open('game/FDOTHER.DAT', 'rb').read()
count = struct.unpack_from('<I', fdother, 6)[0]
offsets = [struct.unpack_from('<I', fdother, 10 + i*4)[0] for i in range(count)]
palette_data = fdother[offsets[7]:offsets[7] + 768]

# 调色板是6-bit还是8-bit？检查数值范围
max_val = max(palette_data)
print(f'FDOTHER palette max value: {max_val}')
# 如果最大值 <= 63，是6-bit；如果是0-255，是8-bit

# 转换为8-bit RGB
if max_val <= 63:
    # 6-bit转8-bit
    palette_8bit = []
    for i in range(256):
        r = palette_data[i*3]
        g = palette_data[i*3+1]
        b = palette_data[i*3+2]
        r8 = (r << 2) | (r >> 4)
        g8 = (g << 2) | (g >> 4)
        b8 = (b << 2) | (b >> 4)
        palette_8bit.extend([min(255, r8), min(255, g8), min(255, b8)])
    print('Converted from 6-bit to 8-bit')
else:
    # 直接使用
    palette_8bit = list(palette_data)
    print('Using 8-bit palette directly')

print(f'First 8 colors: {palette_8bit[:24]}')

# 加载FDFIELD和FDSHAP
fdfield = open('game/FDFIELD.DAT', 'rb').read()
fdshap = open('game/FDSHAP.DAT', 'rb').read()

# 解析FDFIELD
fdfield_offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from('<I', fdfield, pos)[0]
    if o > pos and o < len(fdfield):
        fdfield_offsets.append(o)
    else:
        break
    pos += 4

# 解析FDSHAP
fdshap_count = struct.unpack_from('<I', fdshap, 6)[0]
fdshap_offsets = [struct.unpack_from('<I', fdshap, 10 + i*4)[0] for i in range(fdshap_count)]

# 地图0
map_id = 0
layout_data = fdfield[fdfield_offsets[0]:fdfield_offsets[1]]
w = struct.unpack_from('<H', layout_data, 0)[0]
h = struct.unpack_from('<H', layout_data, 2)[0]

tile_set_data = fdshap[fdshap_offsets[1]:fdshap_offsets[2]]
tile_w = struct.unpack_from('<H', tile_set_data, 0)[0]
tile_h = struct.unpack_from('<H', tile_set_data, 2)[0]
tile_count = struct.unpack_from('<H', tile_set_data, 4)[0]

tile_offsets = []
pos = 6
for i in range(tile_count):
    off = struct.unpack_from('<I', tile_set_data, pos)[0]
    tile_offsets.append(off)
    pos += 4

print(f'Map: {w}x{h} = {w*h} tiles')
print(f'Tile: {tile_w}x{tile_h}, {tile_count} tiles')

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
map_img = Image.new('RGB', (w * tile_w, h * tile_h), (0, 0, 0))
rendered = 0

for i in range(w * h):
    pos = 4 + 4 * i
    tid = struct.unpack_from('<H', layout_data, pos)[0]
    
    # 直接使用地形ID作为瓦片索引
    if tid < len(tile_offsets):
        offset = tile_offsets[tid]
        next_offset = tile_offsets[tid + 1] if tid + 1 < len(tile_offsets) else len(tile_set_data)
        compressed = tile_set_data[offset:next_offset]
        pixels = rle_decompress(compressed, tile_w, tile_h)
        
        if len(pixels) == tile_w * tile_h:
            y = i // w
            x = i % w
            tile_img = Image.new('P', (tile_w, tile_h))
            tile_img.putdata(pixels)
            tile_img.putpalette(palette_8bit[:768])
            map_img.paste(tile_img, (x * tile_w, y * tile_h))
            rendered += 1

map_img.save('output/map_0_correct_palette.png')
print(f'Rendered {rendered}/{w*h} tiles with correct palette from FDOTHER.DAT')
print(f'Saved to: output/map_0_correct_palette.png')
