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

def decode_rle(data, w, h):
    pixels = []
    idx = 0
    while len(pixels) < w * h and idx < len(data):
        cmd = data[idx]
        idx += 1
        mode = cmd & 0xC0
        count = cmd & 0x3F
        
        if mode == 0x00:
            if count == 0: count = 1
            if idx < len(data):
                val = data[idx]
                idx += 1
                pixels.extend([val] * count)
        elif mode == 0x40:
            if count == 0: count = 1
            if idx + count <= len(data):
                pixels.extend(data[idx:idx+count])
                idx += count
        elif mode == 0x80:
            if count == 0: count = 1
            pixels.extend([0] * count)
    return pixels

print('=== 测试不同头格式 ===')

for idx in [1, 11, 15, 55]:
    res_start = offsets[idx]
    res_end = offsets[idx + 1]
    res = data[res_start:res_end]
    
    w = struct.unpack('<H', res[0:2])[0]
    h = struct.unpack('<H', res[2:4])[0]
    
    print(f'\n索引{idx}: {w}x{h}')
    
    for header_size in [5, 6, 8]:
        if len(res) >= header_size:
            pal_win_byte = res[4] if header_size == 5 else struct.unpack('<H', res[4:6])[0]
            decoded = decode_rle(res[header_size:], w, h)
            success = 'OK' if len(decoded) == w * h else 'FAIL'
            print(f'  头{header_size}字节: pal_win={pal_win_byte:5d}, 解码{len(decoded)}/{w*h} -> {success}')

# 专门分析索引1和11的前10字节
print('\n=== 索引1 vs 索引11 头字节对比 ===')
res1 = data[offsets[1]:offsets[2]]
res11 = data[offsets[11]:offsets[12]]

print('索引1 前10字节:', ' '.join(f'{b:02x}' for b in res1[:10]))
print('索引11前10字节:', ' '.join(f'{b:02x}' for b in res11[:10]))

# 索引1: 18 00 18 00 14 00 56 00 00 00
# 索引11: 40 01 c8 00 00 8e 57 01 00 00
# 索引1: w=24, h=24, 56 00可能是某种标志
# 索引11: w=320, h=200, 00 8e可能是某种标志
