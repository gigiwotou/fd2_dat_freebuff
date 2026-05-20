import struct

def try_correct_rle():
    """尝试正确的RLE解码方案"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== 尝试正确的RLE解码 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    f0 = struct.unpack('<I', res_data[4:8])[0]
    f1 = struct.unpack('<I', res_data[8:12])[0]
    
    # 帧数据从偏移开始
    # 前4字节: 50 00 50 00 (宽高)
    # 之后是压缩数据
    compressed = res_data[f0+4:f1]
    print(f'帧数据 (跳过宽高4字节): {len(compressed)} 字节')
    print(f'目标: 6400 像素\n')
    
    # 方案: 0xC0-0xFF 是RLE标记
    # byte & 0x3F = count, 下一个字节 = pixel
    # 但方案4解码出6361像素，差39个
    # 可能需要特殊处理
    
    print('方案A: 0xC0-0xFF是RLE, count=byte&0x3F+1, pixel=next')
    decoded = []
    i = 0
    while i < len(compressed):
        byte = compressed[i]
        if byte >= 0xC0:
            if i + 1 < len(compressed):
                count = (byte & 0x3F) + 1  # +1
                pixel = compressed[i + 1]
                decoded.extend([pixel] * count)
                i += 2
            else:
                break
        else:
            decoded.append(byte)
            i += 1
    
    print(f'  解码像素: {len(decoded)} / 6400')
    print(f'  消耗: {i} / {len(compressed)} 字节')
    if len(decoded) == 6400:
        print('  *** 完全匹配! ***')
        with open('output/frame0_decoded.bin', 'wb') as f:
            f.write(bytes(decoded))
        print('  已保存')
        
        print(f'\n图像前3行:')
        for row in range(3):
            pixels = decoded[row*80:(row+1)*80]
            line = ''.join('.' if p == 0 else '#' for p in pixels)
            print(f'  行{row:2d}: {line}')

def rle_analysis():
    """详细分析RLE编码"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== RLE编码详细分析 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    f0 = struct.unpack('<I', res_data[4:8])[0]
    f1 = struct.unpack('<I', res_data[8:12])[0]
    compressed = res_data[f0+4:f1]
    
    # 显示前100字节的详细分析
    print('压缩数据前100字节，标注可能的RLE/字面量:')
    i = 0
    while i < min(100, len(compressed)):
        byte = compressed[i]
        if byte >= 0xC0:
            count = byte & 0x3F
            if i + 1 < len(compressed):
                pixel = compressed[i + 1]
                print(f'[{i:3d}] RLE: 0x{byte:02X} (count={count}), pixel={pixel}')
                i += 2
            else:
                print(f'[{i:3d}] RLE: 0x{byte:02X} (count={count}), [missing pixel]')
                i += 1
        else:
            print(f'[{i:3d}] LIT: 0x{byte:02X} ({byte})')
            i += 1
    
    # 统计不同的count值
    print('\n统计RLE的count值:')
    count_stats = {}
    i = 0
    while i < len(compressed):
        byte = compressed[i]
        if byte >= 0xC0:
            if i + 1 < len(compressed):
                count = byte & 0x3F
                count_stats[count] = count_stats.get(count, 0) + 1
                i += 2
            else:
                break
        else:
            i += 1
    
    # 按频率排序
    sorted_counts = sorted(count_stats.items(), key=lambda x: x[1], reverse=True)
    print('count值分布 (前20):')
    for count_val, freq in sorted_counts[:20]:
        print(f'  count={count_val:3d}: {freq}次')

def rle_correct_decode():
    """正确的RLE解码"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 正确的RLE解码 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    f0 = struct.unpack('<I', res_data[4:8])[0]
    f1 = struct.unpack('<I', res_data[8:12])[0]
    compressed = res_data[f0+4:f1]
    
    # 根据统计，count=0时应该是64
    # 0xC0 & 0x3F = 0，但实际是64次重复
    print('尝试: 0xC0表示count=64')
    decoded = []
    i = 0
    while i < len(compressed):
        byte = compressed[i]
        if byte >= 0xC0:
            if i + 1 < len(compressed):
                count = byte & 0x3F
                if count == 0:
                    count = 64
                pixel = compressed[i + 1]
                decoded.extend([pixel] * count)
                i += 2
            else:
                break
        else:
            decoded.append(byte)
            i += 1
    
    print(f'解码像素: {len(decoded)} / 6400')
    if len(decoded) == 6400:
        print('*** 完美匹配! ***\n')
        
        # 保存并显示
        with open('output/frame0_decoded.bin', 'wb') as f:
            f.write(bytes(decoded))
        
        print('图像可视化 (前10行):')
        for row in range(10):
            pixels = decoded[row*80:(row+1)*80]
            # 使用ASCII字符可视化
            line = ''
            for p in pixels:
                if p < 20:
                    line += '.'
                elif p < 60:
                    line += '-'
                elif p < 100:
                    line += '+'
                elif p < 150:
                    line += '='
                else:
                    line += '#'
            print(f'  [{row:2d}] |{line}|')

def verify_all_3_frames():
    """验证3帧的解码"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 验证3帧解码 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    frames = [
        struct.unpack('<I', res_data[4:8])[0],
        struct.unpack('<I', res_data[8:12])[0],
        struct.unpack('<I', res_data[12:16])[0],
    ]
    
    for i in range(3):
        frame_off = frames[i]
        next_off = frames[i+1] if i < 2 else len(res_data)
        compressed = res_data[frame_off+4:next_off]
        
        # 解码
        decoded = []
        j = 0
        while j < len(compressed):
            byte = compressed[j]
            if byte >= 0xC0:
                if j + 1 < len(compressed):
                    count = compressed[j] & 0x3F
                    if count == 0:
                        count = 64
                    pixel = compressed[j + 1]
                    decoded.extend([pixel] * count)
                    j += 2
                else:
                    break
            else:
                decoded.append(byte)
                j += 1
        
        print(f'帧{i}: 压缩{len(compressed)}字节 -> 解码{len(decoded)}像素')
        if len(decoded) != 6400:
            print(f'  *** 不匹配! ***')

if __name__ == '__main__':
    try_correct_rle()
    rle_analysis()
    rle_correct_decode()
    verify_all_3_frames()
