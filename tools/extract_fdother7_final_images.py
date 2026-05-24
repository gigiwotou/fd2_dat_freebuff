#!/usr/bin/env python3
"""
提取 _FDOTHER.DAT__7 使用的资源图片 (1:1 根据反汇编实现)

根据 sub_2EB9F:
  v9 = (WORD *)(*(DWORD *)(a5 + 4*a6 + 8) + a5);
  sub_4E98D(v9+9, *v9, v9[1], a7, a8, value);

Tile 头格式 (10 字节):
  [0-1] WORD: width
  [2-3] WORD: height
  [4-7] DWORD: 未知 (可能是tile宽度或其他元数据)
  [8-9] WORD: 未知 (可能是tile高度或其他元数据)
  [9+]   RLE 压缩像素数据

RLE 控制字节格式 (value_1 == -1 模式):
  Bit7=1, Bit6=1: Skip (跳过像素)
  Bit7=1, Bit6=0: Copy (复制源数据)
  Bit7=0, Bit6=0: Fill (填充单色)
  Bit7=0, Bit6=1: Interleaved Fill (交错填充，每隔一个像素)
  计数值 = (value & 0x3F) + 1
"""

import struct
import os
from PIL import Image

def decompress_rle(src_data, width, height):
    """1:1 实现 sub_4E98D (value_1 == -1 模式)"""
    output = bytearray(width * height)
    src_pos = 0
    src_end = len(src_data)
    
    for row in range(height):
        dst_pos = row * width
        count = width
        
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                # Skip: 跳过像素 (dst_pos 前进，不写数据)
                if dst_pos + count_1 > width * height:
                    break
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                # Copy: 从源数据复制
                if src_pos + count_1 > src_end:
                    break
                if dst_pos + count_1 > width * height:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and not bit6:
                # Fill: 填充单色
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 > width * height:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
            else:
                # Interleaved Fill: 交错填充 (每隔一个像素)
                if src_pos >= src_end:
                    break
                if dst_pos + count_1 * 2 > width * height:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
    
    return bytes(output)

def apply_palette(palette_data, pixel_data):
    """应用调色板 (6位颜色扩展到8位)"""
    palette = []
    for i in range(256):
        if i * 3 + 2 < len(palette_data):
            r = palette_data[i * 3]
            g = palette_data[i * 3 + 1]
            b = palette_data[i * 3 + 2]
            # 6位扩展到8位
            r = (r << 2) | (r >> 4)
            g = (g << 2) | (g >> 4)
            b = (b << 2) | (b >> 4)
            palette.append((r, g, b))
        else:
            palette.append((0, 0, 0))
    
    img_data = bytearray(len(pixel_data) * 3)
    for i, idx in enumerate(pixel_data):
        if idx < 256:
            img_data[i * 3] = palette[idx][0]
            img_data[i * 3 + 1] = palette[idx][1]
            img_data[i * 3 + 2] = palette[idx][2]
        else:
            img_data[i * 3] = 0
            img_data[i * 3 + 1] = 0
            img_data[i * 3 + 2] = 0
    
    return bytes(img_data)

def extract_images(dat_path, palette_path, output_dir):
    """提取嵌套 DAT 中的所有 tile 图片"""
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    
    with open(palette_path, 'rb') as f:
        palette_data = f.read()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 解析 FDOTHER.DAT 索引 7
    if dat_data[:6] != b'LLLLLL':
        print(f"不是有效的 FDOTHER.DAT 文件")
        return
    
    count = struct.unpack_from('<I', dat_data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', dat_data, 10 + i * 4)[0]
        offsets.append(offset)
    
    print(f"FDOTHER.DAT 资源数量: {count}")
    
    # 获取索引 7 的资源
    if 7 >= len(offsets):
        print(f"索引 7 超出范围")
        return
    
    res7_start = offsets[7]
    res7_end = offsets[8] if 8 < len(offsets) else len(dat_data)
    res7_data = dat_data[res7_start:res7_end]
    
    print(f"\n索引 7 资源大小: {len(res7_data)} 字节")
    
    # 检查是否是嵌套 DAT
    if res7_data[:6] != b'LLLLLL':
        print(f"索引 7 不是嵌套 DAT 格式")
        return
    
    nested_count = struct.unpack_from('<I', res7_data, 6)[0]
    print(f"嵌套资源数量: {nested_count}")
    
    # 解析嵌套偏移表
    nested_offsets = []
    for i in range(nested_count):
        offset = struct.unpack_from('<I', res7_data, 10 + i * 4)[0]
        nested_offsets.append(offset)
        print(f"  嵌套偏移表[{i}]: 0x{offset:X} ({offset})")
    
    # 提取每个 tile
    offset_table_end = 10 + nested_count * 4
    
    for tile_idx, tile_offset in enumerate(nested_offsets):
        if tile_offset < offset_table_end or tile_offset >= len(res7_data):
            print(f"\nTile {tile_idx}: 偏移无效 (0x{tile_offset:X})")
            continue
        
        tile_data = res7_data[tile_offset:]
        
        if len(tile_data) < 10:
            print(f"\nTile {tile_idx}: 数据太短 ({len(tile_data)} 字节)")
            continue
        
        width = struct.unpack_from('<H', tile_data, 0)[0]
        height = struct.unpack_from('<H', tile_data, 2)[0]
        
        print(f"\n=== Tile {tile_idx} ===")
        print(f"  偏移: 0x{tile_offset:X}")
        print(f"  宽度: {width}")
        print(f"  高度: {height}")
        print(f"  数据大小: {len(tile_data)} 字节")
        
        if width > 1024 or height > 1024 or width == 0 or height == 0:
            print(f"  尺寸不合理，跳过")
            continue
        
        # RLE 数据从偏移 9 开始
        rle_data = tile_data[9:]
        print(f"  RLE 数据大小: {len(rle_data)} 字节")
        
        # 解压缩
        pixel_data = decompress_rle(rle_data, width, height)
        
        # 应用调色板
        img_rgb = apply_palette(palette_data, pixel_data)
        
        # 创建图像
        img = Image.frombytes('RGB', (width, height), img_rgb)
        
        # 保存
        output_path = os.path.join(output_dir, f'tile{tile_idx:03d}_{width}x{height}.png')
        img.save(output_path)
        print(f"  [OK] 导出: {output_path}")

if __name__ == '__main__':
    dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    palette_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    output_dir = r'D:\workspace\fd2_dat_freebuff\output\fdother7_tiles_final'
    
    # 注意：需要从 FDOTHER.DAT 索引 75 提取调色板
    # 这里直接传 FDOTHER.DAT 路径，脚本内部会提取
    
    # 首先提取调色板
    with open(dat_path, 'rb') as f:
        fdother_data = f.read()
    
    if fdother_data[:6] != b'LLLLLL':
        print(f"FDOTHER.DAT 格式错误")
    else:
        count = struct.unpack_from('<I', fdother_data, 6)[0]
        offsets = []
        for i in range(count):
            offset = struct.unpack_from('<I', fdother_data, 10 + i * 4)[0]
            offsets.append(offset)
        
        # 提取调色板 (索引 75)
        pal_start = offsets[75]
        pal_end = offsets[76] if 76 < len(offsets) else len(fdother_data)
        palette_data = fdother_data[pal_start:pal_end]
        
        # 保存到临时文件
        palette_tmp = os.path.join(output_dir, 'palette.bin')
        os.makedirs(output_dir, exist_ok=True)
        with open(palette_tmp, 'wb') as f:
            f.write(palette_data)
        
        print(f"调色板大小: {len(palette_data)} 字节")
        
        # 提取图片
        extract_images(dat_path, palette_tmp, output_dir)
