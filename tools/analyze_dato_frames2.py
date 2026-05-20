import struct

def analyze_frame_structure():
    """深入分析DATO.DAT资源的帧结构"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== DATO.DAT 帧结构分析 ===\n')
    
    # 分析前5个资源
    for idx in range(5):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_size = off_end - off_start
        
        print(f'--- 资源 {idx} ---')
        print(f'资源范围: {hex(off_start)} - {hex(off_end)}, 总大小: {res_size} 字节\n')
        
        # 读取资源数据
        res_data = data[off_start:off_end]
        
        # 解析头部
        header_size = struct.unpack('<I', res_data[0:4])[0]
        frame0_off = struct.unpack('<I', res_data[4:8])[0]
        frame1_off = struct.unpack('<I', res_data[8:12])[0]
        frame2_off = struct.unpack('<I', res_data[12:16])[0]
        width = struct.unpack('<H', res_data[16:18])[0]
        height = struct.unpack('<H', res_data[18:20])[0]
        
        print(f'头部信息:')
        print(f'  头部大小: {header_size}')
        print(f'  宽度: {width}, 高度: {height}')
        print(f'  帧0偏移: {frame0_off} (0x{frame0_off:04X})')
        print(f'  帧1偏移: {frame1_off} (0x{frame1_off:04X})')
        print(f'  帧2偏移: {frame2_off} (0x{frame2_off:04X})')
        
        # 计算帧大小
        frame0_size = frame1_off - frame0_off
        frame1_size = frame2_off - frame1_off
        frame2_size = res_size - frame2_off
        
        print(f'\n帧大小:')
        print(f'  帧0: {frame0_size} 字节')
        print(f'  帧1: {frame1_size} 字节')
        print(f'  帧2: {frame2_size} 字节')
        print(f'  平均: {(frame0_size + frame1_size + frame2_size) / 3:.1f} 字节')
        
        # 验证: 80x80像素应该是6400字节
        expected_size = width * height
        print(f'  预期 (80x80): {expected_size} 字节')
        
        # 分析每帧的内容
        print(f'\n帧数据详细分析:')
        for frame_idx, frame_off in enumerate([frame0_off, frame1_off, frame2_off]):
            if frame_off < res_size:
                frame_data = res_data[frame_off:]
                
                # 尝试解析帧头
                print(f'\n  帧 {frame_idx} (偏移{frame_off}):')
                print(f'    前16字节: {frame_data[:16].hex()}')
                
                # 检查是否有帧头部
                # 尝试不同的偏移解释
                for header_guess in [0, 2, 4]:
                    pixel_start = header_guess
                    if len(frame_data) > pixel_start + 10:
                        # 检查像素数据范围
                        pixels = frame_data[pixel_start:pixel_start+100]
                        min_val = min(pixels)
                        max_val = max(pixels)
                        print(f'    假设帧头{header_guess}字节 - 像素数据范围: [{min_val}, {max_val}]')
        
        # 检查是否还有其他帧偏移在头部
        print(f'\n  检查头部中是否有更多偏移值:')
        print(f'    头部16-48字节 (以DWORD为单位):')
        for i in range(4, 12):
            if i * 4 + 4 <= len(res_data):
                val = struct.unpack('<I', res_data[i*4:i*4+4])[0]
                if val > 0 and val < res_size:
                    print(f'      [{i*4}] {val} (0x{val:04X}) <- 可能是帧偏移')
                else:
                    print(f'      [{i*4}] {val} (0x{val:08X})')
        
        print('\n' + '='*70 + '\n')

def verify_4frame_structure():
    """验证4帧结构"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== 验证4帧结构 ===\n')
    
    # 分析资源0
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_size = off_end - off_start
    
    res_data = data[off_start:off_end]
    
    # 解析头部
    header_size = struct.unpack('<I', res_data[0:4])[0]
    frame0_off = struct.unpack('<I', res_data[4:8])[0]
    frame1_off = struct.unpack('<I', res_data[8:12])[0]
    frame2_off = struct.unpack('<I', res_data[12:16])[0]
    width = struct.unpack('<H', res_data[16:18])[0]
    height = struct.unpack('<H', res_data[18:20])[0]
    
    # 假设字节20-23是帧3的偏移
    if len(res_data) > 24:
        frame3_off = struct.unpack('<I', res_data[20:24])[0]
        print(f'如果字节20-23是帧3偏移: {frame3_off} (0x{frame3_off:08X})')
        if frame3_off < res_size:
            frame3_size = res_size - frame3_off
            print(f'  帧3大小: {frame3_size} 字节')
    
    # 计算已知的3帧
    frames = [
        ('帧0', frame0_off, frame1_off - frame0_off),
        ('帧1', frame1_off, frame2_off - frame1_off),
        ('帧2', frame2_off, res_size - frame2_off),
    ]
    
    print(f'\n已知的3帧:')
    for name, off, size in frames:
        print(f'  {name}: 偏移={off}, 大小={size} 字节')
    
    # 检查是否有第4帧的线索
    # 在字节20之后寻找可能的偏移值
    print(f'\n搜索字节20-48范围内可能的帧3偏移:')
    for i in range(20, 48, 4):
        if i + 4 <= len(res_data):
            val = struct.unpack('<I', res_data[i:i+4])[0]
            if 0 < val < res_size and val > frame2_off:
                print(f'  字节[{i}:{i+4}]: {val} (0x{val:04X}) <- 可能是帧3偏移')
                frame3_size = res_size - val
                print(f'    如果是帧3，大小={frame3_size} 字节')

if __name__ == '__main__':
    analyze_frame_structure()
    print('\n\n')
    verify_4frame_structure()
