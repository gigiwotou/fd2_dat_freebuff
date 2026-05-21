#!/usr/bin/env python3
"""
深度分析DATO.DAT索引表

发现:
- 前139个条目(索引0-138)有效
- 条目135之后出现异常: 索引136的start=16(跳回文件头部)
- 这意味着可能有多个索引表段，或数据结构不同

目标:
1. 完整分析所有554个索引条目
2. 找出所有"有效"的索引范围段
3. 理解为何索引136的start跳回16
"""

import struct
from pathlib import Path

GAME_DIR = Path(__file__).parent.parent / "game"
DATO_PATH = GAME_DIR / "DATO.DAT"

with open(DATO_PATH, 'rb') as f:
    dato_data = f.read()

file_size = len(dato_data)
print(f"文件大小: {file_size} 字节")

# 读取索引数量
count = struct.unpack('<I', dato_data[6:10])[0]
print(f"索引数量: {count}")
print(f"索引表起始偏移: {10}")
print(f"索引表总大小: {count * 4} 字节")
print(f"索引表结束偏移: {10 + count * 4}")
print()

# 分析所有索引条目
print(f"{'索引':<6} {'start':<10} {'end':<10} {'size':<10} {'start%文件':<10} {'有效?':<6} {'备注'}")
print("-" * 80)

prev_end = None
segment_count = 0
segments = []
current_segment_start = 0

for i in range(count):
    offset = 10 + i * 4
    if offset + 4 > file_size:
        print(f"索引{i}: 超出文件范围")
        break
    
    start = struct.unpack('<I', dato_data[offset:offset+4])[0]
    
    # 获取下一个索引的start作为end
    next_offset = 10 + (i + 1) * 4
    if next_offset + 4 <= file_size:
        end = struct.unpack('<I', dato_data[next_offset:next_offset+4])[0]
    else:
        end = file_size
    
    size = end - start
    is_valid = start < file_size and end <= file_size and size > 0
    start_pct = start / file_size * 100
    
    # 检测新段：如果start < prev_end，说明跳回到文件前面
    is_new_segment = False
    if prev_end is not None and start < prev_end - 100:  # 容忍100字节误差
        is_new_segment = True
        segment_count += 1
        segments.append((i, start))
    
    remark = ""
    if i == 0:
        remark = "文件头段开始"
        current_segment_start = 0
    elif is_new_segment:
        remark = f"<<< 新段开始 (跳回到{start})"
        current_segment_start = i
    
    if i < 145 or is_new_segment:  # 显示前145个和新段
        print(f"[{i:<4}] {start:<10} {end:<10} {size:<10} {start_pct:<10.2f}% {'是' if is_valid else '否':<6} {remark}")

print()
print("="*60)
print("段分析:")
print("="*60)

# 找出所有段
current_start = 0
prev_start_val = 0
for i in range(count):
    offset = 10 + i * 4
    start = struct.unpack('<I', dato_data[offset:offset+4])[0]
    
    if i > 0 and start < prev_start_val - 100:
        print(f"段 {current_start} - {i-1}: 共{i-current_start}个条目")
        current_start = i
    
    prev_start_val = start

print(f"段 {current_start} - {count-1}: 共{count-current_start}个条目")

# 检查段136的start=16是什么
print("\n" + "="*60)
print("检查索引136附近:")
print("="*60)
for i in range(130, min(145, count)):
    offset = 10 + i * 4
    start = struct.unpack('<I', dato_data[offset:offset+4])[0]
    next_offset = 10 + (i + 1) * 4
    if next_offset + 4 <= file_size:
        end = struct.unpack('<I', dato_data[next_offset:next_offset+4])[0]
    else:
        end = file_size
    print(f"[{i}] start={start} end={end} size={end-start}")

# 检查start=16处是什么
print(f"\n偏移16处的4字节: {struct.unpack('<I', dato_data[16:20])[0]}")
print(f"偏移16处的数据前16字节: {dato_data[16:32].hex()}")
