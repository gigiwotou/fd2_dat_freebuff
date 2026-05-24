#!/usr/bin/env python3
"""分析索引6的嵌套DAT结构"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 获取索引6的资源
res6_start = offsets[6]
res6_end = offsets[7] if 7 < len(offsets) else len(data)
res6 = data[res6_start:res6_end]

print(f"索引6资源:")
print(f"  大小: {len(res6)} 字节")
print(f"  Magic: {res6[:6]}")

nested_count = struct.unpack_from('<I', res6, 6)[0]
print(f"  嵌套资源数: {nested_count}")

# 查看前几个偏移
offset_table_end = 10 + nested_count * 4
print(f"  偏移表结束位置: 0x{offset_table_end:X}")

print(f"\n前10个偏移:")
for i in range(min(10, nested_count)):
    offset = struct.unpack_from('<I', res6, 10 + i*4)[0]
    print(f"  [{i}] 0x{offset:08X} ({offset})")

# 检查第一个tile的数据
if nested_count > 0:
    tile0_offset = struct.unpack_from('<I', res6, 10)[0]
    print(f"\nTile 0 偏移: 0x{tile0_offset:X}")
    
    if tile0_offset < len(res6):
        tile0_data = res6[tile0_offset:tile0_offset+32]
        print(f"Tile 0 前32字节:")
        for i in range(0, 32, 16):
            hex_str = ' '.join(f'{b:02X}' for b in tile0_data[i:i+16])
            print(f"  {i:03d}: {hex_str}")
        
        # 检查是否有合理的宽高
        w = struct.unpack_from('<H', tile0_data, 0)[0]
        h = struct.unpack_from('<H', tile0_data, 2)[0]
        print(f"  [0-1] WORD: {w}")
        print(f"  [2-3] WORD: {h}")
        
        # 查看最后一个偏移
        if nested_count > 1:
            last_tile_offset = struct.unpack_from('<I', res6, 10 + (nested_count-1)*4)[0]
            print(f"\n最后一个Tile (索引{nested_count-1}) 偏移: 0x{last_tile_offset:X}")
            if last_tile_offset < len(res6):
                last_tile_data = res6[last_tile_offset:last_tile_offset+32]
                print(f"最后Tile 前32字节:")
                for i in range(0, 32, 16):
                    hex_str = ' '.join(f'{b:02X}' for b in last_tile_data[i:i+16])
                    print(f"  {i:03d}: {hex_str}")
