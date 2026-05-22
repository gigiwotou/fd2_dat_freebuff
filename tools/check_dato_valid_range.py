"""
检查DATO.DAT偏移表的有效性范围
"""
import struct

def check_valid_range():
    with open("game/DATO.DAT", "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"资源总数: {count}")
    print(f"文件大小: {file_size}")
    print()
    
    last_valid_idx = -1
    first_invalid_idx = -1
    
    # 找到最后一个有效的索引
    for idx in range(count):
        offset = 10 + idx * 4
        off_start = struct.unpack_from('<I', data, offset)[0]
        off_end = struct.unpack_from('<I', data, offset + 4)[0]
        
        if off_start < file_size and off_end <= file_size:
            last_valid_idx = idx
        else:
            if first_invalid_idx == -1:
                first_invalid_idx = idx
            break
    
    print(f"第一个无效索引: {first_invalid_idx}")
    print(f"最后一个有效索引: {last_valid_idx}")
    print(f"有效资源数量: {last_valid_idx + 1}")
    print()
    
    # 检查最后几个有效索引
    print("最后5个有效索引:")
    print("-" * 80)
    for idx in range(max(0, last_valid_idx - 4), last_valid_idx + 1):
        offset = 10 + idx * 4
        off_start = struct.unpack_from('<I', data, offset)[0]
        off_end = struct.unpack_from('<I', data, offset + 4)[0]
        raw = data[offset:offset+8]
        
        print(f"  索引{idx}:")
        print(f"    位置: {offset}, 原始字节: {raw.hex()}")
        print(f"    start: {off_start}, end: {off_end}")
        print()
    
    # 检查第一个无效索引附近
    if first_invalid_idx >= 0:
        print("第一个无效索引及其前后:")
        print("-" * 80)
        for idx in range(max(0, first_invalid_idx - 2), first_invalid_idx + 3):
            offset = 10 + idx * 4
            off_start = struct.unpack_from('<I', data, offset)[0]
            off_end = struct.unpack_from('<I', data, offset + 4)[0]
            raw = data[offset:offset+8]
            valid = "有效" if off_start < file_size and off_end <= file_size else "无效"
            
            print(f"  索引{idx} [{valid}]:")
            print(f"    位置: {offset}, 原始字节: {raw.hex()}")
            print(f"    start: {off_start}, end: {off_end}")
            print()

if __name__ == "__main__":
    check_valid_range()
