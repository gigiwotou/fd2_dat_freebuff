"""详细分析子资源0的RLE字节序列 - 修正count公式"""
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

# 解码子资源 0
sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]

w = struct.unpack_from("<H", sub0_data, 0)[0]
h = struct.unpack_from("<H", sub0_data, 2)[0]
rle_data = sub0_data[5:]

print(f"子资源0: w={w}, h={h}, RLE大小={len(rle_data)}")

# 详细追踪解码过程 - 使用正确的 count 公式
print(f"\n详细解码 (count = (b & 0x3F) + 1):")
src_idx = 0
total_pixels = 0
total_consumed = 0
n_src = len(rle_data)
while src_idx < n_src and total_pixels < w * h:
    b = rle_data[src_idx]
    top2 = b & 0xC0
    if top2 == 0x00:
        count = b + 1
        v = rle_data[src_idx+1] if src_idx+1 < n_src else 0
        print(f"  [{src_idx:3d}] 0x{b:02X} FILL count={count} value=0x{v:02X} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 2
        total_pixels += count
        total_consumed += 1
    elif top2 == 0x40:
        count = (b & 0x3F) + 1
        v = rle_data[src_idx+1] if src_idx+1 < n_src else 0
        print(f"  [{src_idx:3d}] 0x{b:02X} FILL2 count={count} value=0x{v:02X} (pos {total_pixels}-{total_pixels+2*count-1}, 写入 dst+1, +3, +5...)")
        src_idx += 2
        total_pixels += 2 * count
        total_consumed += 1
    elif top2 == 0x80:
        count = (b & 0x3F) + 1
        values = " ".join(f"{rle_data[src_idx+1+i]:02X}" for i in range(min(count, 8)))
        if count > 8: values += " ..."
        print(f"  [{src_idx:3d}] 0x{b:02X} COPY count={count} values=[{values}] (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 1 + count
        total_pixels += count
        total_consumed += 1
    elif top2 == 0xC0:
        count = (b & 0x3F) + 1
        print(f"  [{src_idx:3d}] 0x{b:02X} SKIP count={count} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 1
        total_pixels += count
        total_consumed += 1
    else:
        print(f"  [{src_idx:3d}] 0x{b:02X} UNKNOWN")
        break

print(f"\n总输出像素: {total_pixels}")
print(f"期望: {w*h}")
print(f"总RLE操作: {total_consumed}")
