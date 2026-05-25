#!/usr/bin/env python3
"""
根据sub_2EB9F的反汇编代码正确提取索引33/34的tile图片。

资源结构（从反汇编推导）：
- [0-1]: width (WORD)
- [2-3]: height (WORD)  
- [4-7]: 未知 (DWORD)
- [8+]: 偏移表，每个条目4字节，存储相对于资源开头的偏移

每个tile的数据格式：
- [0-1]: tile_width (WORD)
- [2-3]: tile_height (WORD)
- [4-8]: 未知 (5字节)
- [9+]: RLE压缩的像素数据

RLE解压缩由sub_4E98D完成。
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother13_tiles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 读取FDOTHER.DAT
fdother_path = os.path.join(WORKSPACE, "bin", "FDOTHER.DAT")
with open(fdother_path, 'rb') as f:
    fdother_data = f.read()

print(f"FDOTHER.DAT 大小: {len(fdother_data)} 字节")

# 解析FDOTHER.DAT索引表
# 格式: [LLLLLL:6][count:4][offsets...][sizes...]
magic = fdother_data[:6]
if magic != b'LLLLLL':
    print(f"错误: 无效的magic: {magic}")
    exit(1)

index_count = struct.unpack_from('<I', fdother_data, 6)[0]
print(f"索引数量: {index_count}")

# 索引表: 前index_count*4字节是偏移，后index_count*4字节是大小
offsets_start = 10
sizes_start = 10 + index_count * 4

def get_resource(index):
    """获取指定索引的资源数据"""
    if index >= index_count:
        return None
    offset = struct.unpack_from('<I', fdother_data, offsets_start + index * 4)[0]
    size = struct.unpack_from('<I', fdother_data, sizes_start + index * 4)[0]
    return fdother_data[offset:offset + size]

# RLE解压缩函数（根据sub_4E98D反汇编实现）
def decompress_rle(src_data, width, height, dst_buffer_size=None):
    """
    解压缩RLE数据。
    src_data: RLE压缩的字节数据
    width: 目标宽度
    height: 目标高度
    返回: 解压缩后的像素数组（每行width字节，共height行）
    """
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    dst_pos = 0
    row = 0
    
    while row < height and src_pos < len(src_data):
        # 计算当前行剩余空间
        row_remaining = width - (dst_pos % width)
        
        byte = src_data[src_pos]
        src_pos += 1
        
        # 检查bit 7 (0x80) - 是否是控制字节
        if byte & 0x80:
            # 控制字节
            # 检查bit 6 (0x40) - 区分跳过/复制
            if byte & 0x40:
                # Bit 6 = 1: 跳过（不写入数据）
                count = ((byte & 0x3F) + 1)
                # 跳过count个像素位置
                dst_pos += count
            else:
                # Bit 6 = 0: 复制count个字节从源
                count = ((byte & 0x3F) + 1)
                for i in range(count):
                    if dst_pos < dst_size:
                        dst[dst_pos] = src_data[src_pos]
                        src_pos += 1
                        dst_pos += 1
        else:
            # 非控制字节: 填充count个相同值
            # count = byte + 1
            count = byte + 1
            # 读取下一个字节作为填充值
            if src_pos < len(src_data):
                fill_value = src_data[src_pos]
                src_pos += 1
                for i in range(count):
                    if dst_pos < dst_size:
                        dst[dst_pos] = fill_value
                        dst_pos += 1
    
    return bytes(dst)

# 提取索引33的tile
for idx in [33, 34]:
    print(f"\n{'='*60}")
    print(f"提取索引 {idx}")
    print(f"{'='*60}")
    
    res_data = get_resource(idx)
    if res_data is None:
        print(f"  索引 {idx} 不存在")
        continue
    
    print(f"  资源大小: {len(res_data)} 字节")
    
    # 解析资源头
    width = struct.unpack_from('<H', res_data, 0)[0]
    height = struct.unpack_from('<H', res_data, 2)[0]
    unknown = struct.unpack_from('<I', res_data, 4)[0]
    
    print(f"  Width: {width}")
    print(f"  Height: {height}")
    print(f"  Unknown[4]: 0x{unknown:08X}")
    
    if width == 0 or height == 0 or width > 2048 or height > 2048:
        print(f"  Width或Height不合理，跳过")
        continue
    
    # 偏移表从偏移8开始
    offset_table_start = 8
    
    # 计算tile数量：查找偏移表中的有效条目
    # 偏移表每个条目4字节
    tile_offsets = []
    max_possible_tiles = (len(res_data) - offset_table_start) // 4
    
    for i in range(max_possible_tiles):
        offset = struct.unpack_from('<I', res_data, offset_table_start + i * 4)[0]
        if offset < len(res_data):
            tile_offsets.append(offset)
        else:
            break
    
    print(f"  Tile数量: {len(tile_offsets)}")
    
    # 提取每个tile
    output_dir = os.path.join(OUTPUT_DIR, f"index{idx}")
    os.makedirs(output_dir, exist_ok=True)
    
    for tile_idx, tile_offset in enumerate(tile_offsets[:10]):  # 先提取前10个tile
        if tile_offset < offset_table_start:
            continue
            
        # 获取下一个tile的偏移，计算当前tile的大小
        if tile_idx + 1 < len(tile_offsets):
            tile_size = tile_offsets[tile_idx + 1] - tile_offset
        else:
            tile_size = len(res_data) - tile_offset
        
        tile_data = res_data[tile_offset:tile_offset + tile_size]
        
        if len(tile_data) < 9:
            continue
        
        # 解析tile头
        tile_width = struct.unpack_from('<H', tile_data, 0)[0]
        tile_height = struct.unpack_from('<H', tile_data, 2)[0]
        tile_unknown = tile_data[4:9]
        
        print(f"\n  Tile {tile_idx} (偏移 {tile_offset}):")
        print(f"    大小: {len(tile_data)} 字节")
        print(f"    Tile Width: {tile_width}")
        print(f"    Tile Height: {tile_height}")
        print(f"    Unknown[4:9]: {' '.join(f'{b:02X}' for b in tile_unknown)}")
        
        if tile_width == 0 or tile_height == 0 or tile_width > 1024 or tile_height > 1024:
            print(f"    Tile尺寸不合理，跳过")
            continue
        
        # RLE数据从偏移9开始
        rle_data = tile_data[9:]
        
        # 解压缩
        try:
            pixels = decompress_rle(rle_data, tile_width, tile_height)
            
            # 创建图像
            img = Image.new('P', (tile_width, tile_height))
            img.putdata(pixels)
            
            # 保存
            img_path = os.path.join(output_dir, f"tile_{tile_idx:04d}.png")
            img.save(img_path)
            print(f"    已保存: {img_path}")
            
        except Exception as e:
            print(f"    解压缩失败: {e}")
    
    print(f"\n  索引 {idx} 提取完成")

print("\n\n所有提取完成！")
