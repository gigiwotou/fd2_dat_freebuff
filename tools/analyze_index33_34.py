#!/usr/bin/env python3
"""分析索引33和34的资源结构"""
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
    
    # 检查索引33和34
    for idx in [33, 34]:
        res_start = offsets[idx]
        res_end = offsets[idx+1] if idx+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        print(f"\n=== 索引 {idx} (大小: {len(res_data)}) ===")
        
        if res_data[:6] == b'LLLLLL':
            print(f"  是嵌套DAT格式")
            nested_count = struct.unpack_from('<I', res_data, 6)[0]
            print(f"  嵌套资源数: {nested_count}")
            
            # 查看偏移表
            print(f"  偏移表 (前10个):")
            for i in range(min(10, nested_count)):
                offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
                print(f"    [{i}] 0x{offset:06X} ({offset})")
                if offset >= len(res_data):
                    print(f"      -> 偏移超出资源大小")
                    break
            
            # 检查第一个tile
            if nested_count > 0:
                tile0_offset = struct.unpack_from('<I', res_data, 10)[0]
                if tile0_offset < len(res_data):
                    tile0_data = res_data[tile0_offset:tile0_offset+32]
                    print(f"\n  Tile 0 前32字节:")
                    hex_str = ' '.join(f'{b:02X}' for b in tile0_data)
                    print(f"    {hex_str}")
                    
                    # 尝试解析宽高头
                    w = struct.unpack_from('<H', tile0_data, 0)[0]
                    h = struct.unpack_from('<H', tile0_data, 2)[0]
                    print(f"    [0-1] width?: {w}")
                    print(f"    [2-3] height?: {h}")
                    print(f"    [4-7]: 0x{struct.unpack_from('<I', tile0_data, 4)[0]:08X}")
                    print(f"    [8-9]: 0x{struct.unpack_from('<H', tile0_data, 8)[0]:04X}")
        else:
            print(f"  不是嵌套DAT格式")
            print(f"  前32字节: {res_data[:32].hex()}")
