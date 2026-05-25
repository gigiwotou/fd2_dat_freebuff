#!/usr/bin/env python3
"""分析索引34的资源结构"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
sizes = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    size = struct.unpack_from('<I', data, 10 + count * 4 + i * 4)[0]
    offsets.append(offset)
    sizes.append(size)

print(f"总索引数: {count}")
print(f"\n索引33:")
print(f"  偏移: 0x{offsets[33]:08X} ({offsets[33]})")
print(f"  大小: {sizes[33]}")
print(f"  前16字节: {' '.join(f'{b:02X}' for b in data[offsets[33]:offsets[33]+16])}")

print(f"\n索引34:")
print(f"  偏移: 0x{offsets[34]:08X} ({offsets[34]})")
print(f"  大小: {sizes[34]}")

res34_start = offsets[34]
res34_end = offsets[34] + sizes[34]
res34_data = data[res34_start:res34_end]

print(f"  实际读取大小: {len(res34_data)}")
print(f"\n前256字节:")
for i in range(0, 256, 16):
    hex_str = ' '.join(f'{b:02X}' for b in res34_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res34_data[i:i+16])
    print(f"  {i:03d}: {hex_str}  {ascii_str}")

# 尝试不同解析方式
print(f"\n解析尝试1: [width:2][height:2]")
w = struct.unpack_from('<H', res34_data, 0)[0]
h = struct.unpack_from('<H', res34_data, 2)[0]
print(f"  Width: {w}, Height: {h}")

print(f"\n解析尝试2: [count:2][count2:2]")
c1 = struct.unpack_from('<H', res34_data, 0)[0]
c2 = struct.unpack_from('<H', res34_data, 2)[0]
print(f"  Count1: {c1}, Count2: {c2}")

print(f"\n解析尝试3: 偏移表从偏移0开始")
for i in range(10):
    offset = struct.unpack_from('<I', res34_data, i * 4)[0]
    if offset < len(res34_data):
        print(f"  [{i}] 0x{offset:06X} ({offset})")
        # 查看该偏移处的数据
        if offset + 16 <= len(res34_data):
            print(f"    数据: {' '.join(f'{b:02X}' for b in res34_data[offset:offset+16])}")
    else:
        print(f"  [{i}] 0x{offset:08X} (超出范围)")
        break
