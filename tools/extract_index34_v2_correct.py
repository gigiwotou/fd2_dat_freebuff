#!/usr/bin/env python3
"""
使用正确的DAT格式读取并提取索引34的资源（角色/物品展示动画）

根据sub_24336的分析:
- 使用FDOTHER索引34
- 循环变量n69从0-100
- 调用sub_2EB9F解压tile

根据sub_2EB9F反汇编:
- tile_data_ptr = arg0 + *(DWORD *)(arg0 + 4*arg4 + 8)
- width = *(WORD *)tile_data_ptr
- height = *(WORD *)(tile_data_ptr + 2)
- RLE数据从 tile_data_ptr + 9 开始

DAT文件格式:
- 文件头: 6字节 (LLLLLL)
- 索引表: 从偏移6开始，每个索引4字节（只有偏移）
- 索引n的数据: offsets[n] 到 offsets[n+1]
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother_index34_correct")
os.makedirs(OUTPUT_DIR, exist_ok=True)

dat_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")

with open(dat_path, 'rb') as f:
    data = f.read()

print(f"文件大小: {len(data)} 字节")

# 验证magic
magic = data[:6]
if magic != b'LLLLLL':
    print("错误: 无效的DAT文件")
    exit(1)

# 读取所有索引偏移
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# 获取索引34的资源
idx34_start = offsets[34]
idx34_end = offsets[35]
idx34_size = idx34_end - idx34_start
res_data = data[idx34_start:idx34_end]

print(f"\n索引34:")
print(f"  起始偏移: 0x{idx34_start:08X} ({idx34_start})")
print(f"  结束偏移: 0x{idx34_end:08X} ({idx34_end})")
print(f"  大小: {idx34_size} 字节")
print(f"  前64字节:")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
    print(f"    {i:03d}: {hex_str}  {ascii_str}")

# 解析资源结构
# 根据之前的分析，可能是: [?:2][tile_count:2][?:4][offset_table...]
val0 = struct.unpack_from('<H', res_data, 0)[0]
val2 = struct.unpack_from('<H', res_data, 2)[0]
val4 = struct.unpack_from('<I', res_data, 4)[0]

print(f"\n解析:")
print(f"  [0-1]: 0x{val0:04X} = {val0}")
print(f"  [2-3]: 0x{val2:04X} = {val2}")
print(f"  [4-7]: 0x{val4:08X} = {val4}")

# 尝试不同的tile_count位置
# 假设[2-3]是tile_count
tile_count = val2
print(f"\n假设tile_count = {tile_count}")

# 偏移表从偏移8开始
offset_table_start = 8
print(f"\n偏移表从偏移{offset_table_start}开始:")

tile_offsets = []
for i in range(tile_count):
    addr = offset_table_start + i * 4
    if addr + 4 > len(res_data):
        break
    offset = struct.unpack_from('<I', res_data, addr)[0]
    if offset < len(res_data):
        tile_offsets.append(offset)
    else:
        print(f"  Tile {i}: 偏移 0x{offset:08X} (超出范围)")
        break

print(f"  有效偏移数: {len(tile_offsets)}")

# 打印前20个偏移
for i, offset in enumerate(tile_offsets[:20]):
    print(f"  Tile {i}: 偏移 {offset} (0x{offset:06X})")
    if offset + 16 <= len(res_data):
        tile_w = struct.unpack_from('<H', res_data, offset)[0]
        tile_h = struct.unpack_from('<H', res_data, offset + 2)[0]
        print(f"    宽高: {tile_w}x{tile_h}")

# 根据sub_4E98D反汇编实现RLE解压缩
def decompress_rle_v2(src_data, width, height):
    """
    根据sub_4E98D反汇编实现的RLE解压缩
    
    控制字节格式:
    - Bit 7 (0x80): 判断是否为控制字节
    - Bit 6 (0x40): 区分跳过/复制操作
    - 低6位: 计数值 = (value & 0x3F) + 1
    """
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    dst_pos = 0
    rows_decoded = 0
    
    while rows_decoded < height and src_pos < len(src_data):
        # 计算当前行起始位置
        row_start = rows_decoded * width
        
        while dst_pos < row_start + width and src_pos < len(src_data):
            byte = src_data[src_pos]
            src_pos += 1
            
            # 检查bit 7 (0x80)
            if byte & 0x80:
                # 控制字节
                # 检查bit 6 (0x40)
                if byte & 0x40:
                    # Bit 6 = 1: 跳过（不写入数据）
                    count = ((byte & 0x3F) + 1)
                    dst_pos += count
                else:
                    # Bit 6 = 0: 复制count个字节从源
                    count = ((byte & 0x3F) + 1)
                    for i in range(count):
                        if dst_pos < dst_size and src_pos < len(src_data):
                            dst[dst_pos] = src_data[src_pos]
                            src_pos += 1
                            dst_pos += 1
            else:
                # 非控制字节: 这是填充命令
                # count = byte + 1 (因为低7位是count-1)
                count = (byte & 0x7F) + 1
                if src_pos < len(src_data):
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count):
                        if dst_pos < dst_size:
                            dst[dst_pos] = fill_value
                            dst_pos += 1
        
        # 移动到下一行
        rows_decoded += 1
        dst_pos = rows_decoded * width
    
    return bytes(dst)

# 提取每个tile
extracted = 0
for tile_idx, tile_offset in enumerate(tile_offsets):
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
    
    print(f"\n  Tile {tile_idx}: {tile_width}x{tile_height}, RLE数据大小: {len(rle_data)}")
    
    try:
        pixels = decompress_rle_v2(rle_data, tile_width, tile_height)
        
        img = Image.new('P', (tile_width, tile_height))
        img.putdata(pixels)
        
        img_path = os.path.join(OUTPUT_DIR, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}.png")
        img.save(img_path)
        extracted += 1
        
        print(f"    已保存: {img_path}")
        
    except Exception as e:
        print(f"    解压缩失败: {e}")
        import traceback
        traceback.print_exc()

print(f"\n总计提取: {extracted} 个tile")
print(f"输出目录: {OUTPUT_DIR}")
