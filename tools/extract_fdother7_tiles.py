"""
解压 FDOTHER.DAT 索引 7 变量使用的所有资源图片

根据分析：
1. _FDOTHER.DAT__7 是动态索引加载的资源
2. sub_2FF01 使用索引 82-90 (ASCII 'R'-'Z')
3. sub_2D80D 使用索引 63, 51, 53, 91, 92, 93
4. 这些资源是嵌套 DAT 格式 (LLLLLL magic)
5. 内部是 RLE 压缩的 tile 数据
"""
import struct
import os
from PIL import Image

def load_palette(fdother_path):
    """加载 FDOTHER.DAT 索引 75 的调色板"""
    with open(fdother_path, "rb") as f:
        f.read(6)  # Magic
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    # 6位扩展到8位
    palette_rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        palette_rgb.append((r, g, b))
    
    return palette_rgb

def decompress_rle(data, width, height):
    """
    RLE 解压缩 (1:1 实现 sub_4E98D)
    """
    output = bytearray(width * height)
    src_pos = 0
    dst_pos = 0
    
    for row in range(height):
        row_start = dst_pos
        count = width
        
        while count > 0 and src_pos < len(data):
            value = data[src_pos]
            src_pos += 1
            
            if value & 0x80:
                # 控制字节
                if value & 0x40:
                    # 跳过 (skip)
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
                    # 复制 (copy)
                    copy_count = ((value & 0x3F) >> 2) + 1
                    if src_pos + copy_count > len(data):
                        break
                    for i in range(copy_count):
                        if dst_pos < len(output):
                            output[dst_pos] = data[src_pos]
                        dst_pos += 1
                        src_pos += 1
                    count -= copy_count
            else:
                # 填充 (fill)
                fill_count = ((value & 0x3F) >> 2) + 1
                if src_pos < len(data):
                    fill_value = data[src_pos]
                    src_pos += 1
                else:
                    fill_value = 0
                
                for i in range(fill_count):
                    if dst_pos < len(output):
                        output[dst_pos] = fill_value
                    dst_pos += 1
                count -= fill_count
        
        # 下一行
        dst_pos = row_start + width
    
    return bytes(output)

def extract_nested_dat(resource_data, palette_rgb, output_dir):
    """提取嵌套 DAT 文件中的 tile 图片"""
    if len(resource_data) < 10 or resource_data[:6] != b'LLLLLL':
        print("  -> 不是有效的嵌套 DAT 格式")
        return
    
    # 解析嵌套 DAT 头部
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"  偏移数量: {offset_count}")
    
    # 找到有效偏移
    offset_table_start = 10
    valid_offsets = []
    
    for i in range(offset_count):
        offset_addr = offset_table_start + i * 4
        if offset_addr + 4 > len(resource_data):
            break
        
        offset_val = struct.unpack("<I", resource_data[offset_addr:offset_addr + 4])[0]
        offset_table_end = offset_table_start + offset_count * 4
        
        # 只接受有效的偏移
        if offset_val < len(resource_data) and offset_val >= offset_table_end:
            valid_offsets.append(offset_val)
        else:
            if valid_offsets:
                print(f"  偏移表在 {len(valid_offsets)} 个有效偏移后结束")
            break
    
    print(f"  有效偏移: {len(valid_offsets)} 个")
    
    if not valid_offsets:
        print("  -> 没有有效偏移")
        return
    
    # 提取每个 tile 块
    for idx, tile_offset in enumerate(valid_offsets):
        tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(resource_data)
        tile_rle_data = resource_data[tile_offset:tile_end]
        
        print(f"\n  Tile {idx}: 偏移 {tile_offset}-{tile_end}, RLE 数据大小 {len(tile_rle_data)}")
        print(f"    前 16 字节: {tile_rle_data[:16].hex()}")
        
        # 尝试不同的尺寸解压缩
        dimensions = [
            (320, 200),  # 全屏幕
            (160, 200),  # 半宽
            (160, 100),  # 1/4 屏幕
            (80, 80),    # 小 tile
            (64, 64),    # 标准 tile
            (48, 48),    # 小 tile
            (32, 32),    # 标准 tile
        ]
        
        for width, height in dimensions:
            try:
                # 解压缩
                pixel_data = decompress_rle(tile_rle_data, width, height)
                
                # 检查非零像素比例
                non_zero = sum(1 for p in pixel_data if p != 0)
                total = len(pixel_data)
                ratio = non_zero / total if total > 0 else 0
                
                # 如果非零像素在合理范围 (1% - 90%)
                if 0.01 <= ratio <= 0.90:
                    # 创建图像
                    img = Image.new("RGB", (width, height))
                    pixels = img.load()
                    
                    for y in range(height):
                        for x in range(width):
                            idx = y * width + x
                            if idx < len(pixel_data):
                                pal_idx = pixel_data[idx]
                                if pal_idx < len(palette_rgb):
                                    pixels[x, y] = palette_rgb[pal_idx]
                    
                    # 保存原始尺寸
                    filename = f"tile_{idx:02d}_{width}x{height}.png"
                    filepath = os.path.join(output_dir, filename)
                    img.save(filepath)
                    
                    print(f"    ✓ {width}x{height}: {non_zero}/{total} 像素 ({ratio*100:.1f}%)")
                    
                    # 如果尺寸较小，生成放大版本
                    if min(width, height) < 100:
                        zoom = max(4, 100 // min(width, height))
                        zoomed = img.resize((width * zoom, height * zoom), Image.NEAREST)
                        zoomed_filename = f"tile_{idx:02d}_{width}x{height}_zoom{zoom}x.png"
                        zoomed_filepath = os.path.join(output_dir, zoomed_filename)
                        zoomed.save(zoomed_filepath)
                        
            except Exception as e:
                pass

def extract_fdother7_tiles(data_dir, output_dir):
    """主函数：提取 _FDOTHER.DAT__7 使用的所有资源图片"""
    fdother_path = os.path.join(data_dir, "FDOTHER.DAT")
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT: {fdother_path}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("解压 _FDOTHER.DAT__7 变量使用的资源图片")
    print("=" * 60)
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(fdother_path)
    print(f"[OK] 调色板加载成功 (256 颜色)")
    
    # 动态索引列表
    # sub_2FF01: 索引 82-90 (ASCII 'R'-'Z')
    # sub_2D80D: 索引 63, 51, 53, 91, 92, 93
    dynamic_indices = {
        "scene_0": 82,   # 'R'
        "scene_1": 82,   # 'R'
        "scene_2": 83,   # 'S'
        "scene_3": 84,   # 'T'
        "scene_4": 85,   # 'U'
        "scene_5": 86,   # 'V'
        "scene_6": 87,   # 'W'
        "scene_7": 88,   # 'X'
        "scene_8": 89,   # 'Y'
        "scene_9": 90,   # 'Z'
        "scene_32": 63,  # '?'
        "scene_33": 51,  # '3'
        "scene_34": 53,  # '5'
        "scene_35": 53,  # '5'
    }
    
    with open(fdother_path, "rb") as f:
        # 读取主 DAT 头部
        f.read(6)  # Magic
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        print(f"\nFDOTHER.DAT 资源数量: {count}")
        
        # 提取每个动态索引的资源
        for scene_name, index in dynamic_indices.items():
            if index >= count:
                print(f"\n跳过 {scene_name} (索引 {index} 超出范围)")
                continue
            
            print(f"\n{'='*60}")
            print(f"处理 {scene_name} (索引 {index})...")
            print(f"{'='*60}")
            
            # 创建场景输出目录
            scene_dir = os.path.join(output_dir, scene_name)
            os.makedirs(scene_dir, exist_ok=True)
            
            # 加载资源数据
            start = offsets[index]
            end = offsets[index + 1] if index + 1 < count else None
            f.seek(start)
            resource_data = f.read(end - start) if end else f.read()
            
            print(f"  资源大小: {len(resource_data)} 字节")
            
            # 检查是否是嵌套 DAT
            if resource_data[:6] == b'LLLLLL':
                print("  ** 嵌套 DAT 格式 **")
                extract_nested_dat(resource_data, palette_rgb, scene_dir)
            else:
                print("  -> 不是嵌套 DAT 格式，可能是其他数据")
    
    print(f"\n{'='*60}")
    print(f"所有资源已导出到: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles"
    
    extract_fdother7_tiles(data_dir, output_dir)
