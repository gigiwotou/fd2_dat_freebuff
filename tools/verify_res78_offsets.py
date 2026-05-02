#!/usr/bin/env python3
"""
直接检查FDOTHER.DAT的偏移表来正确定位res78
"""
import struct
import os

dat_path = os.path.join('game', 'FDOTHER.DAT')

with open(dat_path, 'rb') as f:
    data = f.read()

print(f"FDOTHER.DAT文件大小: {len(data)} bytes")
print(f"Magic: {data[:6]}")
count = struct.unpack_from('<I', data, 6)[0]
print(f"Resource count: {count}")

# 偏移表从0x0A开始
offset_table_start = 0x0A

# 读取所有偏移
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, offset_table_start + i*4)[0]
    offsets.append(off)

# 检查res78
idx = 78
res78_start = offsets[idx]
res78_end = offsets[idx + 1] if idx + 1 < count else len(data)
res78_size = res78_end - res78_start

print(f"\nResource #{idx}:")
print(f"  Start offset in file: 0x{res78_start:x} ({res78_start})")
print(f"  End offset in file: 0x{res78_end:x} ({res78_end})")
print(f"  Size: {res78_size} bytes")

# 读取res78数据
res78 = data[res78_start:res78_end]
print(f"\nres78前32字节: {res78[:32].hex()}")

# 现在根据IDA汇编解析res78头部
# sub_25A96: v8 = buffer, arg_4 = 0
# v13 = *(v8+6) + v8  → sample start = buffer + *(6)
# v12 = *(v8+10) - *(v8+6) → sample size = *(10) - *(6)

# 但*(6)和*(10)作为32-bit值太大了
# 也许应该解读为16-bit值？

print(f"\n尝试16-bit解析:")
v6_w = struct.unpack_from('<H', res78, 6)[0]
v10_w = struct.unpack_from('<H', res78, 10)[0]
print(f"  *(6) as WORD = {v6_w}")
print(f"  *(10) as WORD = {v10_w}")

# 或者，让我们看看res78内部结构
# 也许前16字节是某种头，之后才是真正的样本数据

print(f"\nres78头部逐字节:")
for i in range(16):
    print(f"  offset[{i}] = 0x{res78[i]:02x} ({res78[i]})")

# 检查是否像嵌套的资源格式
# LL header format?
if res78[:2] == b'LL' or res78[:4] == b'LMI1':
    print("\n这是嵌套的LL格式!")

# 尝试不同的头部长度
for header_size in [0, 4, 8, 16, 32]:
    sample_data = res78[header_size:]
    if len(sample_data) < 50:
        continue
    print(f"\n假设头部{header_size}字节:")
    print(f"  样本大小: {len(sample_data)}")
    print(f"  样本前16字节: {sample_data[:16].hex()}")

# 重点: 检查*(0x2C)处的值，这是sub_25A96可能使用的偏移
if len(res78) > 0x30:
    print(f"\n*(0x2C) = {struct.unpack_from('<I', res78, 0x2C)[0]}")
    print(f"*(0x28) = {struct.unpack_from('<I', res78, 0x28)[0]}")
    print(f"*(0x24) = {struct.unpack_from('<I', res78, 0x24)[0]}")
    print(f"*(0x20) = {struct.unpack_from('<I', res78, 0x20)[0]}")
    print(f"*(0x1C) = {struct.unpack_from('<I', res78, 0x1C)[0]}")
    print(f"*(0x18) = {struct.unpack_from('<I', res78, 0x18)[0]}")
