#!/usr/bin/env python3
"""
重新检查FDOTHER.DAT的标准格式

根据sub_111BA反汇编:
- fseek(file_handle, 4 * a7 + 6, 0)
- 读取8字节: [offset:4][next_offset:4]  
- 数据大小 = next_offset - offset

这意味着:
- 文件头: 6字节 (LLLLLL)
- 索引表: 从偏移6开始，每个索引4字节（只有偏移，没有大小）
- 索引n的数据范围: offsets[n] 到 offsets[n+1]
"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

print(f"文件大小: {len(data)} 字节")

# 读取magic
magic = data[:6]
print(f"Magic: {magic}")

if magic != b'LLLLLL':
    print("错误: 不是有效的DAT文件")
    exit(1)

# 根据sub_111BA的公式，索引表从偏移6开始，每个索引4字节
# 读取前几个索引验证
print(f"\n读取索引表（每个索引4字节，从偏移6开始）:")
for i in range(50):
    offset = 6 + i * 4
    if offset + 4 > len(data):
        break
    idx_offset = struct.unpack_from('<I', data, offset)[0]
    # 下一个索引的偏移（用于计算大小）
    if i + 1 < 422:  # 假设有422个索引
        next_offset_addr = 6 + (i + 1) * 4
        if next_offset_addr + 4 <= len(data):
            next_idx_offset = struct.unpack_from('<I', data, next_offset_addr)[0]
            size = next_idx_offset - idx_offset
            print(f"索引 {i:3d}: 偏移 0x{idx_offset:08X} ({idx_offset:8d}), 大小 {size:8d}")
    else:
        print(f"索引 {i:3d}: 偏移 0x{idx_offset:08X} ({idx_offset:8d})")
