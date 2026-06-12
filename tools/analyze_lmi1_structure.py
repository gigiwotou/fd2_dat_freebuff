#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引5 (LMI1格式)的数据结构
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, index):
    """读取DAT资源"""
    index_offset = 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    return file_data[offset0:offset0 + size], offset0, size

# 分析索引5
print("=" * 70)
print("索引 5 分析 (LMI1)")
print("=" * 70)

res5, off5, size5 = read_dat_resource(data, 5)
print(f"偏移: {off5}, 大小: {size5}")
print(f"前20字节: {res5[:20].hex()}")

# 检查是否是LMI1
if res5[:4] == b'LMI1':
    print("类型: LMI1格式")
    tile_count = struct.unpack_from('<H', res5, 4)[0]
    print(f"Tile数量: {tile_count}")

    # 读取前几个偏移
    print(f"\n偏移表 (前10个tile):")
    for i in range(min(10, tile_count)):
        offset_addr = 6 + i * 4
        tile_offset = struct.unpack_from('<I', res5, offset_addr)[0]
        print(f"  tile[{i}]: offset={tile_offset}")

    # 尝试解析第一个tile的数据
    if tile_count > 0:
        tile0_offset = struct.unpack_from('<I', res5, 6)[0]
        tile0_data = res5[tile0_offset:]
        print(f"\n第一个tile数据 (offset {tile0_offset}):")
        print(f"  大小: {len(tile0_data)}")
        print(f"  前20字节: {tile0_data[:20].hex()}")

        # 检查是否有宽高头
        if len(tile0_data) >= 4:
            w = struct.unpack_from('<H', tile0_data, 0)[0]
            h = struct.unpack_from('<H', tile0_data, 2)[0]
            print(f"  可能的尺寸: {w}x{h}")

# 检查索引7 (嵌套DAT)
print("\n" + "=" * 70)
print("索引 7 分析 (嵌套DAT)")
print("=" * 70)

res7, off7, size7 = read_dat_resource(data, 7)
print(f"偏移: {off7}, 大小: {size7}")
print(f"前20字节: {res7[:20].hex()}")

# 检查是否是LLLLLL
if res7[:6] == b'LLLLLL':
    print("类型: LLLLLL格式 (嵌套DAT)")
    sub_count = struct.unpack_from('<I', res7, 6)[0]
    print(f"子资源数量: {sub_count}")

    # 读取前几个偏移
    print(f"\n偏移表 (前10个):")
    for i in range(min(10, sub_count)):
        offset_addr = 10 + i * 4
        if offset_addr + 4 <= len(res7):
            sub_offset = struct.unpack_from('<I', res7, offset_addr)[0]
            print(f"  sub[{i}]: offset={sub_offset}")

    # 解析第一个子资源
    if sub_count > 0:
        sub0_offset = struct.unpack_from('<I', res7, 10)[0]
        sub0_data = res7[sub0_offset:]
        print(f"\n第一个子资源数据 (offset {sub0_offset}):")
        print(f"  大小: {len(sub0_data)}")
        print(f"  前20字节: {sub0_data[:20].hex()}")

        if len(sub0_data) >= 5:
            w = struct.unpack_from('<H', sub0_data, 0)[0]
            h = struct.unpack_from('<H', sub0_data, 2)[0]
            win = sub0_data[4]
            print(f"  尺寸: {w}x{h}")
            print(f"  调色板窗口偏移: 0x{win:02X}")

# 检查索引11 (直接Tile)
print("\n" + "=" * 70)
print("索引 11 分析 (直接Tile)")
print("=" * 70)

res11, off11, size11 = read_dat_resource(data, 11)
print(f"偏移: {off11}, 大小: {size11}")
print(f"前20字节: {res11[:20].hex()}")

if len(res11) >= 5:
    w = struct.unpack_from('<H', res11, 0)[0]
    h = struct.unpack_from('<H', res11, 2)[0]
    win = res11[4]
    print(f"尺寸: {w}x{h}")
    print(f"调色板窗口偏移: 0x{win:02X}")
    print(f"RLE数据大小: {size11 - 5}")

print("\n" + "=" * 70)
