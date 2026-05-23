"""
直接查看FDOTHER索引5的tile原始数据，不解压
检查tile数据是否已经是解压后的格式
"""

import struct
import sys

def main(fdother_path):
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        if len(offsets) <= 5:
            print("索引5不存在")
            return
        
        start = offsets[5]
        end = offsets[6] if len(offsets) > 6 else None
        
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(start)
            data = f.read(file_size - start)
        
        print(f"FDOTHER索引5: {len(data)} 字节")
        print(f"魔术字节: {data[0:4]}")
        print(f"Tile数量: {data[4] | (data[5] << 8)}")
        
        # 查看前17个tile的原始数据
        print("\n=== 前17个Tile原始数据 ===\n")
        
        for i in range(min(17, data[4] | (data[5] << 8))):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            
            tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            
            if tile_offset + 4 > len(data):
                print(f"Tile {i}: 偏移超出范围")
                continue
            
            w = data[tile_offset] | (data[tile_offset + 1] << 8)
            h = data[tile_offset + 2] | (data[tile_offset + 3] << 8)
            
            next_offset = struct.unpack('<I', data[offset_addr+4:offset_addr+8])[0] if i+1 < len(offsets) else len(data)
            tile_data_size = next_offset - tile_offset
            pixel_data_size = tile_data_size - 4
            
            print(f"Tile {i:2d}: offset=0x{tile_offset:03X}, {w:2d}x{h:2d}, "
                  f"总大小={tile_data_size:3d}, 像素数据={pixel_data_size:3d}, "
                  f"预期={w*h:4d}")
            
            # 显示像素数据的前16字节
            if pixel_data_size > 0:
                pixel_start = tile_offset + 4
                pixel_data = data[pixel_start:pixel_start+min(16, pixel_data_size)]
                hex_str = ' '.join(f'{b:02X}' for b in pixel_data)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in pixel_data)
                print(f"       像素数据: {hex_str}")
                print(f"               {ascii_str}")
                
                # 检查是否全为0
                if all(b == 0 for b in pixel_data):
                    print("       [警告] 前16字节全为0!")
                
                # 检查是否有明显的RLE模式 (交替出现 >= 0x80 的字节)
                high_bytes = sum(1 for b in pixel_data[:8] if b >= 0x80)
                if high_bytes >= 4:
                    print(f"       [提示] 高字节({b:02X})出现频繁，可能是RLE压缩")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    main(sys.argv[1])
