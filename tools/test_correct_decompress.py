#!/usr/bin/env python3
"""测试正确解压FDSHAP资源1"""

import struct
from pathlib import Path
from PIL import Image

def rle_decompress(src: bytes, width: int, height: int) -> bytes:
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

def palette_6bit_to_8bit(palette_768: bytes):
    palette = []
    for i in range(256):
        r6 = palette_768[i * 3]
        g6 = palette_768[i * 3 + 1]
        b6 = palette_768[i * 3 + 2]
        r8 = (r6 << 2) | (r6 >> 4)
        g8 = (g6 << 2) | (g6 >> 4)
        b8 = (b6 << 2) | (b6 >> 4)
        palette.append((min(255, max(0, r8)), min(255, max(0, g8)), min(255, max(0, b8))))
    return palette

# 加载FDSHAP.DAT
fdshap = Path("game/FDSHAP.DAT").read_bytes()
count = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP.DAT: {count} resources")

# 获取资源0（调色板）
res0_pos = 4 * 0 + 10
res0_offset = struct.unpack_from('<I', fdshap, res0_pos)[0]
res0_next = struct.unpack_from('<I', fdshap, res0_pos + 4)[0]
res0_size = res0_next - res0_offset

palette_data = fdshap[res0_offset:res0_offset + res0_size]
palette = palette_6bit_to_8bit(palette_data[:768])
print(f"调色板: {len(palette)} 色")

# 获取资源1（tile集）
res1_pos = 4 * 1 + 10
res1_offset = struct.unpack_from('<I', fdshap, res1_pos)[0]
res1_next = struct.unpack_from('<I', fdshap, res1_pos + 4)[0]
res1_size = res1_next - res1_offset

print(f"\n资源1: offset={res1_offset}, size={res1_size}")

# 解析头部
w, h = struct.unpack_from('<HH', fdshap, res1_offset)
print(f"头部: w={w}, h={h}")

# 尝试1: 假设头部是单个tile尺寸，整个资源是一个大tile集
# 计算可能的总尺寸
tile_w, tile_h = 24, 24
tile_pixels = tile_w * tile_h  # 576 pixels per tile

# 资源大小87915字节，减去4字节头部 = 87911字节RLE数据
rle_data_size = res1_size - 4

# 假设RLE压缩比约1.5:1（通常RLE压缩比1.5-3:1）
# 解压后的像素数约 87911 / 1.5 ≈ 58607 pixels
# 58607 / 576 ≈ 102 tiles

# 但这是猜测。让我尝试直接解压，使用不同的宽高组合

# 尝试2: 假设w和h就是tile集的总尺寸
# 但如果w=24, h=24，这只够1个tile，不符合

# 尝试3: 检查资源1前200字节的模式
print(f"\n前200字节(hex):")
data = fdshap[res1_offset:res1_offset+200]
for i in range(0, min(100, len(data)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# 根据hex分析，偏移4开始是递增的值，这应该是偏移表
# 让我尝试不同的偏移表条目大小

for entry_size in [2, 4, 6, 8]:
    print(f"\n=== 尝试偏移表条目大小: {entry_size} 字节 ===")
    
    offsets = []
    pos = res1_offset + 4
    
    while pos < res1_offset + res1_size - entry_size:
        if entry_size == 2:
            val = struct.unpack_from('<H', fdshap, pos)[0]
            if 0 < val < res1_size:
                offsets.append(val)
                pos += entry_size
            else:
                break
        elif entry_size == 4:
            val = struct.unpack_from('<I', fdshap, pos)[0]
            if 0 < val < res1_size:
                offsets.append(val)
                pos += entry_size
            else:
                break
        else:
            break
        
        if len(offsets) > 300:
            break
    
    if offsets:
        print(f"  找到 {len(offsets)} 个偏移")
        print(f"  前10个: {offsets[:10]}")
        
        # 检查偏移是否递增
        if len(offsets) > 1:
            diffs = [offsets[i+1] - offsets[i] for i in range(min(10, len(offsets)-1))]
            avg_diff = sum(diffs) / len(diffs)
            print(f"  平均间距: {avg_diff:.0f} 字节")
