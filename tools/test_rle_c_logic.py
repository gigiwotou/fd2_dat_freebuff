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

def decompress_rle_c(src, width, height, value_param):
    expected = width * height
    num4 = 0
    num3 = len(src) - 1
    num7 = 0
    num8 = 0
    num9 = 0
    b = 0
    num10 = 0
    num11 = 0
    dst = []
    
    while num4 <= num3 and len(dst) < expected:
        flag = (num8 != 0)
        
        if not flag:
            num7 = 0
            num8 = 0
            num9 = 0
            
            if num4 < len(src):
                b = src[num4]
                if b >= 192:
                    num7 = b - 192 + 1
                elif b >= 128:
                    num8 = b - 128 + 1
                elif b >= 64:
                    num9 = b - 64
                    num8 = 1
                else:
                    num8 = 1
                    num9 = b
            
            num10 += num7
            if num10 >= width:
                num10 = 0
                num11 += 1
        else:
            num12 = num9
            num13 = 0
            while num13 <= num12:
                if b >= 64 and b < 128:
                    num10 += 1
                
                if num4 < len(src):
                    index = src[num4]
                    if 0 <= num10 < width and 0 <= num11 < height:
                        if len(dst) < expected:
                            dst.append(index)
                
                num10 += 1
                if num10 >= width:
                    num10 = 0
                    num11 += 1
                
                num13 += 1
            
            num8 -= 1
        
        num4 += 1
        
        if num11 >= height:
            break
    
    return dst

print('=== 使用 C 的 fd_decompress_rle 逻辑测试 ===')

for idx in [1, 11, 15]:
    res_start = offsets[idx]
    res_end = offsets[idx + 1]
    res = data[res_start:res_end]
    
    w = struct.unpack('<H', res[0:2])[0]
    h = struct.unpack('<H', res[2:4])[0]
    
    print(f'\n索引{idx}: {w}x{h}')
    
    # 测试不同头大小
    for header_size in [5, 8]:
        if len(res) >= header_size:
            rle_data = res[header_size:]
            pal_win = res[4] if header_size == 5 else struct.unpack('<H', res[4:6])[0]
            decoded = decompress_rle_c(rle_data, w, h, pal_win)
            status = 'OK' if len(decoded) == w * h else f'FAIL ({len(decoded)}/{w*h})'
            print(f'  头{header_size}字节: pal_win={pal_win}, {status}')

# 额外分析索引1的前12字节
print('\n=== 索引1 详细分析 ===')
res1 = data[offsets[1]:offsets[2]]
print('前12字节:', ' '.join(f'{b:02x}' for b in res1[:12]))
print('  字节0-1 (w):', struct.unpack('<H', res1[0:2])[0])
print('  字节2-3 (h):', struct.unpack('<H', res1[2:4])[0])
print('  字节4-5 (pal_win):', struct.unpack('<H', res1[4:6])[0])
print('  字节6-7 (extra):', struct.unpack('<H', res1[6:8])[0])
print('  字节8-11 (RLE start):', ' '.join(f'{b:02x}' for b in res1[8:12]))
