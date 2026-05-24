#!/usr/bin/env python3
"""分析FDOTHER.DAT索引7的数据结构"""
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
    
    # 检查索引7
    start = offsets[7]
    end = offsets[8] if 8 < len(offsets) else len(data)
    res7 = data[start:end]
    
    print(f"\n索引 7:")
    print(f"  起始: 0x{start:X} ({start})")
    print(f"  结束: 0x{end:X} ({end})")
    print(f"  大小: {len(res7)} 字节")
    print(f"  前16字节: {res7[:16].hex()}")
    print(f"  前16字节ASCII: {res7[:16]}")
    
    # 检查是否是嵌套DAT
    if res7[:6] == b'LLLLLL':
        print("  是嵌套DAT格式")
        nested_count = struct.unpack_from('<I', res7, 6)[0]
        print(f"  嵌套资源数: {nested_count}")
    else:
        print("  不是嵌套DAT格式")
        
        # 检查是否是调色板数据 (768字节 = 256色 * 3)
        if len(res7) == 768:
            print("  大小768字节，可能是调色板数据")
            
    # 检查附近的索引看看哪些是嵌套DAT
    print(f"\n检查索引5-15:")
    for i in range(5, min(15, len(offsets))):
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res = data[s:e]
        is_llllll = res[:6] == b'LLLLLL'
        print(f"  索引{i}: 起始=0x{s:X}, 大小={len(res)}, LLLLLL={is_llllll}")
        if is_llllll:
            nested_count = struct.unpack_from('<I', res, 6)[0]
            print(f"    嵌套资源数: {nested_count}")
            # 打印前几个嵌套偏移
            for j in range(min(3, nested_count)):
                nested_offset = struct.unpack_from('<I', res, 10 + j*4)[0]
                print(f"    嵌套偏移[{j}]: 0x{nested_offset:X}")
