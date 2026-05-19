#!/usr/bin/env python3
"""提取FDOTHER.DAT索引1的资源ID 1-18的实际图形数据"""
import os
import struct

DAT_PATH = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUT_DIR, exist_ok=True)

with open(DAT_PATH, 'rb') as f:
    data = f.read()

# 解析FDOTHER.DAT头部
idx_count = struct.unpack_from('<I', data, 6)[0]
print(f"总索引数: {idx_count}")

# 获取索引1的范围
idx1_offset = struct.unpack_from('<I', data, 0x0A + 1 * 4)[0]
idx2_offset = struct.unpack_from('<I', data, 0x0A + 2 * 4)[0]

idx1_data = data[idx1_offset:idx2_offset]
print(f"索引1数据范围: 0x{idx1_offset:X} - 0x{idx2_offset:X}, 大小: 0x{len(idx1_data):X}")

# 解析前0x46字节的4字节偏移表
# 用户指出前0x46字节包含偏移表。0x46=70字节。
# 为了提取资源ID 1-18，我们需要至少19个偏移值(0到18)来界定区间。
# 19 * 4 = 76字节 (0x4C)。我们将读取前0x4C字节。

print("\n解析4字节偏移表:")
offsets = []
for i in range(20):
    pos = i * 4
    if pos + 4 > len(idx1_data):
        break
    val = struct.unpack_from('<I', idx1_data, pos)[0]
    offsets.append(val)
    print(f"  [{i}] 0x{val:06X} ({val})")

# 提取资源ID 1-18
# 假设 offsets[1] 是资源1的起始，offsets[2] 是资源1的结束（即资源2的起始）
print("\n提取资源ID 1-18:")
for res_id in range(1, 19):
    if res_id >= len(offsets) - 1:
        # 如果没有下一个偏移，使用数据末尾
        start = offsets[res_id] if res_id < len(offsets) else 0
        end = len(idx1_data)
    else:
        start = offsets[res_id]
        end = offsets[res_id + 1]

    if start < end and start < len(idx1_data):
        size = end - start
        res_data = idx1_data[start:end]
        
        filename = f'idx1_res_{res_id}.bin'
        out_path = os.path.join(OUT_DIR, filename)
        with open(out_path, 'wb') as f:
            f.write(res_data)
        
        print(f"  ID {res_id:2d}: 偏移 0x{start:04X} - 0x{end:04X}, 大小 {size:4d} 字节 -> {filename}")
    else:
        print(f"  ID {res_id:2d}: 无效范围 (Start: {start}, End: {end})")

print("\n完成!")
