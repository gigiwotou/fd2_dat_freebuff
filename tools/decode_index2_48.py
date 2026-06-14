"""解码子资源48 (24x16, win=74)"""
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

sub_offsets = []
for i in range(78):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    sub_offsets.append(off)
sub_offsets.append(len(idx2_data))


def decode_rle_v3(src, w, h):
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


# 解码子资源 48
sub_off = sub_offsets[48]
sub_size = sub_offsets[49] - sub_off
sub_data = idx2_data[sub_off:sub_off+sub_size]

w = struct.unpack_from("<H", sub_data, 0)[0]
h = struct.unpack_from("<H", sub_data, 2)[0]
win = sub_data[4]
print(f"子资源48: w={w}, h={h}, palette_window={win}")

# 显示原始 RLE 字节
rle_data = sub_data[5:]
print(f"\nRLE 字节 (前 80 字节):")
for i in range(0, min(80, len(rle_data)), 16):
    line = " ".join(f"{b:02X}" for b in rle_data[i:i+16])
    print(f"  {i:3d}: {line}")

pixels = decode_rle_v3(rle_data, w, h)

print(f"\nASCII 可视化:")
for y, row in enumerate(pixels):
    line = "".join("#" if p != 0 else "." for p in row)
    print(f"  y={y:2d}: {line}")

print(f"\n应用调色板窗口 win={win} 后 (色索引):")
for y, row in enumerate(pixels):
    line = " ".join(f"{(p+win)&0xFF:02X}" if p != 0 else ".." for p in row)
    print(f"  y={y:2d}: {line}")
