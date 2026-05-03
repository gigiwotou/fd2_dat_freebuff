import struct

def analyze_fdother_resources():
    """根据IDA分析FDOTHER.DAT的资源表结构"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)} 字节")
    
    # 根据IDA 16886.c分析：
    # sub_4E98D((__int16 *)(*(_DWORD *)(a7 + 4 * a8 + 6) + a7), 0, 0, a5, a6, -1);
    # 
    # 结构：
    # - 偏移0-5: 未知（可能是头部信息）
    # - 偏移6开始: 资源偏移表，每项4字节（DWORD）
    # - 资源数据: 从某个位置开始
    #
    # 1ACF3.c第35行：
    # sub_4E98D((__int16 *)(*(_DWORD *)(dword_53A81 + 526) + dword_53A81), 0, 0, v6, n456, -1);
    # 526 = 4 * 130 + 6，所以是资源索引130
    
    print("\n=== 检查文件头部（偏移0-5）===")
    header = data[0:6]
    print(f"头部6字节: {' '.join(f'{b:02X}' for b in header)}")
    if len(header) >= 4:
        val = struct.unpack('<I', header[0:4])[0]
        print(f"前4字节作为DWORD: {val} (0x{val:08X})")
    
    print(f"\n=== 资源偏移表（从偏移6开始，每项4字节）===")
    print("检查前20个资源：")
    for idx in range(0, 20):
        offset = 6 + idx * 4
        if offset + 4 > len(data):
            break
        rel_offset = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"\n资源索引 {idx:2d}:")
        print(f"  表项位置: 偏移 {offset} (0x{offset:04X})")
        print(f"  相对偏移: {rel_offset} (0x{rel_offset:08X})")
        
        if rel_offset > 0 and rel_offset < len(data):
            # 检查该位置的数据
            print(f"  数据位置: {rel_offset}")
            if rel_offset + 4 <= len(data):
                w = struct.unpack('<H', data[rel_offset:rel_offset+2])[0]
                h = struct.unpack('<H', data[rel_offset+2:rel_offset+4])[0]
                print(f"  可能尺寸: {w}x{h}")
                if w > 0 and w < 256 and h > 0 and h < 256:
                    print(f"  *** 可能是有效图像 ***")
                    print(f"  RLE前16字节: {' '.join(f'{b:02X}' for b in data[rel_offset+4:rel_offset+20])}")
    
    print(f"\n=== 检查光标资源（索引130，偏移526）===")
    cursor_idx = 130
    cursor_table_offset = 6 + cursor_idx * 4
    print(f"索引: {cursor_idx}")
    print(f"表项位置: 偏移 {cursor_table_offset} (0x{cursor_table_offset:04X})")
    
    if cursor_table_offset + 4 <= len(data):
        cursor_rel_offset = struct.unpack('<I', data[cursor_table_offset:cursor_table_offset+4])[0]
        print(f"相对偏移: {cursor_rel_offset} (0x{cursor_rel_offset:08X})")
        
        if cursor_rel_offset > 0 and cursor_rel_offset < len(data):
            print(f"\n光标数据位置: {cursor_rel_offset}")
            if cursor_rel_offset + 4 <= len(data):
                w = struct.unpack('<H', data[cursor_rel_offset:cursor_rel_offset+2])[0]
                h = struct.unpack('<H', data[cursor_rel_offset+2:cursor_rel_offset+4])[0]
                print(f"宽度: {w}")
                print(f"高度: {h}")
                
                if w > 0 and w < 256 and h > 0 and h < 256:
                    print(f"*** 有效图像尺寸 ***")
                    print(f"RLE前32字节: {' '.join(f'{b:02X}' for b in data[cursor_rel_offset+4:cursor_rel_offset+36])}")
                else:
                    print(f"警告: 尺寸异常！")
                    print(f"前64字节: {' '.join(f'{b:02X}' for b in data[cursor_rel_offset:cursor_rel_offset+64])}")

if __name__ == '__main__':
    analyze_fdother_resources()
