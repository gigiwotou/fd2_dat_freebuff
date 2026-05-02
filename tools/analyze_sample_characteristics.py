#!/usr/bin/env python3
"""
分析res78样本数据特征，确定编码格式
"""
import struct
import os
from collections import Counter

# 加载样本
with open('output/sfx_wav/res078_lightning/sample_raw.bin', 'rb') as f:
    sample = f.read()

print(f"样本大小: {len(sample)} bytes")
print(f"前64字节: {sample[:64].hex()}")

# 前16字节看起来像头部
header = sample[:16]
data = sample[16:]

print(f"\n头部 (16 bytes): {header.hex()}")
print(f"  *(0) = {struct.unpack_from('<I', header, 0)[0]}")
print(f"  *(4) = {struct.unpack_from('<I', header, 4)[0]}")
print(f"  *(8) = {struct.unpack_from('<I', header, 8)[0]}")
print(f"  *(12) = {struct.unpack_from('<I', header, 12)[0]}")

print(f"\n数据部分 (从偏移16开始): {len(data)} bytes")
print(f"数据前32字节: {data[:32].hex()}")

# 分析数据部分的字节分布
print(f"\n数据字节分布分析:")
print(f"  范围: 0x{min(data):02x} - 0x{max(data):02x}")
print(f"  平均值: {sum(data)/len(data):.1f}")
print(f"  中位数: {sorted(data)[len(data)//2]}")

counter = Counter(data)
print(f"  最常见的10个字节: {counter.most_common(10)}")

# 检查高4位和低4位的分布
high_nibbles = [(b >> 4) & 0x0F for b in data]
low_nibbles = [b & 0x0F for b in data]
print(f"\nNibble分析:")
print(f"  高4位范围: {min(high_nibbles)} - {max(high_nibbles)}")
print(f"  低4位范围: {min(low_nibbles)} - {max(low_nibbles)}")

high_counter = Counter(high_nibbles)
low_counter = Counter(low_nibbles)
print(f"  高4位分布: {dict(sorted(high_counter.items()))}")
print(f"  低4位分布: {dict(sorted(low_counter.items()))}")

# 检查是否像IMA ADPCM (高4位应该集中在7-8附近)
print(f"\n如果是IMA ADPCM:")
print(f"  高4位平均值: {sum(high_nibbles)/len(high_nibbles):.2f}")
print(f"  低4位平均值: {sum(low_nibbles)/len(low_nibbles):.2f}")

# 检查相邻字节差值（delta编码特征）
diffs = [abs(data[i] - data[i-1]) for i in range(1, min(1000, len(data)))]
avg_diff = sum(diffs) / len(diffs)
print(f"\nDelta编码分析:")
print(f"  前1000字节平均差值: {avg_diff:.2f}")
print(f"  最大差值: {max(diffs)}")

# 检查是否有明显的周期性
print(f"\n尝试检测周期性:")
for period in [2, 4, 8, 16]:
    correlations = []
    for i in range(0, min(1000-period, len(data)-period)):
        correlations.append(abs(data[i] - data[i+period]))
    avg_corr = sum(correlations) / len(correlations)
    print(f"  周期{period}: 平均相关差值 = {avg_corr:.2f}")
