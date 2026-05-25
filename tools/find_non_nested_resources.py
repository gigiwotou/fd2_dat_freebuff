#!/usr/bin/env python3
"""查找FDOTHER.DAT中是否有不同于嵌套DAT格式的资源"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

if data[:6] != b'LLLLLL':
    print("不是有效的 FDOTHER.DAT 文件")
else:
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    print(f"资源总数: {count}")
    
    # 检查所有资源的前16字节
    print(f"\n所有资源前16字节:")
    for i in range(min(100, count)):
        res_start = offsets[i]
        res_end = offsets[i+1] if i+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        prefix = res_data[:16].hex()
        is_llllll = res_data[:6] == b'LLLLLL'
        
        if not is_llllll:
            print(f"  索引{i} (0x{res_start:X}, {len(res_data)}字节): {prefix}  -> 非嵌套DAT")
