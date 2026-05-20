import struct

def analyze_rle_v2():
    """分析RLE格式 - 使用不同的转义方案"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== RLE压缩格式详细分析 v2 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    frame0_off = struct.unpack('<I', res_data[4:8])[0]
    frame1_off = struct.unpack('<I', res_data[8:12])[0]
    
    # 压缩数据
    compressed = res_data[frame0_off + 20:frame1_off]
    print(f'压缩数据: {len(compressed)} 字节')
    print(f'目标: 6400 像素\n')
    
    # 方案4: 0xC0-0xFF 是转义符，格式 (0xC0+count, pixel)
    # count = byte & 0x3F
    print('方案4: 0xC0-0xFF是RLE，count=byte&0x3F，后面跟pixel')
    decoded = []
    i = 0
    while i < len(compressed) and len(decoded) < 6400:
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
    
    print(f'  解码像素: {len(decoded)} / 6400')
    print(f'  消耗: {i} / {len(compressed)} 字节')
    if len(decoded) == 6400:
        print('  *** 完全匹配! ***')
    
    # 方案5: 0xFE/0xFF 是转义符
    print('\n方案5: 0xFE是转义符，后面跟2字节(count, pixel)')
    decoded = []
    i = 0
    while i < len(compressed) and len(decoded) < 6400:
        byte = compressed[i]
        if byte == 0xFE:
            if i + 2 < len(compressed):
                count = compressed[i + 1]
                pixel = compressed[i + 2]
                decoded.extend([pixel] * count)
                i += 3
            else:
                break
        elif byte == 0xFF:
            if i + 2 < len(compressed):
                count = compressed[i + 1]
                pixel = compressed[i + 2]
                decoded.extend([pixel] * count)
                i += 3
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
        print('  已保存到 output/frame0_decoded.bin')
        
        # 显示前80像素作为图像行
        print(f'\n前3行 (80像素/行):')
        for row in range(3):
            pixels = decoded[row*80:(row+1)*80]
            # 转换为ASCII可视化
            line = ''.join('.' if p < 32 else chr(33 + (p * 90 // 255)) for p in pixels)
            print(f'  行{row:2d}: {line}')
    
    # 方案6: 分析压缩数据，查找模式
    print('\n\n方案6: 分析压缩数据统计')
    byte_counts = [0] * 256
    for b in compressed:
        byte_counts[b] += 1
    
    print('高频字节 (前20):')
    sorted_bytes = sorted(enumerate(byte_counts), key=lambda x: x[1], reverse=True)
    for byte_val, count in sorted_bytes[:20]:
        pct = count / len(compressed) * 100
        print(f'  0x{byte_val:02X} ({byte_val:3d}): {count:5d}次 ({pct:.1f}%)')
    
    # 查看0xFE后的模式
    print('\n0xFE后的字节模式:')
    fe_patterns = {}
    i = 0
    while i < len(compressed) - 2:
        if compressed[i] == 0xFE:
            pattern = (compressed[i+1], compressed[i+2])
            fe_patterns[pattern] = fe_patterns.get(pattern, 0) + 1
            i += 3
        else:
            i += 1
    
    print('最常见的(count, pixel)对:')
    sorted_patterns = sorted(fe_patterns.items(), key=lambda x: x[1], reverse=True)
    for (count, pixel), freq in sorted_patterns[:10]:
        print(f'  count={count:3d}, pixel={pixel:3d}: {freq}次')

def analyze_frame_structure_alternative():
    """分析帧结构的另一种可能性：数据不是RLE"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 帧结构替代分析 ===\n')
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    # 显示完整的资源头部和第一帧
    print('完整资源头部 (前100字节):')
    for i in range(0, 100, 16):
        chunk = res_data[i:i+16]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        print(f'  [{i:3d}] {hex_str}')
    
    # 帧偏移表在4,8,12
    f0 = struct.unpack('<I', res_data[4:8])[0]
    f1 = struct.unpack('<I', res_data[8:12])[0]
    f2 = struct.unpack('<I', res_data[12:16])[0]
    
    print(f'\n帧0: {f0}, 帧1: {f1}, 帧2: {f2}')
    print(f'帧0大小: {f1-f0}, 帧1大小: {f2-f1}, 帧2大小: {len(res_data)-f2}')
    
    # 检查头部字节16-19
    bytes_16_19 = struct.unpack('<I', res_data[16:20])[0]
    print(f'\n字节16-19 (DWORD): {bytes_16_19} (0x{bytes_16_19:08X})')
    print(f'  这正好是 0x00500050 = 80x80 (宽度,高度)')
    
    # 假设帧数据就是压缩数据，没有额外帧头部
    print(f'\n假设: 帧数据从偏移直接开始，没有帧头部')
    frame_data = res_data[f0:f1]
    print(f'帧0数据大小: {len(frame_data)} 字节')
    print(f'前16字节: {frame_data[:16].hex()}')
    print(f'前16字节分解:')
    for i in range(16):
        print(f'  [{i}] 0x{frame_data[i]:02X} ({frame_data[i]:3d})', end='')
        if (i + 1) % 4 == 0:
            print()
    
    # 检查是否有4帧的迹象
    # 也许偏移表在字节0,4,8,12而不是4,8,12
    print(f'\n假设: 字节0是帧0偏移')
    f0_alt = struct.unpack('<I', res_data[0:4])[0]
    print(f'  帧0偏移: {f0_alt}')
    if f0_alt < len(res_data):
        print(f'  帧0数据前16字节: {res_data[f0_alt:f0_alt+16].hex()}')

if __name__ == '__main__':
    analyze_rle_v2()
    analyze_frame_structure_alternative()
