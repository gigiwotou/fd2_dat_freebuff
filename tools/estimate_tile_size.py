"""尝试不同的数据解释方式"""
import struct

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

tile0_data = nested_data[valid_offsets[0]:valid_offsets[1]]
print(f"Tile 0: {valid_offsets[0]} - {valid_offsets[1]}, 大小={len(tile0_data)}")
print(f"前 8 字节: {tile0_data[:8].hex()}")
print(f"前 16 字节: {[f'{b:02x}' for b in tile0_data[:16]]}")

# 关键观察: 字节值在 0x7D-0x80 范围
# 这些值都 >= 125
# 在 RLE 编码中:
# - Bit 7 (0x80): 控制标志
# - Bit 6 (0x40): 如果是控制字节，区分跳过/复制

# 所以:
# 0x7D (0111 1101): Bit7=0 -> 非控制字节，是填充值
# 0x7E (0111 1110): Bit7=0 -> 非控制字节
# 0x7F (0111 1111): Bit7=0 -> 非控制字节
# 0x80 (1000 0000): Bit7=1 -> 控制字节，Bit6=0 -> 复制操作

# 这意味着大部分数据是填充值 (0x7D-0x7F)
# 这些值作为调色板索引是合理的

# 所以数据确实没有宽高头！直接是 RLE 数据
# 但我们不知道 tile 尺寸

# 让我们尝试反向计算: 如果数据是 RLE 编码的，原始像素数是多少？
# 通过模拟解码来计算

def estimate_original_size(data):
    """估算 RLE 解码后的像素数量"""
    src_pos = 0
    dst_count = 0
    
    while src_pos < len(data):
        value = data[src_pos]
        src_pos += 1
        
        if value & 0x80:
            # 控制字节
            count = ((value & 0x3F) >> 2) + 1
            if value & 0x40:
                # 跳过
                dst_count += count
            else:
                # 复制
                dst_count += count
                src_pos += count
        else:
            # 填充
            count = ((value & 0x3F) >> 2) + 1
            if src_pos < len(data):
                src_pos += 1  # 跳过填充值字节
            dst_count += count
    
    return dst_count

original_pixels = estimate_original_size(tile0_data)
print(f"\n估算原始像素数: {original_pixels}")
print(f"RLE 数据大小: {len(tile0_data)}")
print(f"压缩率: {len(tile0_data)/original_pixels:.3f}")

# 找出可能的 w*h 组合
print("\n可能的 tile 尺寸组合:")
for w in [8, 16, 32, 48, 64, 80, 96, 128, 160, 192, 240, 320]:
    if original_pixels % w == 0:
        h = original_pixels // w
        if h > 0 and h <= 400:  # 合理的高度范围
            print(f"  {w}x{h} (像素数={w*h})")
