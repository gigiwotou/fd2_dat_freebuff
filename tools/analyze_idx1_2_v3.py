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

print('=== 索引 1 修复验证 ===')
res1_start = offsets[1]
res1_end = offsets[2]
res1 = data[res1_start:res1_end]

# 新格式：w:2 + h:2 + pal_win:2 + extra:2 = 8字节头
w = struct.unpack('<H', res1[0:2])[0]
h = struct.unpack('<H', res1[2:4])[0]
pal_win = struct.unpack('<H', res1[4:6])[0]
extra = struct.unpack('<H', res1[6:8])[0]
print(f'w={w}, h={h}, pal_win={pal_win}, extra={extra}')

# RLE从偏移8开始
rle_data = res1[8:]
print(f'RLE数据大小: {len(rle_data)}')

# 解码
def decode_rle(data, w, h):
    pixels = []
    idx = 0
    while len(pixels) < w * h and idx < len(data):
        cmd = data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:  # fill
            if count == 0: count = 1
            if idx < len(data):
                val = data[idx]
                idx += 1
                pixels.extend([val] * count)
        elif mode == 0x40:  # copy
            if count == 0: count = 1
            if idx + count <= len(data):
                pixels.extend(data[idx:idx+count])
                idx += count
        elif mode == 0x80:  # skip
            if count == 0: count = 1
            pixels.extend([0] * count)
    
    return pixels

decoded = decode_rle(rle_data, w, h)
print(f'解码像素数: {len(decoded)} (预期 {w*h})')

if len(decoded) == w * h:
    print('解码成功! 像素图案:')
    for row in range(h):
        line = ''
        for col in range(w):
            v = decoded[row*w+col]
            line += '#' if v > 0 else '.'
        print(f'  {line}')

# 索引2：验证偏移表
print(f'\n=== 索引 2 偏移表验证 ===')
res2_start = offsets[2]
res2_end = offsets[3]
res2 = data[res2_start:res2_end]

num_offsets = len(res2) // 4
print(f'偏移数量: {num_offsets}')
print(f'子资源数量: {num_offsets - 1}')

# 验证每个子资源大小
offset0 = struct.unpack('<I', res2[0:4])[0]
offset1 = struct.unpack('<I', res2[4:8])[0]
sub_size = offset1 - offset0
print(f'每个子资源大小: {sub_size} 字节')
print(f'总大小: {(num_offsets-1) * sub_size} 字节 (实际: {len(res2) - offset0})')

# 获取第一个子资源并分析
first_res_start = offset0
first_res_data = res2[first_res_start:first_res_start+sub_size]
print(f'\n第一个子资源 ({sub_size}字节):')
print(f'  前16字节: {" ".join(f"{b:02x}" for b in first_res_data[:16])}')

# 检查是否为Tile
w2 = struct.unpack('<H', first_res_data[0:2])[0]
h2 = struct.unpack('<H', first_res_data[2:4])[0]
print(f'  如果是Tile: w={w2}, h={h2}')
