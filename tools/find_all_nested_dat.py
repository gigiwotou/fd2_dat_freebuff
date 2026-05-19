#!/usr/bin/env python3
"""
查找FDOTHER.DAT中所有嵌套DAT结构
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def find_all_nested_dat():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    res_count = struct.unpack_from("<I", data, 6)[0]
    print(f"FDOTHER.DAT: 共 {res_count} 个资源\n")
    
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    print(f"前20个资源概览:")
    print(f"{'索引':>4} {'偏移':>10} {'大小':>10} {'头8字节'} {'类型'}")
    print("-" * 80)
    
    for i in range(min(20, res_count)):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        sz = e - s
        header = data[s:s+8].hex() if s < len(data) else ""
        
        type_info = ""
        if data[s:s+6] == DAT_MAGIC:
            nested_count = struct.unpack_from("<I", data, s+6)[0]
            type_info = f"嵌套DAT({nested_count})"
        elif sz >= 4:
            w, h = struct.unpack_from("<HH", data, s)
            if 0 < w <= 640 and 0 < h <= 480:
                type_info = f"图像{w}x{h}"
            elif sz == 768:
                type_info = "调色板"
            else:
                type_info = "数据块"
        
        print(f"[{i:3}] {s:10} {sz:10} {header} {type_info}")
    
    # 查找所有嵌套DAT
    print(f"\n{'='*60}")
    print("所有嵌套DAT资源:")
    print(f"{'='*60}")
    
    found_nested = False
    for i in range(res_count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[s:e]
        
        if res_data[:6] == DAT_MAGIC:
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"\n资源 {i}: 嵌套DAT, {nested_count} 个子资源, 总大小={len(res_data)}")
            found_nested = True
            
            # 打印嵌套DAT的偏移表
            nested_offsets = []
            for j in range(min(nested_count, 10)):
                off = 10 + j * 4
                if off + 4 <= len(res_data):
                    nested_offsets.append(struct.unpack_from("<I", res_data, off)[0])
            
            print(f"  前10个偏移: {nested_offsets}")
            
            # 检查是否有201和205
            if nested_count > 205:
                print(f"  *** 包含资源201和205 ***")
                
                # 详细分析201和205
                for idx in [201, 205]:
                    off = 10 + idx * 4
                    if off + 4 <= len(res_data):
                        nested_off = struct.unpack_from("<I", res_data, off)[0]
                        next_off = 10 + (idx+1) * 4
                        if next_off + 4 <= len(res_data):
                            nested_end = struct.unpack_from("<I", res_data, next_off)[0]
                        else:
                            nested_end = len(res_data)
                        
                        sz = nested_end - nested_off
                        print(f"\n  资源 {idx}:")
                        print(f"    偏移: {nested_off}")
                        print(f"    大小: {sz}")
                        
                        if sz >= 4:
                            w, h = struct.unpack_from("<HH", res_data, nested_off)
                            print(f"    尺寸: {w}x{h}")

if __name__ == "__main__":
    find_all_nested_dat()
