"""分析LMI1索引3的原始数据 (修正DAT格式)"""
import struct

with open("bin/FDOTHER.DAT", "rb") as f:
    data = f.read()

# FDOTHER.DAT格式: "LLLLLL" + 4字节偏移表
print("=== FDOTHER.DAT header ===")
print(f"file_size: {len(data)}")
print(f"magic: {data[:6]}")

# 解析偏移表
offsets = []
table_offset = 6
while table_offset + 4 <= len(data):
    res_offset = struct.unpack_from("<I", data, table_offset)[0]
    if res_offset == 0 or res_offset > len(data):
        break
    offsets.append(res_offset)
    table_offset += 4

print(f"resource count: {len(offsets)}")
print(f"first 5 offsets: {offsets[:5]}")
print(f"index 3 offset: {offsets[3]}")
print(f"index 3 size: {offsets[4] - offsets[3]}")

# 读取LMI1 3数据
lmi1_off = offsets[3]
lmi1_size = offsets[4] - offsets[3]
lmi1_data = data[lmi1_off:lmi1_off+lmi1_size]

print(f"\n=== LMI1 3 ({lmi1_size} bytes) ===")
print(f"magic: {lmi1_data[:4]}")
tile_count = struct.unpack_from("<H", lmi1_data, 4)[0]
print(f"tile_count: {tile_count}")

# 读取tile偏移
tile_offsets = []
for i in range(tile_count):
    off = struct.unpack_from("<I", lmi1_data, 6 + i*4)[0]
    tile_offsets.append(off)

print(f"\nfirst 5 tile offsets: {tile_offsets[:5]}")
print(f"tile sizes: {[tile_offsets[i+1] - tile_offsets[i] for i in range(min(5, tile_count-1))]}")
print(f"last tile size: {lmi1_size - tile_offsets[-1]}")

# 检查tile[0]的4字节头
if tile_offsets[0] + 4 <= lmi1_size:
    w0 = struct.unpack_from("<H", lmi1_data, tile_offsets[0])[0]
    h0 = struct.unpack_from("<H", lmi1_data, tile_offsets[0] + 2)[0]
    print(f"\ntile[0] 4-byte header: width={w0}, height={h0}")
    print(f"tile[0] 实际数据前20字节: {lmi1_data[tile_offsets[0]:tile_offsets[0]+20].hex()}")
