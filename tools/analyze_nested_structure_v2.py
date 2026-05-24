#!/usr/bin/env python3
"""重新分析嵌套DAT偏移表结构"""
import struct

dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

# 获取索引82的资源
count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

res82_start = offsets[82]
res82_end = offsets[83] if 83 < len(offsets) else len(data)
res82 = data[res82_start:res82_end]

print(f"索引82资源:")
print(f"  大小: {len(res82)} 字节")

nested_count = struct.unpack_from('<I', res82, 6)[0]
print(f"  嵌套资源数: {nested_count}")

# 根据反汇编，每个偏移条目可能是14字节结构：
# [0-5]: 6字节未知 (可能包含其他元数据)
# [6-9]: DWORD - tile数据起始偏移
# [10-13]: DWORD - tile数据结束偏移

# 但资源数量 (26) 后面的数据是什么？
# 偏移10开始应该是偏移表，但条目大小是多少？

# 让我直接查看偏移10后面的数据
print(f"\n偏移10后的原始数据:")
for i in range(0, min(200, len(res82)-10), 4):
    val = struct.unpack_from('<I', res82, 10 + i)[0]
    print(f"  +{10+i:04X}: 0x{val:08X} ({val})")
    if i > 100 and val > len(res82):
        break

# 检查26是否真的是嵌套资源数
print(f"\n索引6处DWORD: 0x{struct.unpack_from('<I', res82, 6)[0]:08X}")

# 让我检查是否有6字节对齐的偏移表
# 即每个条目是: [6字节][DWORD起始][DWORD结束] = 14字节
# 或者是更小的结构

# 查看前几个可能的tile数据区域
# 假设偏移表条目是4字节 (传统的DWORD偏移)
print(f"\n假设传统4字节偏移表:")
for i in range(min(5, nested_count)):
    tile_offset = struct.unpack_from('<I', res82, 10 + i*4)[0]
    if tile_offset < len(res82):
        tile_data = res82[tile_offset:tile_offset+20]
        print(f"  Tile {i} 偏移: 0x{tile_offset:X}")
        print(f"    前20字节: {' '.join(f'{b:02X}' for b in tile_data)}")
        
        # 检查是否全部是RLE像素数据 (0x70-0x9F范围)
        is_rle = all(0x60 <= b <= 0xAF for b in tile_data)
        print(f"    可能是RLE像素数据: {is_rle}")

# 另一种可能：嵌套资源数后面的数据本身不是偏移表，而是其他格式
# 比如直接是tile数据，或者有不同的结构

# 让我检查26后面是否直接跟了RLE数据
after_count = res82[10:100]
print(f"\n资源数后面的数据:")
for i in range(0, min(90, len(after_count)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in after_count[i:i+16])
    print(f"  {10+i:04X}: {hex_str}")
