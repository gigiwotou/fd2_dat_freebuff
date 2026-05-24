"""正确分析FDOTHER.DAT索引82-90的数据"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]  # 422
        
        offsets = []
        for i in range(count):
            offset = struct.unpack("<I", f.read(4))[0]
            offsets.append(offset)
        
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

def load_fdother_index(data_dir, index):
    """加载FDOTHER指定索引"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
        count = struct.unpack("<I", f.read(4))[0]
        
        offsets = []
        for i in range(count):
            offset = struct.unpack("<I", f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < count else None
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            data = f.read(file_size - start)
    
    return data

def analyze_index(data, index, palette_rgb, output_dir):
    """分析一个索引的数据"""
    print(f"\n{'='*60}")
    print(f"分析索引 {index}")
    print(f"{'='*60}")
    print(f"  数据大小: {len(data)} 字节")
    
    if len(data) < 4:
        print(f"  数据太小")
        return
    
    # 显示前32字节的十六进制
    print(f"  前32字节:")
    for i in range(0, min(32, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"    {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # 检查Magic
    magic = data[0:4]
    
    if magic == b'LMI1':
        print(f"  格式: LMI1 (Tile集)")
        if len(data) >= 6:
            tile_count = struct.unpack("<H", data[4:6])[0]
            print(f"  Tile数量: {tile_count}")
    elif magic == b'LLLL':
        print(f"  格式: LLLL (可能是嵌套资源)")
        if len(data) >= 8:
            sub_count = struct.unpack("<I", data[4:8])[0]
            print(f"  子资源数量: {sub_count}")
            
            if sub_count < 1000 and sub_count > 0:  # 合理的数量
                # 解析子资源
                offset_table_start = 8
                if offset_table_start + sub_count * 4 <= len(data):
                    print(f"  前10个子资源偏移:")
                    for i in range(min(sub_count, 10)):
                        offset = struct.unpack("<I", data[offset_table_start + i * 4:offset_table_start + i * 4 + 4])[0]
                        next_offset = struct.unpack("<I", data[offset_table_start + (i+1) * 4:offset_table_start + (i+1) * 4 + 4])[0] if i + 1 < sub_count else len(data)
                        size = next_offset - offset
                        print(f"    [{i}] 偏移0x{offset:X}, 大小{size}字节")
                        
                        # 尝试解析第一个子资源
                        if i == 0 and offset + 4 <= len(data):
                            sub_data = data[offset:next_offset]
                            if len(sub_data) >= 4:
                                w = struct.unpack("<H", sub_data[0:2])[0]
                                h = struct.unpack("<H", sub_data[2:4])[0]
                                
                                if 0 < w <= 320 and 0 < h <= 200 and w * h <= len(sub_data) - 4:
                                    print(f"      尺寸: {w}x{h}")
                                    pixel_data = sub_data[4:4 + w * h]
                                    
                                    # 导出图像
                                    img = Image.new("RGB", (w, h))
                                    pixels = img.load()
                                    for y in range(h):
                                        for x in range(w):
                                            idx = y * w + x
                                            if idx < len(pixel_data):
                                                pal_idx = pixel_data[idx]
                                                pixels[x, y] = palette_rgb[pal_idx]
                                    
                                    img_path = os.path.join(output_dir, f"index{index}_sub0_{w}x{h}.png")
                                    img.save(img_path)
                                    print(f"      已导出: {img_path}")
                                else:
                                    print(f"      尺寸异常: {w}x{h}")
            else:
                print(f"  子资源数量 {sub_count} 不合理，可能不是LLLL格式")
    else:
        print(f"  Magic: {magic.hex()} (未知格式)")
        
        # 尝试解析为tile数据（直接是w,h,pixels）
        if len(data) >= 4:
            w = struct.unpack("<H", data[0:2])[0]
            h = struct.unpack("<H", data[2:4])[0]
            
            if 0 < w <= 320 and 0 < h <= 200:
                pixel_size = w * h
                if len(data) >= 4 + pixel_size:
                    print(f"  可能是直接tile数据: {w}x{h}")
                    pixel_data = data[4:4 + pixel_size]
                    
                    non_zero = sum(1 for p in pixel_data if p != 0)
                    non_zero_pct = non_zero / len(pixel_data) * 100 if len(pixel_data) > 0 else 0
                    print(f"  非零像素: {non_zero}/{pixel_size} ({non_zero_pct:.1f}%)")
                    
                    # 导出图像
                    img = Image.new("RGB", (w, h))
                    pixels = img.load()
                    for y in range(h):
                        for x in range(w):
                            idx = y * w + x
                            if idx < len(pixel_data):
                                pal_idx = pixel_data[idx]
                                pixels[x, y] = palette_rgb[pal_idx]
                    
                    img_path = os.path.join(output_dir, f"index{index}_{w}x{h}.png")
                    img.save(img_path)
                    print(f"  已导出: {img_path}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "window_tiles_correct")
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析索引82-90
    for idx in range(82, 91):
        try:
            data = load_fdother_index(data_dir, idx)
            analyze_index(data, idx, palette_rgb, output_dir)
        except Exception as e:
            print(f"索引 {idx}: 加载失败 - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
