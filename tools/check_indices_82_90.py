import struct
import os
import sys

def check_fdother_indices(fdother_path):
    with open(fdother_path, 'rb') as f:
        # 读取偏移表（前4字节是条目数）
        count_bytes = f.read(4)
        if len(count_bytes) < 4:
            print("文件太小")
            return
        
        count = struct.unpack('<I', count_bytes)[0]
        print(f"FDOTHER.DAT 总条目数: {count}")
        
        # 读取所有偏移
        offsets = []
        for i in range(count):
            offset_bytes = f.read(4)
            if len(offset_bytes) < 4:
                break
            offset = struct.unpack('<I', offset_bytes)[0]
            offsets.append(offset)
        
        print(f"读取到 {len(offsets)} 个偏移")
        
        # 检查索引82-90
        print("\n检查索引 82-90:")
        for idx in range(82, 91):
            if idx >= len(offsets):
                print(f"  索引 {idx}: 超出范围")
                continue
            
            # 计算当前索引的大小
            if idx + 1 < len(offsets):
                size = offsets[idx + 1] - offsets[idx]
            else:
                # 最后一个条目，使用文件大小
                f.seek(0, 2)
                file_size = f.tell()
                size = file_size - offsets[idx]
            
            if size <= 0 or size > 10000000:  # 异常大小过滤
                print(f"  索引 {idx}: 偏移={offsets[idx]}, 大小={size} (异常)")
                continue
            
            # 读取数据
            f.seek(offsets[idx])
            data = f.read(min(size, 100))  # 只读前100字节
            
            # 检查Magic
            magic = data[:4]
            
            # 尝试解析格式
            if magic == b'LMI1':
                if len(data) >= 6:
                    tile_count = struct.unpack('<H', data[4:6])[0]
                    print(f"  索引 {idx}: 偏移={offsets[idx]}, 大小={size}, Magic=LMI1, Tile数={tile_count}")
                else:
                    print(f"  索引 {idx}: 偏移={offsets[idx]}, 大小={size}, Magic=LMI1 (数据不足)")
            else:
                # 显示前4字节的十六进制
                magic_hex = ' '.join(f'{b:02x}' for b in magic)
                print(f"  索引 {idx}: 偏移={offsets[idx]}, 大小={size}, Magic={magic} ({magic_hex})")

if __name__ == '__main__':
    # 查找FDOTHER.DAT
    possible_paths = [
        r'd:\workspace\fd2_dat_freebuff\data\FDOTHER.DAT',
        r'd:\workspace\fd2_dat_freebuff\FDOTHER.DAT',
    ]
    
    fdother_path = None
    for path in possible_paths:
        if os.path.exists(path):
            fdother_path = path
            break
    
    if not fdother_path:
        print("未找到FDOTHER.DAT文件")
        sys.exit(1)
    
    print(f"使用文件: {fdother_path}\n")
    check_fdother_indices(fdother_path)
