"""
根据汇编代码，嵌套DAT的正确结构是：
- LLLLLL magic (6字节)
- offset_count (4字节)
- offsets[offset_count] (每个tile的起始偏移)
- tile_metadata表 (从 offset_table_end 开始)
  每个条目 12 字节: [data_start_offset:4][data_end_offset:4][? :4]

sub_25A96 访问方式:
v8 = a5 + 4 * a6 + 6
v13 = *(DWORD *)(v8) + a5       # tile_data = 基址 + data_start_offset
v9 = *(DWORD *)(v8 + 4) - *(DWORD *)(v8)  # tile_size = data_end - data_start
"""
import struct
from PIL import Image

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v4\scene_0"

import os
os.makedirs(output_dir, exist_ok=True)

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

palette_rgb = load_palette(fdother_path)

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    # 分析索引 82 (scene_0)
    index = 82
    start = offsets[index]
    end = offsets[index + 1]
    f.seek(start)
    resource_data = f.read(end - start)
    
    print(f"资源大小: {len(resource_data)} 字节")
    
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    offset_table_end = 10 + offset_count * 4
    
    print(f"偏移数量: {offset_count}")
    print(f"偏移表结束: 字节 {offset_table_end}")
    
    # 解析偏移表后的tile元数据
    # 根据 sub_25A96: v8 = a5 + 4 * a6 + 6
    # 所以元数据从字节 6 + 4*offset_count 开始，每个条目 12 字节
    metadata_start = 6 + offset_count * 4
    print(f"\nTile 元数据表开始: 字节 {metadata_start}")
    
    # 读取元数据直到第一个tile数据开始
    first_tile_offset = struct.unpack("<I", resource_data[10:14])[0] if offset_count > 0 else len(resource_data)
    metadata_end = first_tile_offset
    metadata_data = resource_data[metadata_start:metadata_end]
    
    print(f"元数据表大小: {len(metadata_data)} 字节")
    print(f"第一个tile偏移: {first_tile_offset}")
    
    # 每个元数据条目 12 字节
    tile_count = len(metadata_data) // 12
    print(f"可能的tile数量: {tile_count}")
    
    print(f"\n元数据表内容:")
    for i in range(tile_count):
        entry_start = i * 12
        if entry_start + 12 > len(metadata_data):
            break
        
        data_start = struct.unpack("<I", metadata_data[entry_start:entry_start+4])[0]
        data_end = struct.unpack("<I", metadata_data[entry_start+4:entry_start+8])[0]
        unknown = struct.unpack("<I", metadata_data[entry_start+8:entry_start+12])[0]
        
        tile_size = data_end - data_start if data_end > data_start else 0
        
        print(f"  Tile {i}: start={data_start}, end={data_end}, size={tile_size}, unknown={unknown}")
        
        # 提取并解压缩tile数据
        if tile_size > 0 and data_start < len(resource_data) and data_end <= len(resource_data):
            tile_data = resource_data[data_start:data_end]
            print(f"    数据大小: {len(tile_data)}")
            print(f"    前 20 字节: {tile_data[:20].hex()}")
            
            # 尝试解析宽高头
            if len(tile_data) >= 4:
                w, h = struct.unpack("<HH", tile_data[:4])
                print(f"    前4字节宽高: {w} x {h}")
                
                if 0 < w <= 640 and 0 < h <= 480:
                    print(f"    [有效尺寸! 尝试解压缩]")
                    # 解压缩RLE
                    from PIL import Image
                    
                    # 这里需要正确的RLE解压缩逻辑
                    # 暂时先保存原始数据
                    output_path = os.path.join(output_dir, f"tile_{i}_{w}x{h}.raw")
                    with open(output_path, "wb") as out_f:
                        out_f.write(tile_data)
                    print(f"    已保存原始数据到 {output_path}")
