#!/usr/bin/env python3
"""
提取 _FDOTHER.DAT__13 相关的资源图片

根据IDA反汇编分析：
- _FDOTHER.DAT__13 加载的是动态索引: n28 + 33 (场景编号 + 33)
- 资源格式: 嵌套DAT (LLLLLL magic)
- Tile数据格式: 直接是RLE压缩像素数据（没有宽高头）
"""
import struct
import os
from PIL import Image

def decompress_rle(src_data, width, height):
    """RLE解压缩 (1:1 实现 sub_4E98D, value_1 == -1 模式)"""
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
                # Skip
                if dst_pos + count_1 > width * height:
                    break
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                # Copy
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
                # Fill
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
                # Interleaved Fill
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
    """应用调色板 (6位扩展到8位)"""
    palette = []
    for i in range(256):
        if i * 3 + 2 < len(palette_data):
            r = (palette_data[i * 3] << 2) | (palette_data[i * 3] >> 4)
            g = (palette_data[i * 3 + 1] << 2) | (palette_data[i * 3 + 1] >> 4)
            b = (palette_data[i * 3 + 2] << 2) | (palette_data[i * 3 + 2] >> 4)
            palette.append((r, g, b))
        else:
            palette.append((0, 0, 0))
    
    img_data = bytearray(len(pixel_data) * 3)
    for i, idx in enumerate(pixel_data):
        if idx < 256:
            img_data[i * 3] = palette[idx][0]
            img_data[i * 3 + 1] = palette[idx][1]
            img_data[i * 3 + 2] = palette[idx][2]
    
    return bytes(img_data)

def extract_scene_resources(dat_path, output_dir):
    """提取所有场景的资源"""
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    os.makedirs(output_dir, exist_ok=True)
    
    if data[:6] != b'LLLLLL':
        print(f"不是有效的 FDOTHER.DAT 文件")
        return
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    # 提取调色板 (索引75)
    pal_start = offsets[75]
    pal_end = offsets[76] if 76 < len(offsets) else len(data)
    palette_data = data[pal_start:pal_end]
    print(f"调色板大小: {len(palette_data)} 字节")
    
    # 提取索引33-38 (场景0-5) 和 82-90 (特殊场景)
    scene_indices = list(range(33, 39)) + list(range(82, min(91, len(offsets))))
    
    for scene_idx in scene_indices:
        if scene_idx >= len(offsets):
            continue
        
        res_start = offsets[scene_idx]
        res_end = offsets[scene_idx+1] if scene_idx+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        print(f"\n=== 索引 {scene_idx} (偏移 0x{res_start:X}) 大小: {len(res_data)} ===")
        
        # 检查是否是嵌套DAT
        if res_data[:6] == b'LLLLLL':
            nested_count = struct.unpack_from('<I', res_data, 6)[0]
            print(f"  嵌套资源数: {nested_count}")
            
            # 提取有效偏移
            valid_offsets = []
            for i in range(min(nested_count, 100)):
                offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
                if offset < len(res_data):
                    valid_offsets.append((i, offset))
                else:
                    break
            
            print(f"  有效偏移数: {len(valid_offsets)}")
            
            # 输出场景目录
            scene_dir = os.path.join(output_dir, f'scene_{scene_idx}')
            os.makedirs(scene_dir, exist_ok=True)
            
            # 提取每个tile
            for tile_idx, (orig_idx, tile_offset) in enumerate(valid_offsets):
                tile_data = res_data[tile_offset:]
                
                if len(tile_data) < 11:
                    continue
                
                width = struct.unpack_from('<H', tile_data, 0)[0]
                height = struct.unpack_from('<H', tile_data, 2)[0]
                
                print(f"    Tile {orig_idx}: 偏移=0x{tile_offset:X}, w={width}, h={height}")
                
                if width > 1024 or height > 1024 or width == 0 or height == 0:
                    print(f"      尺寸不合理，跳过")
                    continue
                
                # RLE数据从偏移9开始
                rle_data = tile_data[9:]
                
                pixel_data = decompress_rle(rle_data, width, height)
                img_rgb = apply_palette(palette_data, pixel_data)
                img = Image.frombytes('RGB', (width, height), img_rgb)
                
                output_path = os.path.join(scene_dir, f'tile{orig_idx:03d}_{width}x{height}.png')
                img.save(output_path)
                print(f"      [OK] 导出: {output_path}")
        else:
            print(f"  不是嵌套DAT格式，跳过")

if __name__ == '__main__':
    dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    output_dir = r'D:\workspace\fd2_dat_freebuff\output\fdother13_tiles'
    
    extract_scene_resources(dat_path, output_dir)
