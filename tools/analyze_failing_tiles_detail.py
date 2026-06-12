"""
完整分析每个失败 tile 的数据, 并按多种 RLE 协议尝试解码
"""
import struct
import os
import sys

fdother_path = None
for p in ["d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT",
          "d:/workspace/fd2_dat_freebuff/FDOTHER.DAT"]:
    if os.path.exists(p):
        fdother_path = p
        break

if not fdother_path:
    print("ERROR: FDOTHER.DAT not found")
    sys.exit(1)

print(f"Found: {fdother_path}")
with open(fdother_path, "rb") as f:
    data = f.read()

# 解析顶层索引
table_offset = 6
entry_count = 0
while table_offset + 4 <= len(data):
    res_offset = struct.unpack_from("<I", data, table_offset)[0]
    if res_offset == 0 or res_offset > len(data):
        break
    entry_count += 1
    table_offset += 4

# 找索引5
idx5_offset = struct.unpack_from("<I", data, 6 + 5 * 4)[0]
table_idx = 6 + 5 * 4 + 4
while table_idx + 4 <= len(data):
    next_off = struct.unpack_from("<I", data, table_idx)[0]
    if next_off == 0 or next_off > len(data):
        break
    table_idx += 4
idx5_end = struct.unpack_from("<I", data, table_idx)[0]
res5 = data[idx5_offset:idx5_end]
tile_count = struct.unpack_from("<H", res5, 4)[0]
tile_offsets = [struct.unpack_from("<I", res5, 6 + i * 4)[0] for i in range(tile_count + 1)]

# 失败tile列表
fail_tiles = [20, 21, 22, 31, 32, 33, 34, 35, 36, 38, 39, 41, 42, 43, 44, 45, 46, 47, 49, 50, 52,
              68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
              93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 126, 127, 129, 130, 131, 132, 133, 134, 135, 136, 137]

# 完整查看失败tile 31, 32, 33, 35, 68, 69, 70
for ti in [31, 32, 33, 35, 41, 42, 68, 69, 70, 71, 90, 130, 134]:
    if ti >= tile_count: continue
    off = tile_offsets[ti]
    next_off = tile_offsets[ti + 1]
    size = next_off - off
    w, h = struct.unpack_from("<HH", res5, off)
    full = res5[off:off + size]
    print(f"\n=== tile {ti}: w={w} h={h} size={size} (expected {4+w*h}) ===")
    # 完整 hex, 每行16字节
    for i in range(0, len(full), 16):
        chunk = full[i:i+16]
        print(f"  {i:4d}: {chunk.hex()}")
    # 字节值直方图
    hist = [0] * 256
    for b in full[4:]:
        hist[b] += 1
    # 显示高频字节
    high = [(b, c) for b, c in enumerate(hist) if c >= 3]
    high.sort(key=lambda x: -x[1])
    print(f"  high bytes: {[(hex(b), c) for b, c in high[:10]]}")
