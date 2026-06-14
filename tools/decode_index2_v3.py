"""正确的 sub_4E98D RLE 解码器 (FILL2 模式正确处理)"""
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
    """与 sub_4E98D 一致的 RLE 解码 - 正确处理 FILL2 模式"""
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
                # FILL
                count = b + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                for i in range(min(count, w - dst_idx)):
                    row[dst_idx + i] = v
                dst_idx += count
                bx -= count
            elif top2 == 0x40:
                # FILL2 - 隔一个写, 但每次循环 inc edi (skip 1) + stosb
                # 起始 dst_idx, 第一次写入 dst_idx+1
                # 然后 dst_idx+3, dst_idx+5, ..., dst_idx+(2*count-1)
                # 总共消耗 2*count 像素
                count = (b & 0x3F) + 1
                v = src[src_idx + 1] if src_idx + 1 < n_src else 0
                src_idx += 2
                # 写入 dst_idx+1, +3, +5, ..., +(2*count-1)
                for i in range(count):
                    pos = dst_idx + 1 + i * 2
                    if pos < w:
                        row[pos] = v
                dst_idx += count * 2
                bx -= count * 2
            elif top2 == 0x80:
                # COPY
                count = (b & 0x3F) + 1
                src_idx += 1
                for i in range(min(count, w - dst_idx)):
                    if src_idx + i < n_src:
                        row[dst_idx + i] = src[src_idx + i]
                src_idx += count
                dst_idx += count
                bx -= count
            elif top2 == 0xC0:
                # SKIP
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

pixels = decode_rle_v3(sub0_data[5:], w, h)

# ASCII 可视化
print(f"\nASCII可视化:")
for y, row in enumerate(pixels):
    line = "".join("#" if p != 0 else "." for p in row)
    print(f"  y={y:2d}: {line}")

# 总结
total = sum(sum(1 for p in row if p != 0) for row in pixels)
print(f"\n非透明像素: {total} / {w*h}")

# 应用调色板窗口
print(f"\n应用调色板窗口 win={win} 后:")
for y, row in enumerate(pixels):
    if y < 5:
        line = " ".join(f"{(p+win)&0xFF:02X}" if p != 0 else ".." for p in row)
        print(f"  y={y:2d}: {line}")
