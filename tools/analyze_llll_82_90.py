"""分析FDOTHER.DAT索引82-90的LLLL格式数据结构"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(10)  # LLLLLL + count
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

def load_fdother_index(data_dir, index):
    """加载FDOTHER指定索引"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(10)  # LLLLLL + count
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
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

def analyze_llll_index(data, index, palette_rgb, output_dir):
    """分析LLLL格式的资源"""
    print(f"\n{'='*60}")
    print(f"分析索引 {index}")
    print(f"{'='*60}")
    
    if len(data) < 10:
        print(f"  数据太小: {len(data)} 字节")
        return
    
    # 解析LLLL格式
    magic = data[0:4]
    count = struct.unpack("<I", data[4:8])[0]
    
    print(f"  Magic: LLLL")
    print(f"  子资源数量: {count}")
    print(f"  数据大小: {len(data)} 字节")
    
    # 偏移表从偏移8开始
    offset_table_start = 8
    if offset_table_start + count * 4 > len(data):
        print(f"  偏移表超出范围")
        return
    
    offsets = []
    for i in range(count):
        offset = struct.unpack("<I", data[offset_table_start + i * 4:offset_table_start + i * 4 + 4])[0]
        offsets.append(offset)
    
    print(f"  偏移表:")
    for i, offset in enumerate(offsets[:20]):  # 只显示前20个
        print(f"    [{i}] 0x{offset:X}")
    
    # 尝试解析第一个子资源
    if offsets:
        first_offset = offsets[0]
        second_offset = offsets[1] if len(offsets) > 1 else len(data)
        
        if first_offset < len(data):
            sub_data = data[first_offset:second_offset]
            print(f"\n  第一个子资源: 偏移0x{first_offset:X}, 大小{len(sub_data)}字节")
            
            # 检查是否是tile数据
            if len(sub_data) >= 4:
                w = struct.unpack("<H", sub_data[0:2])[0]
                h = struct.unpack("<H", sub_data[2:4])[0]
                
                if 0 < w <= 320 and 0 < h <= 200:
                    pixel_size = w * h
                    if len(sub_data) >= 4 + pixel_size:
                        pixel_data = sub_data[4:4 + pixel_size]
                        
                        # 计算非零像素比例
                        non_zero = sum(1 for p in pixel_data if p != 0)
                        non_zero_pct = non_zero / len(pixel_data) * 100 if len(pixel_data) > 0 else 0
                        
                        print(f"    尺寸: {w}x{h}")
                        print(f"    非零像素: {non_zero}/{pixel_size} ({non_zero_pct:.1f}%)")
                        
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
                        print(f"    已导出图像: {img_path}")
                    else:
                        print(f"    像素数据不足: 需要{4 + pixel_size}字节，实际{len(sub_data)}字节")
                else:
                    print(f"    尺寸异常: {w}x{h}")
                    
                    # 显示前16字节的十六进制
                    hex_str = ' '.join(f'{b:02x}' for b in sub_data[:16])
                    print(f"    前16字节: {hex_str}")
            else:
                hex_str = ' '.join(f'{b:02x}' for b in sub_data[:min(32, len(sub_data))])
                print(f"    数据: {hex_str}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "window_tiles_82_90")
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析索引82-90
    for idx in range(82, 91):
        try:
            data = load_fdother_index(data_dir, idx)
            analyze_llll_index(data, idx, palette_rgb, output_dir)
        except Exception as e:
            print(f"索引 {idx}: 加载失败 - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
