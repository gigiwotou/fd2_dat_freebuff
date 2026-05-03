import struct

def analyze_fdother():
    """分析FDOTHER.DAT的完整结构"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节 (0x{len(data):04X})")
    
    # 检查文件开头
    print(f"\n文件开头64字节:")
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str}")
    
    # 搜索非零数据区域
    print(f"\n=== 搜索非零数据区域 ===")
    non_zero_regions = []
    i = 0
    while i < len(data):
        if data[i] != 0:
            start = i
            while i < len(data) and data[i] != 0:
                i += 1
            end = i
            size = end - start
            if size > 10:  # 只记录大于10字节的非零区域
                non_zero_regions.append((start, end, size))
        else:
            i += 1
    
    print(f"\n找到 {len(non_zero_regions)} 个非零数据区域:")
    for start, end, size in non_zero_regions[:20]:  # 只显示前20个
        print(f"  偏移: 0x{start:04X} ({start:6d}) - 0x{end:04X} ({end:6d}), 大小: {size:4d} 字节")
        # 打印该区域前32字节
        hex_str = ' '.join(f'{b:02X}' for b in data[start:start+32])
        print(f"    数据: {hex_str}")
    
    # 检查是否有文件头或索引结构
    print(f"\n=== 检查可能的文件头结构 ===")
    # 检查前512字节
    print(f"前512字节:")
    for i in range(0, 512, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str}  {ascii_str}")
    
    # 查找所有32位指针（指向文件内的偏移）
    print(f"\n=== 查找32位指针（前1024字节）===")
    for i in range(0, min(1024, len(data)-3), 4):
        ptr = struct.unpack('<I', data[i:i+4])[0]
        if 0 < ptr < len(data):
            # 检查指针指向的位置是否有数据
            target = data[ptr:ptr+4]
            if any(b != 0 for b in target):
                print(f"  偏移 {i:04X} (0x{i:04X}): 指针=0x{ptr:04X} ({ptr:6d}), 目标数据: {' '.join(f'{b:02X}' for b in target)}")

if __name__ == '__main__':
    analyze_fdother()
