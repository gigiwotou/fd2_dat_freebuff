#!/usr/bin/env python3
"""
分析tile_16的RLE数据，检查是否存在行尾填充
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引63
idx63_data, _, _ = read_dat_resource(data, 0, 63)

# 读取tile_16
res16_data, res16_offset, res16_size = read_dat_resource(idx63_data, 0, 16)

w = struct.unpack_from('<H', res16_data, 0)[0]
h = struct.unpack_from('<H', res16_data, 2)[0]
rle_data = res16_data[4:]

print(f"tile_16: {w}x{h}")
print(f"资源总大小: {res16_size}")
print(f"RLE数据大小: {len(rle_data)}")
print(f"期望未压缩大小: {w * h}")

# 计算可能的stride
# 假设每行有padding，使得总RLE数据大小 = h * (compressed_row_size + padding)
# 或者总数据大小 = w * h + padding_per_row * h
expected_pixels = w * h
actual_rle_size = len(rle_data)
total_extra = actual_rle_size * 100 - expected_pixels  # 这只是粗略估计

print(f"\n分析可能的stride:")
print(f"  总数据大小 / 行数 = {res16_size / h:.2f}")
print(f"  (总数据大小 - 4) / 行数 = {(res16_size - 4) / h:.2f}")

# 尝试找出正确的stride
# 假设RLE数据是 [像素数据(宽度w) + 填充] * 高度h
for stride_candidate in range(w, w + 50):
    # 计算期望的总大小
    expected_total = 4 + stride_candidate * h
    if abs(expected_total - res16_size) < 10:
        print(f"  可能的stride: {stride_candidate} (期望总大小: {expected_total}, 实际: {res16_size})")

# 检查tile_16后面的资源
print(f"\n检查资源边界:")
res17_data, res17_offset, res17_size = read_dat_resource(idx63_data, 0, 17)
print(f"  tile_17偏移: {res17_offset}")
print(f"  tile_16结束位置: {res16_offset + res16_size}")
print(f"  间隙: {res17_offset - (res16_offset + res16_size)}")

# 查看tile_16资源末尾的字节
if res16_size > 20:
    print(f"\ntile_16资源末尾20字节:")
    hex_str = ' '.join(f'{b:02X}' for b in res16_data[-20:])
    print(f"  {hex_str}")

# 尝试用原始资源大小作为stride
print(f"\n使用原始资源大小作为stride测试:")
stride = res16_size - 4  # 减去w,h头
print(f"  stride = {stride}")
print(f"  每行像素数 = {stride / h:.2f}")
