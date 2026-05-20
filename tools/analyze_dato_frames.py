import struct

def analyze_dato_frames():
    """分析DATO.DAT头像资源的帧结构"""
    with open('game/DATO.DAT', 'rb') as f:
        data = f.read()
    
    # 文件头
    magic = data[0:6]
    count = struct.unpack('<I', data[6:10])[0]
    print(f'DATO.DAT: 文件头={magic}, 资源数量={count}')
    print(f'文件总大小: {len(data)} 字节\n')
    
    # 分析前5个资源的详细结构
    for idx in range(min(5, count - 1)):
        off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
        off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
        res_size = off_end - off_start
        
        print(f'=== 资源 {idx} ===')
        print(f'偏移: {hex(off_start)} - {hex(off_end)}, 大小: {res_size} 字节')
        
        # 读取头部数据
        res_data = data[off_start:off_end]
        
        # 尝试不同的头部解释
        print(f'\n头部数据前48字节 (16进制):')
        for i in range(0, min(48, len(res_data)), 16):
            hex_str = res_data[i:i+16].hex()
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
            print(f'  [{i:3d}] {hex_str}  {ascii_str}')
        
        # 尝试解释为20字节头部 + 像素数据
        print(f'\n假设1: 20字节头部 + 单帧像素数据')
        w1 = struct.unpack('<h', res_data[16:18])[0]
        h1 = struct.unpack('<h', res_data[18:20])[0]
        pixel_size1 = w1 * h1
        remaining1 = res_size - 20
        print(f'  字节16-17 (宽): {w1}')
        print(f'  字节18-19 (高): {h1}')
        print(f'  预期像素大小: {pixel_size1} 字节 ({w1}x{h1})')
        print(f'  剩余数据: {remaining1} 字节')
        if remaining1 > 0:
            print(f'  剩余数据 / 预期像素: {remaining1 / pixel_size1 if pixel_size1 > 0 else 0:.2f} 倍')
        
        # 尝试解释为可能的帧偏移表
        print(f'\n假设2: 头部包含帧偏移表')
        print(f'  前8个DWORD值:')
        for i in range(8):
            if i * 4 + 4 <= len(res_data):
                val = struct.unpack('<I', res_data[i*4:i*4+4])[0]
                print(f'    偏移{i*4}: {val} (0x{val:08X})')
        
        # 尝试4帧结构
        print(f'\n假设3: 4帧动画结构')
        # 检查字节0-3是否为帧数或某种计数
        frame_count = struct.unpack('<I', res_data[0:4])[0]
        print(f'  字节0-3: {frame_count}')
        
        # 检查是否有4个帧偏移 (从字节4开始)
        print(f'  检查字节4-19作为4个帧偏移:')
        frame_offsets = []
        for i in range(4):
            if 4 + i*4 + 4 <= len(res_data):
                offset = struct.unpack('<I', res_data[4+i*4:4+i*4+4])[0]
                frame_offsets.append(offset)
                print(f'    帧{i}偏移: {offset} (0x{offset:08X})')
        
        # 验证帧偏移是否合理
        if frame_offsets and all(0 < off < res_size for off in frame_offsets):
            print(f'  帧偏移都在资源范围内')
            # 检查帧大小是否一致
            frame_sizes = []
            for i in range(4):
                if i < 3:
                    size = frame_offsets[i+1] - frame_offsets[i]
                else:
                    size = res_size - frame_offsets[i]
                frame_sizes.append(size)
            print(f'  帧大小: {frame_sizes}')
            if len(set(frame_sizes)) == 1:
                print(f'  *** 所有帧大小相同: {frame_sizes[0]} 字节 ***')
                # 检查每帧是否有相同的头部
                for i in range(4):
                    w = struct.unpack('<h', res_data[frame_offsets[i]+0:frame_offsets[i]+2])[0]
                    h = struct.unpack('<h', res_data[frame_offsets[i]+2:frame_offsets[i]+4])[0]
                    print(f'    帧{i}: {w}x{h}')
        
        # 尝试等分4帧
        print(f'\n假设4: 资源等分为4帧')
        header_size = 0  # 假设没有头部
        pixel_data_size = res_size - header_size
        frame_size = pixel_data_size // 4
        remainder = pixel_data_size % 4
        print(f'  总数据: {res_size} 字节')
        print(f'  每帧大小: {frame_size} 字节')
        print(f'  余数: {remainder}')
        if remainder == 0:
            sqrt = int(frame_size ** 0.5)
            if sqrt * sqrt == frame_size:
                print(f'  *** 每帧是 {sqrt}x{sqrt} 的完美正方形 ***')
            # 检查是否是80x80
            if frame_size == 80 * 80:
                print(f'  *** 每帧正好是 80x80 像素! ***')
        
        print('\n' + '='*60 + '\n')

if __name__ == '__main__':
    analyze_dato_frames()
