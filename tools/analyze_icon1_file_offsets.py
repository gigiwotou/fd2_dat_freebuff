#!/usr/bin/env python3
"""分析索引1的偏移是文件偏移还是资源内偏移"""
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
    
    print(f"FDOTHER.DAT 文件大小: {len(data)} 字节")
    
    # 索引1
    res_start = offsets[1]  # 这是文件偏移
    res_end = offsets[2]    # 这是文件偏移
    res_data = data[res_start:res_end]
    
    print(f"\n=== 索引1 ===")
    print(f"文件偏移: 0x{res_start:X} - 0x{res_end:X}")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"外头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 偏移6开始的值
    print(f"\n偏移6开始的值 (可能是文件偏移):")
    for i in range(20):
        pos = 6 + i * 4
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from('<I', res_data, pos)[0]
        
        # 作为文件偏移
        if val < len(data):
            # 读取该位置的数据
            file_data = data[val:val+8]
            print(f"  项{i}: 0x{val:08X} ({val})")
            print(f"    文件位置数据: {' '.join(f'{b:02X}' for b in file_data)}")
            
            # 尝试作为宽高
            if len(file_data) >= 4:
                maybe_w = struct.unpack_from('<H', file_data, 0)[0]
                maybe_h = struct.unpack_from('<H', file_data, 2)[0]
                print(f"    作为宽高: {maybe_w}x{maybe_h}")
                
                # 检查是否是24x24
                if maybe_w == 24 and maybe_h == 24:
                    print(f"    >>> 匹配24x24!")
        else:
            print(f"  项{i}: 0x{val:08X} ({val}) - 超出文件范围")
    
    # 检查偏移56在文件中的位置
    val_56 = 0x56
    if val_56 < len(data):
        print(f"\n\n文件偏移 0x56 的数据:")
        for i in range(0, 200, 16):
            if val_56 + i + 16 > len(data):
                break
            chunk = data[val_56 + i:val_56 + i + 16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"  0x{val_56 + i:06X}: {hex_str}")

if __name__ == '__main__':
    main()
