"""检查嵌套 DAT 的精确结构"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))

# 加载索引 82
start = offsets[82]
end = offsets[83]
with open(fdother_path, "rb") as f:
    f.seek(start)
    data = f.read(end - start)

print(f"索引 82 数据大小: {len(data)} 字节")
print(f"\n完整十六进制转储 (前 200 字节):")
for i in range(0, min(200, len(data)), 16):
    hex_str = " ".join(f"{b:02x}" for b in data[i:i+16])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
    print(f"  {i:04x}: {hex_str:<48} {ascii_str}")

# 按照 tile 图集格式解析 (offset 6 开始是偏移表)
print(f"\n\n按照 tile 图集格式解析:")
print(f"  magic: {data[0:4]}")
tile_count = struct.unpack("<H", data[4:6])[0]
print(f"  tile 数量: {tile_count}")

print(f"\n偏移表 (从偏移 6 开始):")
valid_offsets = []
for i in range(tile_count):
    offset_addr = 6 + i * 4
    if offset_addr + 4 > len(data):
        print(f"  Tile {i}: 偏移表超出范围")
        break
    
    offset_val = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
    print(f"  Tile {i}: 偏移 = {offset_val} (0x{offset_val:X})")
    
    # 检查偏移是否有效
    if offset_val < len(data) and offset_val > 0:
        # 尝试读取宽高
        if offset_val + 4 <= len(data):
            w = struct.unpack("<H", data[offset_val:offset_val + 2])[0]
            h = struct.unpack("<H", data[offset_val + 2:offset_val + 4])[0]
            if 0 < w <= 320 and 0 < h <= 200:
                print(f"    -> 图像: {w}x{h}")
                valid_offsets.append((i, offset_val, w, h))
            else:
                print(f"    -> 无效图像尺寸: {w}x{h}")
        else:
            print(f"    -> 偏移超出范围")
    else:
        print(f"    -> 无效偏移")
        # 如果连续 3 个偏移都无效，说明偏移表结束了
        if len(valid_offsets) > 0 and i > valid_offsets[-1][0] + 3:
            print(f"\n  *** 偏移表在 tile {valid_offsets[-1][0]} 后结束 ***")
            break

print(f"\n\n有效 tile: {len(valid_offsets)} 个")
for idx, offset, w, h in valid_offsets:
    print(f"  Tile {idx}: 偏移 {offset}, 尺寸 {w}x{h}")
