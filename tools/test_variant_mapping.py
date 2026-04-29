#!/usr/bin/env python3
"""测试变体映射公式"""
import struct
from PIL import Image

fdfield = open('game/FDFIELD.DAT','rb').read()
fdshap = open('game/FDSHAP.DAT','rb').read()

# 解析FDFIELD
offsets = []
pos = 6
while pos < len(fdfield) - 4:
    o = struct.unpack_from('<I',fdfield,pos)[0]
    if o > pos and o < len(fdfield): offsets.append(o)
    else: break
    pos += 4

layout = fdfield[offsets[0]:offsets[1]]
w = struct.unpack_from('<H',layout,0)[0]
h = struct.unpack_from('<H',layout,2)[0]

# 解析FDSHAP
fdshap_count = struct.unpack_from('<I',fdshap,6)[0]
fdshap_offsets = [struct.unpack_from('<I',fdshap,10+i*4)[0] for i in range(fdshap_count)]
tile_set_data = fdshap[fdshap_offsets[1]:fdshap_offsets[2]]
palette_data = fdshap[fdshap_offsets[0]:fdshap_offsets[1]]

tile_w = struct.unpack_from('<H',tile_set_data,0)[0]
tile_h = struct.unpack_from('<H',tile_set_data,2)[0]
tile_count = struct.unpack_from('<H',tile_set_data,4)[0]

tile_offsets = []
pos = 6
for i in range(tile_count):
    off = struct.unpack_from('<I',tile_set_data,pos)[0]
    tile_offsets.append(off)
    pos += 4

# 解析调色板
palette = []
if len(palette_data) >= 768:
    pal = palette_data[:768]
    for i in range(256):
        r = (pal[i*3]<<2)|(pal[i*3]>>4)
        g = (pal[i*3+1]<<2)|(pal[i*3+1]>>4)
        b = (pal[i*3+2]<<2)|(pal[i*3+2]>>4)
        palette.extend([min(255,max(0,r)),min(255,max(0,g)),min(255,max(0,b))])

def rle_decompress(src, width, height):
    dst = bytearray(width*height)
    p = 0
    src_end = len(src)
    for row in range(height):
        row_dst = row*width
        count = width
        while count > 0 and p < src_end:
            value = src[p]; p += 1
            count_1 = (value&0x3F)+1
            bit7 = (value>>7)&1; bit6 = (value>>6)&1
            if bit7 and bit6: row_dst += count_1; count -= count_1 if count>=count_1 else count
            elif bit7 and not bit6:
                for i in range(count_1):
                    if count>0 and p<src_end:
                        if row_dst<len(dst): dst[row_dst]=src[p]
                        row_dst+=1; p+=1; count-=1
            elif not bit7 and bit6:
                if p<src_end:
                    fill=src[p]; p+=1
                    for i in range(count_1):
                        if count>=2:
                            if row_dst+1<len(dst): dst[row_dst+1]=fill
                            row_dst+=2; count-=2
                        else:
                            if row_dst<len(dst): dst[row_dst]=fill
                            row_dst+=1; count-=1
            else:
                if p<src_end:
                    fill=src[p]; p+=1
                    for i in range(count_1):
                        if count>0:
                            if row_dst<len(dst): dst[row_dst]=fill
                            row_dst+=1; count-=1
    return bytes(dst)

def render_map(tile_idx_func):
    map_img = Image.new('RGB',(w*tile_w,h*tile_h),(0,0,0))
    rendered = 0
    for i in range(w*h):
        pos = 4+4*i
        b0=layout[pos]; b1=layout[pos+1]; b2=layout[pos+2]; b3=layout[pos+3]
        tile_idx = tile_idx_func(b0,b1,b2,b3)
        if 0<=tile_idx<len(tile_offsets):
            offset=tile_offsets[tile_idx]
            next_offset=tile_offsets[tile_idx+1] if tile_idx+1<len(tile_offsets) else len(tile_set_data)
            pixels = rle_decompress(tile_set_data[offset:next_offset],tile_w,tile_h)
            if len(pixels)==tile_w*tile_h:
                y=i//w; x=i%w
                tile_img = Image.new('P',(tile_w,tile_h))
                tile_img.putdata(pixels)
                tile_img.putpalette(palette[:768])
                map_img.paste(tile_img,(x*tile_w,y*tile_h))
                rendered += 1
    return map_img, rendered

# 测试不同公式
tests = [
    ('byte[0] only (b1=0->b0, b1=1->b0)', lambda b0,b1,b2,b3: b0),
    ('byte[0]+b1*192', lambda b0,b1,b2,b3: b0+b1*192),
    ('b1? b0+192 : b0', lambda b0,b1,b2,b3: b0+192 if b1 else b0),
    ('b1? b0+128 : b0', lambda b0,b1,b2,b3: b0+128 if b1 else b0),
    ('tid & 0x7F', lambda b0,b1,b2,b3: (b0|(b1<<8))&0x7F),
    ('tid if <192 else b0', lambda b0,b1,b2,b3: b0|(b1<<8) if (b0|(b1<<8))<192 else b0),
]

orig = Image.open('output/maps/map_0_final.png')

for name, func in tests:
    img, rendered = render_map(func)
    diff = sum(1 for a,b in zip(orig.getdata(),img.getdata()) if a!=b)
    match = (1-diff/(w*h*tile_w*tile_h))*100
    print(f'{name:40s}: rendered={rendered:3d}/576, match={match:.1f}%')
