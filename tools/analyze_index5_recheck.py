#!/usr/bin/env python3
"""
重新分析FDOTHER.DAT索引5的数据结构
确认tile数据格式和压缩状态
"""

import struct
import os

def analyze_fdother_index5():
    fdother_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'FDOTHER.DAT')
    
    if not os.path.exists(fdother_path):
        print(f"错误: 找不到FDOTHER.DAT文件")
        return
    
    print(f"分析文件: {fdother_path}")
    print(f"文件大小: {os.path.getsize(fdother_path)} 字节")
    print()
    
    with open(fdother_path, 'rb') as f:
        # 读取文件头
        magic = f.read(6)
        print(f"文件魔术字节: {magic}")
        
        f.seek(6)
        resource_count_data = f.read(4)
        resource_count = struct.unpack('<I', resource_count_data)[0]
        print(f"资源数量: {resource_count}")
        
        if resource_count <= 5:
            print(f"错误: 资源数量{resource_count} <= 5，无法访问索引5")
            return
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset_data = f.read(4)
            offset = struct.unpack('<I', offset_data)[0]
            offsets.append(offset)
        
        # 计算索引5的大小
        start = offsets[5]
        if 5 + 1 < resource_count:
            end = offsets[5 + 1]
            size = end - start
        else:
            f.seek(0, 2)  # SEEK_END
            file_size = f.tell()
            end = file_size
            size = file_size - start
        
        print(f"\n索引5信息:")
        print(f"  起始偏移: 0x{start:X} ({start})")
        print(f"  结束偏移: 0x{end:X} ({end})")
        print(f"  数据大小: {size} 字节 ({size/1024:.1f} KB)")
        print()
        
        # 读取索引5的数据
        f.seek(start)
        index5_data = f.read(size)
        
        # 分析头部
        print(f"索引5头部分析:")
        print(f"  前4字节: {index5_data[0:4].hex()}")
        print(f"  前6字节: {index5_data[0:6].hex()}")
        print(f"  前8字节: {index5_data[0:8].hex()}")
        print()
        
        # 检查是否是LMI1格式
        if index5_data[0:4] == b'LMI1':
            print("  V 是LMI1格式")
            tile_count = struct.unpack('<H', index5_data[4:6])[0]
            print(f"  Tile数量: {tile_count}")
            
            # 读取tile偏移表
            print(f"\nTile偏移表 (前30个):")
            for i in range(min(30, tile_count)):
                offset_addr = 6 + i * 4
                if offset_addr + 4 <= size:
                    tile_offset = struct.unpack('<I', index5_data[offset_addr:offset_addr+4])[0]
                    
                    # 读取tile的宽高
                    tile_addr = tile_offset
                    if tile_addr + 4 <= size:
                        w = struct.unpack('<H', index5_data[tile_addr:tile_addr+2])[0]
                        h = struct.unpack('<H', index5_data[tile_addr+2:tile_addr+4])[0]
                        
                        # 计算数据大小
                        if i + 1 < tile_count:
                            next_tile_offset = struct.unpack('<I', index5_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                            data_size = next_tile_offset - tile_offset
                        else:
                            data_size = size - tile_offset
                        
                        pixel_data_size = data_size - 4  # 减去宽高4字节
                        expected_uncompressed = w * h
                        
                        is_compressed = pixel_data_size < expected_uncompressed
                        compression_ratio = expected_uncompressed / pixel_data_size if pixel_data_size > 0 else 0
                        
                        status = "[RLE]" if is_compressed else "[RAW]"
                        print(f"    Tile {i}: offset=0x{tile_offset:X} ({tile_offset}), {w}x{h}, "
                              f"data={data_size}B, pixel={pixel_data_size}B, expected={expected_uncompressed}B, "
                              f"ratio={compression_ratio:.1f}:1 {status}")
                    else:
                        print(f"    Tile {i}: offset=0x{tile_offset:X} ({tile_offset}) - 超出范围")
            
            # 打印tile 1-17的详细信息
            print(f"\n\n窗口边框Tile (1-17) 详细分析:")
            print(f"  Tile | 宽度 | 高度 | 数据大小 | 预期大小 | 压缩比 | 状态")
            print(f"  " + "-"*60)
            for i in range(1, 18):
                if i >= tile_count:
                    break
                offset_addr = 6 + i * 4
                tile_offset = struct.unpack('<I', index5_data[offset_addr:offset_addr+4])[0]
                
                tile_addr = tile_offset
                if tile_addr + 4 <= size:
                    w = struct.unpack('<H', index5_data[tile_addr:tile_addr+2])[0]
                    h = struct.unpack('<H', index5_data[tile_addr+2:tile_addr+4])[0]
                    
                    if i + 1 < tile_count:
                        next_tile_offset = struct.unpack('<I', index5_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                        data_size = next_tile_offset - tile_offset
                    else:
                        data_size = size - tile_offset
                    
                    pixel_data_size = data_size - 4
                    expected_uncompressed = w * h
                    is_compressed = pixel_data_size < expected_uncompressed
                    ratio = expected_uncompressed / pixel_data_size if pixel_data_size > 0 else 0
                    
                    status = "RLE压缩" if is_compressed else "未压缩"
                    print(f"  {i:5d} | {w:5d} | {h:5d} | {data_size:9d} | {expected_uncompressed:9d} | {ratio:6.1f}:1 | {status}")
        else:
            print("  X 不是LMI1格式")

if __name__ == '__main__':
    analyze_fdother_index5()
