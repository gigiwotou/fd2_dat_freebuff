#!/usr/bin/env python3
"""详细检查索引1的字节"""
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
    
    print("索引1 原始字节:")
    for i in range(0, 90, 4):
        chunk = res_data[i:i+4]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        
        if len(chunk) == 4:
            val_le = struct.unpack_from('<I', chunk, 0)[0]
            val_be = struct.unpack_from('>I', chunk, 0)[0]
            print(f"  偏移{i}: [{hex_str}] 小端={val_le} (0x{val_le:X}) 大端={val_be} (0x{val_be:X})")
        else:
            print(f"  偏移{i}: [{hex_str}]")
    
    # 尝试不同的解释
    print(f"\n\n尝试解释为偏移表:")
    # 假设偏移5开始的4字节是第一个偏移
    # 00 56 00 00 可能是 0x00000056 如果按大端？
    # 或者是 56 00 = 86 作为2字节偏移？
    
    print(f"\n前200字节的4字节值 (从偏移5开始):")
    pos = 5
    for i in range(20):
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from('<I', res_data, pos)[0]
        # 计算相对于数据区开始的偏移
        rel_off = val - 5 if val > 5 else val
        print(f"  项{i} @偏移{pos}: 0x{val:08X} = {val}, 相对偏移={rel_off}")
        pos += 4
    
    # 如果偏移是相对于偏移5的位置
    print(f"\n\n尝试解释: 偏移值相对于偏移5")
    pos = 5
    for i in range(20):
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from('<I', res_data, pos)[0]
        # 如果偏移是相对于整个资源
        if val < len(res_data):
            print(f"  项{i}: 偏移{val} (0x{val:X}) 在范围内")
            # 检查这个位置的数据
            if val + 4 <= len(res_data):
                next_bytes = res_data[val:val+8]
                print(f"    数据: {' '.join(f'{b:02X}' for b in next_bytes)}")
        pos += 4

if __name__ == '__main__':
    main()
