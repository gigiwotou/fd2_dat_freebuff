import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

# 解析索引表
offsets = []
table_start = 6
for i in range(103):
    offset_addr = table_start + i * 4
    offset_val = struct.unpack_from('<I', data, offset_addr)[0]
    offsets.append(offset_val)

# 索引1详细分析
print('=== 索引 1 (24x24 Tile) ===')
res1_start = offsets[1]
res1_end = offsets[2]
res1 = data[res1_start:res1_end]

w, h = struct.unpack('<HH', res1[:4])
print(f'w={w}, h={h}')
print(f'前10字节 hex:', ' '.join(f'{b:02x}' for b in res1[:10]))

# 尝试不同的RLE起始偏移
for start_offset in [4, 5, 6, 7, 8]:
    rle_data = res1[start_offset:]
    
    # 解码
    pixels = []
    idx = 0
    while len(pixels) < w * h and idx < len(rle_data):
        if idx >= len(rle_data):
            break
        cmd = rle_data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:  # fill
            if count == 0:
                count = 1
            if idx < len(rle_data):
                val = rle_data[idx]
                idx += 1
                pixels.extend([val] * count)
        elif mode == 0x40:  # copy
            if count == 0:
                count = 1
            if idx + count <= len(rle_data):
                pixels.extend(rle_data[idx:idx+count])
                idx += count
        elif mode == 0x80:  # skip
            if count == 0:
                count = 1
            pixels.extend([0] * count)
    
    expected = w * h
    diff = len(pixels) - expected
    print(f'\nRLE从偏移{start_offset}: 解码{len(pixels)}像素 (预期{expected}, 差{diff:+d})')
    
    if abs(diff) <= 2:
        print('  *** 接近正确! ***')
        if len(pixels) == expected:
            # 打印前3行像素
            print('  前3行:')
            for row in range(3):
                line = ' '.join(f'{pixels[row*w+col]:02X}' for col in range(w))
                print(f'    Row {row}: {line}')

# 索引2分析
print(f'\n=== 索引 2 (37680字节) ===')
res2_start = offsets[2]
res2_end = offsets[3]
res2 = data[res2_start:res2_end]
print(f'大小: {len(res2)} 字节')

# 检查前16字节
print('前16字节 hex:', ' '.join(f'{b:02x}' for b in res2[:16]))

# 检查是否为偏移表
print('\n前12个4字节值:')
for i in range(12):
    val = struct.unpack('<I', res2[i*4:(i+1)*4])[0]
    print(f'  [{i}] = 0x{val:08X} ({val})')

# 检查是否每个4字节都是递增的偏移
print('\n偏移差值:')
prev = 0
for i in range(10):
    val = struct.unpack('<I', res2[i*4:(i+1)*4])[0]
    diff = val - prev if i > 0 else val
    print(f'  [{i}] = {val:8d}, 差 = {diff:8d}')
    prev = val

# 检查37680 / 24 = 1570 (24字节/图标?)
# 检查37680 / 32 = 1177.5 (不是整数)
# 检查37680 / 72 = 523.3 (24x24/8 = 72字节/图标)
# 检查37680 = 24 * 1570 (24字节/图标, 1570个图标)

# 检查前几个24字节块
print('\n前3个24字节块:')
for i in range(3):
    block = res2[i*24:(i+1)*24]
    hex_str = ' '.join(f'{b:02x}' for b in block)
    print(f'  Block {i}: {hex_str}')
