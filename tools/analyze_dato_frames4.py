import struct

def deep_frame_analysis():
    """深度分析帧结构 - 每帧都有重复的头部"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== DATO.DAT 帧深度分析 ===\n')
    print('关键发现：每帧开头都有 50005000 (80x80 的 WORD 表示)\n')
    
    # 分析资源0
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_size = off_end - off_start
    
    res_data = data[off_start:off_end]
    
    # 解析文件级头部
    header_size = struct.unpack('<I', res_data[0:4])[0]
    frame0_off = struct.unpack('<I', res_data[4:8])[0]
    frame1_off = struct.unpack('<I', res_data[8:12])[0]
    frame2_off = struct.unpack('<I', res_data[12:16])[0]
    width = struct.unpack('<H', res_data[16:18])[0]
    height = struct.unpack('<H', res_data[18:20])[0]
    
    print(f'资源级头部 (20字节):')
    print(f'  [0-3]   头部大小/未知: {header_size}')
    print(f'  [4-7]   帧0偏移: {frame0_off}')
    print(f'  [8-11]  帧1偏移: {frame1_off}')
    print(f'  [12-15] 帧2偏移: {frame2_off}')
    print(f'  [16-17] 宽度: {width}')
    print(f'  [18-19] 高度: {height}')
    print(f'  注意: 只有3个帧偏移!\n')
    
    # 分析每帧
    frames_offsets = [frame0_off, frame1_off, frame2_off]
    
    for i, frame_off in enumerate(frames_offsets):
        print(f'\n--- 帧 {i} (偏移 {frame_off}) ---')
        
        # 读取帧数据
        frame_data = res_data[frame_off:]
        
        # 显示帧头部
        print(f'帧数据前32字节:')
        for j in range(0, 32, 16):
            chunk = frame_data[j:j+16]
            hex_str = chunk.hex()
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f'  [{j:3d}] {hex_str}  {ascii_str}')
        
        # 解析帧头部
        if len(frame_data) >= 20:
            # 检查前4字节是否是 50005000 (80x80)
            frame_magic = struct.unpack('<I', frame_data[0:4])[0]
            frame_w = struct.unpack('<H', frame_data[0:2])[0]
            frame_h = struct.unpack('<H', frame_data[2:4])[0]
            
            print(f'\n帧头部解析:')
            print(f'  [0-1]   宽度: {frame_w}')
            print(f'  [2-3]   高度: {frame_h}')
            print(f'  [0-3]   魔数: 0x{frame_magic:08X} ({frame_magic})')
            
            # 检查后续字节
            if len(frame_data) >= 20:
                bytes_4_7 = struct.unpack('<I', frame_data[4:8])[0]
                bytes_8_11 = struct.unpack('<I', frame_data[8:12])[0]
                bytes_12_15 = struct.unpack('<I', frame_data[12:16])[0]
                bytes_16_19 = struct.unpack('<I', frame_data[16:20])[0]
                
                print(f'  [4-7]   未知: 0x{bytes_4_7:08X}')
                print(f'  [8-11]  未知: 0x{bytes_8_11:08X}')
                print(f'  [12-15] 未知: 0x{bytes_12_15:08X}')
                print(f'  [16-19] 未知: 0x{bytes_16_19:08X}')
                
                # 像素数据从哪开始？
                # 检查字节20后的数据
                pixel_data = frame_data[20:20+100]
                min_val = min(pixel_data)
                max_val = max(pixel_data)
                print(f'\n  像素数据 (从字节20开始):')
                print(f'    范围: [{min_val}, {max_val}]')
                print(f'    前16字节: {pixel_data[:16].hex()}')
        
        # 计算帧大小
        if i < 2:
            frame_size = frames_offsets[i+1] - frame_off
        else:
            frame_size = res_size - frame_off
        
        print(f'\n帧大小: {frame_size} 字节')
        expected_pixels = width * height  # 6400
        print(f'预期像素大小: {expected_pixels} (80x80)')
        print(f'剩余字节: {frame_size - 20} (减去帧头部)')
    
    # 总结结构
    print(f'\n\n=== 结构总结 ===')
    print(f'资源格式:')
    print(f'  [0-3]   DWORD: 未知值 (通常是16)')
    print(f'  [4-7]   DWORD: 帧0相对偏移')
    print(f'  [8-11]  DWORD: 帧1相对偏移')
    print(f'  [12-15] DWORD: 帧2相对偏移')
    print(f'  [16-17] WORD:  宽度 (80)')
    print(f'  [18-19] WORD:  高度 (80)')
    print(f'\n每帧格式 (从偏移开始):')
    print(f'  [0-1]   WORD:  宽度 (80)')
    print(f'  [2-3]   WORD:  高度 (80)')
    print(f'  [4-19]  16字节: 未知数据')
    print(f'  [20-...] 像素索引数据 (8位，80*80=6400字节)')
    
    print(f'\n\n=== 验证像素数据 ===')
    for i, frame_off in enumerate(frames_offsets):
        frame_data = res_data[frame_off + 20:]  # 跳过帧头部
        if len(frame_data) >= 6400:
            pixels = frame_data[:6400]
            print(f'帧{i}: 像素范围=[{min(pixels)},{max(pixels)}], 唯一值={len(set(pixels))}')
            # 检查是否有明显图像特征
            # 第一行
            row0 = pixels[:80]
            print(f'     第一行前20像素: {list(row0[:20])}')

if __name__ == '__main__':
    deep_frame_analysis()
