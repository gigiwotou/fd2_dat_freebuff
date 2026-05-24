"""深度分析 RLE 数据格式"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

# 加载 FDOTHER.DAT 索引 82 的资源
with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))

    # 定位索引 82
    idx_82_start = offsets[82]
    idx_82_end = offsets[83] if 83 < count else None
    
    f.seek(idx_82_start)
    nested_data = f.read(idx_82_end - idx_82_start if idx_82_end else 0)

print(f"索引 82 资源总大小: {len(nested_data)} 字节")
print(f"Magic: {nested_data[:6]}")
print(f"偏移数量: {struct.unpack('<I', nested_data[6:10])[0]}")

# 找到有效偏移
offset_table_start = 10
valid_offsets = []
for i in range(struct.unpack('<I', nested_data[6:10])[0]):
    offset_addr = offset_table_start + i * 4
    if offset_addr + 4 > len(nested_data):
        break
    offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr + 4])[0]
    offset_table_end = offset_table_start + struct.unpack('<I', nested_data[6:10])[0] * 4
    if offset_val < len(nested_data) and offset_val >= offset_table_end:
        valid_offsets.append(offset_val)
    else:
        break

print(f"有效偏移数量: {len(valid_offsets)}")

# 分析第一个 tile 数据
tile0_data = nested_data[valid_offsets[0]:valid_offsets[1]]
print(f"\n第一个 tile 数据大小: {len(tile0_data)} 字节")
print(f"前 32 字节 hex: {tile0_data[:32].hex()}")

# 分析 RLE 数据格式
# 根据汇编: arg0 的前 2 字节是 count, arg0[1] 是 height
# 所以数据格式是: count (2字节), height (2字节), RLE数据
if len(tile0_data) >= 4:
    rle_count = struct.unpack("<H", tile0_data[:2])[0]
    rle_height = struct.unpack("<H", tile0_data[2:4])[0]
    rle_payload = tile0_data[4:]
    
    print(f"\nRLE 数据头部解析:")
    print(f"  count (宽度?): {rle_count}")
    print(f"  height: {rle_height}")
    print(f"  RLE payload 大小: {len(rle_payload)} 字节")
    print(f"  预期像素数: {rle_count * rle_height}")
    print(f"  预期像素数/2: {(rle_count * rle_height)//2}")  # 因为 count 是 word

# 尝试不同的解析方式
print(f"\n尝试不同的解析方式:")
for fmt in ['<H', '<B', '<I']:
    try:
        val = struct.unpack(fmt, tile0_data[:struct.calcsize(fmt)])[0]
        print(f"  {fmt}: {val}")
    except:
        pass

# 分析 RLE 控制字节分布
print(f"\nRLE payload 前 100 字节分析:")
for i, byte in enumerate(rle_payload[:100]):
    is_control = bool(byte & 0x80)
    is_skip = bool(byte & 0x40) if is_control else False
    count_val = ((byte & 0x3F) >> 2) + 1 if is_control else 0
    print(f"  [{i:3d}] 0x{byte:02x}: 控制={is_control}, 跳过={is_skip}, 计数={count_val}")
