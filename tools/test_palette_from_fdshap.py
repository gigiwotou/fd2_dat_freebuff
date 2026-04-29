import struct
import numpy as np
from PIL import Image
import sys
import os

def parse_fdshap_offsets(file_data):
    """解析FDSHAP.DAT的资源偏移表"""
    magic = file_data[:6]
    if magic != b"LLLLLL":
        raise ValueError(f"Invalid FDSHAP magic: {magic}")
    
    resource_count = struct.unpack_from("<I", file_data, 6)[0]
    offsets = []
    for i in range(resource_count):
        offset = struct.unpack_from("<I", file_data, 10 + i * 4)[0]
        offsets.append(offset)
    
    return offsets

def decompress_rle(data, width, height):
    """RLE解压缩"""
    result = []
    pos = 0
    total_pixels = width * height
    
    while len(result) < total_pixels and pos < len(data):
        cmd = data[pos]
        pos += 1
        
        if cmd & 0x80:
            if cmd & 0x40:
                count = cmd & 0x3F
                if pos + count > len(data):
                    break
                result.extend(data[pos:pos+count])
                pos += count
            else:
                count = cmd & 0x3F
                if pos >= len(data):
                    break
                value = data[pos]
                pos += 1
                result.extend([value] * count)
        else:
            count = cmd
            if pos + count > len(data):
                break
            result.extend(data[pos:pos+count])
            pos += count
    
    return result[:total_pixels]

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_palette_from_fdshap.py <FDSHAP.DAT> <output.png>")
        return
    
    fdshap_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # 读取FDSHAP.DAT
    with open(fdshap_path, 'rb') as f:
        fdshap_data = f.read()
    
    # 解析偏移表
    offsets = parse_fdshap_offsets(fdshap_data)
    print(f"找到 {len(offsets)} 个资源")
    
    # 分析资源0（调色板）
    if len(offsets) > 1:
        res0_size = offsets[1] - offsets[0]
    else:
        res0_size = len(fdshap_data) - offsets[0]
    
    res0_data = fdshap_data[offsets[0]:offsets[0]+res0_size]
    print(f"\n资源0大小: {res0_size} 字节")
    
    # 检查是否是调色板（768字节 = 256色 * 3通道）
    if res0_size == 768 or res0_size >= 768:
        palette_data = res0_data[:768]
        print(f"前768字节作为调色板")
        
        # 分析调色板
        unique_colors = len(set(palette_data))
        print(f"唯一字节数: {unique_colors}")
        print(f"值范围: {min(palette_data)}-{max(palette_data)}")
        
        # 检查是否6-bit (0-63)
        if max(palette_data) <= 63:
            print("调色板是6-bit格式 (0-63)")
            # 转换为8-bit
            palette_8bit = [(b << 2) | (b >> 4) for b in palette_data]
            print(f"转换后值范围: {min(palette_8bit)}-{max(palette_8bit)}")
        else:
            print("调色板是8-bit格式 (0-255)")
            palette_8bit = list(palette_data)
        
        # 打印前10个颜色
        print("\n前10个颜色 (R,G,B):")
        for i in range(10):
            r = palette_8bit[i*3]
            g = palette_8bit[i*3+1]
            b = palette_8bit[i*3+2]
            print(f"  颜色{i}: ({r}, {g}, {b})")
        
        # 分析资源1（瓦片集）
        if len(offsets) > 1:
            res1_size = offsets[2] - offsets[1] if len(offsets) > 2 else len(fdshap_data) - offsets[1]
            res1_data = fdshap_data[offsets[1]:offsets[1]+res1_size]
            print(f"\n资源1大小: {res1_size} 字节")
            
            # 解析瓦片偏移表
            if res1_size >= 6:
                tile_count = struct.unpack_from("<I", res1_data, 6)[0]
                print(f"瓦片数量: {tile_count}")
                
                if tile_count > 0 and tile_count < 1000:
                    tile_offsets = []
                    for i in range(tile_count):
                        offset = struct.unpack_from("<I", res1_data, 10 + i * 4)[0]
                        tile_offsets.append(offset)
                    
                    print(f"解析到 {len(tile_offsets)} 个瓦片")
                    
                    # 显示第一个瓦片
                    if len(tile_offsets) >= 2:
                        tile0_size = tile_offsets[1] - tile_offsets[0]
                        print(f"瓦片0大小: {tile0_size} 字节")
                        
                        # 尝试解压缩
                        tile0_data = res1_data[tile_offsets[0]:tile_offsets[0]+tile0_size]
                        for size in [(16, 16), (32, 32), (64, 64)]:
                            w, h = size
                            if w * h == tile0_size or w * h < tile0_size:
                                pixels = decompress_rle(tile0_data, w, h)
                                if len(pixels) == w * h:
                                    print(f"成功解压缩为 {w}x{h}")
                                    
                                    # 创建图像
                                    img_array = np.array(pixels, dtype=np.uint8).reshape((h, w))
                                    img = Image.fromarray(img_array, mode='P')
                                    
                                    # 设置调色板
                                    palette_array = np.array(palette_8bit, dtype=np.uint8)
                                    # 扩展到256色
                                    if len(palette_array) < 768:
                                        palette_array = np.pad(palette_array, (0, 768 - len(palette_array)))
                                    img.putpalette(palette_array.tolist())
                                    
                                    img.save(output_path)
                                    print(f"已保存到 {output_path}")
                                    return
        
        # 如果瓦片解析失败，只保存调色板图像
        palette_img = Image.new('P', (16, 16))
        palette_8bit_array = np.array(palette_8bit, dtype=np.uint8)
        if len(palette_8bit_array) < 768:
            palette_8bit_array = np.pad(palette_8bit_array, (0, 768 - len(palette_8bit_array)))
        palette_img.putpalette(palette_8bit_array.tolist())
        palette_img.save(output_path)
        print(f"只保存调色板到 {output_path}")
    else:
        print(f"资源0不是调色板 (大小: {res0_size})")

if __name__ == "__main__":
    main()
