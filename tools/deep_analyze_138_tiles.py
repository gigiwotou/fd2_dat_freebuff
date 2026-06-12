"""
详细分析所有138个tile，找出'解析成功但实际错误'的情况:
1. 错误的分辨率 (w/h 异常)
2. 解码方法选择错误 (本应A方法却用B方法)
3. 解码后图像完全不像图 (全0/全相同值/全0xff/被截断)
"""
import struct
from collections import Counter

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


def is_reasonable_pixels(pixels, w, h):
    """检查像素是否合理 (不是全0, 不是全相同值, 不是大部分是0)"""
    if pixels is None:
        return False
    n = len(pixels)
    if n == 0:
        return False
    nz = sum(1 for p in pixels if p != 0)
    # 至少要有些非0像素
    if nz < 5:
        return False, f"只有 {nz}/{n} 个非0像素"
    return True, "ok"


# 统计每个tile的尺寸分布
print("=== 138个tile的尺寸分析 ===")
dims = Counter()
for ti in range(tile_count):
    off = tile_offsets[ti]
    size = tile_offsets[ti+1] - off
    if off + 4 > len(res5):
        continue
    w, h = struct.unpack_from("<HH", res5, off)
    dims[(w, h)] += 1

print("不同尺寸分布:")
for d, c in sorted(dims.items()):
    print(f"  {d[0]}x{d[1]}: {c}个")

print(f"\n=== 详细分析每个tile ===")
print(f"{'idx':>3} {'w':>4} {'h':>4} {'size':>5} {'ratio':>6} {'method':>14} {'nz%':>5} {'uniq':>4} {'状态'}")
print("-" * 80)

suspect = []
for ti in range(tile_count):
    try:
        off = tile_offsets[ti]
        size = tile_offsets[ti+1] - off
        if off + 4 > len(res5):
            continue
        w, h = struct.unpack_from("<HH", res5, off)
        src = res5[off+4:off+size]
        total = w * h
        ratio = size / max(total, 1)

        # 试所有方法
        methods_tried = []
        pixels_uncomp = decode_uncompressed(src, total) if len(src) >= total else None
        pixels_4e = decode_4e_rle(src, total)
        pixels_sub4ec66 = decode_sub4ec66(src, total)

        # 哪个方法返回了有效结果?
        valid_methods = []
        if pixels_uncomp is not None and len(pixels_uncomp) == total:
            valid_methods.append(("uncomp", pixels_uncomp))
        if pixels_4e is not None:
            valid_methods.append(("4e", pixels_4e))
        if pixels_sub4ec66 is not None:
            valid_methods.append(("sub4ec66", pixels_sub4ec66))

        # 期望的方法: 基于size/total ratio
        # - size == total: uncompressed
        # - size < total: 压缩
        expected_method = "uncomp" if len(src) == total else "压缩"

        # 选择最终方法
        chosen_method = None
        chosen_pixels = None
        if len(src) >= total:
            chosen_method = "uncomp"
            chosen_pixels = pixels_uncomp
        else:
            if pixels_4e is not None:
                chosen_method = "4e"
                chosen_pixels = pixels_4e
            elif pixels_sub4ec66 is not None:
                chosen_method = "sub4ec66"
                chosen_pixels = pixels_sub4ec66

        if chosen_pixels is None:
            print(f"{ti:>3} {w:>4} {h:>4} {size:>5} {ratio:>6.2f} {'FAIL':>14}")
            suspect.append((ti, w, h, size, "FAIL"))
            continue

        nz = sum(1 for p in chosen_pixels if p != 0)
        nz_pct = 100.0 * nz / max(len(chosen_pixels), 1)
        uniq = len(set(chosen_pixels))

        # 检查异常情况
        flags = []
        if nz < 5:
            flags.append("几乎全0")
        if uniq <= 2:
            flags.append(f"只有{uniq}种值")
        # 检查尺寸是否异常
        if w > 100 or h > 100:
            flags.append(f"尺寸异常大")
        if w < 5 or h < 5:
            flags.append(f"尺寸异常小")
        # 多种方法都成功时, 可能选择错了
        if len(valid_methods) > 1:
            flags.append(f"多种方法都成功{len(valid_methods)}")

        status = " | ".join(flags) if flags else "OK"
        if flags:
            suspect.append((ti, w, h, size, chosen_method, nz_pct, uniq, flags, valid_methods))

        print(f"{ti:>3} {w:>4} {h:>4} {size:>5} {ratio:>6.2f} {chosen_method:>14} {nz_pct:>4.0f}% {uniq:>4} {status}")
    except Exception as e:
        print(f"{ti:>3} ERROR: {e}")
        continue

print(f"\n=== 怀疑有问题的tile: {len(suspect)} ===")
for s in suspect:
    print(f"  tile {s[0]}: w={s[1]} h={s[2]} size={s[3]} {s[4:]}")
