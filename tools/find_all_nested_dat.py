#!/usr/bin/env python3
"""查找FDOTHER.DAT中所有嵌套DAT格式的资源"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

if data[:6] != b'LLLLLL':
    print("FDOTHER.DAT 格式错误")
else:
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    print(f"资源总数: {count}")
    
    # 查找所有嵌套DAT (LLLLLL magic)
    nested_indices = []
    for i in range(count):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res = data[s:e]
        if res[:6] == b'LLLLLL':
            nested_count = struct.unpack_from('<I', res, 6)[0]
            nested_indices.append((i, len(res), nested_count))
    
    print(f"\n找到 {len(nested_indices)} 个嵌套DAT资源:")
    for idx, size, nested_count in nested_indices:
        print(f"  索引{idx}: 大小={size}, 嵌套数={nested_count}")
