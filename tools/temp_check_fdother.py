import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    # 读取文件头
    magic = f.read(6)
    print(f'文件头: {magic}')
    
    # 读取资源数量
    count_data = f.read(4)
    count = struct.unpack('<I', count_data)[0]
    print(f'资源数量: {count}')
    
    # 读取所有偏移
    offsets = []
    for i in range(count):
        offset_data = f.read(4)
        offset = struct.unpack('<I', offset_data)[0]
        offsets.append(offset)
    
    print(f'\n前30个资源:')
    for i in range(min(30, count)):
        start = offsets[i]
        if i + 1 < count:
            end = offsets[i + 1]
        else:
            f.seek(0, 2)
            end = f.tell()
        size = end - start
        
        f.seek(start)
        header = f.read(4)
        
        if len(header) >= 4:
            w, h = struct.unpack('<HH', header[:4])
            if 0 < w <= 640 and 0 < h <= 480:
                print(f'资源{i}: 偏移={start} (0x{start:X}), 大小={size}, 尺寸={w}x{h} (RLE图像)')
            else:
                # 检查是否是调色板或其他数据
                if size == 768:
                    print(f'资源{i}: 偏移={start} (0x{start:X}), 大小={size} (调色板768字节)')
                elif header[:4] == b'LLLL':
                    print(f'资源{i}: 偏移={start} (0x{start:X}), 大小={size} (嵌套DAT)')
                elif header[:3] == b'LMI':
                    print(f'资源{i}: 偏移={start} (0x{start:X}), 大小={size} (LMI音频)')
                else:
                    print(f'资源{i}: 偏移={start} (0x{start:X}), 大小={size}, 前4字节={header[:4].hex()} (二进制数据)')

    print(f'\n重点关注的索引:')
    for idx in [1, 2, 3, 4, 5, 6, 20]:
        if idx < count:
            start = offsets[idx]
            if idx + 1 < count:
                end = offsets[idx + 1]
            else:
                end = 3382481
            size = end - start
            f.seek(start)
            header = f.read(4)
            if len(header) >= 4:
                w, h = struct.unpack('<HH', header[:4])
                print(f'索引{idx}: start={start}, size={size}, w={w}, h={h}')
