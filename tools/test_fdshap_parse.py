#!/usr/bin/env python3
"""测试FDSHAP.DAT解析"""

import struct
from pathlib import Path

def parse_dat(data: bytes):
    """解析DAT文件，返回(start, end)列表"""
    magic = data[:6]
    print(f"Magic: {magic}")
    
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"Resource count: {count}")
    
    resources = []
    for i in range(count):
        pos = 4 * i + 10
        if pos + 4 > len(data):
            break
        offset = struct.unpack_from('<I', data, pos)[0]
        resources.append(offset)
    
    return resources

data = Path("game/FDSHAP.DAT").read_bytes()
resources = parse_dat(data)

print(f"\n总共 {len(resources)} 个资源偏移")

# 计算每个资源大小
for i in range(min(20, len(resources))):
    start = resources[i]
    end = resources[i + 1] if i + 1 < len(resources) else len(data)
    size = end - start
    
    print(f"\n资源 {i}: start={start}, size={size}")
    if size > 0 and size < 3000:
        first_bytes = data[start:start+min(32, size)]
        print(f"  数据: {first_bytes.hex()}")
