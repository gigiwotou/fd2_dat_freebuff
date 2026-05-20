#!/usr/bin/env python3
"""分析FDOTHER.DAT中的所有调色板资源"""

import struct
from pathlib import Path

def analyze_fdother_palettes():
    fdother = Path("game/FDOTHER.DAT")
    if not fdother.exists():
        print("FDOTHER.DAT not found")
        return
    
    data = fdother.read_bytes()
    
    # 解析头部
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"FDOTHER.DAT: {count} 资源\n")
    
    # 解析偏移表
    offsets = []
    for i in range(count - 1):
        s = struct.unpack_from('<I', data, 10 + i*4)[0]
        e = struct.unpack_from('<I', data, 10 + (i+1)*4)[0]
        offsets.append((s, e, e - s))
    
    # 查找可能是调色板的资源 (768字节 = 256颜色 * 3字节)
    print("=== 可能的调色板资源 (768字节) ===")
    for i, (s, e, sz) in enumerate(offsets):
        if sz == 768:
            print(f"\n索引 {i}: 偏移 0x{s:X} - 0x{e:X}, 大小 {sz} 字节")
            
            # 读取前10个颜色的RGB值
            pal_data = data[s:s+30]
            print("前10个颜色 (R, G, B):")
            for j in range(10):
                r, g, b = struct.unpack_from('<BBB', pal_data, j*3)
                print(f"  [{j:3d}]: {r:3d} {g:3d} {b:3d}  (R={r:02X}, G={g:02X}, B={b:02X})")
            
            # 检查是否有肤色色调 (人物头像常用颜色)
            # 肤色通常是: R高, G中等, B低
            skin_like = 0
            for j in range(256):
                r, g, b = struct.unpack_from('<BBB', data[s:], j*3)
                if r > 40 and 20 < g < 50 and b < 20:
                    skin_like += 1
            print(f"  肤色色调颜色数量: {skin_like}")

if __name__ == "__main__":
    analyze_fdother_palettes()
