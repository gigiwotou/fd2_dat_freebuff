#!/usr/bin/env python3
"""直接查看嵌套DAT资源的原始数据结构"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 检查场景0 (索引33)
for scene_idx in [33, 34, 35]:
    res_start = offsets[scene_idx]
    res_end = offsets[scene_idx+1] if scene_idx+1 < len(offsets) else len(data)
    res_data = data[res_start:res_end]
    
    print(f"\n=== 索引 {scene_idx} (大小: {len(res_data)}) ===")
    print(f"  Magic: {res_data[:6]}")
    
    if res_data[:6] == b'LLLLLL':
        nested_count = struct.unpack_from('<I', res_data, 6)[0]
        print(f"  嵌套资源数: {nested_count}")
        
        # 查看偏移表
        print(f"  偏移表内容:")
        for i in range(min(nested_count, 10)):
            offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
            print(f"    [{i}] 0x{offset:08X} ({offset})")
        
        # 检查第一个tile数据
        if nested_count > 0:
            tile0_offset = struct.unpack_from('<I', res_data, 10)[0]
            if tile0_offset < len(res_data):
                tile0_data = res_data[tile0_offset:tile0_offset+64]
                print(f"\n  Tile 0 前64字节 (偏移 0x{tile0_offset:X}):")
                for i in range(0, 64, 16):
                    hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in tile0_data[i:i+16])
                    print(f"    {i:03d}: {hex_str}  {ascii_str}")
                
                # 字节范围
                values = list(tile0_data)
                print(f"  字节范围: {min(values)} (0x{min(values):02X}) - {max(values)} (0x{max(values):02X})")
                
                # 尝试不同的宽高头解释
                for header_offset in [0, 2, 4, 6, 8, 10]:
                    w = struct.unpack_from('<H', tile0_data, header_offset)[0]
                    h = struct.unpack_from('<H', tile0_data, header_offset+2)[0]
                    print(f"  头偏移{header_offset}: w={w}, h={h}")
