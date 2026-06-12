"""
用 4E 范围 RLE 试解所有 138 个 tile
"""
import struct
import os
import sys

fdother_path = "d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"
with open(fdother_path, "rb") as f:
    data = f.read()

table_offset = 6
entry_count = 0
while table_offset + 4 <= len(data):
    res_offset = struct.unpack_from("<I", data, table_offset)[0]
    if res_offset == 0 or res_offset > len(data):
        break
    entry_count += 1
    table_offset += 4

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


def decode_4e_rle(src, total):
    """4E 范围 RLE 解码: FILL/ALT/COPY/SKIP, count = ((4*v)&0xFF)>>2+1"""
    pixels = []
    sp = 0
    out = 0
    while out < total and sp < len(src):
        v = src[sp]
        sp += 1
        top2 = v & 0xC0
        count = (((4 * v) & 0xFF) >> 2) + 1
        if top2 == 0x00:  # FILL
            if sp >= len(src): return None
            value = src[sp]
            sp += 1
            for k in range(min(count, total - out)):
                pixels.append(value)
                out += 1
        elif top2 == 0x40:  # ALT
            if sp >= len(src): return None
            value = src[sp]
            sp += 1
            for k in range(min(count, total - out)):
                pixels.append(value)
                out += 1
            for k in range(min(count, total - out)):
                pixels.append(0)  # 透明
                out += 1
        elif top2 == 0x80:  # COPY
            for k in range(min(count, total - out)):
                if sp >= len(src): return None
                pixels.append(src[sp])
                sp += 1
                out += 1
        else:  # SKIP
            for k in range(min(count, total - out)):
                pixels.append(0)  # 透明
                out += 1
    if out != total:
        return None
    return pixels


# 尝试所有 tile
print(f"=== 138 个 tile 的 4E 范围 RLE 解码结果 ===")
success = 0
fail = []
for i in range(tile_count):
    off = tile_offsets[i]
    size = tile_offsets[i + 1] - off
    if off + 4 > len(res5):
        fail.append((i, "truncated"))
        continue
    w, h = struct.unpack_from("<HH", res5, off)
    if w <= 0 or h <= 0 or w > 1024 or h > 1024:
        fail.append((i, f"bad w/h: {w}x{h}"))
        continue
    src = res5[off+4:off+size]
    total = w * h
    pixels = decode_4e_rle(src, total)
    if pixels is not None:
        success += 1
    else:
        fail.append((i, f"4E RLE fail (w={w} h={h} size={size} src={len(src)})"))

print(f"Success: {success}/{tile_count}")
print(f"Failed: {len(fail)}")
if fail:
    print("Failed tiles:")
    for i, reason in fail:
        print(f"  tile {i}: {reason}")
