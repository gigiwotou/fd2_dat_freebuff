#!/usr/bin/env python3
"""分析索引1的图标数据格式"""

import struct
import sys

def main():
    filepath = "game/FDOTHER.DAT"
    
    with open(filepath, "rb") as f:
        # Read header
        magic = f.read(6)
        print(f"Magic: {magic}")
        
        resource_count = struct.unpack("<I", f.read(4))[0]
        print(f"Resource count: {resource_count}")
        
        # Read offset table
        f.seek(10)
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack("<I", f.read(4))[0]
            offsets.append(offset)
        
        # Get resource 1
        start = offsets[1]
        end = offsets[2] if 2 < resource_count else -1
        
        if end == -1:
            f.seek(0, 2)
            end = f.tell()
        
        size = end - start
        print(f"\nResource 1: offset={start:#x}, size={size}")
        
        f.seek(start)
        data = f.read(size)
        
        # 分析前100字节
        print(f"\n前100字节 (hex):")
        for i in range(0, min(100, len(data)), 16):
            hex_str = " ".join(f"{b:02x}" for b in data[i:i+16])
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
            print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
        
        # 尝试解析为相对偏移表
        if size >= 4:
            first_value = struct.unpack("<I", data[0:4])[0]
            print(f"\n第一个DWORD值: {first_value:#x} ({first_value})")
            
            # 如果是相对偏移表，第一个值应该是偏移数量
            offset_count = first_value
            print(f"假设第一个值是偏移数量: {offset_count}")
            
            if offset_count > 0 and offset_count < 1000:
                # 读取偏移表
                print(f"\n偏移表 ({offset_count}个偏移):")
                for i in range(offset_count):
                    offset_pos = 4 + i * 4
                    if offset_pos + 4 <= size:
                        offset = struct.unpack("<I", data[offset_pos:offset_pos+4])[0]
                        print(f"  偏移[{i}] = {offset:#x} ({offset}) - 实际位置: {start + offset:#x}")
                        
                        # 读取该位置的数据
                        if offset < size:
                            tile_data = data[offset:offset+20]
                            hex_str = " ".join(f"{b:02x}" for b in tile_data)
                            print(f"    数据: {hex_str}")
                            
                            # 尝试解析宽高
                            if len(tile_data) >= 4:
                                w = tile_data[0] | (tile_data[1] << 8)
                                h = tile_data[2] | (tile_data[3] << 8)
                                print(f"    可能的宽高: {w}x{h}")

if __name__ == "__main__":
    main()
