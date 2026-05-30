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

# 索引1: Tile图像 24x24
print('=== 索引 1 (Tile 24x24) ===')
res1_start = offsets[1]
res1_end = offsets[2]
res1 = data[res1_start:res1_end]
w, h = struct.unpack('<HH', res1[:4])
pal_win = res1[4]
rle_data = res1[5:]
print(f'w={w}, h={h}, palette_window={pal_win}')
print(f'RLE数据大小: {len(rle_data)}')

# 手动RLE解码
def decode_rle(data, w, h):
    pixels = []
    idx = 0
    while len(pixels) < w * h and idx < len(data):
        cmd = data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:
            # 填充模式
            if idx < len(data):
                val = data[idx]
                idx += 1
                pixels.extend([val] * count)
        elif mode == 0x40:
            # 复制模式
            if idx + count <= len(data):
                pixels.extend(data[idx:idx+count])
                idx += count
        elif mode == 0x80:
            # 跳过模式
            pixels.extend([0] * count)
    
    return pixels

decoded = decode_rle(rle_data, w, h)
print(f'解码像素数: {len(decoded)}')
if len(decoded) == w * h:
    print('解码成功!')
    # 打印前几行
    for row in range(min(5, h)):
        line = ' '.join(f'{decoded[row*w+col]:02X}' for col in range(w))
        print(f'  Row {row}: {line}')
else:
    print(f'解码失败! 预期 {w*h} 像素, 实际 {len(decoded)} 像素')

# 索引2: 检查是否为偏移表
print(f'\n=== 索引 2 (37680字节) ===')
res2_start = offsets[2]
res2_end = offsets[3]
res2 = data[res2_start:res2_end]

# 前几个4字节值
print('前12个4字节值 (可能是偏移表):')
for i in range(12):
    val = struct.unpack('<I', res2[i*4:(i+1)*4])[0]
    print(f'  offset[{i}] = 0x{val:08X} ({val})')

# 检查偏移是否规律
print('\n偏移差值:')
prev = 0
for i in range(10):
    val = struct.unpack('<I', res2[i*4:(i+1)*4])[0]
    diff = val - prev
    print(f'  [{i}] = {val}, 差 = {diff}')
    prev = val

# 最后一个偏移值
last_idx = (len(res2) // 4) - 1
last_val = struct.unpack('<I', res2[last_idx*4:(last_idx+1)*4])[0]
print(f'\n最后一个偏移值 (索引{last_idx}): 0x{last_val:08X} ({last_val})')
print(f'总偏移数: {len(res2) // 4}')
print(f'如果这是偏移表，资源数 = {(len(res2) // 4) - 1}')

# 检查res2是否本身就是嵌套DAT (LLLLLL格式)
if res2[:6] == b'LLLLLL':
    count = struct.unpack('<I', res2[6:10])[0]
    print(f'\n是嵌套DAT! 子资源数: {count}')
else:
    print(f'\n不是嵌套DAT格式')
    print(f'前6字节 hex: {res2[:6].hex(" ")}')
