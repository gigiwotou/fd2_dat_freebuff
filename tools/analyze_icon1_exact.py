#!/usr/bin/env python3
"""准确分析索引1的数据结构"""

import struct

def main():
    filepath = "game/FDOTHER.DAT"
    
    with open(filepath, "rb") as f:
        # Read header
        magic = f.read(6)
        resource_count = struct.unpack("<I", f.read(4))[0]
        
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
        f.seek(start)
        data = f.read(size)
        
        print(f"Resource 1: offset=0x{start:x}, size={size}")
        print(f"\n=== 前20字节 (hex) ===")
        for i in range(0, min(20, len(data)), 16):
            hex_str = " ".join(f"{b:02x}" for b in data[i:i+16])
            print(f"  0x{i:04x}: {hex_str}")
        
        # 尝试不同的解析方式
        print(f"\n=== 解析尝试 ===")
        
        # 方式1: 前4字节是宽高
        w1 = data[0] | (data[1] << 8)
        h1 = data[2] | (data[3] << 8)
        print(f"方式1 (前4字节是宽高): width={w1}, height={h1}")
        
        # 方式2: 第一个值是偏移表大小
        table_size = struct.unpack("<I", data[0:4])[0]
        print(f"方式2 (第一个值是偏移表大小): {table_size} 字节 = {table_size//4} 个偏移")
        
        if table_size > 0 and table_size < size:
            # 解析偏移表
            offset_count = table_size // 4
            print(f"\n=== 偏移表 ({offset_count}个偏移) ===")
            offsets_list = []
            for i in range(min(offset_count, 10)):
                offset = struct.unpack("<I", data[4 + i*4:4 + i*4 + 4])[0]
                offsets_list.append(offset)
                print(f"  偏移[{i}] = 0x{offset:04x} ({offset})")
                
                # 检查该偏移处的数据
                if offset < size and offset > 0:
                    tile_w = data[offset] | (data[offset+1] << 8)
                    tile_h = data[offset+2] | (data[offset+3] << 8)
                    print(f"    -> tile数据: {tile_w}x{tile_h}")
            
            # 计算相邻偏移的差值
            if len(offsets_list) >= 2:
                diff = offsets_list[1] - offsets_list[0]
                print(f"\n相邻偏移差值: {diff}")
                print(f"假设tile大小 = {diff}, 则像素数据大小 = {diff - 4}")
                print(f"像素数量 = {diff - 4}")
                
                # 如果tile是24x20，像素数量应该是480
                if diff - 4 == 480:
                    print("✓ 这与24x20的tile匹配！(24*20=480像素 + 4字节头 = 484字节)")

if __name__ == "__main__":
    main()
