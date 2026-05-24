#!/usr/bin/env python3
"""分析FDOTHER.DAT索引82-90和32-35，看看哪些是嵌套DAT"""
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
    
    # 检查索引32-35和82-90
    indices_to_check = list(range(32, 36)) + list(range(82, min(91, len(offsets))))
    
    print(f"\n检查动态索引场景:")
    for i in indices_to_check:
        if i >= len(offsets):
            continue
        s = offsets[i]
        e = offsets[i+1] if i+1 < len(offsets) else len(data)
        res = data[s:e]
        is_llllll = res[:6] == b'LLLLLL'
        print(f"\n  索引{i}: 起始=0x{s:X}, 大小={len(res)}, LLLLLL={is_llllll}")
        if is_llllll:
            nested_count = struct.unpack_from('<I', res, 6)[0]
            print(f"    嵌套资源数: {nested_count}")
            # 打印前几个嵌套偏移
            offset_table_end = 10 + nested_count * 4
            for j in range(min(5, nested_count)):
                nested_offset = struct.unpack_from('<I', res, 10 + j*4)[0]
                print(f"    嵌套偏移[{j}]: 0x{nested_offset:X} ({nested_offset})")
                if nested_offset < offset_table_end or nested_offset >= len(res):
                    print(f"      -> 偏移无效!")
                else:
                    tile_data = res[nested_offset:]
                    w = struct.unpack_from('<H', tile_data, 0)[0]
                    h = struct.unpack_from('<H', tile_data, 2)[0]
                    print(f"      -> 头: w={w}, h={h}")
