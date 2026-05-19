#!/usr/bin/env python3
"""验证FDOTHER.DAT索引1提取的资源ID 1-18的图形数据"""
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

print("验证提取的资源文件:")
print("=" * 70)

for res_id in range(1, 19):
    filename = f'idx1_res_{res_id}.bin'
    filepath = os.path.join(OUT_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"  ID {res_id:2d}: 文件不存在 {filename}")
        continue
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    size = len(data)
    
    # 尝试解析图形数据
    # 根据游戏常见的图形格式: 可能包含宽高信息
    if size >= 4:
        # 尝试多种格式解析
        w1 = struct.unpack_from('<H', data, 0)[0]
        h1 = struct.unpack_from('<H', data, 2)[0]
        
        print(f"  ID {res_id:2d}: {size:4d} 字节, "
              f"可能尺寸: {w1:3d}x{h1:3d} -> {filename}")
        
        # 显示前16字节的十六进制内容
        hex_str = ' '.join(f'{b:02X}' for b in data[:16])
        print(f"        前16字节: {hex_str}")
    else:
        print(f"  ID {res_id:2d}: {size:4d} 字节 (太小无法解析) -> {filename}")
    
    print()

print("验证完成!")
