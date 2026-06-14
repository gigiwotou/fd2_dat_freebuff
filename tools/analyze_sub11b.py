"""分析子资源 11 的 RLE 数据 - 详细"""
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

# 分析子资源 11
i = 11
sub_off = sub_offsets[i]
sub_size = sub_offsets[i+1] - sub_off
sub_data = idx2_data[sub_off:sub_off+sub_size]
print(f"Sub {i}: sub_off=0x{sub_off:x} sub_size={sub_size}")
print(f"前 5 字节 (头): {sub_data[:5].hex()}")
print(f"RLE 总大小: {len(sub_data) - 5}")
print(f"RLE 头 32 字节:")
for j in range(0, 32, 16):
    print(f"  {j:3d}: {sub_data[5+j:5+j+16].hex()}")

# 数一下非零字节
rle = sub_data[5:]
nonzero = sum(1 for b in rle if b != 0)
print(f"\n非零字节数: {nonzero} / {len(rle)}")

# 找到非零位置
print(f"\n非零字节位置和值:")
for j, b in enumerate(rle):
    if b != 0:
        print(f"  [{j:3d}] = 0x{b:02x} ({b})")
        if j > 200:
            print("  ...")
            break
