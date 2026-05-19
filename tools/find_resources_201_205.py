#!/usr/bin/env python3
"""
查找所有包含201和205子资源的嵌套DAT
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def find_resources_201_and_205():
    """在所有嵌套DAT中查找资源201和205"""
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: 共 {res_count} 个资源\n")
    
    # 解析索引表
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    found = False
    
    # 检查所有资源
    for i in range(res_count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[s:e]
        
        # 检查是否是嵌套DAT
        if res_data[:6] != DAT_MAGIC:
            continue
        
        nested_count = struct.unpack_from("<I", res_data, 6)[0]
        
        # 只检查包含205以上子资源的嵌套DAT
        if nested_count <= 205:
            continue
        
        print(f"\n{'='*80}")
        print(f"找到嵌套DAT: 资源 {i}, {nested_count} 个子资源")
        print(f"{'='*80}")
        found = True
        
        # 解析所有偏移
        nested_offsets = []
        for j in range(nested_count):
            off = 10 + j * 4
            if off + 4 <= len(res_data):
                nested_offsets.append(struct.unpack_from("<I", res_data, off)[0])
        
        # 详细分析201和205
        for idx in [201, 205]:
            if idx < len(nested_offsets) and nested_offsets[idx] < len(res_data):
                sub_s = nested_offsets[idx]
                sub_e = nested_offsets[idx+1] if idx+1 < len(nested_offsets) else len(res_data)
                sub_sz = sub_e - sub_s
                
                print(f"\n资源 {idx}:")
                print(f"  偏移: {sub_s} (0x{sub_s:X})")
                print(f"  大小: {sub_sz} 字节")
                
                if sub_sz >= 4:
                    w, h = struct.unpack_from("<HH", res_data, sub_s)
                    print(f"  尺寸: {w}x{h}")
                    
                    # 显示前32字节的hex
                    hex_data = res_data[sub_s:sub_s+32].hex()
                    print(f"  前32字节: {hex_data}")
                    
                    # 计算压缩比
                    if sub_sz > 4:
                        uncompressed = w * h
                        compressed = sub_sz - 4
                        ratio = uncompressed / compressed if compressed > 0 else 0
                        print(f"  未压缩: {uncompressed} 字节")
                        print(f"  压缩后: {compressed} 字节")
                        print(f"  压缩比: {ratio:.2f}:1")
            else:
                print(f"\n资源 {idx}: 不存在或偏移无效")
        
        # 输出所有资源的尺寸信息
        print(f"\n所有资源尺寸列表:")
        print(f"{'索引':>4} {'尺寸':>10} {'大小':>8}")
        print("-" * 40)
        
        for j in range(len(nested_offsets)):
            if nested_offsets[j] >= len(res_data):
                continue
            
            sub_s = nested_offsets[j]
            sub_e = nested_offsets[j+1] if j+1 < len(nested_offsets) else len(res_data)
            sub_sz = sub_e - sub_s
            
            if sub_sz >= 4:
                w, h = struct.unpack_from("<HH", res_data, sub_s)
                print(f"[{j:3}] {w}x{h:<7} {sub_sz}")
    
    if not found:
        print("未找到包含201和205资源的嵌套DAT")

if __name__ == "__main__":
    find_resources_201_and_205()
