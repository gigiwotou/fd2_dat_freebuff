import struct

def verify_correct_structure():
    """验证正确的帧结构"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('=== 验证正确的帧结构 ===\n')
    
    # 关键发现: 字节0是头部大小=16，不是帧偏移
    # 所以只有3个帧偏移在字节4,8,12
    
    idx = 0
    off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    res_data = data[off_start:off_end]
    
    print(f'资源{idx} 完整头部 (前24字节):')
    for i in range(0, 24, 4):
        dword = struct.unpack('<I', res_data[i:i+4])[0]
        print(f'  [{i:3d}-{i+3:3d}] {dword:10d} (0x{dword:08X})')
    
    print(f'\n解释:')
    print(f'  [0-3]   头部大小 = {struct.unpack("<I", res_data[0:4])[0]}')
    print(f'  [4-7]   帧0偏移  = {struct.unpack("<I", res_data[4:8])[0]}')
    print(f'  [8-11]  帧1偏移  = {struct.unpack("<I", res_data[8:12])[0]}')
    print(f'  [12-15] 帧2偏移  = {struct.unpack("<I", res_data[12:16])[0]}')
    print(f'  [16-17] 宽度     = {struct.unpack("<H", res_data[16:18])[0]}')
    print(f'  [18-19] 高度     = {struct.unpack("<H", res_data[18:20])[0]}')
    
    f0 = struct.unpack('<I', res_data[4:8])[0]
    f1 = struct.unpack('<I', res_data[8:12])[0]
    f2 = struct.unpack('<I', res_data[12:16])[0]
    
    print(f'\n帧数据:')
    print(f'  帧0: 偏移{f0}, 大小{f1-f0} (包含4字节宽高 + 压缩数据)')
    print(f'  帧1: 偏移{f1}, 大小{f2-f1} (包含4字节宽高 + 压缩数据)')
    print(f'  帧2: 偏移{f2}, 大小{len(res_data)-f2} (包含4字节宽高 + 压缩数据)')
    
    print(f'\n字节20之后是什么?')
    bytes_20 = res_data[20:40]
    print(f'  字节20-39: {bytes_20.hex()}')
    print(f'  这应该是帧0的像素数据(从帧0偏移+4开始)')
    
    # 验证: 帧0的像素数据从 f0+4 开始
    frame0_pixel_start = f0 + 4
    print(f'\n帧0像素数据起始: {frame0_pixel_start}')
    print(f'帧0像素数据前20字节: {res_data[frame0_pixel_start:frame0_pixel_start+20].hex()}')
    
    # 字节20-39是否等于帧0的像素数据?
    if bytes_20 == res_data[frame0_pixel_start:frame0_pixel_start+20]:
        print(f'*** 字节20 = 帧0像素数据起始! ***')
        print(f'这意味着头部大小16是正确的，像素数据从字节20开始')
        print(f'但头部包含3个帧偏移，所以只有3帧')

def search_4frame_resources():
    """搜索可能有4帧的资源"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 搜索可能有4帧的资源 ===\n')
    
    count = struct.unpack('<I', data[6:10])[0]
    print(f'总资源数: {count}\n')
    
    four_frame_count = 0
    three_frame_count = 0
    
    for idx in range(min(100, count - 1)):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_data = data[off_start:off_end]
        
        if len(res_data) < 24:
            continue
        
        header_size = struct.unpack('<I', res_data[0:4])[0]
        
        # 如果头部大小 > 16，可能有更多帧偏移
        if header_size > 16:
            num_offsets = (header_size - 16) // 4
            print(f'资源{idx:3d}: 头部大小={header_size}, 可能有{num_offsets}个帧偏移')
            
            # 解析所有偏移
            offsets = []
            for i in range(num_offsets):
                pos = 4 + i * 4
                if pos + 4 <= len(res_data):
                    offset = struct.unpack('<I', res_data[pos:pos+4])[0]
                    offsets.append(offset)
            
            if offsets:
                print(f'          偏移: {offsets[:6]}...')
            four_frame_count += 1
        elif header_size == 16:
            three_frame_count += 1
    
    print(f'\n统计:')
    print(f'  3帧资源 (头部=16): {three_frame_count}')
    print(f'  头部>16的资源: {four_frame_count}')

def analyze_header_size_20():
    """分析头部大小=20的资源"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 分析头部大小=20的资源 ===\n')
    
    count = struct.unpack('<I', data[6:10])[0]
    
    for idx in range(count - 1):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_data = data[off_start:off_end]
        
        if len(res_data) < 24:
            continue
        
        header_size = struct.unpack('<I', res_data[0:4])[0]
        
        if header_size == 20:
            print(f'找到资源{idx}: 头部大小=20')
            # 解析
            f0 = struct.unpack('<I', res_data[4:8])[0]
            f1 = struct.unpack('<I', res_data[8:12])[0]
            f2 = struct.unpack('<I', res_data[12:16])[0]
            f3 = struct.unpack('<I', res_data[16:20])[0]
            width = struct.unpack('<H', res_data[20:22])[0]
            height = struct.unpack('<H', res_data[22:24])[0]
            
            print(f'  帧0={f0}, 帧1={f1}, 帧2={f2}, 帧3={f3}')
            print(f'  宽高={width}x{height}')
            break

def final_analysis():
    """最终分析"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    print('\n\n=== 最终分析：帧数统计 ===\n')
    
    count = struct.unpack('<I', data[6:10])[0]
    
    header_sizes = {}
    
    for idx in range(count - 1):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_data = data[off_start:off_end]
        
        if len(res_data) < 4:
            continue
        
        header_size = struct.unpack('<I', res_data[0:4])[0]
        header_sizes[header_size] = header_sizes.get(header_size, 0) + 1
    
    print('头部大小分布:')
    for size, freq in sorted(header_sizes.items()):
        num_frames = (size - 16) // 4 if size >= 16 else 0
        print(f'  头部大小={size:3d}: {freq:4d}个资源 ({num_frames}帧)')

if __name__ == '__main__':
    verify_correct_structure()
    search_4frame_resources()
    analyze_header_size_20()
    final_analysis()
