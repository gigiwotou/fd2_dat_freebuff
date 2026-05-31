#!/usr/bin/env python3
"""详细分析索引1图标0的解码过程"""
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
    
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    # 图标0
    start_off = 0x56
    end_off = 0x133
    icon_data = res_data[start_off:end_off]
    
    print("=== 图标0 原始数据分析 ===")
    print(f"大小: {len(icon_data)} 字节")
    print(f"\n原始字节 (前80字节):")
    for i in range(0, min(80, len(icon_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in icon_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in icon_data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} |{ascii_str}|")
    
    # 手动模拟sub_4EC66解码，打印详细步骤
    print(f"\n\n=== sub_4EC66解码步骤 (前30步) ===")
    src_pos = 0
    ah = 0
    prev_al = 0
    dst_pos = 0
    steps = 0
    
    while dst_pos < 30 and src_pos < len(icon_data):
        if ah > 0:
            ah -= 1
            pixel = prev_al
            print(f"  步骤{steps}: AH={ah+1}->0, 重复像素={pixel:02X}")
        else:
            if src_pos >= len(icon_data):
                break
            al = icon_data[src_pos]
            src_pos += 1
            
            if al > 0xC0:
                ah = al - 0xC1
                if src_pos < len(icon_data):
                    new_al = icon_data[src_pos]
                    src_pos += 1
                    prev_al = new_al
                    pixel = new_al
                    print(f"  步骤{steps}: 读取{al:02X} (>0xC0), AH={ah}, 读取像素{new_al:02X}")
                else:
                    print(f"  步骤{steps}: 读取{al:02X} (>0xC0), AH={ah}, 但数据不足")
            else:
                ah = 0
                prev_al = al
                pixel = al
                print(f"  步骤{steps}: 读取{al:02X} (<=0xC0), 像素={al:02X}")
        
        print(f"    -> 像素[{dst_pos}] = {pixel:02X}")
        dst_pos += 1
        steps += 1

if __name__ == '__main__':
    main()
