#!/usr/bin/env python3
"""重新分析索引1的偏移表结构"""
import struct

def main():
    filepath = 'game/FDOTHER.DAT'
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 主偏移表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    offsets.append(len(data))
    
    # 索引1资源
    res_start = offsets[1]
    res_end = offsets[2]
    res_data = data[res_start:res_end]
    
    print(f"索引1资源: 绝对偏移={res_start}, 大小={len(res_data)}字节")
    print(f"前20字节: {' '.join(f'{b:02X}' for b in res_data[:20])}")
    
    outer_w = struct.unpack_from('<H', res_data, 0)[0]
    outer_h = struct.unpack_from('<H', res_data, 2)[0]
    pal_win = res_data[4]
    print(f"\n外层头: {outer_w}x{outer_h}, pal_window={pal_win}")
    
    # 尝试两种偏移解析方式
    print("\n=== 方式1: 从偏移6开始解析相对偏移表 ===")
    rel_offsets_v1 = []
    pos = 6
    while pos + 4 <= len(res_data):
        rel_off = struct.unpack_from('<I', res_data, pos)[0]
        rel_offsets_v1.append(rel_off)
        pos += 4
        if len(rel_offsets_v1) >= 22:  # 多读几个看看
            break
    
    print(f"读取了{len(rel_offsets_v1)}个偏移")
    for i, off in enumerate(rel_offsets_v1[:5]):
        abs_pos = res_start + off if off < len(res_data) else off
        print(f"  偏移{i}: 相对=0x{off:X}, 绝对位置=0x{abs_pos:X}")
        if off < len(res_data):
            chunk = res_data[off:off+8]
            print(f"    数据: {' '.join(f'{b:02X}' for b in chunk)}")
    
    # 检查：如果第一个偏移是0x56，从那里开始的数据是否合理？
    print("\n=== 检查偏移0x56处的数据 ===")
    pos_56 = 0x56
    if pos_56 < len(res_data):
        chunk = res_data[pos_56:pos_56+20]
        print(f"数据: {' '.join(f'{b:02X}' for b in chunk)}")
        
        # 尝试解析为宽高
        w = struct.unpack_from('<H', chunk, 0)[0]
        h = struct.unpack_from('<H', chunk, 2)[0]
        print(f"作为宽高: {w}x{h}")
    
    print("\n=== 方式2: 检查是否是嵌套DAT结构 ===")
    # 看看偏移6开始的是否是嵌套DAT（有资源数量+偏移表+资源数据）
    print(f"偏移6处4字节: {' '.join(f'{b:02X}' for b in res_data[6:10])}")
    
    # 尝试解析为资源数量
    if len(res_data) >= 10:
        count = struct.unpack_from('<I', res_data, 6)[0]
        print(f"作为DWORD: {count}")

if __name__ == '__main__':
    main()
