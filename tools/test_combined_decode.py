"""
组合策略: 4E 范围 RLE + sub_4EC66 RLE + 未压缩
"""
import struct

fdother_path = "d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"
with open(fdother_path, "rb") as f:
    data = f.read()

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
    """4E 范围 RLE: FILL/ALT/COPY/SKIP, count = ((4*v)&0xFF)>>2+1"""
    pixels = []
    sp = 0
    out = 0
    while out < total and sp < len(src):
        v = src[sp]; sp += 1
        top2 = v & 0xC0
        count = (((4 * v) & 0xFF) >> 2) + 1
        if top2 == 0x00:  # FILL
            if sp >= len(src): return None
            value = src[sp]; sp += 1
            for k in range(min(count, total - out)):
                pixels.append(value)
                out += 1
        elif top2 == 0x40:  # ALT
            if sp >= len(src): return None
            value = src[sp]; sp += 1
            for k in range(min(count, total - out)):
                pixels.append(value)
                out += 1
            for k in range(min(count, total - out)):
                pixels.append(0)
                out += 1
        elif top2 == 0x80:  # COPY
            for k in range(min(count, total - out)):
                if sp >= len(src): return None
                pixels.append(src[sp])
                sp += 1
                out += 1
        else:  # SKIP
            for k in range(min(count, total - out)):
                pixels.append(0)
                out += 1
    if out != total: return None
    return pixels


def decode_sub4ec66(src, total):
    """sub_4EC66 协议: 0xC0 阈值, ah-al 状态机"""
    pixels = []
    sp = 0
    ah = 0
    al = 0
    for i in range(total):
        if ah == 0:
            if sp >= len(src): return None
            al = src[sp]; sp += 1
            if al > 0xC0:
                ah = (al - 0xC1) & 0xFF
                if sp >= len(src): return None
                al = src[sp]; sp += 1
        else:
            ah = (ah - 1) & 0xFF
        pixels.append(al)
    return pixels


def decode_uncompressed(src, total):
    """未压缩: 直接读 w*h 字节, 0=透明"""
    if len(src) < total: return None
    return list(src[:total])


# 组合策略解码
print(f"=== 138 个 tile 的组合策略解码结果 ===")
results = {}  # ti -> (method, pixels)
fail = []

for ti in range(tile_count):
    off = tile_offsets[ti]
    size = tile_offsets[ti+1] - off
    if off + 4 > len(res5):
        fail.append((ti, "truncated"))
        continue
    w, h = struct.unpack_from("<HH", res5, off)
    if w <= 0 or w > 1024 or h <= 0 or h > 1024:
        fail.append((ti, f"bad w/h: {w}x{h}"))
        continue
    src = res5[off+4:off+size]
    total = w * h

    # 策略 1: 未压缩
    if len(src) == total:
        pixels = decode_uncompressed(src, total)
        if pixels is not None:
            results[ti] = ("uncompressed", pixels)
            continue

    # 策略 2: 4E 范围 RLE
    pixels = decode_4e_rle(src, total)
    if pixels is not None:
        results[ti] = ("4e_rle", pixels)
        continue

    # 策略 3: sub_4EC66 RLE
    pixels = decode_sub4ec66(src, total)
    if pixels is not None:
        results[ti] = ("sub4ec66", pixels)
        continue

    # 策略 4: 未压缩 (即使 size < w*h, 取前 size 字节填充)
    fail.append((ti, f"all fail (w={w} h={h} size={size})"))

print(f"Success: {len(results)}/{tile_count}")
print(f"Failed: {len(fail)}")
for ti, reason in fail:
    print(f"  tile {ti}: {reason}")

# 统计方法分布
from collections import Counter
methods = Counter(m for m, _ in results.values())
print(f"\nMethod distribution: {dict(methods)}")
