#!/usr/bin/env python3
"""
根据IDA Pro MCP分析结果实现完整的RLE解压缩
sub_4E98D函数的Python实现
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/nested_dat_tiles_v5_rle"
os.makedirs(output_dir, exist_ok=True)

def decompress_sub_4E98D(src_data, width, height, stride, value_1=-1):
    """
    精确实现sub_4E98D的RLE解压缩逻辑
    
    参数:
    - src_data: RLE压缩数据 (不包含w,h头)
    - width: 图像宽度
    - height: 图像高度  
    - stride: 行宽 (通常等于width)
    - value_1: 颜色模式 (-1=原始颜色, 0-255=固定颜色, >255=调色板偏移)
    """
    output_size = stride * height
    output = bytearray(output_size)
    
    src_pos = 0
    src_len = len(src_data)
    
    # 当前行起始位置（相对于输出缓冲区的绝对偏移）
    row_start = 0
    # 当前行已写入的像素数
    col_pos = 0
    # 当前处理的行号
    current_row = 0
    
    while current_row < height and src_pos < src_len:
        ctrl = src_data[src_pos]
        src_pos += 1
        
        count = (ctrl & 0x3F) + 1  # 低6位 + 1
        
        if ctrl & 0x80:  # Bit 7 = 1: 压缩命令
            if ctrl & 0x40:  # Bit 6 = 1: 跳过
                # 跳过count个像素
                col_pos += count
            else:  # Bit 6 = 0: 复制
                # 从源数据复制count个字节
                for i in range(count):
                    if src_pos < src_len and col_pos < width:
                        pixel = src_data[src_pos]
                        src_pos += 1
                        
                        # 计算输出位置
                        out_pos = row_start + col_pos
                        
                        if value_1 == -1:
                            output[out_pos] = pixel
                        elif value_1 > 0xFF:
                            modified = value_1 + (((value_1 >> 8) + pixel) & 7)
                            output[out_pos] = modified & 0xFF
                        else:
                            output[out_pos] = value_1 & 0xFF
                        
                        col_pos += 1
        else:  # Bit 7 = 0: 填充模式
            if src_pos < src_len:
                fill_value = src_data[src_pos]
                src_pos += 1
                
                if value_1 == -1:
                    fill_byte = fill_value
                elif value_1 > 0xFF:
                    fill_byte = (value_1 + (((value_1 >> 8) + fill_value) & 7)) & 0xFF
                else:
                    fill_byte = value_1 & 0xFF
                
                for i in range(count):
                    if col_pos < width:
                        out_pos = row_start + col_pos
                        output[out_pos] = fill_byte
                        col_pos += 1
        
        # 检查是否需要换行
        if col_pos >= width:
            current_row += 1
            row_start += stride
            col_pos = 0
    
    return bytes(output)


with open(dat_path, 'rb') as f:
    data = f.read()

def read_dat_resource(file_data, base_offset, index):
    """正确的DAT读取方式"""
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
print(f"索引63: 大小 {idx63_size}")

# 尝试读取前20个资源并解压缩
print(f"\n提取并解压缩tile:")
for i in range(20):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data is None or len(res_data) < 4:
        continue
    
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    
    if 0 < w <= 320 and 0 < h <= 200:
        rle_data = res_data[4:]  # 跳过w,h头
        
        # 使用value_1=-1 (原始颜色模式)解压缩
        decompressed = decompress_sub_4E98D(rle_data, w, h, w, -1)
        
        if len(decompressed) >= w * h:
            # 创建灰度图像
            img = Image.new('L', (w, h))
            for y in range(h):
                for x in range(w):
                    px_idx = y * w + x
                    if px_idx < len(decompressed):
                        img.putpixel((x, y), decompressed[px_idx])
            
            # 保存
            img_path = os.path.join(output_dir, f"tile_{i}_{w}x{h}.png")
            img.save(img_path)
            print(f"  [{i}] {w}x{h} -> 已保存")
            
            # 统计像素值
            pixel_values = list(decompressed[:w*h])
            non_zero = sum(1 for v in pixel_values if v > 0)
            print(f"      非零像素: {non_zero}/{w*h} ({non_zero/(w*h)*100:.1f}%)")
        else:
            print(f"  [{i}] {w}x{h} -> 解压缩失败 (大小 {len(decompressed)} < {w*h})")

print(f"\n完成！图像已保存到: {output_dir}")
