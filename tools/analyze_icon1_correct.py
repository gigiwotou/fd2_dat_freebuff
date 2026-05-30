#!/usr/bin/env python3
"""正确解析索引1的偏移表"""
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
    
    print("=== 索引1 偏移表解析 ===")
    start = offsets[1]
    end = offsets[2]
    res_data = data[start:end]
    
    print(f"总大小: {len(res_data)} 字节")
    
    # 头5字节
    w = struct.unpack_from('<H', res_data, 0)[0]
    h = struct.unpack_from('<H', res_data, 2)[0]
    pal_window = res_data[4]
    print(f"头: {w}x{h}, 调色板窗口={pal_window}")
    
    # 从偏移5开始解析4字节偏移
    data_start = 5
    print(f"\n从偏移{data_start}开始解析4字节偏移:")
    
    icon_offsets = []
    pos = data_start
    max_count = 100
    
    while pos + 4 <= len(res_data) and len(icon_offsets) < max_count:
        off = struct.unpack_from('<I', res_data, pos)[0]
        
        # 第一个偏移应该是0
        if len(icon_offsets) == 0 and off != 0:
            print(f"第一个偏移不是0: {off}")
            # 尝试另一种解析：也许偏移是相对于数据区开始
            if off < len(res_data) - data_start:
                print(f"  偏移 {off} 在数据区内，继续...")
            else:
                print(f"  停止解析")
                break
        
        # 检查偏移是否合理
        if off > len(res_data):
            print(f"偏移 {off} (0x{off:X}) 超出范围，停止")
            break
        
        icon_offsets.append(off)
        pos += 4
    
    print(f"\n找到 {len(icon_offsets)} 个偏移")
    print(f"前20个偏移:")
    for i, off in enumerate(icon_offsets[:20]):
        if i + 1 < len(icon_offsets):
            size = icon_offsets[i + 1] - off
            print(f"  图标{i}: 偏移 0x{off:X} ({off}), 大小 {size} 字节")
        else:
            print(f"  图标{i}: 偏移 0x{off:X} ({off})")
    
    if len(icon_offsets) > 1:
        print(f"\n最后偏移: 0x{icon_offsets[-1]:X} = {icon_offsets[-1]}")
        remaining = len(res_data) - icon_offsets[-1]
        print(f"剩余数据: {remaining} 字节")

if __name__ == '__main__':
    main()
