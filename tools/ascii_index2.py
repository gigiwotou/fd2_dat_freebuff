"""分析索引2子资源0的解码是否合理，输出 ASCII 可视化"""
import struct

FDOTHER_PATH = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"

with open(FDOTHER_PATH, "rb") as f:
    data = f.read()

offsets = []
pos = 6
while pos + 4 <= len(data):
    off = struct.unpack_from("<I", data, pos)[0]
    if off == 0 or off > len(data):
        break
    offsets.append(off)
    pos += 4

idx2_start = offsets[2]
idx2_end = offsets[3]
idx2_data = data[idx2_start:idx2_end]

# 78个dword偏移表
sub_offsets = []
for i in range(78):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    sub_offsets.append(off)
sub_offsets.append(len(idx2_data))


def decode_rle_correct(src, w, h):
    """与 sub_4E98D 一致的 RLE 解码"""
    src_idx = 0
    n_src = len(src)
    pixels = []
    for y in range(h):
        row = [0] * w
        bx = w
        dst_idx = 0
        while bx > 0:
            if src_idx >= n_src:
                break
            b = src[src_idx]
            top2 = b & 0xC0
            if top2 == 0x00:
                count = b + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                for i in range(min(count, w - dst_idx)):
                    row[dst_idx + i] = v
                dst_idx += count
                bx -= count
            elif top2 == 0x40:
                count = (b & 0x3F) + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                for i in range(count):
                    pos = dst_idx + 1 + i * 2
                    if pos < w:
                        row[pos] = v
                dst_idx += count * 2
                bx -= count * 2
            elif top2 == 0x80:
                count = (b & 0x3F) + 1
                src_idx += 1
                for i in range(min(count, w - dst_idx)):
                    if src_idx + i < n_src:
                        row[dst_idx + i] = src[src_idx + i]
                src_idx += count
                dst_idx += count
                bx -= count
            elif top2 == 0xC0:
                count = (b & 0x3F) + 1
                src_idx += 1
                dst_idx += count
                bx -= count
        pixels.append(row)
    return pixels


# 解码子资源 0
sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]

w = struct.unpack_from("<H", sub0_data, 0)[0]
h = struct.unpack_from("<H", sub0_data, 2)[0]
win = sub0_data[4]
print(f"子资源0: w={w}, h={h}, palette_window={win}")

pixels = decode_rle_correct(sub0_data[5:], w, h)

# ASCII 可视化: #表示非透明, .表示透明
print(f"\nASCII可视化 (palette_window={win}):")
for y, row in enumerate(pixels):
    line = "".join("#" if p != 0 else "." for p in row)
    print(f"  y={y:2d}: {line}")

# 总结
total = sum(sum(1 for p in row if p != 0) for row in pixels)
print(f"\n非透明像素: {total} / {w*h}")
