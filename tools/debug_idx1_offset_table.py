"""
分析索引1是否包含偏移表
"""
import struct

def analyze_idx1_as_offset_table():
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
    
    # 解析5字节头
    w = idx1_data[0] | (idx1_data[1] << 8)
    h = idx1_data[2] | (idx1_data[3] << 8)
    palette_window = idx1_data[4]
    
    print(f"头: w={w}, h={h}, palette_window={palette_window}")
    
    # 从字节5开始是偏移表
    offset_table_data = idx1_data[5:]
    print(f"\n偏移表数据大小: {len(offset_table_data)} 字节")
    
    # 读取4字节偏移量
    offset_count = len(offset_table_data) // 4
    offsets_list = []
    
    for i in range(min(20, offset_count)):
        addr = i * 4
        off = offset_table_data[addr] | (offset_table_data[addr+1] << 8) | \
              (offset_table_data[addr+2] << 16) | (offset_table_data[addr+3] << 24)
        offsets_list.append(off)
    
    print(f"前20个偏移量:")
    for i, off in enumerate(offsets_list):
        print(f"  偏移{i}: 0x{off:08x} ({off})")
    
    # 检查偏移量是否递增
    if len(offsets_list) > 1:
        diffs = [offsets_list[i+1] - offsets_list[i] for i in range(len(offsets_list)-1)]
        print(f"\n相邻偏移量差值:")
        for i, diff in enumerate(diffs[:10]):
            print(f"  offset[{i+1}] - offset[{i}] = {diff}")
    
    # 检查最大偏移量
    max_offset = max(offsets_list)
    print(f"\n最大偏移量: {max_offset}")
    print(f"数据区起始偏移: 5 + {len(offsets_list)} * 4 = {5 + len(offsets_list) * 4}")
    print(f"总数据大小: {len(idx1_data)}")
    
    if max_offset < len(idx1_data):
        print(f"\n✓ 偏移量在数据范围内")
    else:
        print(f"\n✗ 偏移量超出数据范围")
    
    # 假设偏移表指向子资源
    print(f"\n=== 分析子资源 ===")
    for i in range(min(5, len(offsets_list)-1)):
        sub_start = offsets_list[i]
        sub_end = offsets_list[i+1]
        sub_size = sub_end - sub_start
        
        print(f"\n子资源{i}: 偏移{sub_start}-{sub_end}, 大小{sub_size}")
        
        if sub_start < len(idx1_data) and sub_end <= len(idx1_data):
            sub_data = idx1_data[sub_start:sub_end]
            print(f"  数据前8字节: {sub_data[:8].hex()}")
            
            # 尝试解析为Tile
            if len(sub_data) >= 5:
                sw = sub_data[0] | (sub_data[1] << 8)
                sh = sub_data[2] | (sub_data[3] << 8)
                spw = sub_data[4]
                print(f"  可能的Tile: {sw}x{sh}, palette_window={spw}")

if __name__ == "__main__":
    analyze_idx1_as_offset_table()
