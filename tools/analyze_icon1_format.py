#!/usr/bin/env python3
"""详细分析索引1图标数据格式"""
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
    
    print("=== 索引1 资源结构分析 ===")
    print(f"资源起始: 0x{res_start:X}")
    print(f"资源大小: {len(res_data)} 字节")
    
    # 外头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"\n外头: {outer_w}x{outer_h}, pal_window={pal_win}")
    print(f"外头5字节: {' '.join(f'{b:02X}' for b in res_data[:5])}")
    
    # 相对偏移表（假设从偏移6开始）
    print("\n=== 相对偏移表分析 ===")
    pos = 6
    icon_offsets = []
    
    for i in range(5):
        if pos + 4 > len(res_data):
            break
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        icon_offsets.append(rel_off)
        
        # 检查这个相对偏移指向的数据
        if rel_off < len(res_data):
            target_data = res_data[rel_off:rel_off+20]
            print(f"相对偏移[{i}]: 0x{pos:X} -> 相对偏移=0x{rel_off:X}")
            print(f"  指向数据前20字节: {' '.join(f'{b:02X}' for b in target_data)}")
            
            # 尝试作为宽高解析
            w = struct.unpack_from('<H', target_data, 0)[0]
            h = struct.unpack_from('<H', target_data, 2)[0]
            print(f"  作为宽高(LE): {w}x{h}")
            
            # 尝试大端序
            w_be = struct.unpack_from('>H', target_data, 0)[0]
            h_be = struct.unpack_from('>H', target_data, 2)[0]
            print(f"  作为宽高(BE): {w_be}x{h_be}")
            
            # 检查第5字节
            if len(target_data) > 4:
                print(f"  第5字节: 0x{target_data[4]:02X} = {target_data[4]}")
        
        pos += 4
        print()
    
    # 分析：如果所有图标的宽高都相同，那么图标数据应该不包含宽高头
    # 检查是否所有相对偏移指向的数据前2字节都相同
    print("=== 检查图标数据前4字节是否一致 ===")
    prefix_counts = {}
    for i, rel_off in enumerate(icon_offsets):
        if rel_off + 4 <= len(res_data):
            prefix = tuple(res_data[rel_off:rel_off+4])
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    for prefix, count in prefix_counts.items():
        print(f"前缀 {' '.join(f'{b:02X}' for b in prefix)}: 出现{count}次")

if __name__ == '__main__':
    main()
