"""详细分析子资源0的RLE字节序列"""
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
sub0_off = sub_offsets[0]
sub1_off = sub_offsets[1]
sub0_size = sub1_off - sub0_off
sub0_data = idx2_data[sub0_off:sub0_off+sub0_size]

w = struct.unpack_from("<H", sub0_data, 0)[0]
h = struct.unpack_from("<H", sub0_data, 2)[0]
rle_data = sub0_data[5:]

print(f"子资源0: w={w}, h={h}, RLE大小={len(rle_data)}")
print(f"\nRLE字节: ")
for i in range(0, len(rle_data), 16):
    line = " ".join(f"{b:02X}" for b in rle_data[i:i+16])
    print(f"  {i:3d}: {line}")

# 详细追踪解码过程
print(f"\n\n详细解码:")
src_idx = 0
total_pixels = 0
while src_idx < len(rle_data) and total_pixels < w * h:
    b = rle_data[src_idx]
    top2 = b & 0xC0
    if top2 == 0x00:
        # FILL (b&0x3F + 1) 次
        count = (b & 0x3F) + 1
        v = rle_data[src_idx+1]
        print(f"  [{src_idx:3d}] 0x{b:02X} FILL count={count} value=0x{v:02X} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 2
        total_pixels += count
    elif top2 == 0x40:
        # FILL2 count = ((b&0x3F)>>2)+1
        count = ((b & 0x3F) >> 2) + 1
        v = rle_data[src_idx+1]
        print(f"  [{src_idx:3d}] 0x{b:02X} FILL2 count={count} value=0x{v:02X} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 2
        total_pixels += count
    elif top2 == 0x80:
        # COPY
        count = (b & 0x3F) + 1
        print(f"  [{src_idx:3d}] 0x{b:02X} COPY count={count}, value={' '.join(f'{rle_data[src_idx+1+i]:02X}' for i in range(count))} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 1 + count
        total_pixels += count
    elif top2 == 0xC0:
        # SKIP
        count = ((b & 0x3F) >> 2) + 1
        print(f"  [{src_idx:3d}] 0x{b:02X} SKIP count={count} (pos {total_pixels}-{total_pixels+count-1})")
        src_idx += 1
        total_pixels += count
    else:
        print(f"  [{src_idx:3d}] 0x{b:02X} UNKNOWN")
        break

print(f"\n总输出像素: {total_pixels}")
print(f"期望: {w*h}")
