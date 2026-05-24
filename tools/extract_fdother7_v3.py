"""
根据 IDA 反汇编修正 FDOTHER_DAT__7 解析

sub_25A96 关键代码:
  v8 = a5 + 4 * a6          (a5=FDOTHER_DAT__7基址, a6=tile_index)
  v13 = *(DWORD *)(v8 + 6) + a5    tile数据起始偏移
  v12 = *(DWORD *)(v8 + 10) - *(DWORD *)(v8 + 6)  tile数据大小

所以格式是:
  偏移 6+0: tile 0 起始偏移 (DWORD)
  偏移 6+4: tile 0 结束偏移 (DWORD)
  偏移 6+8: tile 1 起始偏移 (DWORD)
  偏移 6+12: tile 1 结束偏移 (DWORD)
  ...

tile 数据格式 (根据 sub_4E98D):
  [0:2] width (WORD)
  [2:4] height (WORD)  
  [4:] RLE 压缩像素数据
"""
import struct
import os
from PIL import Image

def load_palette(fdother_path):
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
                    skip_count = ((value & 0x3F) >> 2) + 1
                    dst_pos += skip_count
                    count -= skip_count
                else:
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

def extract_tiles_v3(fdother_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    palette = load_palette(fdother_path)
    
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        
        # 加载索引 82 (scene_0)
        f.seek(offsets[82])
        data_82 = f.read(offsets[83] - offsets[82])
        
        print(f"索引 82 大小: {len(data_82)}")
        print(f"前 16 字节: {data_82[:16].hex()}")
        
        # 根据 sub_25A96: 偏移 6 开始是 tile 偏移表 (每个 tile 2 个 DWORD)
        # 但首先检查偏移 6-9 是什么
        val_at_6 = struct.unpack("<I", data_82[6:10])[0]
        print(f"偏移 6-9 的值: {val_at_6} (0x{val_at_6:X})")
        
        # 如果这个值较小 (< 100)，可能是 tile 数量
        # 然后偏移表从 10 开始
        
        tile_count = val_at_6
        if tile_count > 100 or tile_count == 0:
            print(f"  -> 值不合理，尝试其他解释")
            return
        
        print(f"Tile 数量: {tile_count}")
        
        # 偏移表从 10 开始，每个 tile 有起始和结束偏移
        # 但之前我们发现只有 3 个有效偏移
        # 让我们尝试: 偏移表只存储起始偏移，结束偏移从下一个起始偏移推断
        
        offset_table_start = 10
        tile_offsets = []
        
        for i in range(tile_count):
            offset_addr = offset_table_start + i * 4
            if offset_addr + 4 > len(data_82):
                break
            
            offset_val = struct.unpack("<I", data_82[offset_addr:offset_addr+4])[0]
            
            # 检查偏移是否合理 (在文件范围内，且在偏移表之后)
            offset_table_end = offset_table_start + tile_count * 4
            if offset_val < len(data_82) and offset_val >= offset_table_end:
                tile_offsets.append(offset_val)
            else:
                print(f"Tile {i}: 偏移 {offset_val} 无效，停止")
                break
        
        print(f"找到 {len(tile_offsets)} 个有效 tile 偏移")
        print(f"偏移: {tile_offsets}")
        
        # 提取每个 tile
        for idx, tile_start in enumerate(tile_offsets):
            tile_end = tile_offsets[idx + 1] if idx + 1 < len(tile_offsets) else len(data_82)
            tile_data = data_82[tile_start:tile_end]
            
            print(f"\nTile {idx}: {tile_start}-{tile_end}, 大小={len(tile_data)}")
            print(f"  前 8 字节: {tile_data[:8].hex()}")
            
            if len(tile_data) < 4:
                print(f"  -> 数据太小")
                continue
            
            # 尝试读取宽高头
            width = struct.unpack("<H", tile_data[:2])[0]
            height = struct.unpack("<H", tile_data[2:4])[0]
            
            print(f"  假设宽高头: {width}x{height}")
            
            # 检查合理性
            if width > 0 and width <= 320 and height > 0 and height <= 200:
                rle_data = tile_data[4:]
                expected_pixels = width * height
                
                print(f"  RLE 数据大小: {len(rle_data)}, 预期像素: {expected_pixels}")
                
                # 解压缩
                try:
                    pixel_data = decompress_rle(rle_data, width, height)
                    
                    non_zero = sum(1 for p in pixel_data if p != 0)
                    ratio = non_zero / len(pixel_data) if len(pixel_data) > 0 else 0
                    
                    print(f"  非零像素: {non_zero}/{len(pixel_data)} ({ratio*100:.1f}%)")
                    
                    # 创建图像
                    img = Image.new("RGB", (width, height))
                    pixels = img.load()
                    for y in range(height):
                        for x in range(width):
                            idx_p = y * width + x
                            if idx_p < len(pixel_data):
                                pal_idx = pixel_data[idx_p]
                                if pal_idx < len(palette):
                                    pixels[x, y] = palette[pal_idx]
                    
                    # 保存
                    img_path = os.path.join(output_dir, f"tile_{idx:03d}_{width}x{height}.png")
                    img.save(img_path)
                    print(f"  -> 保存: {img_path}")
                    
                    if min(width, height) < 100:
                        zoom = max(2, 100 // min(width, height))
                        zoomed = img.resize((width * zoom, height * zoom), Image.NEAREST)
                        zoomed_path = os.path.join(output_dir, f"tile_{idx:03d}_{width}x{height}_zoom{zoom}x.png")
                        zoomed.save(zoomed_path)
                except Exception as e:
                    print(f"  -> 解压失败: {e}")
            else:
                print(f"  -> 宽高不合理")
                
                # 尝试不加宽高头，直接使用 RLE 数据
                # 但这需要知道正确的宽高
                print(f"  尝试推断宽高...")
                
                # 估算像素数
                src_pos = 0
                dst_count = 0
                while src_pos < len(tile_data):
                    value = tile_data[src_pos]
                    src_pos += 1
                    if value & 0x80:
                        count = ((value & 0x3F) >> 2) + 1
                        if value & 0x40:
                            dst_count += count
                        else:
                            dst_count += count
                            src_pos += count
                    else:
                        count = ((value & 0x3F) >> 2) + 1
                        if src_pos < len(tile_data):
                            src_pos += 1
                        dst_count += 1  # 填充值本身也算
                
                print(f"  估算像素数: {dst_count}")

if __name__ == "__main__":
    fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
    output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_v3"
    extract_tiles_v3(fdother_path, output_dir)
