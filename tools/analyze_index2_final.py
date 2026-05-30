"""
索引2完整结构分析 - 最终版本
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

idx2_start = main_offsets[2]
idx2_end = main_offsets[3]
idx2_size = idx2_end - idx2_start
idx2_data = file_data[idx2_start:idx2_end]

print("="*70)
print("索引2 完整结构分析")
print("="*70)
print(f"文件位置: 0x{idx2_start:X} - 0x{idx2_end:X}")
print(f"总大小: {idx2_size} 字节")

# ========================================
# 1. 偏移表占多少字节
# ========================================
print("\n" + "="*70)
print("1. 偏移表分析")
print("="*70)

offset_count = 78
offset_table_size = offset_count * 4

print(f"偏移表条目数: {offset_count}")
print(f"偏移表大小: {offset_table_size} 字节 (前312字节)")
print(f"偏移表范围: 字节 0 - {offset_table_size-1}")

print("\n偏移表内容 (78个偏移值):")
offsets = []
for i in range(offset_count):
    off = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
    offsets.append(off)
    print(f"  [{i:2d}] = {off:5d} (0x{off:04X})")

# 计算每个子资源的大小
print("\n子资源大小分布:")
sizes = []
for i in range(offset_count - 1):
    size = offsets[i+1] - offsets[i]
    sizes.append(size)

size_484 = sizes.count(484)
size_388 = sizes.count(388)
print(f"  484字节: {size_484} 个")
print(f"  388字节: {size_388} 个")

# ========================================
# 2. 数据区从哪里开始
# ========================================
print("\n" + "="*70)
print("2. 数据区位置")
print("="*70)

data_start = offsets[0]
data_end = offsets[-1]
print(f"偏移表结束: {offset_table_size} 字节")
print(f"第一个偏移值: {data_start}")
print(f"数据区起始: 字节 {data_start} (正好是偏移表之后!)")
print(f"数据区结束: 字节 {data_end}")
print(f"数据区大小: {data_end - data_start} 字节")
print(f"子资源数量: {offset_count - 1}")

# ========================================
# 3. 偏移值类型
# ========================================
print("\n" + "="*70)
print("3. 偏移值类型")
print("="*70)
print(f"偏移值范围: {offsets[0]} - {offsets[-1]}")
print(f"索引2总大小: {idx2_size}")
print(f"所有偏移值 < 索引2大小: {max(offsets) < idx2_size}")
print("=> 相对偏移 (相对于索引2数据的起始位置)")

# ========================================
# 4. 第一个子资源的完整数据格式
# ========================================
print("\n" + "="*70)
print("4. 第一个子资源完整数据格式")
print("="*70)

res0_start = offsets[0]
res0_end = offsets[1]
res0_size = res0_end - res0_start
res0_data = idx2_data[res0_start:res0_end]

print(f"位置: 字节 {res0_start} - {res0_end}")
print(f"大小: {res0_size} 字节")

print(f"\n完整Hex Dump ({res0_size} 字节):")
for i in range(0, len(res0_data), 16):
    hex_bytes = ' '.join(f'{b:02X}' for b in res0_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res0_data[i:i+16])
    print(f"  {i:4d}: {hex_bytes:<48} {ascii_str}")

# 解析头部
width = struct.unpack_from('<H', res0_data, 0)[0]
height = struct.unpack_from('<H', res0_data, 2)[0]
pixel_data = res0_data[4:]

print(f"\n结构解析:")
print(f"  [0-1] word: width = {width}")
print(f"  [2-3] word: height = {height}")
print(f"  [4-{res0_size-1}] byte[{res0_size-4}]: 像素数据")
print(f"  像素数: {width * height} (预期)")
print(f"  像素数据大小: {len(pixel_data)} 字节 (实际)")
print(f"  每像素字节数: {len(pixel_data) / (width * height):.2f}")

# 像素值统计
unique_colors = sorted(set(pixel_data))
print(f"\n像素值分析:")
print(f"  唯一颜色值 ({len(unique_colors)}个): {unique_colors}")
print(f"  这可能是调色板索引")

# 分析所有子资源的宽高
print("\n" + "="*70)
print("所有子资源的尺寸")
print("="*70)
for i in range(offset_count - 1):
    start = offsets[i]
    end = offsets[i+1]
    data = idx2_data[start:end]
    if len(data) >= 4:
        w = struct.unpack_from('<H', data, 0)[0]
        h = struct.unpack_from('<H', data, 2)[0]
        size = end - start
        print(f"  [{i:2d}] {w:3d}x{h:3d} ({size:4d}字节)")
