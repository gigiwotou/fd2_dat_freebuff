#!/usr/bin/env python3
"""分析地图0的tile数据"""

import struct
from pathlib import Path
import sys
sys.path.insert(0, 'src')

# 使用fd2_decoder.c中的RLE解压逻辑
def rle_decompress(src: bytes, width: int, height: int) -> bytes:
    """RLE解压 - 按照IDA sub_4E98D的逻辑"""
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
                # 11: skip (transparent)
                row_dst += count_1
                count -= count_1 if count >= count_1 else count
            elif bit7 and not bit6:
                # 10: copy from source
                for i in range(count_1):
                    if count > 0 and p < src_end:
                        if row_dst < len(dst):
                            dst[row_dst] = src[p]
                        row_dst += 1
                        p += 1
                        count -= 1
            elif not bit7 and bit6:
                # 01: sparse fill
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
                # 00: regular fill
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

# 加载FDSHAP.DAT
fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 解析资源
count = struct.unpack_from('<I', fdshap, 6)[0]
print(f"FDSHAP资源数量: {count}")

# 获取资源0（调色板）和资源1（tile集）
res0_start = struct.unpack_from('<I', fdshap, 10)[0]
res0_end = struct.unpack_from('<I', fdshap, 14)[0]
res0_size = res0_end - res0_start
print(f"\n资源0（调色板）: offset={res0_start}, size={res0_size}")

res1_start = struct.unpack_from('<I', fdshap, 14)[0]
res1_end = struct.unpack_from('<I', fdshap, 18)[0]
res1_size = res1_end - res1_start
print(f"资源1（tile集）: offset={res1_start}, size={res1_size}")

# 检查资源1的前4字节
res1_data = fdshap[res1_start:res1_start+res1_size]
if len(res1_data) >= 4:
    w, h = struct.unpack_from('<HH', res1_data, 0)
    print(f"\n资源1前4字节: w={w}, h={h}")
    print(f"资源1前20字节: {res1_data[:20].hex()}")
    
    # 如果w=24, h=24，这可能是单个tile
    # 解压RLE数据
    pixels = rle_decompress(res1_data[4:], w, h)
    print(f"解压后像素数: {len(pixels)}")
    
    # 统计非零像素
    non_zero = sum(1 for p in pixels if p != 0)
    print(f"非零像素: {non_zero}")
    
    # 检查是否有多个tile（如果资源1包含所有tile，应该有多个24x24的区域）
    # 计算可能的tile数量
    if w == 24 and h == 24:
        print("这看起来是单个24x24 tile，不是tile集")
        print("地图可能只使用一个tile？或者我的理解有误")
