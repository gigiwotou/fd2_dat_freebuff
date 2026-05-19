#!/usr/bin/env python3
"""
列出所有嵌套DAT及其子资源数量
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def main():
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
    
    # 找出所有嵌套DAT
    print(f"所有嵌套DAT资源:")
    print(f"{'索引':>4} {'子资源数':>10} {'总大小':>10}")
    print("-" * 40)
    
    nested_list = []
    for i in range(res_count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[s:e]
        
        if res_data[:6] == DAT_MAGIC:
            nested_count = struct.unpack_from("<I", res_data, 6)[0]
            print(f"[{i:3}] {nested_count:10} {len(res_data):10}")
            nested_list.append((i, nested_count, len(res_data)))
    
    # 检查索引6和索引62（之前看到有130个子资源）
    print(f"\n\n详细检查大嵌套DAT:")
    for idx, count, size in nested_list:
        if count > 100:
            print(f"\n{'='*60}")
            print(f"资源 {idx}: {count} 个子资源, 大小 {size}")
            print(f"{'='*60}")
            
            s = offsets[idx]
            e = offsets[idx+1] if idx+1 < len(offsets) else len(data)
            res_data = data[s:e]
            
            # 解析偏移表
            nested_offsets = []
            for j in range(count):
                off = 10 + j * 4
                if off + 4 <= len(res_data):
                    nested_offsets.append(struct.unpack_from("<I", res_data, off)[0])
            
            # 输出最后几个资源
            print(f"\n最后20个资源:")
            print(f"{'索引':>4} {'偏移':>8} {'大小':>8} {'尺寸':>10}")
            print("-" * 50)
            
            for j in range(max(0, count-20), count):
                if j >= len(nested_offsets):
                    continue
                if nested_offsets[j] >= len(res_data):
                    print(f"[{j:3}] 偏移超出范围")
                    continue
                
                sub_s = nested_offsets[j]
                sub_e = nested_offsets[j+1] if j+1 < len(nested_offsets) else len(res_data)
                sub_sz = sub_e - sub_s
                
                if sub_sz >= 4:
                    w, h = struct.unpack_from("<HH", res_data, sub_s)
                    print(f"[{j:3}] {sub_s:8} {sub_sz:8} {w}x{h}")
                else:
                    print(f"[{j:3}] {sub_s:8} {sub_sz:8} N/A")

if __name__ == "__main__":
    main()
