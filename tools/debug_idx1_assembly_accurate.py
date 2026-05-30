#!/usr/bin/env python3
"""基于MCP汇编精确分析RLE解码 - 特别关注COPY_SPEC的间隔写入特征"""
import struct

print("="*70)
print("基于MCP反汇编的RLE算法精确实现")
print("="*70)

with open('data/FDOTHER.dat', 'rb') as f:
    f.seek(0x800)
    header = f.read(0x600)

num_entries = len(header) // 12
print(f"总条目数: {num_entries}")

# 索引1
entry1 = struct.unpack('<III', header[1*12:1*12+12])
idx1_offset = entry1[0]
idx1_size = entry1[1]
print(f"\n索引1: offset=0x{idx1_offset:08x}, size={idx1_size}")

f.seek(idx1_offset)
data = f.read(min(idx1_size, 2000))

# 尝试5字节header
width1 = struct.unpack('<H', data[0:2])[0]
height1 = struct.unpack('<H', data[2:4])[0]
pal_window1 = data[4]
print(f"5字节header: {width1}x{height1}, palette_window={pal_window1}")
print(f"预期像素数: {width1 * height1}")

rle_data = data[5:5+idx1_size]
print(f"RLE数据大小: {len(rle_data)}")

# 加载调色板
import os
pal_path = 'data/PALETTE.dat'
if os.path.exists(pal_path):
    with open(pal_path, 'rb') as pf:
        pf.seek(0x800 + 0 * 12)
        pal_hdr = pf.read(12)
        pal_off, pal_sz = struct.unpack('<II', pal_hdr[:8])
        pf.seek(pal_off)
        pal_data = pf.read(pal_sz)
    
    palette = []
    for i in range(0, min(pal_sz, 256*3), 3):
        palette.append((pal_data[i], pal_data[i+1], pal_data[i+2]))
    
    # 补齐到256色
    while len(palette) < 256:
        palette.append((0, 0, 0))
    
    print(f"调色板加载完成, {len(palette)}色")
else:
    print("警告: 未找到PALETTE.dat")
    palette = [(i, i, i) for i in range(256)]

def decompress_rle_assembly_accurate(src, dst_size):
    """
    根据MCP汇编代码100%精确实现
    
    关键发现: COPY_SPEC模式(bit7=0, bit6=1)是间隔写入!
    - 每次循环: dst_idx前进2,但只写入1个值
    - sub bx, cx 执行两次,表示消耗2*count个像素位置
    
    操作类型:
    - bit7=0, bit6=0: FILL - 读取1个值,连续填充count个位置
    - bit7=0, bit6=1: COPY_SPEC - 读取1个值,间隔写入count个位置(每2个位置写1个)
    - bit7=1, bit6=0: COPY_STD - 从src复制count个字节到dst
    - bit7=1, bit6=1: SKIP - 跳过count个位置
    """
    dst = [0] * dst_size
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    remaining = dst_size  # 对应汇编中的bx
    
    while remaining > 0 and src_idx < src_size:
        ctrl = src[src_idx]
        src_idx += 1
        
        bit7 = (ctrl >> 7) & 1
        bit6 = (ctrl >> 6) & 1
        count = (ctrl & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL: 连续填充
                if src_idx < src_size:
                    val = src[src_idx]
                    src_idx += 1
                    for i in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 1
                            remaining -= 1
            else:
                # COPY_SPEC: 间隔写入(关键!每次前进2,写入1)
                if src_idx < src_size:
                    val = src[src_idx]
                    src_idx += 1
                    for i in range(count):
                        if dst_idx < dst_size:
                            dst[dst_idx] = val
                            dst_idx += 2  # 关键: 前进2!
                            remaining -= 2  # 消耗2个位置
        else:
            if bit6 == 0:
                # COPY_STD: 连续复制
                for i in range(count):
                    if dst_idx < dst_size and src_idx < src_size:
                        dst[dst_idx] = src[src_idx]
                        src_idx += 1
                        dst_idx += 1
                        remaining -= 1
            else:
                # SKIP: 跳过
                dst_idx += count
                remaining -= count
    
    return dst

# 解码索引1
expected = width1 * height1
decoded = decompress_rle_assembly_accurate(rle_data, expected)

non_zero = sum(1 for p in decoded if p != 0)
print(f"解码后非零像素: {non_zero}/{expected}")

# 应用palette window
adjusted = [(pal_window1 + p) & 0xFF for p in decoded]
adjusted_non_zero = sum(1 for p in adjusted if p != 0)
print(f"应用palette_window({pal_window1})后非零像素: {adjusted_non_zero}/{expected}")

# 渲染图像
from PIL import Image

img = Image.new('RGB', (width1, height1))
for y in range(height1):
    for x in range(width1):
        idx = y * width1 + x
        pal_idx = adjusted[idx]
        img.putpixel((x, y), palette[pal_idx])

img.save('output/idx1_assembly_accurate.png')
print(f"\n保存图像: output/idx1_assembly_accurate.png")
print(f"图像尺寸: {width1}x{height1}")

# 对比分析
print("\n" + "="*70)
print("COPY_SPEC间隔写入效果分析")
print("="*70)

# 统计COPY_SPEC操作数量
src_idx = 0
copy_spec_count = 0
copy_spec_pixels = 0
while src_idx < len(rle_data) - 1:
    ctrl = rle_data[src_idx]
    src_idx += 1
    bit7 = (ctrl >> 7) & 1
    bit6 = (ctrl >> 6) & 1
    count = (ctrl & 0x3F) + 1
    
    if bit7 == 0 and bit6 == 1:
        copy_spec_count += 1
        copy_spec_pixels += count * 2  # 每个COPY_SPEC消耗2*count个位置
        src_idx += 1  # 跳过值字节

print(f"COPY_SPEC操作数: {copy_spec_count}")
print(f"COPY_SPEC消耗像素位置: {copy_spec_pixels}")
print(f"占总像素比例: {copy_spec_pixels/expected*100:.1f}%")

# 前10个操作分析
print("\n前10个RLE操作:")
src_idx = 0
for i in range(10):
    if src_idx >= len(rle_data) - 1:
        break
    ctrl = rle_data[src_idx]
    src_idx += 1
    bit7 = (ctrl >> 7) & 1
    bit6 = (ctrl >> 6) & 1
    count = (ctrl & 0x3F) + 1
    
    if bit7 == 0 and bit6 == 0:
        op = "FILL"
        src_idx += 1
    elif bit7 == 0 and bit6 == 1:
        op = "COPY_SPEC(间隔)"
        src_idx += 1
    elif bit7 == 1 and bit6 == 0:
        op = "COPY_STD"
        src_idx += count
    else:
        op = "SKIP"
    
    print(f"  [{i}] ctrl=0x{ctrl:02x} ({op}) count={count}")
