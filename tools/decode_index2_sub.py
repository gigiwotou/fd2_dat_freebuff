"""
解码索引2子资源0 - 使用 4E98D 的 RLE 格式
头: [w:2][h:2][palette_window:1][RLE...]
"""
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

# 解码子资源 0
def decode_rle(src, w, h):
    """sub_4E98D 无调色板版本 (value=-1)
    控制字节:
      bit7=0, bit6=0: FILL count=((b&0x3F)+1), 下一个字节是填充值
      bit7=0, bit6=1: FILL2 count=((b&0x3F)>>2)+1, 下一个字节是填充值
      bit7=1, bit6=0: COPY count=((b&0x3F)+1), 后面count个字节直接复制
      bit7=1, bit6=1: SKIP count=((b&0x3F)>>2)+1
    """
    pixels = []
    src_idx = 0
    for y in range(h):
        row = []
        remaining = w
        while remaining > 0:
            b = src[src_idx]
            src_idx += 1
            top2 = b & 0xC0
            if top2 == 0x00:
                # bit7=0, bit6=0: FILL
                count = (b & 0x3F) + 1
                v = src[src_idx]
                src_idx += 1
                row.extend([v] * count)
            elif top2 == 0x40:
                # bit7=0, bit6=1: FILL2
                count = ((b & 0x3F) >> 2) + 1
                v = src[src_idx]
                src_idx += 1
                row.extend([v] * count)
            elif top2 == 0x80:
                # bit7=1, bit6=0: COPY
                count = (b & 0x3F) + 1
                for _ in range(count):
                    row.append(src[src_idx])
                    src_idx += 1
            elif top2 == 0xC0:
                # bit7=1, bit6=1: SKIP
                count = ((b & 0x3F) >> 2) + 1
                row.extend([0] * count)
            remaining -= count
        pixels.append(row)
    return pixels

# 解码子资源 0
print("="*60)
print("子资源 0 (起始 312, 大小 484)")
sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]

w = struct.unpack_from("<H", sub0_data, 0)[0]
h = struct.unpack_from("<H", sub0_data, 2)[0]
win = sub0_data[4]
print(f"  头: w={w}, h={h}, palette_window={win}")
print(f"  RLE data ({sub0_size-5} 字节): " + " ".join(f"{b:02X}" for b in sub0_data[5:37]))

pixels = decode_rle(sub0_data[5:], w, h)
print(f"\n解码后像素 ({len(pixels)}x{len(pixels[0]) if pixels else 0}):")
for y, row in enumerate(pixels):
    if y < 10:
        line = " ".join(f"{p:02X}" if p > 0 else ".." for p in row)
        print(f"  y={y:2d}: {line}")

# 检查非0像素
nonzero = 0
for row in pixels:
    for p in row:
        if p != 0:
            nonzero += 1
print(f"\n非0像素: {nonzero}")

# 解码子资源 1
print("\n" + "="*60)
print("子资源 1 (起始 796)")
sub1_off = sub_offsets[1]
sub2_off = sub_offsets[2]
sub1_size = sub2_off - sub1_off
sub1_data = idx2_data[sub1_off:sub1_off+sub1_size]

w1 = struct.unpack_from("<H", sub1_data, 0)[0]
h1 = struct.unpack_from("<H", sub1_data, 2)[0]
win1 = sub1_data[4]
print(f"  头: w={w1}, h={h1}, palette_window={win1}")
print(f"  RLE data ({sub1_size-5} 字节): " + " ".join(f"{b:02X}" for b in sub1_data[5:37]))

pixels1 = decode_rle(sub1_data[5:], w1, h1)
nonzero1 = 0
for row in pixels1:
    for p in row:
        if p != 0:
            nonzero1 += 1
print(f"非0像素: {nonzero1}")

# 输出像素分布
print(f"\n像素值分布 (子资源0):")
from collections import Counter
c = Counter()
for row in pixels:
    for p in row:
        c[p] += 1
for v, n in sorted(c.items()):
    print(f"  像素 {v:3d} (0x{v:02X}): {n} 次")
