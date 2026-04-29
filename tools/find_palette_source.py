#!/usr/bin/env python3
"""查找实际的调色板数据来源"""
import struct
from pathlib import Path

game_dir = Path("game")

# 检查所有DAT文件
for dat_file in game_dir.glob("*.DAT"):
    print(f"\n{'='*60}")
    print(f"文件: {dat_file.name}")
    print(f"{'='*60}")
    
    with open(dat_file, "rb") as f:
        data = f.read()
    
    print(f"  大小: {len(data)} 字节")
    print(f"  前6字节: {data[:6]}")
    
    if data[:6] != b"LLLLLL":
        print(f"  不是标准LLLLLL格式")
        continue
    
    # 尝试解析为资源文件
    # 方式1: byte 6是计数
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"  方式1 (byte6=计数): 资源数={count}")
    
    if count < 1000 and 10 + count * 4 < len(data):
        offsets = []
        valid = True
        for i in range(min(count, 50)):
            off = struct.unpack_from('<I', data, 10 + i*4)[0]
            if off >= len(data):
                valid = False
                break
            offsets.append(off)
        
        if valid and offsets:
            print(f"  找到 {len(offsets)} 个有效偏移")
            # 查找768字节的资源（调色板）
            for i in range(len(offsets)-1):
                res_size = offsets[i+1] - offsets[i]
                if res_size == 768:
                    print(f"    资源{i}: 768字节 - 可能是调色板!")
                    res_data = data[offsets[i]:offsets[i]+20]
                    print(f"      前20字节: {res_data.hex(' ')}")
    else:
        # 方式2: 直接从byte 6开始偏移表
        print(f"  方式2 (byte6+=偏移): 尝试解析...")
        offsets = []
        pos = 6
        while pos < len(data) - 4:
            off = struct.unpack_from('<I', data, pos)[0]
            if off > pos and off < len(data):
                offsets.append(off)
            else:
                break
            pos += 4
        
        if len(offsets) > 1:
            print(f"  找到 {len(offsets)} 个偏移")
            for i in range(min(20, len(offsets)-1)):
                res_size = offsets[i+1] - offsets[i]
                if res_size == 768:
                    print(f"    资源{i}: 768字节 - 可能是调色板!")
                    res_data = data[offsets[i]:offsets[i]+20]
                    print(f"      前20字节: {res_data.hex(' ')}")
