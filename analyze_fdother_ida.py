import struct

def analyze_fdother_structure():
    """根据IDA分析dword_53A81的资源表结构"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)} 字节")
    
    # 根据IDA反编译，dword_53A81是指向某个资源表结构的指针
    # 格式: *(_DWORD *)(dword_53A81 + 4 * index + 6) + dword_53A81
    # 偏移526 = 4 * 130 + 6，所以index=130
    
    # 先验证表结构
    print("\n=== 验证资源表结构 ===")
    print("检查偏移0-512，寻找资源表头")
    
    # 偏移0-5可能包含表头信息
    print(f"\n偏移0-64:")
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        print(f"  {i:04d} (0x{i:04X}): {hex_str}")
    
    # 从偏移6开始是资源偏移表，每个4字节
    print(f"\n=== 检查偏移6开始的资源表 (4字节/项) ===")
    for idx in range(0, 20):
        offset = 6 + idx * 4
        if offset + 4 > len(data):
            break
        rel_offset = struct.unpack('<I', data[offset:offset+4])[0]
        print(f"  索引{idx:2d} (偏移{offset:4d}/0x{offset:04X}): 相对偏移={rel_offset:8d} (0x{rel_offset:08X})")
        
        # 如果相对偏移有效，查看该位置数据
        if rel_offset > 0 and rel_offset < len(data):
            # 检查是否是图像数据（前2字节是宽高）
            width = struct.unpack('<H', data[rel_offset:rel_offset+2])[0]
            height = struct.unpack('<H', data[rel_offset+2:rel_offset+4])[0]
            if width > 0 and width < 256 and height > 0 and height < 256:
                print(f"    -> 可能是图像: {width}x{height}")
                # 打印前16字节RLE数据
                rle_hex = ' '.join(f'{b:02X}' for b in data[rel_offset+4:rel_offset+20])
                print(f"    RLE前16字节: {rle_hex}")
    
    # 特别检查偏移526（索引130）
    print(f"\n=== 检查偏移526 (索引130，光标资源) ===")
    offset_526 = struct.unpack('<I', data[526:530])[0]
    print(f"偏移526处的相对偏移: {offset_526} (0x{offset_526:08X})")
    
    if offset_526 > 0 and offset_526 < len(data):
        print(f"光标数据位置: {offset_526}")
        width = struct.unpack('<H', data[offset_526:offset_526+2])[0]
        height = struct.unpack('<H', data[offset_526+2:offset_526+4])[0]
        print(f"宽度: {width}, 高度: {height}")
        print(f"前32字节: {' '.join(f'{b:02X}' for b in data[offset_526:offset_526+32])}")

if __name__ == '__main__':
    analyze_fdother_structure()
