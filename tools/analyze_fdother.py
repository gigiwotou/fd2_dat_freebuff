import struct

filepath = 'game/FDOTHER.DAT'

with open(filepath, 'rb') as f:
    file_size = f.seek(0, 2)
    f.seek(0)
    
    print(f'=== FDOTHER.DAT 分析 ===')
    print(f'文件大小: {file_size} 字节')
    
    # 读取文件头
    magic = f.read(6)
    print(f'文件头(0-5): {magic}')
    
    # 偏移6处开始的值
    f.seek(6)
    val_at_6 = struct.unpack('<I', f.read(4))[0]
    print(f'偏移6处的值: {val_at_6} (0x{val_at_6:X})')
    
    f.seek(10)
    val_at_10 = struct.unpack('<I', f.read(4))[0]
    print(f'偏移10处的值: {val_at_10} (0x{val_at_10:X})')
    
    # 假设偏移6处是第一个偏移表项
    # 读取前50个偏移表项
    print(f'\n=== 偏移表分析 (从偏移6开始) ===')
    offsets = []
    f.seek(6)
    for i in range(50):
        data = f.read(4)
        if len(data) < 4:
            break
        offset = struct.unpack('<I', data)[0]
        if offset >= file_size:
            print(f'索引{i}: offset={offset} (超出文件大小，可能是资源数量或结束标记)')
            break
        offsets.append(offset)
    
    print(f'\n前20个资源:')
    for i in range(min(20, len(offsets))):
        start = offsets[i]
        if i + 1 < len(offsets):
            end = offsets[i + 1]
        else:
            end = file_size
        size = end - start
        
        f.seek(start)
        header = f.read(8)
        
        # 检查是否是图像（前2字节是宽高）
        w = struct.unpack('<H', header[:2])[0]
        h = struct.unpack('<H', header[2:4])[0]
        
        is_image = (0 < w <= 640 and 0 < h <= 480)
        is_palette = (size == 768)
        is_lmi = (header[:3] == b'LMI')
        is_nested_dat = (header[:4] == b'LLLL')
        
        if is_image:
            print(f'  [{i:2d}] start={start:7d}, size={size:6d}, dims={w}x{h} [IMAGE]')
        elif is_palette:
            print(f'  [{i:2d}] start={start:7d}, size={size} [PALETTE]')
        elif is_lmi:
            print(f'  [{i:2d}] start={start:7d}, size={size:6d} [LMI AUDIO]')
        elif is_nested_dat:
            print(f'  [{i:2d}] start={start:7d}, size={size:6d} [NESTED DAT]')
        else:
            print(f'  [{i:2d}] start={start:7d}, size={size:6d}, header={header[:4].hex()} [BINARY]')
    
    # 重点检查1,2,3,4,5,6,20
    print(f'\n=== 重点资源检查 ===')
    for idx in [1, 2, 3, 4, 5, 6, 20]:
        if idx < len(offsets):
            start = offsets[idx]
            if idx + 1 < len(offsets):
                end = offsets[idx + 1]
            else:
                end = file_size
            size = end - start
            
            f.seek(start)
            header = f.read(16)
            w, h = struct.unpack('<HH', header[:4])
            
            print(f'\n索引{idx}:')
            print(f'  start={start}, end={end}, size={size}')
            print(f'  w={w}, h={h}')
            print(f'  header(16字节)={header.hex()}')
            
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                print(f'  -> 有效图像 {w}x{h}')
            else:
                print(f'  -> 不是标准图像格式')
