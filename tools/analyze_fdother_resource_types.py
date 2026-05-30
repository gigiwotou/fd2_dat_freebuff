#!/usr/bin/env python3
"""
检查FDOTHER.DAT中每个索引是否有自己的调色板
分析哪些资源是调色板，哪些是tile数据
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    if 6 + (i + 1) * 4 > len(data):
        break
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

print("分析FDOTHER.DAT所有索引的资源类型:")
print(f"{'索引':<5} {'偏移':<10} {'大小':<10} {'类型'}")
print("-" * 60)

for i in range(min(120, len(offsets))):
    size = offsets[i + 1] - offsets[i] if i + 1 < len(offsets) else len(data) - offsets[i]
    resource_data = data[offsets[i]:offsets[i] + min(20, size)]
    
    # 检查是否是调色板（768字节）
    is_palette = (size == 768)
    
    # 检查是否是嵌套DAT
    is_nested_dat = (size >= 6 and resource_data[:6] == b"LLLLLL")
    
    # 检查是否是tile数据
    is_tile = False
    if size >= 4 and not is_palette and not is_nested_dat:
        try:
            w = struct.unpack_from('<H', resource_data, 0)[0]
            h = struct.unpack_from('<H', resource_data, 2)[0]
            if 0 < w <= 320 and 0 < h <= 200:
                is_tile = True
        except:
            pass
    
    type_str = ""
    if is_palette:
        type_str = "调色板"
    elif is_nested_dat:
        type_str = "嵌套DAT"
    elif is_tile:
        type_str = f"Tile"
    elif size < 50:
        type_str = "小资源"
    else:
        type_str = "其他"
    
    print(f"{i:<5} {offsets[i]:<10} {size:<10} {type_str}")
