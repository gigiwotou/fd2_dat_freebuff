"""分析子资源 11 的 RLE 数据"""
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

# 分析子资源 11 (失败)
i = 11
sub_off = sub_offsets[i]
sub_size = sub_offsets[i+1] - sub_off
sub_data = idx2_data[sub_off:sub_off+sub_size]
w = struct.unpack_from("<H", sub_data, 0)[0]
h = struct.unpack_from("<H", sub_data, 2)[0]
win = sub_data[4]
rle = sub_data[5:]
print(f"Sub {i}: w={w} h={h} win={win} rle_size={len(rle)}")
print(f"RLE 头 16 字节: {rle[:16].hex()}")

# 模拟 sub_4E98D_no_header 解码
src_idx = 0
y = 0
bx = w
dst_idx = 0
row_pixels = []
trace = []
while y < h and src_idx < len(rle):
    start = src_idx
    bx = w
    dst_idx = 0
    while bx > 0:
        if src_idx >= len(rle):
            break
        b = rle[src_idx]
        top2 = b & 0xC0
        if top2 == 0x00:
            count = b + 1
            v = rle[src_idx + 1]
            src_idx += 2
            dst_idx += count
            bx -= count
            trace.append(("FILL", count, v))
        elif top2 == 0x40:
            count = (b & 0x3F) + 1
            v = rle[src_idx + 1]
            src_idx += 2
            dst_idx += count * 2
            bx -= count * 2
            trace.append(("FILL2", count, v))
        elif top2 == 0x80:
            count = (b & 0x3F) + 1
            src_idx += 1
            src_idx += count
            dst_idx += count
            bx -= count
            trace.append(("COPY", count, -1))
        elif top2 == 0xC0:
            count = (b & 0x3F) + 1
            src_idx += 1
            dst_idx += count
            bx -= count
            trace.append(("SKIP", count, -1))
        if bx < 0:
            print(f"  bx<0 at row {y}, src_idx={src_idx}: {trace[-1]}")
            break
    y += 1

print(f"\n解码行数: {y}/{h}, src_idx: {src_idx}/{len(rle)}")
print(f"剩余字节: {len(rle) - src_idx}")

# 看看头几个 trace
print(f"\n前30条 trace:")
for t in trace[:30]:
    print(f"  {t}")
