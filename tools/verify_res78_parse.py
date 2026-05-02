#!/usr/bin/env python3
"""
验证res78解析 - 手动检查每个字节
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

idx = 78
start = offsets[idx]
end = offsets[idx + 1] if idx + 1 < count else os.path.getsize(dat_path)

with open(dat_path, 'rb') as f:
    f.seek(start)
    raw = f.read(end - start)

print(f"res78 total size: {len(raw)} bytes")
print(f"\n前64字节逐字节:")
for i in range(64):
    print(f"  offset[{i}] = 0x{raw[i]:02x} ({raw[i]})")

print(f"\n关键偏移的DWORD值:")
for offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24]:
    if offset + 4 <= len(raw):
        val = struct.unpack_from('<I', raw, offset)[0]
        print(f"  *({offset}) = 0x{val:08x} = {val}")

# 根据IDA: 样本从raw+*(6)开始, 大小=*(10)-*(6)
v6 = struct.unpack_from('<I', raw, 6)[0]
v10 = struct.unpack_from('<I', raw, 10)[0]

print(f"\nIDA解析:")
print(f"  v6  = *(6) = {v6}")
print(f"  v10 = *(10) = {v10}")
print(f"  样本起始 = {v6}")
print(f"  样本大小 = {v10 - v6}")

# 但也许*(6)和*(10)是相对文件开始而不是资源开始?
# 尝试将v6解释为FDOTHER.DAT中的绝对偏移
print(f"\n如果v6是绝对偏移:")
with open(dat_path, 'rb') as f:
    f.seek(0x0A + 78 * 4)
    # 读res78的offset entry
    res78_offset = struct.unpack('<I', f.read(4))[0]
    res78_next = struct.unpack('<I', f.read(4))[0]
    print(f"  res78 offset entry: {res78_offset}")
    print(f"  res78 next entry: {res78_next}")
    print(f"  res78 size from table: {res78_next - res78_offset}")
