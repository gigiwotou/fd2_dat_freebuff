#!/usr/bin/env python3
"""
分析多个res资源的头部结构，找出规律
"""
import struct
import os

dat_path = os.path.join('game', 'FDOTHER.DAT')

with open(dat_path, 'rb') as f:
    # 解析文件头
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # 读取offset table
    f.seek(0x0A)
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])

# 分析多个res资源的头部
res_ids_to_check = [7, 8, 9, 10, 15, 20, 34, 39, 74, 78]

print("资源头部结构分析:")
print("="*80)

for idx in res_ids_to_check:
    if idx >= count:
        continue
    
    start = offsets[idx]
    end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
    size = end - start
    
    with open(dat_path, 'rb') as f:
        f.seek(start)
        raw = f.read(min(64, size))
    
    print(f"\nResource #{idx} (size={size}):")
    print(f"  前32字节: {raw[:32].hex()}")
    print(f"  *(0) [4B LE]: {struct.unpack_from('<I', raw, 0)[0]}")
    print(f"  *(4) [4B LE]: {struct.unpack_from('<I', raw, 4)[0]}")
    print(f"  *(8) [4B LE]: {struct.unpack_from('<I', raw, 8)[0]}")
    print(f"  *(12) [4B LE]: {struct.unpack_from('<I', raw, 12)[0]}")

# 重点分析res9（已知可以正常工作的音效）
print("\n" + "="*80)
print("res9 深度分析:")
print("="*80)

idx = 9
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
size = end - start

with open(dat_path, 'rb') as f:
    f.seek(start)
    raw9 = f.read(size)

print(f"res9 size: {size}")
print(f"res9 前128字节:")
for i in range(0, min(128, len(raw9)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in raw9[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw9[i:i+16])
    print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")

# 重点分析res78
print("\n" + "="*80)
print("res78 深度分析:")
print("="*80)

idx = 78
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)
size = end - start

with open(dat_path, 'rb') as f:
    f.seek(start)
    raw78 = f.read(size)

print(f"res78 size: {size}")
print(f"res78 前128字节:")
for i in range(0, min(128, len(raw78)), 16):
    hex_str = ' '.join(f'{b:02x}' for b in raw78[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw78[i:i+16])
    print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")

# 对比res9和res78的字节分布
print("\n" + "="*80)
print("res9 vs res78 字节分布对比:")
print("="*80)

def byte_stats(data, name):
    print(f"\n{name}:")
    print(f"  大小: {len(data)}")
    print(f"  范围: 0x{min(data):02x} - 0x{max(data):02x}")
    print(f"  平均值: {sum(data)/len(data):.1f}")
    
    # 检查是否有明显的模式
    high_bits = sum(1 for b in data if b & 0x80)
    low_bits = len(data) - high_bits
    print(f"  高位(0x80+)比例: {high_bits/len(data)*100:.1f}%")

byte_stats(raw9, "res9完整数据")
byte_stats(raw9[4:], "res9[4:]数据")
byte_stats(raw78, "res78完整数据")
byte_stats(raw78[4:], "res78[4:]数据")
