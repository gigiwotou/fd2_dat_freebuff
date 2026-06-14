"""正确的 RLE 解码 - 与 sub_4E98D 严格一致

控制字节 b:
  bit7=0, bit6=0 (b<0x40): FILL    count=b+1,            连续写 count 个填充值
  bit7=0, bit6=1 (0x40<=b<0x80): FILL2  count=(b&0x3F)+1, 隔一个写 count 个填充值 (bx减2*count)
  bit7=1, bit6=0 (0x80<=b<0xC0): COPY    count=(b&0x3F)+1, 连续从src复制count字节
  bit7=1, bit6=1 (b>=0xC0): SKIP      count=(b&0x3F)+1, 跳过count像素

FILL2 与其他模式不同: 写入的像素之间间隔一个空位, 相当于 ALT(隔写)
"""
import struct
import sys

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


def decode_rle_correct(src, w, h):
    """与 sub_4E98D 一致的 RLE 解码 (无调色板 value=-1)"""
    src_idx = 0
    pixels = []
    for y in range(h):
        row = [0] * w
        bx = w  # 剩余像素计数
        dst_idx = 0
        while bx > 0:
            if src_idx >= len(src):
                break
            b = src[src_idx]
            top2 = b & 0xC0
            if top2 == 0x00:
                # FILL: count = b + 1
                count = b + 1
                v = src[src_idx + 1]
                src_idx += 2
                for i in range(count):
                    if dst_idx + i < w:
                        row[dst_idx + i] = v
                dst_idx += count
            elif top2 == 0x40:
                # FILL2: count = (b & 0x3F) + 1, 隔一个写
                count = (b & 0x3F) + 1
                v = src[src_idx + 1]
                src_idx += 2
                for i in range(count):
                    pos = dst_idx + 1 + i * 2
                    if pos < w:
                        row[pos] = v
                dst_idx += count * 2
            elif top2 == 0x80:
                # COPY: count = (b & 0x3F) + 1
                count = (b & 0x3F) + 1
                src_idx += 1
                for i in range(count):
                    if dst_idx + i < w:
                        row[dst_idx + i] = src[src_idx + i]
                src_idx += count
                dst_idx += count
            elif top2 == 0xC0:
                # SKIP: count = (b & 0x3F) + 1
                count = (b & 0x3F) + 1
                src_idx += 1
                dst_idx += count
            bx -= count if top2 != 0x40 else count * 2
            if top2 == 0x40:
                bx -= count  # FILL2 减去 2*count
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
print(f"子资源0: w={w}, h={h}, palette_window={win}, RLE大小={sub0_size-5}")

pixels = decode_rle_correct(sub0_data[5:], w, h)
print(f"\n前10行像素 (应用调色板窗口 win={win}):")
for y, row in enumerate(pixels):
    if y < 10:
        line = " ".join(f"{(p+win)&0xFF:02X}" if p != 0 else ".." for p in row)
        print(f"  y={y:2d}: {line}")

print(f"\n像素分布:")
from collections import Counter
c = Counter()
for row in pixels:
    for p in row:
        c[p] += 1
for v, n in sorted(c.items()):
    print(f"  像素 {v:3d} (0x{v:02X}): {n} 次")
