"""
分析索引1是否包含偏移表结构
"""
import struct

def analyze_idx1_as_nested():
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(6)
        offsets = []
        while True:
            data = f.read(4)
            if len(data) < 4:
                break
            off = struct.unpack('<I', data)[0]
            if off > 10000000:
                break
            offsets.append(off)
            if len(offsets) > 103:
                break
    
    idx1_start = offsets[1]
    idx1_end = offsets[2]
    
    with open("game/FDOTHER.DAT", "rb") as f:
        f.seek(idx1_start)
        idx1_data = f.read(idx1_end - idx1_start)
    
    print(f"索引1数据大小: {len(idx1_data)} 字节")
    print(f"完整数据(前200字节hex): {idx1_data[:200].hex()}")
    
    # 检查是否是8字节头的Tile
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    byte5 = idx1_data[5] if len(idx1_data) > 5 else 0
    
    print(f"\n=== 假设是Tile图像 ===")
    print(f"宽: {w}, 高: {h}, 字节5: 0x{byte5:02x}")
    
    if byte5 == 0:
        print(f"5字节头格式")
        header_size = 5
        rle_data = idx1_data[5:]
    else:
        print(f"8字节头格式")
        header_size = 8
        rle_data = idx1_data[8:]
    
    # 分析RLE数据中的模式
    print(f"\n=== 分析RLE数据模式 ===")
    print(f"RLE数据大小: {len(rle_data)}")
    print(f"RLE前50字节: {rle_data[:50].hex()}")
    
    # 检查是否有4字节的偏移量模式
    print(f"\n=== 检查偏移表模式 ===")
    # 每4字节读取一个值
    potential_offsets = []
    for i in range(0, min(100, len(rle_data)), 4):
        if i + 4 <= len(rle_data):
            val = rle_data[i] | (rle_data[i+1] << 8) | (rle_data[i+2] << 16) | (rle_data[i+3] << 24)
            potential_offsets.append(val)
    
    print(f"前25个4字节值:")
    for i, val in enumerate(potential_offsets[:25]):
        print(f"  偏移{i*4}: 0x{val:08x} ({val})")
    
    # 检查这些值是否是递增的偏移量
    if len(potential_offsets) > 1:
        diffs = [potential_offsets[i+1] - potential_offsets[i] for i in range(len(potential_offsets)-1)]
        print(f"\n相邻偏移量差值:")
        for i, diff in enumerate(diffs[:20]):
            print(f"  offset[{i+1}] - offset[{i}] = {diff}")
    
    # 检查是否所有偏移量都在合理范围内
    max_offset = max(potential_offsets[:20]) if potential_offsets else 0
    print(f"\n前20个偏移量的最大值: {max_offset}")
    print(f"RLE数据总大小: {len(rle_data)}")
    
    if max_offset < len(rle_data):
        print("✓ 所有偏移量都在RLE数据范围内")
    else:
        print("✗ 有偏移量超出RLE数据范围")
    
    # 尝试解析为嵌套DAT
    print(f"\n=== 尝试解析为嵌套结构 ===")
    if len(idx1_data) >= 8:
        # 假设前8字节是头（w:2, h:2, 未知:4）
        # 或者前5字节是头（w:2, h:2, pal_win:1）
        # 然后是偏移表
        
        # 方案1: 5字节头 + 偏移表
        offset_table_start = 5
        offset_count = (len(idx1_data) - offset_table_start) // 4
        
        print(f"方案1: 5字节头 + {offset_count}个偏移量")
        print(f"偏移表起始: {offset_table_start}")
        
        offsets_list = []
        for i in range(min(20, offset_count)):
            addr = offset_table_start + i * 4
            if addr + 4 <= len(idx1_data):
                off = idx1_data[addr] | (idx1_data[addr+1] << 8) | \
                      (idx1_data[addr+2] << 16) | (idx1_data[addr+3] << 24)
                offsets_list.append(off)
        
        print(f"前10个偏移量: {[hex(o) for o in offsets_list[:10]]}")
        
        # 检查偏移量是否递增
        is_increasing = all(offsets_list[i] < offsets_list[i+1] for i in range(len(offsets_list)-1))
        print(f"偏移量是否递增: {is_increasing}")
        
        if is_increasing and len(offsets_list) > 1:
            print(f"✓ 索引1很可能包含偏移表结构！")
            print(f"  偏移量数量: {offset_count}")
            print(f"  第一个子资源偏移: {offsets_list[0]}")
            print(f"  最后一个子资源偏移: {offsets_list[-1] if offsets_list else 'N/A'}")

if __name__ == "__main__":
    analyze_idx1_as_nested()
