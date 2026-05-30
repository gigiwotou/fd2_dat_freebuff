"""
分析索引2的完整结构
"""
import struct

fdother_path = "game/FDOTHER.DAT"

with open(fdother_path, "rb") as f:
    file_data = f.read()

# 读取主偏移表
main_offsets = []
for i in range(422):
    off = struct.unpack('<I', file_data[6 + i * 4:6 + i * 4 + 4])[0]
    main_offsets.append(off)

# 索引2的范围
idx2_start = main_offsets[2]
idx2_end = main_offsets[3]
idx2_size = idx2_end - idx2_start

print("=" * 70)
print("索引2 完整结构分析")
print("=" * 70)
print(f"\n文件中的位置: 0x{idx2_start:08X} - 0x{idx2_end:08X}")
print(f"数据总大小: {idx2_size} 字节")

# 读取索引2的全部数据
idx2_data = file_data[idx2_start:idx2_end]

# ========================================
# 1. 分析偏移表
# ========================================
print(f"\n{'='*70}")
print("1. 偏移表分析")
print(f"{'='*70}")

# 读取所有偏移值
all_offsets = []
for i in range(idx2_size // 4):
    off = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
    all_offsets.append(off)

print(f"偏移值总数: {len(all_offsets)}")
print(f"偏移表原始大小: {len(all_offsets) * 4} 字节")

# 分析偏移间距
print(f"\n偏移间距分析:")
spans = []
for i in range(1, min(20, len(all_offsets))):
    span = all_offsets[i] - all_offsets[i-1]
    spans.append(span)
    print(f"  [{i-1}] -> [{i}]: {span} 字节")

# 检查是否有统一的间距
unique_spans = set(spans)
print(f"\n唯一间距值: {unique_spans}")

# 验证偏移值是否递增
is_ascending = all(all_offsets[i] < all_offsets[i+1] for i in range(len(all_offsets)-1))
print(f"偏移值是否严格递增: {is_ascending}")

# 第一个和最后一个偏移
print(f"\n第一个偏移: {all_offsets[0]}")
print(f"最后一个偏移: {all_offsets[-1]}")

# ========================================
# 2. 数据区起始位置
# ========================================
print(f"\n{'='*70}")
print("2. 数据区起始位置")
print(f"{'='*70}")

# 偏移表占用的字节数
offset_table_size = len(all_offsets) * 4
print(f"偏移表占用: {offset_table_size} 字节")

# 第一个偏移指向的位置
first_offset = all_offsets[0]
print(f"第一个偏移值: {first_offset}")

# 检查第一个偏移是在偏移表内部还是外部
if first_offset < offset_table_size:
    print(f"第一个偏移在偏移表内部!")
    print(f"  偏移表范围: 0 - {offset_table_size-1}")
    print(f"  数据区起始: {first_offset} (在偏移表内部)")
else:
    print(f"第一个偏移在偏移表外部")
    print(f"  偏移表范围: 0 - {offset_table_size-1}")
    print(f"  数据区起始: {first_offset}")

# 检查是否有偏移值小于第一个偏移
small_offsets = [i for i, off in enumerate(all_offsets) if off < first_offset]
if small_offsets:
    print(f"\n警告: 有 {len(small_offsets)} 个偏移值小于第一个偏移: {small_offsets[:10]}")
else:
    print(f"\n所有偏移值都 >= 第一个偏移 ({first_offset})")

# ========================================
# 3. 偏移值类型分析 (相对 vs 绝对)
# ========================================
print(f"\n{'='*70}")
print("3. 偏移值类型分析")
print(f"{'='*70}")

# 检查偏移值是否可能是相对偏移 (相对于偏移表结束)
# 或者绝对偏移 (相对于索引2数据起始)
print(f"最大偏移值: {max(all_offsets)}")
print(f"索引2数据总大小: {idx2_size}")

if max(all_offsets) < idx2_size:
    print(f"所有偏移值都在索引2数据范围内 -> 可能是相对偏移")
else:
    print(f"有偏移值超出索引2数据范围 -> 可能是绝对偏移或其他含义")

# 检查偏移值是否均匀分布
print(f"\n偏移值分布:")
for i in range(0, len(all_offsets), max(1, len(all_offsets)//10)):
    print(f"  [{i:5d}] = {all_offsets[i]:5d} (0x{all_offsets[i]:04X})")

# ========================================
# 4. 第一个子资源的完整数据格式
# ========================================
print(f"\n{'='*70}")
print("4. 第一个子资源完整数据格式")
print(f"{'='*70}")

# 第一个子资源的起始和结束
res0_start = all_offsets[0]
res0_end = all_offsets[1]
res0_size = res0_end - res0_start

print(f"第一个子资源:")
print(f"  起始偏移: {res0_start}")
print(f"  结束偏移: {res0_end}")
print(f"  大小: {res0_size} 字节")

# 读取第一个子资源的数据
res0_data = idx2_data[res0_start:res0_end]
print(f"\n第一个子资源 Hex Dump (前128字节):")
for i in range(0, min(128, len(res0_data)), 16):
    hex_bytes = ' '.join(f'{b:02X}' for b in res0_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res0_data[i:i+16])
    print(f"  {i:4d}: {hex_bytes:<48} {ascii_str}")

# 尝试解析可能的结构
print(f"\n可能的结构解析:")

# 尝试解析为宽高
if len(res0_data) >= 4:
    w = struct.unpack_from('<H', res0_data, 0)[0]
    h = struct.unpack_from('<H', res0_data, 2)[0]
    print(f"  [0-1] word: {w} (0x{w:04X})")
    print(f"  [2-3] word: {h} (0x{h:04X})")
    print(f"  可能是图像尺寸: {w}x{h}")

# 解析后续数据
if len(res0_data) >= 8:
    print(f"  [4-7] dword: 0x{struct.unpack_from('<I', res0_data, 4)[0]:08X}")

# 检查是否有调色板或像素数据
print(f"\n数据分布分析:")
non_zero = sum(1 for b in res0_data if b != 0)
print(f"  总字节数: {len(res0_data)}")
print(f"  非零字节: {non_zero}")
print(f"  零字节: {len(res0_data) - non_zero}")

# 分析唯一值
unique_values = set(res0_data)
print(f"  唯一值数量: {len(unique_values)}")
print(f"  唯一值: {sorted(unique_values)}")

# 如果宽高是24x20，检查像素数据
if w == 24 and h == 20:
    print(f"\n图像尺寸 24x20 确认:")
    pixel_data_start = 8  # 假设前8字节是头部
    expected_pixels = 24 * 20
    pixel_data = res0_data[pixel_data_start:]
    print(f"  像素数据起始: {pixel_data_start}")
    print(f"  预期像素数: {expected_pixels}")
    print(f"  可用像素数据: {len(pixel_data)} 字节")
    
    # 检查是否是RLE压缩
    print(f"\nRLE压缩可能性分析:")
    # RLE通常有重复模式
    rle_patterns = 0
    for i in range(0, len(pixel_data)-3, 2):
        if pixel_data[i] > 0 and pixel_data[i+1] == pixel_data[i+2]:
            rle_patterns += 1
    print(f"  可能的RLE模式: {rle_patterns}")

# 分析所有子资源的大小
print(f"\n{'='*70}")
print("所有子资源大小分析")
print(f"{'='*70}")

sizes = []
for i in range(len(all_offsets)-1):
    size = all_offsets[i+1] - all_offsets[i]
    sizes.append(size)

# 统计大小分布
from collections import Counter
size_counts = Counter(sizes)
print(f"子资源数量: {len(sizes)}")
print(f"\n大小分布 (前20个最常见的):")
for size, count in size_counts.most_common(20):
    print(f"  {size:5d} 字节: {count:4d} 个资源")

print(f"\n大小统计:")
print(f"  最小: {min(sizes)} 字节")
print(f"  最大: {max(sizes)} 字节")
print(f"  平均: {sum(sizes)/len(sizes):.1f} 字节")
