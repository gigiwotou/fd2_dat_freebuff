#!/usr/bin/env python3
"""分析索引1：偏移是相对于资源的偏移"""
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
    res_start_file = offsets[1]  # 文件偏移
    res_end_file = offsets[2]
    res_data = data[res_start_file:res_end_file]
    res_size = len(res_data)
    
    print("=== 索引1 分析 ===")
    print(f"文件偏移: 0x{res_start_file:X}")
    print(f"资源大小: {res_size} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"头: {w}x{h}, pal_window={pal_win}")
    
    # 偏移6开始是相对偏移表
    print(f"\n偏移6开始的相对偏移:")
    for i in range(21):
        pos = 6 + i * 4
        if pos + 4 > res_size:
            break
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        file_off = res_start_file + rel_off
        
        print(f"\n图标{i}: 相对偏移0x{rel_off:X} (文件0x{file_off:X})")
        
        # 读取该位置的数据
        if file_off < len(data):
            chunk = data[file_off:file_off+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"  数据: {hex_str}")
            
            # 尝试作为宽高
            if len(chunk) >= 4:
                maybe_w = struct.unpack_from('<H', chunk, 0)[0]
                maybe_h = struct.unpack_from('<H', chunk, 2)[0]
                print(f"  作为宽高: {maybe_w}x{maybe_h}")
                
                if maybe_w == w and maybe_h == h:
                    print(f"  >>> 匹配 24x24!")
                elif maybe_w > 0 and maybe_w <= 320 and maybe_h > 0 and maybe_h <= 200:
                    print(f"  >>> 合理的宽高!")
        
        if i > 0:
            prev_rel = struct.unpack_from('<I', res_data, pos - 4)[0]
            size = rel_off - prev_rel
            print(f"  大小: {size} 字节")

if __name__ == '__main__':
    main()
