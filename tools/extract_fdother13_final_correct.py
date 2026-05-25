#!/usr/bin/env python3
"""
提取 _FDOTHER.DAT__13 (0x54153) 指向的资源

根据sub_2D80D反汇编:
- v36 = "?355[\\]^" (ASCII: 63, 51, 53, 53, 91, 92, 93, 94)
- _FDOTHER.DAT__13 加载索引 = v36[n28]

这些索引对应的资源是嵌套DAT格式，包含多个tile。
"""
import os
import struct
from PIL import Image

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
OUTPUT_DIR = os.path.join(WORKSPACE, "output", "fdother_dat_13_correct")
os.makedirs(OUTPUT_DIR, exist_ok=True)

dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"

with open(dat_path, 'rb') as f:
    data = f.read()

# 读取索引表
NUM_INDICES = 422
offsets = []
for i in range(NUM_INDICES):
    offset = struct.unpack_from('<I', data, 6 + i * 4)[0]
    offsets.append(offset)

# _FDOTHER.DAT__13 使用的索引
v36_indices = [63, 51, 53, 91, 92, 93, 94]

print(f"_FDOTHER.DAT__13 使用的索引: {v36_indices}")

# RLE解压缩（精确实现sub_4E98D）
def decompress_rle_exact(src_data, width, height):
    dst_size = width * height
    dst = bytearray(dst_size)
    
    src_pos = 0
    row = 0
    
    while row < height:
        count = width
        dst_pos = row * width
        
        while count > 0 and src_pos < len(src_data):
            value = src_data[src_pos]
            src_pos += 1
            
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            if bit7 == 1:
                if bit6 == 1:
                    count_val = (value & 0x3F) + 1
                    dst_pos += count_val
                    count -= count_val
                else:
                    count_val = (value & 0x3F) + 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size and src_pos < len(src_data):
                            dst[dst_pos] = src_data[src_pos]
                            src_pos += 1
                            dst_pos += 1
                            count -= 1
            else:
                if bit6 == 1:
                    count_val = (value & 0x3F) + 1
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count >= 2 and dst_pos + 1 < dst_size:
                            dst[dst_pos + 1] = fill_value
                            dst_pos += 2
                            count -= 2
                else:
                    count_val = (value & 0x3F) + 1
                    fill_value = src_data[src_pos]
                    src_pos += 1
                    for i in range(count_val):
                        if count > 0 and dst_pos < dst_size:
                            dst[dst_pos] = fill_value
                            dst_pos += 1
                            count -= 1
        
        row += 1
    
    return bytes(dst)

# 提取每个索引的资源
for idx in v36_indices:
    if idx >= len(offsets):
        print(f"\n索引 {idx} 超出范围")
        continue
    
    idx_start = offsets[idx]
    idx_end = offsets[idx + 1] if idx + 1 < len(offsets) else len(data)
    res_data = data[idx_start:idx_end]
    
    print(f"\n{'='*60}")
    print(f"索引 {idx}")
    print(f"{'='*60}")
    print(f"  大小: {len(res_data)} 字节")
    print(f"  前16字节: {' '.join(f'{b:02X}' for b in res_data[:16])}")
    
    # 检查是否是嵌套DAT格式
    if res_data[:6] == b'LLLLLL':
        print(f"  嵌套DAT格式")
        
        # 解析嵌套DAT
        nested_count = struct.unpack_from('<I', res_data, 6)[0]
        print(f"  嵌套资源数量: {nested_count}")
        
        # 嵌套DAT的索引表
        nested_offsets_start = 10
        nested_offsets = []
        for i in range(nested_count):
            addr = nested_offsets_start + i * 4
            if addr + 4 > len(res_data):
                break
            offset = struct.unpack_from('<I', res_data, addr)[0]
            if offset < len(res_data):
                nested_offsets.append(offset)
        
        print(f"  嵌套资源偏移数: {len(nested_offsets)}")
        
        # 提取嵌套资源
        output_subdir = os.path.join(OUTPUT_DIR, f"index{idx}_nested")
        os.makedirs(output_subdir, exist_ok=True)
        
        for tile_idx, tile_offset in enumerate(nested_offsets[:20]):
            if tile_idx + 1 < len(nested_offsets):
                tile_size = nested_offsets[tile_idx + 1] - tile_offset
            else:
                tile_size = len(res_data) - tile_offset
            
            tile_data = res_data[tile_offset:tile_offset + tile_size]
            
            if len(tile_data) < 9:
                continue
            
            tile_width = struct.unpack_from('<H', tile_data, 0)[0]
            tile_height = struct.unpack_from('<H', tile_data, 2)[0]
            
            if tile_width == 0 or tile_height == 0 or tile_width > 1024 or tile_height > 1024:
                continue
            
            rle_data = tile_data[9:]
            
            try:
                pixels = decompress_rle_exact(rle_data, tile_width, tile_height)
                
                # 检查像素值
                non_zero = sum(1 for p in pixels if p != 0)
                
                img = Image.new('P', (tile_width, tile_height))
                img.putdata(pixels)
                
                img_path = os.path.join(output_subdir, f"tile_{tile_idx:04d}_{tile_width}x{tile_height}_nz{non_zero}.png")
                img.save(img_path)
                
                print(f"    Tile {tile_idx}: {tile_width}x{tile_height}, 非零像素: {non_zero}/{len(pixels)} ({non_zero/len(pixels)*100:.1f}%)")
                
            except Exception as e:
                print(f"    Tile {tile_idx} 失败: {e}")
    else:
        print(f"  非嵌套DAT格式，跳过")

print(f"\n\n提取完成！输出目录: {OUTPUT_DIR}")
