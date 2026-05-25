#!/usr/bin/env python3
"""
提取 _FDOTHER.DAT__13 指向的资源图片

根据分析：
- 嵌套DAT中偏移表只有5-6个有效偏移
- tile数据直接是RLE压缩像素数据（无宽高头）
- 宽高信息必须从其他地方获取

从sub_2EB9F:
  v9 = (WORD *)(*(DWORD *)(a5 + 4*a6 + 8) + a5)
  sub_4E98D(v9+9, *v9, v9[1], ...)

但sub_25A96不使用sub_2EB9F，而是使用sub_39694

需要查看sub_39694的原始实现
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
                if dst_pos + count_1 > width * height:
                    break
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
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

def extract_tile_images(dat_path, output_dir):
    """提取嵌套DAT中的tile图片"""
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
    
    # _FDOTHER.DAT__13 使用的索引: v36[n28] = "?355[\\]^"
    # 场景0: 63, 场景1: 51, 场景2: 53, 场景3: 53, 场景4: 91, 场景5: 92, 场景6: 93, 场景7: 94
    scene_indices = [63, 51, 53, 91, 92, 93, 94]
    
    for scene_idx in scene_indices:
        if scene_idx >= len(offsets):
            continue
        
        res_start = offsets[scene_idx]
        res_end = offsets[scene_idx+1] if scene_idx+1 < len(offsets) else len(data)
        res_data = data[res_start:res_end]
        
        if res_data[:6] != b'LLLLLL':
            continue
        
        nested_count = struct.unpack_from('<I', res_data, 6)[0]
        
        # 查找有效偏移 (直到遇到无效值)
        valid_offsets = []
        for i in range(min(nested_count, 100)):
            offset = struct.unpack_from('<I', res_data, 10 + i*4)[0]
            if offset < len(res_data):
                valid_offsets.append((i, offset))
            else:
                break
        
        if len(valid_offsets) < 2:
            continue
        
        print(f"\n=== 场景 {scene_idx} ({len(valid_offsets)} tiles) ===")
        
        scene_dir = os.path.join(output_dir, f'scene_{scene_idx}')
        os.makedirs(scene_dir, exist_ok=True)
        
        # 提取每个tile
        for tile_idx in range(len(valid_offsets) - 1):
            orig_idx, tile_offset = valid_offsets[tile_idx]
            _, next_offset = valid_offsets[tile_idx + 1]
            
            tile_size = next_offset - tile_offset
            tile_data = res_data[tile_offset:next_offset]
            
            print(f"\nTile {orig_idx}: 大小={tile_size} 字节")
            
            # 尝试各种可能的宽高组合
            # tile_size 是RLE压缩后的大小
            # 尝试将tile_size视为解压后的大小
            test_sizes = []
            for w in range(16, 321, 16):
                if tile_size % w == 0:
                    h = tile_size // w
                    if 16 <= h <= 256:
                        test_sizes.append((w, h))
            
            # 添加常见尺寸
            common_sizes = [
                (320, 200), (160, 100), (80, 50),
                (64, 48), (48, 64), (32, 32), (16, 16),
                (128, 128), (256, 256), (160, 120), (120, 160),
            ]
            for s in common_sizes:
                if s not in test_sizes:
                    test_sizes.append(s)
            
            # 对每个可能尺寸尝试解压缩
            exported = False
            for width, height in test_sizes[:5]:  # 限制数量
                try:
                    pixel_data = decompress_rle(tile_data, width, height)
                    img_rgb = apply_palette(palette_data, pixel_data)
                    img = Image.frombytes('RGB', (width, height), img_rgb)
                    output_path = os.path.join(scene_dir, f'tile{orig_idx:03d}_{width}x{height}.png')
                    img.save(output_path)
                    print(f"  [导出] {width}x{height}: {output_path}")
                    exported = True
                except Exception as e:
                    pass
            
            if not exported:
                print(f"  [失败] 无法导出")

if __name__ == '__main__':
    dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'
    output_dir = r'D:\workspace\fd2_dat_freebuff\output\fdother13_correct'
    
    extract_tile_images(dat_path, output_dir)
