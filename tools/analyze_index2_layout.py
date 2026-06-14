"""分析索引2所有子资源的尺寸"""
import struct

FDOTHER_PATH = "D:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT"
with open(FDOTHER_PATH, "rb") as f:
    data = f.read()

# 解析主索引表
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
print(f"索引2 大小: {len(idx2_data)} 字节")
print(f"文件末尾: {len(data)} 字节")

# 解析78个dword偏移表
sub_offsets = []
for i in range(78):
    off = struct.unpack_from("<I", idx2_data, i*4)[0]
    sub_offsets.append(off)
# 文件结束作为最后一个
sub_offsets.append(len(idx2_data))

# 打印每个子资源
print("\n子资源列表:")
print("Idx | Offset   | Size     | W   | H   | Win | RLE大小")
print("----+----------+----------+-----+-----+-----+--------")
for i in range(78):
    sub_off = sub_offsets[i]
    sub_size = sub_offsets[i+1] - sub_off
    if sub_off + 5 > len(idx2_data):
        print(f"{i:3d} | 0x{sub_off:06x} | {sub_size:6d}   | (越界)")
        continue
    if sub_size < 5:
        print(f"{i:3d} | 0x{sub_off:06x} | {sub_size:6d}   | (过小)")
        continue
    sub_data = idx2_data[sub_off:sub_off+sub_size]
    if len(sub_data) < 5:
        print(f"{i:3d} | 0x{sub_off:06x} | {sub_size:6d}   | (截断)")
        continue
    w = struct.unpack_from("<H", sub_data, 0)[0]
    h = struct.unpack_from("<H", sub_data, 2)[0]
    win = sub_data[4]
    rle_size = sub_size - 5
    print(f"{i:3d} | 0x{sub_off:06x} | {sub_size:6d}   | {w:3d} | {h:3d} | {win:3d} | {rle_size:6d}")
