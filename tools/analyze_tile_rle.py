#!/usr/bin/env python3
"""
分析tile数据是否需要RLE解压缩
"""
import struct

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 正确的DAT读取方式
def read_dat_resource(file_data, base_offset, index):
    index_offset = base_offset + 4 * index + 6
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    size = offset1 - offset0
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    if offset0 + size > len(file_data):
        size = len(file_data) - offset0
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取索引63
idx63_data, idx63_offset, idx63_size = read_dat_resource(data, 0, 63)

print(f"索引63:")
print(f"  大小: {idx63_size}")

# 读取嵌套DAT的索引0（320x200）
res0_data, res0_offset, res0_size = read_dat_resource(idx63_data, 0, 0)
print(f"\n嵌套DAT索引0:")
print(f"  偏移: {res0_offset}")
print(f"  大小: {res0_size}")
print(f"  期望像素数 (320x200): {320*200}")

if res0_size < 4:
    print("错误：数据太小")
    exit(1)

w = struct.unpack_from('<H', res0_data, 0)[0]
h = struct.unpack_from('<H', res0_data, 2)[0]
print(f"  尺寸: {w}x{h}")

# 检查数据模式
print(f"\n数据分析:")
print(f"  前16字节: {' '.join(f'{b:02X}' for b in res0_data[:16])}")

# 检查是否是RLE压缩数据
# RLE控制字节格式：
# Bit 7 (0x80) = 1: 压缩命令
#   Bit 6 (0x40) = 1: 跳过
#   Bit 6 (0x40) = 0: 复制
# Bit 7 (0x80) = 0: 未压缩数据
#   Bit 6 (0x40) = 0: 填充
#   Bit 6 (0x40) = 1: 隔行写入

# 查看前100字节的控制字节模式
print(f"\n前100字节的控制字节分析:")
for i in range(min(100, len(res0_data))):
    byte = res0_data[i]
    bit7 = (byte & 0x80) >> 7
    bit6 = (byte & 0x40) >> 6
    count = byte & 0x3F
    if bit7 == 1:
        if bit6 == 1:
            type_str = "跳过"
        else:
            type_str = "复制"
    else:
        if bit6 == 1:
            type_str = "隔行"
        else:
            type_str = "填充"
    print(f"  [{i}] 0x{byte:02X}: {type_str} (count={count})")

# 尝试简单的RLE解压缩
print(f"\n尝试RLE解压缩...")
def decompress_rle_simple(src_data, expected_size):
    """简单的RLE解压缩"""
    output = bytearray()
    src_pos = 0
    src_len = len(src_data)
    
    while src_pos < src_len and len(output) < expected_size:
        ctrl = src_data[src_pos]
        src_pos += 1
        
        if ctrl & 0x80:  # 压缩命令
            if ctrl & 0x40:  # 跳过
                count = ctrl & 0x3F
                output.extend(b'\x00' * count)
            else:  # 复制
                count = ctrl & 0x3F
                if src_pos + count <= src_len:
                    output.extend(src_data[src_pos:src_pos + count])
                    src_pos += count
        else:  # 未压缩
            if ctrl & 0x40:  # 隔行
                # 跳过，需要更复杂的处理
                count = ctrl & 0x3F
                # 这里简化处理
                output.extend(b'\x00' * count)
            else:  # 填充
                count = ctrl & 0x3F
                if src_pos < src_len:
                    value = src_data[src_pos]
                    src_pos += 1
                    output.extend(bytes([value]) * count)
    
    return bytes(output)

# 解压缩
decompressed = decompress_rle_simple(res0_data[4:], 320 * 200)
print(f"解压缩后大小: {len(decompressed)}")
print(f"期望大小: {320 * 200}")

# 分析解压缩后的像素值
if len(decompressed) > 0:
    pixel_values = list(decompressed[:1000])
    print(f"\n前1000像素值统计:")
    print(f"  最小值: {min(pixel_values)}")
    print(f"  最大值: {max(pixel_values)}")
    print(f"  平均值: {sum(pixel_values) / len(pixel_values):.2f}")
    
    # 计算非零像素比例
    non_zero = sum(1 for v in pixel_values if v > 0)
    print(f"  非零像素: {non_zero}/{len(pixel_values)} ({non_zero/len(pixel_values)*100:.1f}%)")
