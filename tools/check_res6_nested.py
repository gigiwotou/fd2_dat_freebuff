#!/usr/bin/env python3
"""
直接检查FDOTHER资源6的嵌套DAT结构
验证是否有125个子资源（资源0是菜单背景320x200，资源1-6是按钮）
"""

import struct
import sys
from pathlib import Path

GAME_DIR = Path("game")

def main():
    data = (GAME_DIR / "FDOTHER.DAT").read_bytes()
    
    # 读取偏移表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        offsets.append(struct.unpack_from("<I", data, 10 + i*4)[0])
    
    # 获取资源6
    start = offsets[6]
    end = offsets[7] if 7 < len(offsets) else len(data)
    res6_data = data[start:end]
    
    print(f"资源6: 偏移={start}, 大小={len(res6_data)}")
    print(f"前6字节: {res6_data[:6]}")
    
    if res6_data[:6] != b"LLLLLL":
        print("不是DAT格式")
        return
    
    # 读取嵌套资源数
    nested_count = struct.unpack_from("<I", res6_data, 6)[0]
    print(f"嵌套资源数: {nested_count}")
    
    # 读取所有偏移
    nested_offsets = []
    for i in range(nested_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > len(res6_data):
            print(f"偏移表在索引 {i} 处结束")
            break
        nested_offsets.append(struct.unpack_from("<I", res6_data, off_pos)[0])
    
    print(f"实际读取偏移数: {len(nested_offsets)}")
    
    # 检查偏移有效性
    valid_count = 0
    for i, off in enumerate(nested_offsets):
        if off < len(res6_data):
            valid_count += 1
        else:
            print(f"索引 {i} 偏移 {off} 超出范围 ({len(res6_data)})")
            break
    
    print(f"有效偏移数: {valid_count}")
    
    # 打印前20个资源
    print(f"\n前20个子资源:")
    for i in range(min(20, len(nested_offsets))):
        s = nested_offsets[i]
        e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res6_data)
        sz = e - s
        header = res6_data[s:s+4].hex() if s < len(res6_data) else ""
        print(f"  [{i:3}] 偏移={s:8}, 大小={sz:8}, 头={header}")
    
    if len(nested_offsets) > 20:
        print(f"  ... (共{len(nested_offsets)}个)")
        # 打印最后几个
        for i in range(max(20, len(nested_offsets)-5), len(nested_offsets)):
            if i < len(nested_offsets):
                s = nested_offsets[i]
                e = nested_offsets[i+1] if i+1 < len(nested_offsets) else len(res6_data)
                sz = e - s
                print(f"  [{i:3}] 偏移={s:8}, 大小={sz:8}")

if __name__ == "__main__":
    main()
