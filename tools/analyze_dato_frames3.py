import struct

def find_all_frame_offsets():
    """找出所有4帧的偏移位置"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== 寻找所有4帧的偏移 ===\n')
    
    # 分析资源0
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_size = off_end - off_start
    
    res_data = data[off_start:off_end]
    
    print(f'资源 {idx}: 大小={res_size} 字节')
    print(f'\n完整头部数据 (前64字节):')
    for i in range(0, 64, 16):
        hex_str = res_data[i:i+16].hex()
        print(f'  [{i:3d}] {hex_str}')
    
    print(f'\n以DWORD解析前64字节:')
    for i in range(16):
        if i * 4 + 4 <= len(res_data):
            val = struct.unpack('<I', res_data[i*4:i*4+4])[0]
            word0 = struct.unpack('<H', res_data[i*4:i*4+2])[0]
            word1 = struct.unpack('<H', res_data[i*4+2:i*4+4])[0]
            print(f'  [{i*4:3d}] DWORD={val:10d} (0x{val:08X}), WORDs=({word0}, {word1})')
    
    # 已知结构:
    # [0-3] = 头部大小 = 16
    # [4-7] = 帧0偏移 = 3165
    # [8-11] = 帧1偏移 = 6328  
    # [12-15] = 帧2偏移 = 9512
    # [16-17] = 宽度 = 80
    # [18-19] = 高度 = 80
    
    # 寻找帧3偏移
    # 应该在字节20之后，或者可能是隐含的
    print(f'\n验证已知的3帧:')
    frame_off_0 = struct.unpack('<I', res_data[4:8])[0]
    frame_off_1 = struct.unpack('<I', res_data[8:12])[0]
    frame_off_2 = struct.unpack('<I', res_data[12:16])[0]
    
    frame_size_0 = frame_off_1 - frame_off_0
    frame_size_1 = frame_off_2 - frame_off_1
    remaining_after_2 = res_size - frame_off_2
    
    print(f'  帧0: 偏移={frame_off_0}, 大小={frame_size_0}')
    print(f'  帧1: 偏移={frame_off_1}, 大小={frame_size_1}')
    print(f'  帧2: 偏移={frame_off_2}, 大小={remaining_after_2} (到文件末尾)')
    
    # 假设字节20-23是帧3偏移
    print(f'\n假设字节20-23是帧3偏移:')
    if len(res_data) >= 24:
        frame_off_3 = struct.unpack('<I', res_data[20:24])[0]
        print(f'  帧3偏移 = {frame_off_3} (0x{frame_off_3:08X})')
        print(f'  是否有效: {0 < frame_off_3 < res_size}')
        
        if 0 < frame_off_3 < res_size:
            print(f'  *** 找到第4帧! ***')
            print(f'  帧3大小 = {res_size - frame_off_3}')
            
            # 检查4帧大小是否一致
            print(f'\n4帧大小对比:')
            print(f'  帧0: {frame_size_0} 字节')
            print(f'  帧1: {frame_size_1} 字节')
            print(f'  帧2: {frame_off_3 - frame_off_2} 字节')
            print(f'  帧3: {res_size - frame_off_3} 字节')
    
    # 尝试另一种解释: 只有3个显式偏移，第4帧隐含在末尾
    print(f'\n\n另一种假设: 只有3帧')
    print(f'  帧0: {frame_size_0} 字节')
    print(f'  帧1: {frame_size_1} 字节')
    print(f'  帧2: {remaining_after_2} 字节')
    print(f'  总计: {frame_size_0 + frame_size_1 + remaining_after_2} 字节')
    
    # 验证像素数据
    print(f'\n检查每帧的像素数据:')
    expected_pixel_size = 80 * 80  # 6400
    
    for i, off in enumerate([frame_off_0, frame_off_1, frame_off_2]):
        print(f'\n  帧{i} 起始于偏移{off}:')
        # 检查前几个字节
        chunk = res_data[off:off+20]
        print(f'    前20字节: {chunk.hex()}')
        
        # 检查是否有帧头部
        # 假设帧数据就是像素索引
        pixels = res_data[off:off+expected_pixel_size]
        if len(pixels) == expected_pixel_size:
            min_val = min(pixels)
            max_val = max(pixels)
            unique = len(set(pixels))
            print(f'    6400字节像素数据: 范围=[{min_val},{max_val}], 唯一值={unique}')

def check_multiple_resources():
    """检查多个资源来验证帧结构"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 检查多个资源的帧结构 ===\n')
    
    for idx in range(10):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_size = off_end - off_start
        
        res_data = data[off_start:off_end]
        
        if len(res_data) < 24:
            continue
        
        header = struct.unpack('<I', res_data[0:4])[0]
        f0 = struct.unpack('<I', res_data[4:8])[0]
        f1 = struct.unpack('<I', res_data[8:12])[0]
        f2 = struct.unpack('<I', res_data[12:16])[0]
        w = struct.unpack('<H', res_data[16:18])[0]
        h = struct.unpack('<H', res_data[18:20])[0]
        f3_candidate = struct.unpack('<I', res_data[20:24])[0]
        
        print(f'资源{idx:2d}: 大小={res_size:6d}, 头={header}, 帧0={f0:5d}, 帧1={f1:5d}, 帧2={f2:5d}, 帧3候选={f3_candidate:5d}, {w}x{h}')
        
        # 检查帧3候选是否有效
        if 0 < f3_candidate < res_size and f3_candidate > f2:
            frame2_size = f3_candidate - f2
            frame3_size = res_size - f3_candidate
            print(f'          -> 如果帧3有效: 帧2大小={frame2_size}, 帧3大小={frame3_size}')
            # 检查4帧大小是否相近
            sizes = [f1-f0, f2-f1, frame2_size, frame3_size]
            avg = sum(sizes) / len(sizes)
            variance = sum((s - avg)**2 for s in sizes) / len(sizes)
            print(f'          -> 4帧大小: {sizes}, 平均={avg:.0f}, 方差={variance:.0f}')

if __name__ == '__main__':
    find_all_frame_offsets()
    check_multiple_resources()
