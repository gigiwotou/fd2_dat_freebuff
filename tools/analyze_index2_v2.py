"""
重新分析索引2的真实结构
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

print(f"索引2: 文件偏移 0x{idx2_start:08X} - 0x{idx2_end:08X}, 大小 {idx2_size} 字节")

idx2_data = file_data[idx2_start:idx2_end]

# ========================================
# 分析：哪些是有效的递增偏移？
# ========================================
print("\n" + "="*70)
print("寻找有效的递增偏移序列")
print("="*70)

# 读取前100个值
values = []
for i in range(100):
    val = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
    values.append(val)
    if i < 80:
        print(f"  [{i:3d}] = {val:10d} (0x{val:08X})")

# 检查递增序列
print("\n递增序列分析:")
seq_start = 0
seq_len = 1
for i in range(1, len(values)):
    if values[i] > values[i-1]:
        seq_len += 1
    else:
        if seq_len > 10:
            print(f"  递增序列: [{seq_start}] - [{i-1}], 长度 {seq_len}")
        seq_start = i
        seq_len = 1

if seq_len > 10:
    print(f"  递增序列: [{seq_start}] - [{len(values)-1}], 长度 {seq_len}")

# ========================================
# 假设前78个是偏移表，指向后面的数据
# ========================================
print("\n" + "="*70)
print("假设: 前78个值是偏移表，指向数据区")
print("="*70)

offset_count = 78
offsets = []
for i in range(offset_count):
    off = struct.unpack('<I', idx2_data[i*4:i*4+4])[0]
    offsets.append(off)

print(f"\n偏移表 ({offset_count} 个条目):")
for i in range(offset_count):
    print(f"  [{i:3d}] = {offsets[i]:5d}")

# 检查间距
print(f"\n偏移间距:")
for i in range(1, offset_count):
    span = offsets[i] - offsets[i-1]
    print(f"  [{i-1}] -> [{i}]: {span}")

# 数据区从哪里开始？
print(f"\n数据区分析:")
print(f"  第一个偏移: {offsets[0]}")
print(f"  偏移表结束: {offset_count * 4} 字节")

# 第一个偏移是否在偏移表之后？
if offsets[0] >= offset_count * 4:
    print(f"  数据区起始: {offsets[0]} (在偏移表之后)")
    print(f"  数据区到: {offsets[-1]}")
else:
    print(f"  第一个偏移在偏移表内部: {offsets[0]}")

# 计算每个子资源的大小
print(f"\n子资源大小 (假设前78个是偏移):")
for i in range(offset_count - 1):
    size = offsets[i+1] - offsets[i]
    if size > 0 and size < 1000:
        print(f"  子资源[{i}]: 偏移 {offsets[i]} - {offsets[i+1]}, 大小 {size}")

# ========================================
# 另一种理解: 整个37680字节就是一连串数据块
# 每个数据块484字节，共78个块
# ========================================
print("\n" + "="*70)
print("假设: 索引2包含78个固定大小的块，每个484字节")
print("="*70)

block_size = 484
block_count = idx2_size // block_size
print(f"块大小: {block_size} 字节")
print(f"块数量: {block_count}")
print(f"总大小: {block_count * block_size} 字节 (实际: {idx2_size})")

# 分析第一个块
print(f"\n第一个块 (索引 0):")
block0 = idx2_data[0:block_size]
print(f"  Hex Dump (前64字节):")
for i in range(0, 64, 16):
    hex_bytes = ' '.join(f'{b:02X}' for b in block0[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in block0[i:i+16])
    print(f"    {i:4d}: {hex_bytes:<48} {ascii_str}")

# 解析头部
w = struct.unpack_from('<H', block0, 0)[0]
h = struct.unpack_from('<H', block0, 2)[0]
print(f"\n  头部解析:")
print(f"    [0-1] 宽度: {w}")
print(f"    [2-3] 高度: {h}")
print(f"    像素数据: {w * h} 像素")
print(f"    可用数据: {block_size - 4} 字节")

# 分析唯一颜色值
pixel_data = block0[4:]
unique_colors = set(pixel_data)
print(f"\n  颜色分析:")
print(f"    唯一颜色值: {sorted(unique_colors)}")
print(f"    颜色数量: {len(unique_colors)}")

# 检查是否每个块都是484字节
print(f"\n验证块大小一致性:")
for i in range(min(10, block_count)):
    block = idx2_data[i*block_size:(i+1)*block_size]
    if len(block) == block_size:
        w2 = struct.unpack_from('<H', block, 0)[0]
        h2 = struct.unpack_from('<H', block, 2)[0]
        print(f"  块[{i:2d}]: 尺寸 {w2}x{h2}, 数据大小 {block_size} 字节")

# ========================================
# 结论
# ========================================
print("\n" + "="*70)
print("结论")
print("="*70)
print(f"""
索引2结构分析结果:

1. 偏移表占多少字节:
   - 索引2没有传统意义上的"偏移表+数据区"分离结构
   - 整个37680字节是连续的数据块
   - 或者前78个dword (312字节) 是偏移表，但这不太可能

2. 数据区从哪里开始:
   - 如果是固定块结构: 数据区从字节0开始
   - 每个块484字节，共78个块
   - 第一个块从字节0开始

3. 偏移值是相对还是绝对:
   - 前78个值看起来是相对偏移 (从0开始递增，间距484)
   - 但后续值超出范围，可能是像素数据

4. 第一个子资源格式:
   - 前4字节: 头部 [宽度=24, 高度=20]
   - 后续480字节: 像素数据 (24×20=480像素)
   - 每个像素1字节 (调色板索引)
   - 使用的颜色: {0, 20, 24, 74, 77, 197, 199}
""")
