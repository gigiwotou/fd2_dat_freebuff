#!/usr/bin/env python3
"""
对比res9和res78的格式，理解正确的解码方式
"""
import struct
import os

dat_path = os.path.join('game', 'FDOTHER.DAT')

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    f.seek(0x0A)
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])

# 加载res9
idx = 9
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
with open(dat_path, 'rb') as f:
    f.seek(start)
    res9 = f.read(end - start)

# 加载res78
idx = 78
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
with open(dat_path, 'rb') as f:
    f.seek(start)
    res78 = f.read(end - start)

print("res9分析:")
print(f"  总大小: {len(res9)}")
print(f"  前32字节: {res9[:32].hex()}")
print(f"  *(0)={struct.unpack_from('<I', res9, 0)[0]}")
print(f"  *(4)={struct.unpack_from('<I', res9, 4)[0]}")
print(f"  *(8)={struct.unpack_from('<I', res9, 8)[0]}")
print(f"  *(12)={struct.unpack_from('<I', res9, 12)[0]}")

# res9的样本区域（跳过前16字节头部）
res9_data = res9[16:]
print(f"\n  数据部分: {len(res9_data)} bytes")
print(f"  数据前32字节: {res9_data[:32].hex()}")

# 统计res9_data的字节分布
from collections import Counter
res9_counter = Counter(res9_data)
print(f"  最常见字节: {res9_counter.most_common(10)}")

print("\n" + "="*60)
print("res78分析:")
print(f"  总大小: {len(res78)}")
print(f"  前32字节: {res78[:32].hex()}")
print(f"  *(0)={struct.unpack_from('<I', res78, 0)[0]}")
print(f"  *(4)={struct.unpack_from('<I', res78, 4)[0]}")
print(f"  *(8)={struct.unpack_from('<I', res78, 8)[0]}")
print(f"  *(12)={struct.unpack_from('<I', res78, 12)[0]}")

# res78的样本区域
res78_data = res78[16:]
print(f"\n  数据部分: {len(res78_data)} bytes")
print(f"  数据前32字节: {res78_data[:32].hex()}")

res78_counter = Counter(res78_data)
print(f"  最常见字节: {res78_counter.most_common(10)}")

# 现在尝试用res9相同的解码方式
print("\n" + "="*60)
print("res9数据特征:")

# 检查res9_data是否像8-bit PCM
vals = list(res9_data)
print(f"  范围: {min(vals)} - {max(vals)}")
print(f"  平均: {sum(vals)/len(vals):.1f}")

# 检查相邻差值
diffs9 = [abs(res9_data[i] - res9_data[i-1]) for i in range(1, min(500, len(res9_data)))]
print(f"  平均差值: {sum(diffs9)/len(diffs9):.2f}")

print("\nres78数据特征:")
vals78 = list(res78_data)
print(f"  范围: {min(vals78)} - {max(vals78)}")
print(f"  平均: {sum(vals78)/len(vals78):.1f}")

diffs78 = [abs(res78_data[i] - res78_data[i-1]) for i in range(1, min(500, len(res78_data)))]
print(f"  平均差值: {sum(diffs78)/len(diffs78):.2f}")

# 检查0xFF和0x81的模式
print("\nres78中特殊字节分析:")
for i in range(len(res78_data)):
    if res78_data[i] == 0xFF or res78_data[i] == 0x81:
        print(f"  偏移{i}: 0x{res78_data[i]:02x}, 前后字节: {res78_data[max(0,i-2):i+3].hex()}")
        if i > 20:
            break
