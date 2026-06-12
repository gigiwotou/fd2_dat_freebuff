"""
分析索引5的所有138个tile的实际格式
找出哪些tile解析失败以及失败原因
"""
import struct
import os
import sys

# 找 FDOTHER.DAT
fdother_paths = [
    "d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT",  # 原始文件
    "d:/workspace/fd2_dat_freebuff/FDOTHER.DAT",
    "d:/workspace/fd2_dat_freebuff/fdother.dat",
    "d:/workspace/fd2_dat_freebuff/FDOTHER",
    "D:/workspace/fd2_dat_freebuff/FDOTHER.DAT",
]

# 查找FDOTHER.DAT
fdother_path = None
for p in fdother_paths:
    if os.path.exists(p):
        fdother_path = p
        break

if not fdother_path:
    # 搜索整个目录
    for root, dirs, files in os.walk("d:/workspace/fd2_dat_freebuff"):
        for f in files:
            if f.upper() == "FDOTHER.DAT":
                fdother_path = os.path.join(root, f)
                break
        if fdother_path:
            break

if not fdother_path:
    print("ERROR: FDOTHER.DAT not found")
    sys.exit(1)

print(f"Found FDOTHER.DAT: {fdother_path}")

with open(fdother_path, "rb") as f:
    data = f.read()

# 解析FDOTHER.DAT顶层索引
# 格式: [magic:6 "LLLLLL"] + [offset_table: 4字节/项]
# 索引表项数通过 res_offset == 0 || res_offset > file_size 终止
if data[:6] != b"LLLLLL":
    print(f"ERROR: not a LLLLLL file, magic={data[:6]!r}")
    sys.exit(1)

# 找索引表项数
table_offset = 6
entry_count = 0
while table_offset + 4 <= len(data):
    res_offset = struct.unpack_from("<I", data, table_offset)[0]
    if res_offset == 0 or res_offset > len(data):
        break
    entry_count += 1
    table_offset += 4

print(f"FDOTHER.DAT: {entry_count} entries (table size {entry_count*4} bytes)")

# 找到索引5的偏移
idx5_offset_in_table = 6 + 5 * 4
res5_offset = struct.unpack_from("<I", data, idx5_offset_in_table)[0]

# 计算索引5的大小 (下一个非零偏移 - res5_offset)
table_idx = idx5_offset_in_table + 4
while table_idx + 4 <= len(data):
    next_off = struct.unpack_from("<I", data, table_idx)[0]
    if next_off == 0 or next_off > len(data):
        break
    table_idx += 4
res5_end = struct.unpack_from("<I", data, table_idx)[0]
res5_size = res5_end - res5_offset
print(f"索引5: offset={res5_offset}, size={res5_size}, end_offset={res5_end}")

# 读取索引5数据
res5_data = data[res5_offset:res5_offset + res5_size]
print(f"  magic: {res5_data[:4]!r}")
tile_count = struct.unpack_from("<H", res5_data, 4)[0]
print(f"  tile_count: {tile_count}")

# 读取所有tile偏移
tile_offsets = []
for i in range(tile_count + 1):
    off = struct.unpack_from("<I", res5_data, 6 + i * 4)[0]
    tile_offsets.append(off)

# 分析每个tile
print(f"\n=== 分析 {tile_count} 个 tile ===")
print(f"{'idx':>4} | {'offset':>8} | {'size':>5} | {'W':>4}x{'H':>3} | {'4+H':>6} | {'256':>4} | {'first 16 bytes'}")

fail_count = 0
fail_tiles = []
unique_sizes = {}

for i in range(tile_count):
    tile_offset = tile_offsets[i]
    next_offset = tile_offsets[i + 1]
    tile_size = next_offset - tile_offset

    # 读取前4字节作为可能的宽高头
    if tile_offset + 4 <= res5_size:
        w, h = struct.unpack_from("<HH", res5_data, tile_offset)
    else:
        w, h = 0, 0

    # 判断格式
    is_type_a = (w > 0 and w <= 1024 and h > 0 and h <= 1024
                 and (4 + w * h) == tile_size)
    is_type_b = (tile_size == 256)

    if not is_type_a and not is_type_b:
        fail_count += 1
        fail_tiles.append(i)
        first16 = res5_data[tile_offset:tile_offset+16].hex()
        print(f"{i:>4} | {tile_offset:>8} | {tile_size:>5} | {w:>4}x{h:<3} | {4+w*h:>6} | {'Y' if is_type_b else 'N':>4} | {first16}  *** FAIL ***")
    else:
        # 显示
        first16 = res5_data[tile_offset:tile_offset+8].hex()
        # 只在变化时打印
        if i < 5 or i >= tile_count - 5 or (i in fail_tiles if 'fail_tiles' in dir() else False):
            print(f"{i:>4} | {tile_offset:>8} | {tile_size:>5} | {w:>4}x{h:<3} | {4+w*h:>6} | {'Y' if is_type_b else 'N':>4} | {first16}")

    # 统计大小
    if tile_size not in unique_sizes:
        unique_sizes[tile_size] = 0
    unique_sizes[tile_size] += 1

print(f"\n=== 总结 ===")
print(f"总tile: {tile_count}")
print(f"解析失败: {fail_count}")
print(f"\n=== 唯一大小分布 ===")
for size, count in sorted(unique_sizes.items()):
    print(f"  size={size:>5}: {count} 个 tile")

if fail_tiles:
    print(f"\n=== 失败tile前10个详细数据 ===")
    for fi in fail_tiles[:10]:
        tile_offset = tile_offsets[fi]
        next_offset = tile_offsets[fi + 1]
        tile_size = next_offset - tile_offset
        w, h = struct.unpack_from("<HH", res5_data, tile_offset)
        # 看前 32 字节的 hex
        data_hex = res5_data[tile_offset:tile_offset+min(32, tile_size)].hex()
        # 计算每个非零字节后的字节数
        non_zero = sum(1 for b in res5_data[tile_offset+4:tile_offset+tile_size] if b != 0)
        print(f"  tile {fi}: w={w} h={h} size={tile_size} expected={4+w*h} non_zero={non_zero}")
        print(f"    data: {data_hex}")
