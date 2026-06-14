"""验证 decode_rle 函数"""
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

# 使用正确的RLE解码 - 与 sub_4E98D 严格一致
def decode_rle_v2(src, w, h):
    """sub_4E98D (无调色板版本 value=-1)

    控制字节:
      bit7=0, bit6=0 (b<0x40): FILL count=b+1, 下一个字节是填充值
      bit7=0, bit6=1 (0x40<=b<0x80): FILL2 count=(b&0x3F)+1, 下一个字节是填充值
      bit7=1, bit6=0 (0x80<=b<0xC0): COPY count=(b&0x3F)+1, 后面count个字节
      bit7=1, bit6=1 (b>=0xC0): SKIP count=((b&0x3F)>>2)+1
    """
    pixels = []
    src_idx = 0
    for y in range(h):
        row = []
        remaining = w
        while remaining > 0:
            if src_idx >= len(src):
                break
            b = src[src_idx]
            top2 = b & 0xC0
            if top2 == 0x00:
                # FILL (b<0x40): count = b+1
                count = (b & 0x3F) + 1
                v = src[src_idx+1]
                src_idx += 2
                row.extend([v] * count)
            elif top2 == 0x40:
                # FILL2 (0x40<=b<0x80): count = (b&0x3F)+1
                count = (b & 0x3F) + 1
                v = src[src_idx+1]
                src_idx += 2
                row.extend([v] * count)
            elif top2 == 0x80:
                # COPY (0x80<=b<0xC0): count = (b&0x3F)+1
                count = (b & 0x3F) + 1
                src_idx += 1
                for _ in range(count):
                    row.append(src[src_idx])
                    src_idx += 1
            elif top2 == 0xC0:
                # SKIP (b>=0xC0): count = ((b&0x3F)>>2)+1
                count = ((b & 0x3F) >> 2) + 1
                src_idx += 1
                row.extend([0] * count)
            remaining -= count
        pixels.append(row)
    return pixels

# 解码子资源 0
sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]

w = struct.unpack_from("<H", sub0_data, 0)[0]
h = struct.unpack_from("<H", sub0_data, 2)[0]
print(f"子资源0: w={w}, h={h}, RLE大小={sub0_size-5}")

pixels = decode_rle_v2(sub0_data[5:], w, h)
print(f"\n像素分布:")
from collections import Counter
c = Counter()
for row in pixels:
    for p in row:
        c[p] += 1
for v, n in sorted(c.items()):
    print(f"  像素 {v:3d} (0x{v:02X}): {n} 次")

# 输出解码后的像素 (前5行)
print(f"\n前5行像素:")
for y, row in enumerate(pixels):
    if y < 5:
        line = " ".join(f"{p:02X}" for p in row)
        print(f"  y={y:2d}: {line}")
