#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引7的数据结构
确认大小、格式、tile数量和压缩状态
"""

import struct
import os

def analyze_fdother_index7():
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
        
        if resource_count <= 7:
            print(f"错误: 资源数量{resource_count} <= 7，无法访问索引7")
            return
        
        # 读取偏移表
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset_data = f.read(4)
            offset = struct.unpack('<I', offset_data)[0]
            offsets.append(offset)
        
        # 计算索引7的大小
        start = offsets[7]
        if 7 + 1 < resource_count:
            end = offsets[7 + 1]
            size = end - start
        else:
            f.seek(0, 2)  # SEEK_END
            file_size = f.tell()
            end = file_size
            size = file_size - start
        
        print(f"\n索引7信息:")
        print(f"  起始偏移: 0x{start:X} ({start})")
        print(f"  结束偏移: 0x{end:X} ({end})")
        print(f"  数据大小: {size} 字节")
        print()
        
        # 读取索引7的数据
        f.seek(start)
        index7_data = f.read(size)
        
        # 分析头部
        print(f"索引7头部分析:")
        print(f"  前4字节: {index7_data[0:4].hex()} = '{index7_data[0:4].decode('ascii', errors='replace')}'")
        print(f"  前6字节: {index7_data[0:6].hex()} = '{index7_data[0:6].decode('ascii', errors='replace')}'")
        print(f"  前8字节: {index7_data[0:8].hex()}")
        print()
        
        # 检查是否是LMI1格式
        if index7_data[0:4] == b'LMI1':
            print("  V 是LMI1格式")
            tile_count = struct.unpack('<H', index7_data[4:6])[0]
            print(f"  Tile数量: {tile_count}")
            
            # 读取tile偏移表
            print(f"\nTile偏移表 (前20个):")
            for i in range(min(20, tile_count)):
                offset_addr = 6 + i * 4
                if offset_addr + 4 <= size:
                    tile_offset = struct.unpack('<I', index7_data[offset_addr:offset_addr+4])[0]
                    
                    # 读取tile的宽高
                    tile_addr = tile_offset
                    if tile_addr + 4 <= size:
                        w = struct.unpack('<H', index7_data[tile_addr:tile_addr+2])[0]
                        h = struct.unpack('<H', index7_data[tile_addr+2:tile_addr+4])[0]
                        
                        # 计算数据大小
                        next_offset = offsets[7 + 1] - offsets[7] if 7 + 1 < resource_count else size
                        if i + 1 < tile_count:
                            next_tile_offset = struct.unpack('<I', index7_data[6 + (i+1)*4:6 + (i+1)*4+4])[0]
                            data_size = next_tile_offset - tile_offset
                        else:
                            data_size = size - tile_offset
                        
                        pixel_data_size = data_size - 4  # 减去宽高4字节
                        expected_uncompressed = w * h
                        
                        is_compressed = pixel_data_size < expected_uncompressed
                        
                        print(f"    Tile {i}: offset=0x{tile_offset:X} ({tile_offset}), {w}x{h}, "
                              f"数据大小={data_size}, 预期无压缩={expected_uncompressed}, "
                              f"{'RLE压缩' if is_compressed else '未压缩'}")
                    else:
                        print(f"    Tile {i}: offset=0x{tile_offset:X} ({tile_offset}) - 超出范围")
        else:
            print("  X 不是LMI1格式")
            
            # 尝试其他格式解析
            # 可能是简单的偏移表格式
            print(f"\n尝试解析为简单偏移表格式:")
            
            # 前几个字节可能是tile数量或其他信息
            possible_tile_count = struct.unpack('<H', index7_data[0:2])[0]
            print(f"  前2字节作为WORD: {possible_tile_count}")
            
            possible_tile_count2 = struct.unpack('<I', index7_data[0:4])[0]
            print(f"  前4字节作为DWORD: {possible_tile_count2}")
            
            # 打印前64字节的hex dump
            print(f"\n前64字节hex dump:")
            for i in range(0, min(64, size), 16):
                hex_str = ' '.join(f'{b:02x}' for b in index7_data[i:i+16])
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in index7_data[i:i+16])
                print(f"  0x{i:04X}: {hex_str:<48s} {ascii_str}")

if __name__ == '__main__':
    analyze_fdother_index7()
