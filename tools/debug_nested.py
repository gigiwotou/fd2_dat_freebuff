"""查看原始汇编数据，确定嵌套 DAT 的偏移格式"""
import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))

# 定位索引 82 的位置
idx_82_start = offsets[82]
idx_82_end = offsets[83] if 83 < count else None

print(f"索引 82 在 FDOTHER.DAT 中的位置: {idx_82_start} - {idx_82_end}")

with open(fdother_path, "rb") as f:
    f.seek(idx_82_start)
    # 读取嵌套 DAT 的前 200 字节
    nested_data = f.read(200)
    
print(f"\n嵌套 DAT 前 200 字节:")
for i in range(0, min(200, len(nested_data)), 16):
    hex_str = " ".join(f"{b:02x}" for b in nested_data[i:i+16])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in nested_data[i:i+16])
    print(f"  {i:04x}: {hex_str:<48} {ascii_str}")

# 解析嵌套 DAT 头部
magic = nested_data[:6]
res_count = struct.unpack("<I", nested_data[6:10])[0]
print(f"\nMagic: {magic}")
print(f"资源数量: {res_count}")

# 读取偏移表 (从偏移 10 开始，每个偏移 4 字节)
print(f"\n偏移表 (从偏移 10 开始):")
for i in range(min(res_count, 10)):
    offset_addr = 10 + i * 4
    offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr+4])[0]
    print(f"  资源 {i}: 偏移 = {offset_val} (0x{offset_val:X})")

# 检查资源数据 (偏移表结束后)
offset_table_end = 10 + res_count * 4
print(f"\n偏移表结束位置: {offset_table_end}")
print(f"资源数据从偏移 {offset_table_end} 开始:")

# 读取第一个资源的前 64 字节
if offset_table_end < len(nested_data):
    res_start = offset_table_end
    res_data = nested_data[res_start:res_start+64]
    print(f"  第一个资源前 64 字节:")
    for i in range(0, len(res_data), 16):
        hex_str = " ".join(f"{b:02x}" for b in res_data[i:i+16])
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in res_data[i:i+16])
        print(f"    {i:04x}: {hex_str:<48} {ascii_str}")
