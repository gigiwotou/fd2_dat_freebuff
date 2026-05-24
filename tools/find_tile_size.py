"""找出可能的 tile 尺寸因子"""
import struct

pixels_list = [43785, 21755, 27931]

for pixels in pixels_list:
    print(f"\n像素数: {pixels}")
    print(f"  因子分解:")
    for w in range(8, 321, 8):  # 8 的倍数
        if pixels % w == 0:
            h = pixels // w
            if 8 <= h <= 400:
                print(f"    {w}x{h}")

# 也许 tile 数据包含宽高头？
# 让我们重新检查数据

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    f.seek(offsets[82])
    nested_data = f.read(offsets[83] - offsets[82])

# 找到有效偏移
offset_table_start = 10
res_count = struct.unpack("<I", nested_data[6:10])[0]
valid_offsets = []
for i in range(res_count):
    offset_addr = offset_table_start + i * 4
    if offset_addr + 4 > len(nested_data):
        break
    offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr + 4])[0]
    offset_table_end = offset_table_start + res_count * 4
    if offset_val < len(nested_data) and offset_val >= offset_table_end:
        valid_offsets.append(offset_val)
    else:
        break

print(f"\n偏移: {valid_offsets}")

# 检查每个 tile 数据的前几个字节
for idx, offset in enumerate(valid_offsets):
    end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(nested_data)
    data = nested_data[offset:end]
    
    print(f"\nTile {idx}:")
    print(f"  大小: {len(data)}")
    print(f"  前 8 字节 hex: {data[:8].hex()}")
    print(f"  前 8 字节 dec: {[b for b in data[:8]]}")
    
    # 尝试解释为宽高
    if len(data) >= 4:
        w_le = struct.unpack("<H", data[:2])[0]
        h_le = struct.unpack("<H", data[2:4])[0]
        w_be = struct.unpack(">H", data[:2])[0]
        h_be = struct.unpack(">H", data[2:4])[0]
        
        print(f"  小端 WxH: {w_le}x{h_le} = {w_le*h_le}")
        print(f"  大端 WxH: {w_be}x{h_be} = {w_be*h_be}")
        
        # 检查 w*h 是否接近像素数
        if w_le * h_le <= len(data) * 2:  # RLE 压缩后应该更小
            print(f"  -> 小端可能: {w_le}x{h_le}")
        if w_be * h_be <= len(data) * 2:
            print(f"  -> 大端可能: {w_be}x{h_be}")
