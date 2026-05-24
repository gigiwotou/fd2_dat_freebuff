"""分析FDOTHER.DAT索引82-90的LLLLLL格式数据结构"""
import struct
import os
from PIL import Image

def load_palette(data_dir):
    """加载索引75调色板"""
    path = os.path.join(data_dir, "FDOTHER.DAT")
    with open(path, "rb") as f:
        f.read(6)  # LLLLLL
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
        f.read(6)  # LLLLLL
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

def analyze_llllll_index(data, index, palette_rgb, output_dir):
    """分析LLLLLL格式的资源（6个L的格式）"""
    print(f"\n{'='*60}")
    print(f"分析索引 {index}")
    print(f"{'='*60}")
    
    if len(data) < 10:
        print(f"  数据太小: {len(data)} 字节")
        return
    
    # 解析LLLLLL格式
    magic = data[0:6]
    
    # 尝试不同的偏移量解析
    # 方式1: 偏移6-7是WORD count
    count_word = struct.unpack("<H", data[6:8])[0]
    
    # 方式2: 偏移6-9是DWORD count  
    count_dword = struct.unpack("<I", data[6:10])[0]
    
    print(f"  Magic: {magic}")
    print(f"  数据大小: {len(data)} 字节")
    print(f"  偏移6-7 (WORD): {count_word}")
    print(f"  偏移6-9 (DWORD): {count_dword}")
    
    # 判断哪个是合理的count
    if count_word < 100 and count_word > 0:
        print(f"  => 使用WORD count: {count_word}")
        count = count_word
        offset_table_start = 8
    elif count_dword < 1000 and count_dword > 0:
        print(f"  => 使用DWORD count: {count_dword}")
        count = count_dword
        offset_table_start = 10
    else:
        print(f"  => count不合理，尝试直接解析为tile数据")
        count = None
        offset_table_start = None
    
    if count is not None and offset_table_start is not None:
        # 解析偏移表
        if offset_table_start + count * 4 > len(data):
            print(f"  偏移表超出范围: 需要{offset_table_start + count * 4}字节，实际{len(data)}字节")
            return
        
        offsets = []
        for i in range(count):
            offset = struct.unpack("<I", data[offset_table_start + i * 4:offset_table_start + i * 4 + 4])[0]
            offsets.append(offset)
        
        print(f"  前{min(count, 10)}个偏移:")
        for i in range(min(count, 10)):
            offset = offsets[i]
            next_offset = offsets[i + 1] if i + 1 < count else len(data)
            size = next_offset - offset
            
            print(f"    [{i}] 偏移0x{offset:X}, 大小{size}字节")
            
            # 尝试解析为tile数据
            if offset + 4 <= len(data) and size > 4:
                sub_data = data[offset:next_offset]
                w = struct.unpack("<H", sub_data[0:2])[0]
                h = struct.unpack("<H", sub_data[2:4])[0]
                
                if 0 < w <= 320 and 0 < h <= 200:
                    pixel_size = w * h
                    if len(sub_data) >= 4 + pixel_size:
                        pixel_data = sub_data[4:4 + pixel_size]
                        
                        non_zero = sum(1 for p in pixel_data if p != 0)
                        non_zero_pct = non_zero / len(pixel_data) * 100 if len(pixel_data) > 0 else 0
                        
                        print(f"        尺寸: {w}x{h}, 非零像素: {non_zero}/{pixel_size} ({non_zero_pct:.1f}%)")
                        
                        # 只导出前几个tile
                        if i < 5:
                            img = Image.new("RGB", (w, h))
                            pixels = img.load()
                            for y in range(h):
                                for x in range(w):
                                    idx = y * w + x
                                    if idx < len(pixel_data):
                                        pal_idx = pixel_data[idx]
                                        pixels[x, y] = palette_rgb[pal_idx]
                            
                            img_path = os.path.join(output_dir, f"index{index}_sub{i}_{w}x{h}.png")
                            img.save(img_path)
                    else:
                        print(f"        尺寸: {w}x{h}, 像素数据不足")
                else:
                    print(f"        尺寸异常: {w}x{h}")

if __name__ == "__main__":
    data_dir = r"D:\workspace\fd2_dat_freebuff\bin"
    
    print(f"数据目录: {data_dir}")
    
    # 加载调色板
    print("\n加载调色板...")
    palette_rgb = load_palette(data_dir)
    print("调色板加载成功")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "window_tiles_llllll")
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析索引82-90
    for idx in range(82, 91):
        try:
            data = load_fdother_index(data_dir, idx)
            analyze_llllll_index(data, idx, palette_rgb, output_dir)
        except Exception as e:
            print(f"索引 {idx}: 加载失败 - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 完成 ===")
    print(f"图像已保存到: {output_dir}")
