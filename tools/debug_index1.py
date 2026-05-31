"""调试索引1原始数据"""
import struct

fdother_path = 'game/FDOTHER.DAT'
with open(fdother_path, 'rb') as f:
    data = f.read()

# 解析索引表
count = struct.unpack_from('<I', data, 6)[0]
print(f"总资源数: {count}")

# 打印前10个资源的偏移
for i in range(min(10, count)):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    print(f"  索引{i}: 偏移 {off}")

# 索引1
idx = 1
start = struct.unpack_from('<I', data, 10 + idx * 4)[0]
end = struct.unpack_from('<I', data, 10 + (idx + 1) * 4)[0]
print(f"\n索引1: 偏移 {start} - {end}, 大小 {end - start}")

# 读取索引1的前20字节
res_data = data[start:end]
print(f"索引1前20字节: {res_data[:20].hex(' ')}")

# 尝试不同的解析方式
print(f"\n解析尝试:")
print(f"  作为[width:2][height:2]: w={struct.unpack_from('<H', res_data, 0)[0]}, h={struct.unpack_from('<H', res_data, 2)[0]}")
print(f"  作为[width:2][height:2][pal:1]: w={struct.unpack_from('<H', res_data, 0)[0]}, h={struct.unpack_from('<H', res_data, 2)[0]}, pal={res_data[4]}")

# 检查是否有LLLLLL头
print(f"\n前6字节: {res_data[:6]}")
if res_data[:6] == b'LLLLLL':
    print("  有LLLLLL头!")
else:
    print("  无LLLLLL头")

# 直接从FDOTHER.DAT读取索引1的原始位置
print(f"\n直接从文件读取索引1位置 {start}:")
raw = data[start:start+20]
print(f"  前20字节: {raw.hex(' ')}")

# 索引0
idx0_start = struct.unpack_from('<I', data, 10 + 0 * 4)[0]
idx0_end = struct.unpack_from('<I', data, 10 + 1 * 4)[0]
print(f"\n索引0: 偏移 {idx0_start} - {idx0_end}, 大小 {idx0_end - idx0_start}")
pal_data = data[idx0_start:idx0_end]
print(f"  前20字节: {pal_data[:20].hex(' ')}")
