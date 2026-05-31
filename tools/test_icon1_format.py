#!/usr/bin/env python3
"""验证索引1图标数据格式 - 是否有4字节宽高头"""
import struct

def main():
    filepath = 'game/FDOTHER.DAT'
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 解析主偏移表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    offsets.append(len(data))
    
    print(f"总偏移数: {len(offsets)-1}")
    
    # 索引1资源
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print(f"\n索引1资源: {len(res_data)}字节")
    print(f"前16字节: {' '.join(f'{b:02X}' for b in res_data[:16])}")
    
    # 解析外层头
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"\n外层头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 解析相对偏移表
    icon_offsets = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        if rel_off >= len(res_data):
            break
        icon_offsets.append(rel_off)
        pos += 4
    
    print(f"\n相对偏移表: {len(icon_offsets)}个偏移")
    for i, off in enumerate(icon_offsets[:5]):
        print(f"  图标{i}: 相对偏移=0x{off:X}")
    
    # 分析每个图标数据
    print("\n=== 图标数据分析 ===")
    for i in range(min(3, len(icon_offsets)-1)):
        rel_off = icon_offsets[i]
        next_rel = icon_offsets[i+1] if i+1 < len(icon_offsets) else len(res_data)
        icon_data = res_data[rel_off:next_rel]
        
        print(f"\n图标{i}: {len(icon_data)}字节")
        print(f"前16字节: {' '.join(f'{b:02X}' for b in icon_data[:16])}")
        
        # 尝试解析为包含4字节宽高头
        if len(icon_data) >= 4:
            inner_w = struct.unpack_from('<H', icon_data, 0)[0]
            inner_h = struct.unpack_from('<H', icon_data, 2)[0]
            print(f"  作为4字节头: {inner_w}x{inner_h}")
            
            # 检查宽高是否合理 (应该是24x24左右)
            if inner_w == outer_w and inner_h == outer_h:
                print(f"  ✅ 宽高与外层头匹配! 说明图标数据包含4字节宽高头")
                print(f"  像素数据从偏移4开始: {len(icon_data)-4}字节")
                print(f"  像素数据前8字节: {' '.join(f'{b:02X}' for b in icon_data[4:12])}")
            elif inner_w > 1000 or inner_h > 1000:
                print(f"  ❌ 宽高异常 ({inner_w}x{inner_h}), 图标数据可能不包含宽高头")
            else:
                print(f"  ⚠️ 宽高不匹配: {inner_w}x{inner_h} vs {outer_w}x{outer_h}")

if __name__ == '__main__':
    main()
