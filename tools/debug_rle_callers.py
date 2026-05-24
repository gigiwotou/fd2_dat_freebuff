"""分析 sub_4E98D 的调用方式，确定参数传递格式"""
# 根据汇编分析，我们需要找到调用 sub_4E98D 的地方
# 特别关注参数是如何设置的

# 从反汇编代码看：
# arg0: 指向包含 count 和 height 的数据头 (各 2 字节)
# arg4: 目标缓冲区基址
# arg8: x 偏移
# argC: y 偏移  
# arg10: stride (行跨度)
# value_1: 调色板偏移

# 所以 tile 数据格式应该是:
# [0:2] width (count)
# [2:4] height
# [4:] RLE 压缩的像素数据

# 但我们之前解析出 width=32637, height=32384，这不合理
# 让我们尝试大端序或者其他解释

import struct

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

# 加载数据
with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    f.seek(offsets[82])
    nested_data = f.read(offsets[83] - offsets[82])

# 找到第一个 tile
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
print(f"Tile 0 数据大小: {len(tile0_data)} 字节")
print(f"前 8 字节: {tile0_data[:8].hex()}")

# 尝试各种解释
print("\n前 4 字节的各种解释:")
print(f"  小端 H,H: {struct.unpack('<HH', tile0_data[:4])}")
print(f"  大端 H,H: {struct.unpack('>HH', tile0_data[:4])}")
print(f"  小端 H: {struct.unpack('<H', tile0_data[:2])[0]}")
print(f"  大端 H: {struct.unpack('>H', tile0_data[:2])[0]}")
print(f"  字节值: {[b for b in tile0_data[:4]]}")

# 分析 RLE 控制字节的分布
print("\nRLE 控制字节分布:")
control_count = 0
skip_count = 0
copy_count = 0
fill_count = 0
for byte in tile0_data:
    if byte & 0x80:
        control_count += 1
        if byte & 0x40:
            skip_count += 1
        else:
            copy_count += 1
    else:
        fill_count += 1

total = len(tile0_data)
print(f"  总字节数: {total}")
print(f"  控制字节: {control_count} ({control_count/total*100:.1f}%)")
print(f"    跳过: {skip_count}")
print(f"    复制: {copy_count}")
print(f"  填充字节: {fill_count} ({fill_count/total*100:.1f}%)")

# 假设数据有宽高头，重新解析
# 也许宽高不是在前 4 字节，而是在其他地方？
# 或者 tile 数据根本没有宽高头，宽高是通过其他方式传递的？

print("\n假设没有宽高头，直接解压缩:")
# 根据反汇编，sub_4E98D 的第一个参数是指向 count 的指针
# 这意味着数据应该包含 count 信息
# 但也许这个 count 不是 width，而是其他含义？

# 让我们查看 sub_2D80D 如何调用 sub_4E98D
# 从文档中知道，sub_2D80D 调用 sub_4E98D 时传递了 tile 数据

# 假设 tile 数据格式为:
# [0:2] count (可能是某种索引或标志)
# [2:4] height  
# [4:] RLE 数据

# 如果 count 是 125 (0x7D)，那可能表示某种 tile 类型
# height 是 127 (0x7F)，这看起来像合理的 tile 高度

# 但 127x127 的 tile 不太常见
# 让我们尝试其他解释

# 也许数据没有头，直接是 RLE 数据？
# 如果是这样，我们需要知道 tile 尺寸

# 根据游戏分辨率 320x200，常见的 tile 尺寸可能是:
# 32x32, 16x16, 8x8, 64x64 等

# 让我们计算如果 tile 是某种尺寸，RLE 压缩率如何
for w, h in [(32, 32), (16, 16), (64, 64), (80, 80), (48, 48)]:
    pixels = w * h
    # RLE 压缩后的数据大小应该小于原始像素数
    # 但实际上 RLE 数据可能比原始数据大（如果有很多不连续的像素）
    print(f"  {w}x{h}: 像素数={pixels}, RLE数据={len(tile0_data)}, 压缩率={len(tile0_data)/pixels:.2f}")
