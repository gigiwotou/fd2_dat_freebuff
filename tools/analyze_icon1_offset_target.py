#!/usr/bin/env python3
"""检查索引1偏移6开始的值是指向哪里"""
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
    res_start = offsets[1]  # 0x4A6
    res_end = offsets[2]    # 0xD61
    res_data = data[res_start:res_end]
    
    print(f"\n=== 索引1 ===")
    print(f"文件偏移: 0x{res_start:X} - 0x{res_end:X}")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"外头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 检查偏移6开始的第一个值: 0x56
    val_0 = struct.unpack_from('<I', res_data, 6)[0]
    print(f"\n偏移6的第一个值: 0x{val_0:X} = {val_0}")
    
    # 假设是相对于资源开始的偏移
    file_offset_1 = res_start + val_0
    print(f"作为相对偏移: 文件位置 0x{file_offset_1:X} = {file_offset_1}")
    
    if file_offset_1 < len(data):
        print(f"该位置的数据 (前32字节):")
        chunk = data[file_offset_1:file_offset_1+32]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  {hex_str}")
        
        # 尝试作为宽高
        maybe_w = struct.unpack_from('<H', chunk, 0)[0]
        maybe_h = struct.unpack_from('<H', chunk, 2)[0]
        print(f"  作为宽高: {maybe_w}x{maybe_h}")
        
        if maybe_w == w and maybe_h == h:
            print(f"  >>> 匹配外部宽高 24x24!")
    
    # 假设是文件偏移
    if val_0 < len(data):
        print(f"\n作为文件偏移: 文件位置 0x{val_0:X} = {val_0}")
        chunk = data[val_0:val_0+32]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  数据: {hex_str}")
        
        maybe_w = struct.unpack_from('<H', chunk, 0)[0]
        maybe_h = struct.unpack_from('<H', chunk, 2)[0]
        print(f"  作为宽高: {maybe_w}x{maybe_h}")
    
    # 第二个值: 0x133
    val_1 = struct.unpack_from('<I', res_data, 10)[0]
    print(f"\n偏移10的第二个值: 0x{val_1:X} = {val_1}")
    
    # 作为相对偏移
    file_offset_2 = res_start + val_1
    print(f"作为相对偏移: 文件位置 0x{file_offset_2:X} = {file_offset_2}")
    
    if file_offset_2 < len(data):
        chunk = data[file_offset_2:file_offset_2+32]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f"  数据: {hex_str}")
        
        maybe_w = struct.unpack_from('<H', chunk, 0)[0]
        maybe_h = struct.unpack_from('<H', chunk, 2)[0]
        print(f"  作为宽高: {maybe_w}x{maybe_h}")
    
    # 比较两个位置的差值
    diff = val_1 - val_0
    print(f"\n差值: 0x{diff:X} = {diff}")
    print(f"如果是相对偏移，差值也是: {diff}")
    
    # 如果是24x24 tile，每个tile的像素数据应该大约是多少？
    # 使用EC66编码，24x24=576像素
    # 假设平均压缩率2:1，大约288字节
    print(f"\n24x24 tile的预期大小:")
    print(f"  原始像素: 576字节")
    print(f"  EC66编码后: 假设200-400字节")
    print(f"  实际差值: {diff}字节")
    
    # 列出前10个偏移作为相对偏移
    print(f"\n\n前10个偏移 (作为相对偏移):")
    for i in range(10):
        pos = 6 + i * 4
        if pos + 4 > len(res_data):
            break
        val = struct.unpack_from('<I', res_data, pos)[0]
        file_off = res_start + val
        print(f"  项{i}: 相对0x{val:X} = 文件0x{file_off:X}")
        
        if i > 0:
            prev_val = struct.unpack_from('<I', res_data, pos - 4)[0]
            size = val - prev_val
            print(f"    大小: {size}字节")

if __name__ == '__main__':
    main()
