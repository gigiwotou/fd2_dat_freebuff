#!/usr/bin/env python3
"""详细分析索引1的偏移值"""
import struct

def load_fdother(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    
    offsets.append(len(data))
    return data, offsets

def main():
    filepath = 'game/FDOTHER.DAT'
    data, offsets = load_fdother(filepath)
    
    # 索引1
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print("=== 索引1 偏移分析 ===")
    print(f"资源起始: 0x{res_start:X} ({res_start})")
    print(f"资源结束: 0x{res_end:X} ({res_end})")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"\n头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 偏移6开始的偏移表
    print(f"\n偏移6开始的值:")
    for i in range(25):
        pos = 6 + i * 4
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from('<I', res_data, pos)[0]
        
        # 检查作为文件偏移
        if val < len(data):
            file_offset_data = data[val:val+8]
            print(f"  项{i} @偏移{pos}: 0x{val:08X} ({val})")
            print(f"    作为文件偏移: {' '.join(f'{b:02X}' for b in file_offset_data)}")
            
            # 检查是否像宽高数据
            if len(file_offset_data) >= 4:
                maybe_w = struct.unpack_from('<H', file_offset_data, 0)[0]
                maybe_h = struct.unpack_from('<H', file_offset_data, 2)[0]
                print(f"    作为宽高: {maybe_w}x{maybe_h}")
                if maybe_w == w and maybe_h == h:
                    print(f"    >>> 匹配外部宽高!")
        else:
            print(f"  项{i} @偏移{pos}: 0x{val:08X} ({val}) - 超出文件范围")
    
    # 尝试另一种解释: 偏移6开始的2字节值
    print(f"\n\n尝试2字节偏移:")
    pos = 6
    for i in range(50):
        if pos + 2 > len(res_data):
            break
        val = struct.unpack_from('<H', res_data, pos)[0]
        print(f"  项{i} @偏移{pos}: 0x{val:04X} = {val}")
        pos += 2

if __name__ == '__main__':
    main()
