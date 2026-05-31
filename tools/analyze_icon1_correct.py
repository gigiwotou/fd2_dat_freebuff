#!/usr/bin/env python3
"""正确分析索引1的数据结构"""

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
        
        print(f"Resource 1 size: {size} bytes")
        print(f"\n尝试不同解析方式:\n")
        
        # 方式1: 第一个DWORD是偏移数量
        count_v1 = struct.unpack("<I", data[0:4])[0]
        print(f"方式1: 第一个DWORD = {count_v1}")
        if count_v1 < 1000:
            print(f"  如果是偏移数量，则占用 {count_v1 * 4} 字节")
        
        # 方式2: 第一个DWORD是总大小或其他
        print(f"\n方式2: 检查前20个DWORD值")
        for i in range(min(20, len(data)//4)):
            val = struct.unpack("<I", data[i*4:i*4+4])[0]
            print(f"  [{i}] @ {i*4:#06x}: {val:#010x} ({val})")
            
            # 如果值看起来像偏移（在资源范围内）
            if val < size and val > 0:
                tile_data = data[val:val+4]
                if len(tile_data) == 4:
                    w = tile_data[0] | (tile_data[1] << 8)
                    h = tile_data[2] | (tile_data[3] << 8)
                    if w > 0 and w < 100 and h > 0 and h < 100:
                        print(f"       -> 可能的宽高: {w}x{h}")
        
        # 方式3: 查找合理的偏移表大小
        print(f"\n方式3: 从偏移值推断结构")
        print(f"  数据大小: {size}")
        
        # 检查第一个合理的偏移值
        for i in range(1, len(data)//4):
            val = struct.unpack("<I", data[i*4:i*4+4])[0]
            # 如果值在合理范围内且是递增的
            if val > 0 and val < size and val > i*4:
                print(f"  第一个合理偏移 @ [{i}]: {val:#x}")
                # 检查这个位置的数据
                if val + 4 <= size:
                    w = data[val] | (data[val+1] << 8)
                    h = data[val+2] | (data[val+3] << 8)
                    print(f"    该位置数据: {w}x{h}")
                break

if __name__ == "__main__":
    main()
