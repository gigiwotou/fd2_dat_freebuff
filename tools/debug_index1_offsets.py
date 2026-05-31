#!/usr/bin/env python3
"""详细分析索引1的实际数据结构和偏移计算"""
import struct

def read_dword(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def read_word(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def main():
    filepath = 'game/FDOTHER.DAT'
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 解析主偏移表
    main_offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = read_dword(data, offset)
        if off == 0 or off >= len(data):
            break
        main_offsets.append(off)
        offset += 4
    
    print("主偏移表:")
    for i, off in enumerate(main_offsets[:5]):
        print(f"  [{i}] 0x{off:X} ({off})")
    
    # 索引0 = 调色板
    pal_start = main_offsets[0]
    pal_end = main_offsets[1]
    pal_size = pal_end - pal_start
    print(f"\n索引0 (调色板): 0x{pal_start:X} - 0x{pal_end:X}, 大小={pal_size}")
    
    # 索引1 = 多图标
    res1_start = main_offsets[1]
    res1_end = main_offsets[2]
    res1_size = res1_end - res1_start
    print(f"索引1 (多图标): 0x{res1_start:X} - 0x{res1_end:X}, 大小={res1_size}")
    
    # 读取索引1数据
    res1 = data[res1_start:res1_end]
    
    # 尝试解析索引1头部
    print(f"\n=== 索引1数据解析 ===")
    print(f"前16字节: {' '.join(f'{b:02X}' for b in res1[:16])}")
    
    # 方式A: [w:2][h:2][pw:1][pad:1][offsets...]
    w_a = read_word(res1, 0)
    h_a = read_word(res1, 2)
    pw_a = res1[4]
    print(f"\n方式A ([w:2][h:2][pw:1][pad:1]):")
    print(f"  Width: {w_a} (0x{w_a:04X})")
    print(f"  Height: {h_a} (0x{h_a:04X})")
    print(f"  Palette Window: {pw_a} (0x{pw_a:02X})")
    
    # 从偏移6开始读取偏移表
    offsets_a = []
    pos = 6
    while pos + 4 <= len(res1):
        rel_off = read_dword(res1, pos)
        if rel_off > res1_size:
            break
        offsets_a.append(rel_off)
        pos += 4
    print(f"  偏移表数量: {len(offsets_a)}")
    print(f"  前5个偏移: {[hex(o) for o in offsets_a[:5]]}")
    
    # 方式B: [pw:2][w:2][h:2][offsets...]  
    pw_b = read_word(res1, 0)
    w_b = read_word(res1, 2)
    h_b = read_word(res1, 4)
    print(f"\n方式B ([pw:2][w:2][h:2]):")
    print(f"  Palette Window: {pw_b} (0x{pw_b:04X})")
    print(f"  Width: {w_b} (0x{w_b:04X})")
    print(f"  Height: {h_b} (0x{h_b:04X})")
    
    # 从偏移8开始读取偏移表
    offsets_b = []
    pos = 8
    while pos + 4 <= len(res1):
        rel_off = read_dword(res1, pos)
        if rel_off > res1_size:
            break
        offsets_b.append(rel_off)
        pos += 4
    print(f"  偏移表数量: {len(offsets_b)}")
    print(f"  前5个偏移: {[hex(o) for o in offsets_b[:5]]}")
    
    # 方式C: 检查相对偏移是否指向正确位置
    # 如果第一个偏移是86 (0x56)，那说明偏移是从资源开始算的
    print(f"\n=== 验证相对偏移 ===")
    if len(offsets_a) > 0:
        first_icon_off = offsets_a[0]
        if first_icon_off < res1_size:
            icon_data = res1[first_icon_off:]
            print(f"方式A第一个图标:")
            print(f"  相对偏移: {first_icon_off} (0x{first_icon_off:04X})")
            print(f"  绝对偏移: 0x{res1_start + first_icon_off:X}")
            print(f"  前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
            
            # 尝试读取图标宽高
            if len(icon_data) >= 4:
                icon_w = read_word(icon_data, 0)
                icon_h = read_word(icon_data, 2)
                print(f"  图标宽高: {icon_w}x{icon_h}")
                print(f"  前4字节作为宽高是否合理: {icon_w <= 200 and icon_h <= 200}")
    
    # 如果偏移是绝对的（指向FDOTHER.DAT文件中的位置）
    print(f"\n=== 检查绝对偏移 ===")
    if len(offsets_a) > 0:
        # 尝试作为绝对偏移
        abs_off = offsets_a[0]
        if abs_off < len(data):
            abs_data = data[abs_off:]
            print(f"作为绝对偏移 0x{abs_off:X}:")
            print(f"  前16字节: {' '.join(f'{b:02X}' for b in abs_data[:16])}")
            
            if len(abs_data) >= 4:
                icon_w = read_word(abs_data, 0)
                icon_h = read_word(abs_data, 2)
                print(f"  图标宽高: {icon_w}x{icon_h}")
                print(f"  是否合理: {icon_w <= 200 and icon_h <= 200}")
    
    # 检查索引2的结构对比
    print(f"\n=== 索引2结构对比 ===")
    res2_start = main_offsets[2]
    res2_end = main_offsets[3]
    res2_size = res2_end - res2_start
    res2 = data[res2_start:res2_end]
    print(f"索引2: 0x{res2_start:X} - 0x{res2_end:X}, 大小={res2_size}")
    print(f"前16字节: {' '.join(f'{b:02X}' for b in res2[:16])}")
    
    w2 = read_word(res2, 0)
    h2 = read_word(res2, 2)
    print(f"  Width: {w2} (0x{w2:04X})")
    print(f"  Height: {h2} (0x{h2:04X})")

if __name__ == '__main__':
    main()
