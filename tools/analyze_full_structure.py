"""分析 FDOTHER 索引 82 的完整结构"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    f.seek(offsets[82])
    data = f.read(offsets[83] - offsets[82])

print(f"总大小: {len(data)}")
print(f"\n头部:")
print(f"  Magic: {data[:6]}")
print(f"  偏移 6-9: {struct.unpack('<I', data[6:10])[0]}")

# 偏移表
print(f"\n偏移表 (从偏移 10 开始，每 4 字节):")
for i in range(30):
    addr = 10 + i * 4
    if addr + 4 > len(data):
        break
    val = struct.unpack("<I", data[addr:addr+4])[0]
    valid = "OK" if val < len(data) and val >= 10 + 30*4 else "X"
    print(f"  [{i:2d}] offset {addr:5d}: {val:6d} (0x{val:X}) [{valid}]")

# 分析偏移表结束位置到第一个 tile 之间的数据
offset_table_end = 10 + 26 * 4  # 假设 26 个偏移
first_tile = 6587

print(f"\n偏移表结束: {offset_table_end}")
print(f"第一个 tile: {first_tile}")
print(f"中间区域: {first_tile - offset_table_end} 字节")

# 查看中间区域的数据
print(f"\n中间区域前 64 字节:")
region = data[offset_table_end:offset_table_end+64]
for i in range(0, len(region), 16):
    hex_str = " ".join(f"{b:02x}" for b in region[i:i+16])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in region[i:i+16])
    print(f"  {offset_table_end+i:04x}: {hex_str:<48} {ascii_str}")

# 分析字节值分布
from collections import Counter
middle_data = data[offset_table_end:first_tile]
byte_counts = Counter(middle_data)
print(f"\n中间区域字节值分布 (Top 20):")
for byte_val, cnt in byte_counts.most_common(20):
    print(f"  0x{byte_val:02x} ({byte_val:3d}): {cnt:4d} 次 ({cnt/len(middle_data)*100:.1f}%)")

# 检查第一个 tile 数据
print(f"\n第一个 tile 数据 (偏移 {first_tile}):")
tile0 = data[first_tile:first_tile+32]
for i in range(0, len(tile0), 16):
    hex_str = " ".join(f"{b:02x}" for b in tile0[i:i+16])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in tile0[i:i+16])
    print(f"  {first_tile+i:04x}: {hex_str:<48} {ascii_str}")
