import struct

def analyze_rle_compression():
    """分析帧数据是否使用RLE压缩"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== 分析帧数据压缩格式 ===\n')
    
    # 分析资源0的帧0
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    frame0_off = struct.unpack('<I', res_data[4:8])[0]
    frame1_off = struct.unpack('<I', res_data[8:12])[0]
    frame0_size = frame1_off - frame0_off
    
    # 帧数据
    frame_data = res_data[frame0_off:]
    
    print(f'帧0大小: {frame0_size} 字节')
    print(f'帧头部: 20字节')
    print(f'帧数据: {frame0_size - 20} 字节\n')
    
    # 如果80x80像素=6400字节，但帧只有~3163字节
    # 说明数据被压缩了！
    print(f'80x80原始像素: 6400 字节')
    print(f'实际帧数据: {frame0_size - 20} 字节')
    print(f'压缩比: {(frame0_size - 20) / 6400 * 100:.1f}%\n')
    
    # 显示帧数据（跳过20字节头部）
    compressed = frame_data[20:20+100]
    print(f'压缩数据前100字节:')
    for i in range(0, 100, 16):
        chunk = compressed[i:i+16]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        print(f'  [{i:3d}] {hex_str}')
    
    # 尝试不同的RLE解码
    print(f'\n尝试RLE解码方案1: (count, pixel) 格式')
    decoded = []
    i = 0
    while i < len(compressed) and len(decoded) < 160:
        count = compressed[i]
        if i + 1 < len(compressed):
            pixel = compressed[i + 1]
            decoded.extend([pixel] * count)
            i += 2
        else:
            break
    print(f'  解码前80像素 (第一行): {decoded[:80]}')
    print(f'  消耗压缩数据: {i} 字节')
    
    print(f'\n尝试RLE解码方案2: (pixel, count) 格式')
    decoded2 = []
    i = 0
    while i < len(compressed) and len(decoded2) < 160:
        pixel = compressed[i]
        if i + 1 < len(compressed):
            count = compressed[i + 1]
            decoded2.extend([pixel] * count)
            i += 2
        else:
            break
    print(f'  解码前80像素 (第一行): {decoded2[:80]}')
    print(f'  消耗压缩数据: {i} 字节')
    
    # 尝试方案3: 0x00是转义符
    print(f'\n尝试RLE解码方案3: 0xC0+是转义符，后面跟(count, pixel)')
    decoded3 = []
    i = 0
    while i < len(compressed) and len(decoded3) < 160:
        byte = compressed[i]
        if byte >= 0xC0:  # 转义符
            if i + 2 < len(compressed):
                count = compressed[i + 1]
                pixel = compressed[i + 2]
                decoded3.extend([pixel] * count)
                i += 3
            else:
                break
        else:
            decoded3.append(byte)
            i += 1
    print(f'  解码前80像素 (第一行): {decoded3[:80]}')
    print(f'  消耗压缩数据: {i} 字节')

def check_all_frames_same():
    """检查所有3帧是否相同"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 检查3帧是否相同 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    frames = [
        struct.unpack('<I', res_data[4:8])[0],
        struct.unpack('<I', res_data[8:12])[0],
        struct.unpack('<I', res_data[12:16])[0],
    ]
    
    for i, off in enumerate(frames):
        size = (frames[i+1] if i < 2 else len(res_data)) - off
        print(f'帧{i} 偏移={off}, 大小={size}')
    
    # 比较3帧的数据
    frame0_data = res_data[frames[0]:frames[0]+50]
    frame1_data = res_data[frames[1]:frames[1]+50]
    frame2_data = res_data[frames[2]:frames[2]+50]
    
    print(f'\n帧0前50字节: {frame0_data.hex()}')
    print(f'帧1前50字节: {frame1_data.hex()}')
    print(f'帧2前50字节: {frame2_data.hex()}')
    
    print(f'\n帧0 == 帧1: {frame0_data == frame1_data}')
    print(f'帧1 == 帧2: {frame1_data == frame2_data}')

def try_decode_full_frame():
    """尝试完整解码一帧"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 尝试完整解码一帧 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    frame0_off = struct.unpack('<I', res_data[4:8])[0]
    frame1_off = struct.unpack('<I', res_data[8:12])[0]
    frame_size = frame1_off - frame0_off
    
    # 跳过帧头部20字节
    compressed = res_data[frame0_off + 20:frame0_off + frame_size]
    
    print(f'压缩数据大小: {len(compressed)} 字节')
    print(f'目标: 6400像素 (80x80)\n')
    
    # 方案3的详细解码
    decoded = []
    i = 0
    escaped_runs = 0
    literal_count = 0
    
    while i < len(compressed):
        byte = compressed[i]
        if byte >= 0xC0:  # 转义符
            if i + 2 < len(compressed):
                count = compressed[i + 1]
                pixel = compressed[i + 2]
                decoded.extend([pixel] * count)
                i += 3
                escaped_runs += 1
            else:
                break
        else:
            decoded.append(byte)
            i += 1
            literal_count += 1
    
    print(f'解码结果:')
    print(f'  总像素: {len(decoded)}')
    print(f'  预期: 6400')
    print(f'  字面量: {literal_count}')
    print(f'  RLE序列: {escaped_runs}')
    
    if len(decoded) == 6400:
        print(f'\n*** 成功解码! ***')
        # 保存为图像查看
        with open('output/frame0_decoded.bin', 'wb') as f:
            f.write(bytes(decoded))
        print(f'已保存到 output/frame0_decoded.bin')
        
        # 显示前几行
        print(f'\n前3行像素:')
        for row in range(3):
            pixels = decoded[row*80:(row+1)*80]
            print(f'  行{row}: {pixels[:40]}...')
    else:
        print(f'\n解码像素数不匹配: {len(decoded)} vs 6400')

if __name__ == '__main__':
    analyze_rle_compression()
    check_all_frames_same()
    try_decode_full_frame()
