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

print('前16字节 hex:', ' '.join(f'{b:02x}' for b in res1[:16]))

# 尝试不同格式
print('\n尝试格式1: w:2 + h:2 + pal_win:1 = 5字节头')
w1 = struct.unpack('<H', res1[0:2])[0]
h1 = struct.unpack('<H', res1[2:4])[0]
pw1 = res1[4]
print(f'  w={w1}, h={h1}, pal_win={pw1}')
print(f'  RLE从偏移5开始: {" ".join(f"{b:02x}" for b in res1[5:12])}')

print('\n尝试格式2: w:2 + h:2 + pal_win:2 = 6字节头')
w2 = struct.unpack('<H', res1[0:2])[0]
h2 = struct.unpack('<H', res1[2:4])[0]
pw2 = struct.unpack('<H', res1[4:6])[0]
print(f'  w={w2}, h={h2}, pal_win={pw2}')
print(f'  RLE从偏移6开始: {" ".join(f"{b:02x}" for b in res1[6:13])}')

print('\n尝试格式3: w:1 + h:1 + pal_win:1 = 3字节头')
w3 = res1[0]
h3 = res1[1]
pw3 = res1[2]
print(f'  w={w3}, h={h3}, pal_win={pw3}')
print(f'  RLE从偏移3开始: {" ".join(f"{b:02x}" for b in res1[3:10])}')

# RLE解码测试 (从偏移5)
print('\n=== RLE解码测试 (从偏移5) ===')
rle_data = res1[5:]

def decode_rle(data, max_pixels):
    pixels = []
    idx = 0
    steps = 0
    while len(pixels) < max_pixels and idx < len(data) and steps < 100:
        cmd = data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:
            # 填充
            if idx < len(data):
                val = data[idx]
                idx += 1
                pixels.extend([val] * count)
                print(f'  cmd=0x{cmd:02X}: fill {count} x 0x{val:02X}')
        elif mode == 0x40:
            # 复制
            if idx + count <= len(data):
                chunk = data[idx:idx+count]
                pixels.extend(chunk)
                idx += count
                print(f'  cmd=0x{cmd:02X}: copy {count} bytes')
        elif mode == 0x80:
            # 跳过
            pixels.extend([0] * count)
            print(f'  cmd=0x{cmd:02X}: skip {count}')
        
        steps += 1
    
    return pixels

decoded5 = decode_rle(rle_data, 24*24)
print(f'解码像素数: {len(decoded5)}')

# RLE解码测试 (从偏移6)
print('\n=== RLE解码测试 (从偏移6) ===')
rle_data6 = res1[6:]

def decode_rle_v2(data, max_pixels):
    pixels = []
    idx = 0
    while len(pixels) < max_pixels and idx < len(data):
        cmd = data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:
            if idx < len(data):
                val = data[idx]
                idx += 1
                pixels.extend([val] * count)
        elif mode == 0x40:
            if idx + count <= len(data):
                pixels.extend(data[idx:idx+count])
                idx += count
        elif mode == 0x80:
            pixels.extend([0] * count)
    
    return pixels

decoded6 = decode_rle_v2(rle_data6, 24*24)
print(f'解码像素数: {len(decoded6)}')

if len(decoded6) == 576:
    print('解码成功! 前3行像素:')
    for row in range(3):
        line = ' '.join(f'{decoded6[row*24+col]:02X}' for col in range(24))
        print(f'  Row {row}: {line}')
