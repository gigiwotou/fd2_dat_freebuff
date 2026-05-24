"""
提取 _FDOTHER.DAT__7 (0x53a81) 使用的所有 tile 图片

根据反汇编分析，该变量通过动态索引加载资源，然后通过 tile 索引访问：
tile_data = 资源基址 + *(DWORD*)(资源基址 + 4*tile索引 + 6)

资源格式:
- 0-5: "LLLLLL" magic
- 6-9: 资源数量
- 10+: 偏移表 (每个偏移 4 字节)
- 偏移表结束后: 实际的 RLE 压缩数据
"""
import struct
import os
from PIL import Image


def load_palette(fdother_path):
    """加载 FDOTHER.DAT 索引 75 的调色板"""
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    palette_rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        palette_rgb.append((r, g, b))
    
    return palette_rgb


def load_fdother_resource(fdother_path, index):
    """加载 FDOTHER.DAT 指定索引的原始数据"""
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        data = f.read(end - start) if end else f.read()
    return data


def decompress_rle(data, width, height, stride=320):
    """
    实现 sub_4E98D 的 RLE 解压缩逻辑
    输入: 纯 RLE 数据 (无宽高头)
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
                if value & 0x40:
                    # 跳过像素
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
                    # 复制像素数据
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
                # 填充相同像素
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
        
        dst_pos = row_start + stride
    
    return bytes(output)


def create_image_from_pixels(pixel_data, width, height, palette_rgb):
    """从像素数据创建 PIL 图像"""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(pixel_data):
                pal_idx = pixel_data[idx]
                if pal_idx < len(palette_rgb):
                    pixels[x, y] = palette_rgb[pal_idx]
    
    return img


def extract_tile_atlas(nested_data, palette_rgb, output_dir, prefix=""):
    """
    提取 tile 图集
    格式:
    - 0-5: "LLLLLL" magic
    - 6-9: 偏移数量
    - 10+: 偏移表 (每个 4 字节)
    - 偏移表结束后: RLE 压缩的 tile 数据 (无宽高头，每个 tile 是 32x32 或类似尺寸)
    """
    if len(nested_data) < 10 or nested_data[:6] != b'LLLLLL':
        print("  不是有效的嵌套 DAT 格式")
        return
    
    # 读取偏移数量
    offset_count = struct.unpack("<I", nested_data[6:10])[0]
    print(f"  偏移数量: {offset_count}")
    
    # 读取偏移表
    offset_table_start = 10
    valid_offsets = []
    
    for i in range(offset_count):
        offset_addr = offset_table_start + i * 4
        if offset_addr + 4 > len(nested_data):
            break
        
        offset_val = struct.unpack("<I", nested_data[offset_addr:offset_addr + 4])[0]
        
        # 只接受有效的偏移 (在文件范围内，且大于偏移表结束位置)
        offset_table_end = offset_table_start + offset_count * 4
        if offset_val < len(nested_data) and offset_val >= offset_table_end:
            valid_offsets.append((i, offset_val))
        else:
            # 如果偏移无效，说明偏移表结束了
            if valid_offsets:
                print(f"  偏移表在 {len(valid_offsets)} 个有效偏移后结束")
            break
    
    print(f"  有效偏移: {len(valid_offsets)} 个")
    
    # 计算 tile 尺寸 (假设所有 tile 尺寸相同)
    # 根据游戏 320x200 分辨率，tile 可能是 32x32 或 16x16 等
    # 我们先计算总数据大小，然后除以 tile 数量
    if len(valid_offsets) >= 2:
        # 使用第一个和第二个偏移计算 tile 数据大小
        first_tile_size = valid_offsets[1][1] - valid_offsets[0][1]
        # 假设这是单个 tile 的 RLE 压缩数据大小
        print(f"  第一个 tile 数据大小: {first_tile_size} 字节")
    
    # 直接导出整个 RLE 数据作为一个大图像
    # 找到偏移表结束位置
    offset_table_end = offset_table_start + len(valid_offsets) * 4
    
    # 从偏移表结束后开始提取
    tile_start = valid_offsets[0][1] if valid_offsets else offset_table_end
    
    # 提取 tile 数据
    for idx, (tile_idx, tile_offset) in enumerate(valid_offsets):
        # 获取 tile 数据范围
        tile_end = valid_offsets[idx + 1][1] if idx + 1 < len(valid_offsets) else len(nested_data)
        tile_rle_data = nested_data[tile_offset:tile_end]
        
        print(f"\n  Tile {tile_idx}: 偏移 {tile_offset}-{tile_end}, RLE 数据大小 {len(tile_rle_data)} 字节")
        print(f"    前 16 字节: {tile_rle_data[:16].hex()}")
        
        # 尝试不同的 tile 尺寸
        for tile_w, tile_h in [(32, 32), (16, 16), (64, 64), (48, 48), (80, 80), (160, 200), (320, 200)]:
            expected_size = tile_w * tile_h
            # RLE 压缩后的数据通常小于原始大小
            if len(tile_rle_data) < expected_size * 2:  # RLE 数据通常不超过原始大小的 2 倍
                # 尝试解压缩
                try:
                    pixel_data = decompress_rle(tile_rle_data, tile_w, tile_h)
                    
                    # 检查是否有非零像素
                    non_zero = sum(1 for p in pixel_data if p != 0)
                    if non_zero > 0 and non_zero > len(pixel_data) * 0.01:  # 至少 1% 非零像素
                        # 创建图像
                        img = create_image_from_pixels(pixel_data, tile_w, tile_h, palette_rgb)
                        
                        # 保存
                        img_path = os.path.join(output_dir, f"{prefix}tile_{tile_idx:03d}_{tile_w}x{tile_h}.png")
                        img.save(img_path)
                        print(f"    -> 成功: {tile_w}x{tile_h}, 非零像素: {non_zero}/{len(pixel_data)} -> {img_path}")
                        
                        # 放大保存
                        if min(tile_w, tile_h) < 20:
                            zoom_factor = max(4, 20 // min(tile_w, tile_h))
                            zoomed = img.resize((tile_w * zoom_factor, tile_h * zoom_factor), Image.NEAREST)
                            zoomed_path = os.path.join(output_dir, f"{prefix}tile_{tile_idx:03d}_{tile_w}x{tile_h}_zoom{zoom_factor}x.png")
                            zoomed.save(zoomed_path)
                except:
                    pass


def extract_fdother7_tiles(data_dir, output_dir):
    """提取 _FDOTHER.DAT__7 使用的所有 tile 图片"""
    fdother_path = os.path.join(data_dir, "FDOTHER.DAT")
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT 文件: {fdother_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("加载调色板...")
    palette_rgb = load_palette(fdother_path)
    print(f"调色板加载成功 ({len(palette_rgb)} 颜色)")
    
    # 动态索引列表
    dynamic_indices = {
        "scene_0_index": ord('R'),  # 82
        "scene_32_index": ord('?'),  # 63
    }
    
    print("\n提取 _FDOTHER.DAT__7 使用的资源...")
    for scene_name, index in dynamic_indices.items():
        print(f"\n处理 {scene_name} (索引 {index})...")
        
        scene_dir = os.path.join(output_dir, scene_name)
        os.makedirs(scene_dir, exist_ok=True)
        
        try:
            resource_data = load_fdother_resource(fdother_path, index)
            print(f"  资源大小: {len(resource_data)} 字节")
        except Exception as e:
            print(f"  错误: 无法加载索引 {index}: {e}")
            continue
        
        if resource_data[:6] == b'LLLLLL':
            print("  ** 嵌套 DAT 格式 **")
            extract_tile_atlas(resource_data, palette_rgb, scene_dir)
    
    print(f"\n所有资源已导出到: {output_dir}")


if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles"
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    extract_fdother7_tiles(data_dir, output_dir)
    
    print("\n=== 完成 ===")
