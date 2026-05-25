#!/usr/bin/env python3
"""
根据IDA反汇编的sub_4E98D精确实现RLE解压缩

RLE控制字节格式 (value):
- Bit 7 (0x80) = 1, Bit 6 (0x40) = 1: 跳过count字节
- Bit 7 = 1, Bit 6 = 0: 从源复制count字节  
- Bit 7 = 0, Bit 6 = 0: 填充count字节（读取下一个字节作为填充值）
- Bit 7 = 0, Bit 6 = 1: 隔行写入（每隔一个字节写入value）

count = (value & 0x3F) + 1
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother_index34_final")
os.makedirs(OUTPUT_DIR, exist_ok=True)

dat_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引34的资源
idx34_start = offsets[34]
idx34_end = offsets[35]
res_data = data[idx34_start:idx34_end]

print(f"索引34大小: {len(res_data)} 字节")

# 解析tile_count
tile_count = struct.unpack_from('<H', res_data, 0)[0]
print(f"Tile数量: {tile_count}")

# 偏移表从偏移8开始
offset_table_start = 8
tile_offsets = []
for i in range(tile_count):
    addr = offset_table_start + i * 4
    if addr + 4 > len(res_data):
        break
    offset = struct.unpack_from('<I', res_data, addr)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)
    else:
        break

print(f"有效偏移数: {len(tile_offsets)}")

# RLE解压缩（精确对应IDA sub_4E98D）
def decompress_rle_exact(src_data, width, height):
    """
    精确实现sub_4E98D的RLE解压缩
    
    参数:
    - src_data: RLE压缩数据
    - width: 图像宽度
    - height: 图像高度
    
    返回: 解压缩后的像素数据
    """
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    row = 0
    
    while row < height:
        # count = width (每行像素数)
        count = width
        dst_pos = row * width
        
        while count > 0 and src_pos < len(src_data):
            value = src_data[src_pos]
            src_pos += 1
            
            # 检查bit 7
            if value & 0x80:
                # Bit 7 = 1: 控制字节
                # 检查bit 6
                if value & 0x40:
                    # Bit 6 = 1: 跳过
                    count_val = (value & 0x3F) + 1
                    dst_pos += count_val
                    count -= count_val
                else:
                    # Bit 6 = 0: 复制
                    count_val = (value & 0x3F) + 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size and src_pos < len(src_data):
                            dst[dst_pos] = src_data[src_pos]
                            src_pos += 1
                            dst_pos += 1
                            count -= 1
            else:
                # Bit 7 = 0
                # 检查bit 6
                if value & 0x40:
                    # Bit 6 = 1: 隔行写入
                    count_val = (value & 0x3F) + 1
                    value2 = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count >= 2 and dst_pos + 1 < dst_size:
                            dst[dst_pos + 1] = value2
                            dst_pos += 2
                            count -= 2
                else:
                    # Bit 6 = 0: 填充
                    count_val = (value & 0x3F) + 1
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size:
                            dst[dst_pos] = fill_value
                            dst_pos += 1
                            count -= 1
        
        row += 1
    
    return bytes(dst)

# 提取tile
extracted = 0
for tile_idx, tile_offset in enumerate(tile_offsets[:10]):
    if tile_idx + 1 < len(tile_offsets):
        tile_size = tile_offsets[tile_idx + 1] - tile_offset
    else:
        tile_size = len(res_data) - tile_offset
    
    tile_data = res_data[tile_offset:tile_offset + tile_size]
    
    if len(tile_data) < 9:
        continue
    
    tile_width = struct.unpack_from('<H', tile_data, 0)[0]
    tile_height = struct.unpack_from('<H', tile_data, 2)[0]
    
    if tile_width == 0 or tile_height == 0 or tile_width > 1024 or tile_height > 1024:
        continue
    
    rle_data = tile_data[9:]
    
    print(f"\nTile {tile_idx}: {tile_width}x{tile_height}, RLE大小: {len(rle_data)}")
    
    try:
        pixels = decompress_rle_exact(rle_data, tile_width, tile_height)
        
        img = Image.new('P', (tile_width, tile_height))
        img.putdata(pixels)
        
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}.png")
        img.save(img_path)
        extracted += 1
        
        print(f"  已保存: {img_path}")
        
    except Exception as e:
        print(f"  失败: {e}")
        import traceback
        traceback.print_exc()

print(f"\n总计: {extracted} 个tile")
