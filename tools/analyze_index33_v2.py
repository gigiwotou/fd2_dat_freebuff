#!/usr/bin/env python3
"""
根据sub_2EB9F的反汇编代码重新分析索引33/34的资源格式。

从反汇编看:
- v8 = a5 + *(DWORD *)(a5 + a1 + 8)  (a1是a6*4)
- width = *(WORD *)v8
- height = *(WORD *)(v8 + 2)
- RLE数据从 v8 + 9 开始

所以格式应该是: [width:2][height:2][?:5][RLE数据]

现在需要找到元数据表在哪里，以及如何定位到每个tile。
"""
import os
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_dir = os.path.join(WORKSPACE, "FD2_DAT")
fdother_path = os.path.join(dat_dir, "FDOTHER.DAT")

# 读取FDOTHER.DAT
with open(fdother_path, 'rb') as f:
    fdother_data = f.read()

print(f"FDOTHER.DAT 大小: {len(fdother_data)} 字节")

# 读取索引表（前6字节是LLLLLL magic，然后是4字节的索引数量，再是每个索引的8字节条目）
magic = fdother_data[:6]
print(f"Magic: {magic}")

if magic != b'LLLLLL':
    print("错误: 不是有效的FDOTHER.DAT文件")
    exit(1)

# 索引数量在偏移6处（4字节）
index_count = struct.unpack_from('<I', fdother_data, 6)[0]
print(f"索引数量: {index_count}")

# 索引表从偏移10开始（6 + 4）
index_table_start = 10

# 读取索引33和34的信息
for idx in [33, 34]:
    if idx >= index_count:
        print(f"\n索引 {idx} 超出范围")
        continue
    
    offset = index_table_start + idx * 8
    tile_offset = struct.unpack_from('<I', fdother_data, offset)[0]
    tile_size = struct.unpack_from('<I', fdother_data, offset + 4)[0]
    
    print(f"\n=== 索引 {idx} ===")
    print(f"偏移: 0x{tile_offset:08X} ({tile_offset})")
    print(f"大小: 0x{tile_size:08X} ({tile_size})")
    
    # 读取tile数据
    tile_data = fdother_data[tile_offset:tile_offset + tile_size]
    
    # 检查前16字节
    print(f"前16字节: {' '.join(f'{b:02x}' for b in tile_data[:16])}")
    
    # 解析为可能的格式: [width:2][height:2][?:5][RLE数据]
    if len(tile_data) >= 9:
        width = struct.unpack_from('<H', tile_data, 0)[0]
        height = struct.unpack_from('<H', tile_data, 2)[0]
        unknown = tile_data[4:9]
        
        print(f"假设格式 [width:2][height:2][?:5][RLE数据]:")
        print(f"  Width: {width}")
        print(f"  Height: {height}")
        print(f"  Unknown [4:9]: {' '.join(f'{b:02x}' for b in unknown)}")
        
        # 检查RLE数据开始处
        rle_start = 9
        if rle_start < len(tile_data):
            print(f"  RLE数据开始 ({rle_start}): {' '.join(f'{b:02x}' for b in tile_data[rle_start:rle_start+16])}")
            
            # 验证width和height是否合理
            if 0 < width <= 1024 and 0 < height <= 1024:
                print(f"  Width和Height看起来合理")
                expected_size = width * height
                actual_rle_size = tile_size - rle_start
                print(f"  预期像素数: {expected_size}")
                print(f"  实际RLE数据大小: {actual_rle_size}")
                print(f"  压缩比: {actual_rle_size / expected_size:.2f}" if expected_size > 0 else "  N/A")
            else:
                print(f"  Width或Height不合理，可能不是这个格式")

print("\n\n尝试另一种解析方式...")
print("索引33/34可能是直接包含多个tile的数组，需要先找到tile数量")

# 读取索引33
idx33_offset = struct.unpack_from('<I', fdother_data, index_table_start + 33 * 8)[0]
idx33_size = struct.unpack_from('<I', fdother_data, index_table_start + 33 * 8 + 4)[0]
idx33_data = fdother_data[idx33_offset:idx33_offset + idx33_size]

print(f"\n索引33 大小: {idx33_size}")
print(f"前64字节: {' '.join(f'{b:02x}' for b in idx33_data[:64])}")

# 尝试解析为: [tile_count:2][tile_entries...]
# 每个tile entry: [offset:4] 或 [offset:4][size:4]
tile_count = struct.unpack_from('<H', idx33_data, 0)[0]
print(f"\n如果[0:2]是tile数量: {tile_count}")
if tile_count < 1000:  # 合理的tile数量
    # 尝试解析偏移表
    entry_start = 2
    print(f"前几个可能的偏移:")
    for i in range(min(10, tile_count)):
        entry_offset = entry_start + i * 4
        if entry_offset + 4 <= len(idx33_data):
            offset_val = struct.unpack_from('<I', idx33_data, entry_offset)[0]
            print(f"  Tile {i}: 偏移 0x{offset_val:08X} ({offset_val})")
            # 检查这个偏移是否在合理范围内
            if offset_val < idx33_size:
                print(f"    数据: {' '.join(f'{b:02x}' for b in idx33_data[offset_val:offset_val+16])}")
