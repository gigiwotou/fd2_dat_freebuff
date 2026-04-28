#!/usr/bin/env python3
"""分析FDSHAP.DAT资源1的真实结构"""

import struct
from pathlib import Path

fdshap = Path("game/FDSHAP.DAT").read_bytes()

# 获取资源1
res1_start = struct.unpack_from('<I', fdshap, 14)[0]
res1_end = struct.unpack_from('<I', fdshap, 18)[0]
res1_size = res1_end - res1_start

print(f"资源1: size={res1_size} bytes")
print(f"前100字节: {fdshap[res1_start:res1_start+100].hex()}")

# 尝试不同的宽高解释
w1, h1 = struct.unpack_from('<HH', fdshap, res1_start)
w2, h2 = struct.unpack_from('>HH', fdshap, res1_start)
print(f"\n小端序: w={w1}, h={h1}")
print(f"大端序: w={w2}, h={h2}")

# 如果w=24, h=24是单个tile尺寸
# 那么87915字节可能包含多少tile？
# 假设每个tile压缩后平均大小：
if w1 == 24 and h1 == 24:
    tile_pixels = 24 * 24
    # 假设平均压缩比2:1
    approx_tile_size = tile_pixels // 2  # 约288字节
    num_tiles = res1_size // approx_tile_size
    print(f"\n如果每个tile压缩后约{approx_tile_size}字节")
    print(f"可能包含约 {num_tiles} 个tile")
    
    # 如果是网格排列，可能是 NxN
    import math
    grid_size = int(math.sqrt(num_tiles))
    print(f"如果是正方形网格: {grid_size}x{grid_size}")
    
    # 尝试计算总图像的宽高
    total_w = grid_size * 24
    total_h = grid_size * 24
    print(f"总图像尺寸可能是: {total_w}x{total_h}")
    print(f"总像素: {total_w * total_h}")
