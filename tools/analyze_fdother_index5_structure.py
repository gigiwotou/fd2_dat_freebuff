"""
分析FDOTHER索引5的tile数据结构
确认是否为RLE压缩格式，以及tile的正确尺寸
"""

import struct
import sys

def analyze_fdother_index5(fdother_path):
    with open(fdother_path, 'rb') as f:
        # 读取DAT头部
        magic = f.read(6)
        print(f"Magic: {magic}")
        
        resource_count_data = f.read(4)
        if len(resource_count_data) < 4:
            print("Failed to read resource count")
            return
        
        resource_count = struct.unpack('<I', resource_count_data)[0]
        print(f"Resource count: {resource_count}")
        
        # 读取偏移表
        offsets = []
        for i in range(resource_count):
            offset_data = f.read(4)
            if len(offset_data) < 4:
                break
            offset = struct.unpack('<I', offset_data)[0]
            offsets.append(offset)
        
        if len(offsets) <= 5:
            print("Not enough resources")
            return
        
        # 获取索引5的数据范围
        start = offsets[5]
        end = offsets[6] if len(offsets) > 6 else None
        
        print(f"\nIndex 5: start=0x{start:X} ({start}), end={'0x%X' % end if end else 'EOF'}")
        
        if end:
            size = end - start
        else:
            # 获取文件大小
            f.seek(0, 2)
            file_size = f.tell()
            size = file_size - start
        
        print(f"Index 5 size: {size} bytes")
        
        # 读取索引5的数据
        f.seek(start)
        data = f.read(size)
        
        # 解析头部
        if len(data) < 6:
            print("Data too small")
            return
        
        total_w = struct.unpack('<H', data[0:2])[0]
        total_h = struct.unpack('<H', data[2:4])[0]
        tile_count = struct.unpack('<H', data[4:6])[0]
        
        print(f"\nTile set header:")
        print(f"  Total width: {total_w}")
        print(f"  Total height: {total_h}")
        print(f"  Tile count: {tile_count}")
        
        # 解析tile偏移表
        print(f"\nTile offsets:")
        tile_offsets = []
        for i in range(min(tile_count, 20)):  # 只显示前20个
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            
            tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            tile_offsets.append(tile_offset)
            
            # 读取tile头部
            if tile_offset + 4 <= len(data):
                w = struct.unpack('<H', data[tile_offset:tile_offset+2])[0]
                h = struct.unpack('<H', data[tile_offset+2:tile_offset+4])[0]
                
                # 计算下一个tile的偏移，得到当前tile的数据大小
                next_offset = tile_offsets[i+1] if i+1 < len(tile_offsets) else len(data)
                tile_data_size = next_offset - tile_offset
                
                print(f"  Tile {i:3d}: offset=0x{tile_offset:X} ({tile_offset:6d}), "
                      f"w={w:3d}, h={h:3d}, data_size={tile_data_size:6d}, "
                      f"expected_uncompressed={w*h+4}")
            else:
                print(f"  Tile {i:3d}: offset=0x{tile_offset:X} ({tile_offset:6d}), OUT OF RANGE")
        
        if tile_count > 20:
            print(f"  ... ({tile_count - 20} more tiles)")
        
        # 分析前几个tile的数据，判断是否RLE压缩
        print(f"\nAnalyzing tile data format:")
        for i in range(min(5, tile_count)):
            if i >= len(tile_offsets):
                break
            
            tile_offset = tile_offsets[i]
            if tile_offset + 4 > len(data):
                continue
            
            w = struct.unpack('<H', data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', data[tile_offset+2:tile_offset+4])[0]
            
            next_offset = tile_offsets[i+1] if i+1 < len(tile_offsets) else len(data)
            tile_data_size = next_offset - tile_offset
            pixel_data_size = tile_data_size - 4
            
            print(f"\n  Tile {i} (w={w}, h={h}):")
            print(f"    Raw data size: {tile_data_size}")
            print(f"    Pixel data size: {pixel_data_size}")
            print(f"    Expected uncompressed size: {w * h}")
            
            if w * h == pixel_data_size:
                print(f"    -> UNCOMPRESSED (pixel data matches w*h)")
            elif w * h < pixel_data_size:
                print(f"    -> LIKELY RLE COMPRESSED (pixel data > w*h)")
            else:
                print(f"    -> UNKNOWN (pixel data < w*h)")
            
            # 显示前16字节的像素数据
            pixel_start = tile_offset + 4
            pixel_end = min(pixel_start + 16, len(data))
            pixel_bytes = data[pixel_start:pixel_end]
            hex_str = ' '.join(f'{b:02X}' for b in pixel_bytes)
            print(f"    First 16 bytes: {hex_str}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <FDOTHER.DAT path>")
        sys.exit(1)
    
    analyze_fdother_index5(sys.argv[1])
