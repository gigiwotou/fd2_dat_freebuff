"""批量分析所有子资源，输出每个的尺寸、调色板窗口、非透明像素数"""
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

print(f"{'idx':>3} {'w':>3} {'h':>3} {'win':>4} {'size':>5} {'rle':>5}")
for i in range(78):
    sub_off = sub_offsets[i]
    sub_size = sub_offsets[i+1] - sub_off
    if sub_off + 5 > len(idx2_data):
        print(f"{i:3d} - (out of range)")
        continue
    sub_data = idx2_data[sub_off:sub_off+sub_size]
    w = struct.unpack_from("<H", sub_data, 0)[0]
    h = struct.unpack_from("<H", sub_data, 2)[0]
    win = sub_data[4]
    rle_size = sub_size - 5
    print(f"{i:3d} {w:3d} {h:3d} {win:4d} {sub_size:5d} {rle_size:5d}")
