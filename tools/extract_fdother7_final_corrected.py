"""
基于 IDA Pro 反汇编修正 FDOTHER_DAT__7 解压

关键发现:
1. 嵌套 DAT 的偏移表在偏移 10 开始，但只有前 3 个是有效偏移
2. 从偏移 114 开始到 6587 之间的 6473 字节是 **内联的 RLE 数据** (不是偏移表)
3. 字节值在 0x70-0x8C 范围，这是 RLE 控制字节 (0x80=复制1, 0x7D=填充29等)
4. 前 3 个偏移指向的是大的 tile 块 (每个约 6000-12000 字节)

根据 sub_4E98D 的调用方式:
- sub_4E98D(arg0, ...) 其中 arg0[0]=width, arg0[1]=height
- 所以 tile 数据格式是: [width:2][height:2][RLE_data]
- 但实际数据中前 4 字节不是有效的宽高 (32637x32384 不合理)

需要进一步分析:
1. 检查前 3 个偏移指向的数据是否真的是 tile 数据
2. 或者这些偏移指向的是其他格式的数据
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

def decompress_rle(data, width, height):
    """RLE 解压缩，stride = width"""
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
                    # 跳过
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
                    # 复制
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
                # 填充
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
        
        dst_pos = row_start + width
    
    return bytes(output)

def extract_scene_resources(data_dir, output_dir):
    """提取 scene_0 和 scene_32 的资源图片"""
    fdother_path = os.path.join(data_dir, "FDOTHER.DAT")
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到 FDOTHER.DAT: {fdother_path}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    palette = load_palette(fdother_path)
    
    # 动态索引: scene_0 使用索引 82, scene_32 使用索引 63
    indices = {
        "scene_0_index": 82,  # 'R'
        "scene_32_index": 63,  # '?'
    }
    
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        for scene_name, index in indices.items():
            print(f"\n处理 {scene_name} (索引 {index})...")
            
            scene_dir = os.path.join(output_dir, scene_name)
            os.makedirs(scene_dir, exist_ok=True)
            
            # 加载资源
            f.seek(offsets[index])
            end = offsets[index + 1] if index + 1 < count else None
            resource_data = f.read(end - offsets[index] if end else 0)
            
            print(f"  资源大小: {len(resource_data)} 字节")
            print(f"  Magic: {resource_data[:6]}")
            
            if resource_data[:6] != b'LLLLLL':
                print(f"  -> 不是嵌套 DAT 格式，跳过")
                continue
            
            # 解析嵌套 DAT
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
                
                # 只接受有效的偏移 (在文件范围内，且大于偏移表结束位置)
                if offset_val < len(resource_data) and offset_val >= offset_table_end:
                    valid_offsets.append(offset_val)
                else:
                    if valid_offsets:
                        print(f"  偏移表在 {len(valid_offsets)} 个有效偏移后结束")
                    break
            
            print(f"  有效偏移: {len(valid_offsets)} 个")
            
            if not valid_offsets:
                print(f"  -> 没有有效偏移，尝试提取内联数据")
                # 尝试提取偏移表后的内联 RLE 数据
                inline_start = offset_table_start + offset_count * 4
                if inline_start < len(resource_data):
                    inline_data = resource_data[inline_start:]
                    print(f"  内联数据大小: {len(inline_data)} 字节")
                    # 尝试不同的尺寸解压缩
                    for w, h in [(320, 200), (160, 100), (80, 80), (64, 64), (48, 48), (32, 32)]:
                        try:
                            pixel_data = decompress_rle(inline_data, w, h)
                            non_zero = sum(1 for p in pixel_data if p != 0)
                            if non_zero > 0 and non_zero < len(pixel_data) * 0.99:
                                img = Image.new("RGB", (w, h))
                                pixels = img.load()
                                for y in range(h):
                                    for x in range(w):
                                        idx = y * w + x
                                        if idx < len(pixel_data):
                                            pal_idx = pixel_data[idx]
                                            if pal_idx < len(palette):
                                                pixels[x, y] = palette[pal_idx]
                                
                                img_path = os.path.join(scene_dir, f"inline_{w}x{h}.png")
                                img.save(img_path)
                                print(f"    -> {w}x{h}: 非零像素 {non_zero}/{len(pixel_data)}")
                        except:
                            pass
                continue
            
            # 提取每个 tile
            for idx, tile_offset in enumerate(valid_offsets):
                tile_end = valid_offsets[idx + 1] if idx + 1 < len(valid_offsets) else len(resource_data)
                tile_data = resource_data[tile_offset:tile_end]
                
                print(f"\n  Tile {idx}: 偏移 {tile_offset}-{tile_end}, 大小 {len(tile_data)}")
                print(f"    前 16 字节: {tile_data[:16].hex()}")
                
                # 尝试直接解压缩 (假设没有宽高头)
                for w, h in [(320, 200), (160, 200), (160, 100), (80, 80), (64, 64), (48, 48), (32, 32)]:
                    try:
                        pixel_data = decompress_rle(tile_data, w, h)
                        
                        # 检查是否有非零像素
                        non_zero = sum(1 for p in pixel_data if p != 0)
                        ratio = non_zero / len(pixel_data) if len(pixel_data) > 0 else 0
                        
                        # 如果非零像素比例在 1%-90% 之间，可能是有效图像
                        if 0.01 < ratio < 0.90:
                            # 创建图像
                            img = Image.new("RGB", (w, h))
                            pixels = img.load()
                            
                            for y in range(h):
                                for x in range(w):
                                    idx_p = y * w + x
                                    if idx_p < len(pixel_data):
                                        pal_idx = pixel_data[idx_p]
                                        if pal_idx < len(palette):
                                            pixels[x, y] = palette[pal_idx]
                            
                            # 保存原始尺寸
                            img_path = os.path.join(scene_dir, f"tile_{idx:03d}_{w}x{h}.png")
                            img.save(img_path)
                            print(f"    -> {w}x{h}: 非零像素 {non_zero}/{len(pixel_data)} ({ratio*100:.1f}%)")
                            
                            # 如果尺寸小，放大保存
                            if min(w, h) < 100:
                                zoom = max(2, 100 // min(w, h))
                                zoomed = img.resize((w * zoom, h * zoom), Image.NEAREST)
                                zoomed_path = os.path.join(scene_dir, f"tile_{idx:03d}_{w}x{h}_zoom{zoom}x.png")
                                zoomed.save(zoomed_path)
                    except Exception as e:
                        pass
            
            print(f"\n  {scene_name} 处理完成")
    
    print(f"\n所有资源已导出到: {output_dir}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_extract"
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    extract_scene_resources(data_dir, output_dir)
    
    print("\n=== 完成 ===")
