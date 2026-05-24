#!/usr/bin/env python3
"""
测试RLE解压算法，验证fd2_decode_fdother_resource是否正确
"""

import struct
import os

def decompress_rle(src_data, width, height):
    """
    1:1实现fd2_decode_fdother_resource的RLE解压算法
    """
    # 跳过宽高头
    compressed = src_data[4:]
    comp_size = len(compressed)
    
    dst = [0] * (width * height)
    
    num4 = 0  # 源数据索引
    num3 = comp_size - 1
    num7 = 0  # 跳过计数
    num8 = 0  # 是否在处理中
    num9 = 0  # 复制计数
    b = 0     # 控制字节
    num10 = 0 # x坐标
    num11 = 0 # y坐标
    
    pixel_idx = 0
    expected = width * height
    
    while num4 <= num3 and pixel_idx < expected:
        flag = (num8 != 0)
        
        if not flag:
            num7 = 0
            num8 = 0
            num9 = 0
            
            if num4 < comp_size:
                b = compressed[num4]
                if b >= 192:
                    num7 = b - 192 + 1
                elif b >= 128:
                    num8 = b - 128 + 1
                elif b >= 64:
                    num9 = b - 64
                    num8 = 1
                else:
                    num8 = 1
                    num9 = b
            
            num10 += num7
            if num10 >= width:
                num10 = 0
                num11 += 1
        else:
            num12 = num9
            num13 = 0
            while num13 <= num12:
                if b >= 64 and b < 128:
                    num10 += 1
                
                if num4 < comp_size:
                    index = compressed[num4]
                    if num10 >= 0 and num10 < width and num11 >= 0 and num11 < height:
                        if pixel_idx < expected:
                            dst[pixel_idx] = index
                            pixel_idx += 1
                
                num10 += 1
                if num10 >= width:
                    num10 = 0
                    num11 += 1
                
                num13 += 1
            
            num8 -= 1
        
        num4 += 1
        
        if num11 >= height:
            break
    
    return bytes(dst)

def test_tile_decompression():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到FDOTHER.DAT文件")
        return
    
    print(f"分析文件: {fdother_path}")
    
    with open(fdother_path, 'rb') as f:
        # 读取文件头
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        # 读取索引5
        start = offsets[5]
        end = offsets[6] if 6 < resource_count else os.path.getsize(fdother_path)
        size = end - start
        
        f.seek(start)
        index5_data = f.read(size)
        
        tile_count = struct.unpack('<H', index5_data[4:6])[0]
        print(f"Tile数量: {tile_count}")
        
        # 测试解压tile 1-4（角tile）
        for i in [1, 2, 3, 4]:
            offset_addr = 6 + i * 4
            tile_offset = struct.unpack('<I', index5_data[offset_addr:offset_addr+4])[0]
            
            tile_addr = tile_offset
            w = struct.unpack('<H', index5_data[tile_addr:tile_addr+2])[0]
            h = struct.unpack('<H', index5_data[tile_addr+2:tile_addr+4])[0]
            
            if i + 1 < tile_count:
                next_tile_offset = struct.unpack('<I', index5_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                compressed_size = next_tile_offset - tile_offset
            else:
                compressed_size = size - tile_offset
            
            compressed_data = index5_data[tile_addr:tile_addr+compressed_size]
            
            print(f"\nTile {i}: {w}x{h}, 压缩大小={compressed_size}B")
            print(f"  压缩数据前20字节: {compressed_data[4:24].hex()}")
            
            # 解压
            try:
                decompressed = decompress_rle(compressed_data, w, h)
                
                # 统计非零像素
                non_zero = sum(1 for p in decompressed if p != 0)
                print(f"  解压成功! 非零像素={non_zero}/{w*h}")
                print(f"  解压数据前20字节: {decompressed[:20].hex()}")
                
                # 打印像素统计
                unique_values = set(decompressed)
                print(f"  唯一颜色值: {len(unique_values)}个")
                
            except Exception as e:
                print(f"  解压失败: {e}")

if __name__ == '__main__':
    test_tile_decompression()
