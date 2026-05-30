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

def decompress_rle_v1(src, width, height):
    """版本1: 简单的RLE解码"""
    dst = []
    idx = 0
    while len(dst) < width * height and idx < len(src):
        cmd = src[idx]
        idx += 1
        
        bit7 = (cmd >> 7) & 1
        bit6 = (cmd >> 6) & 1
        count = (cmd & 0x3F) + 1
        
        if bit7 == 0 and bit6 == 0:
            # FILL
            if idx < len(src):
                val = src[idx]
                idx += 1
                dst.extend([val] * count)
        elif bit7 == 0 and bit6 == 1:
            # SKIP
            dst.extend([0] * count)
        elif bit7 == 1 and bit6 == 0:
            # COPY
            if idx + count <= len(src):
                dst.extend(src[idx:idx+count])
                idx += count
        else:
            # SKIP
            dst.extend([0] * count)
    
    return dst

def decompress_rle_v2(src, width, height):
    """版本2: 根据MCP代码的精确实现"""
    expected = width * height
    dst = [0] * expected
    dst_pos = 0
    
    # 每行处理
    for row in range(height):
        count = width  # 当前行剩余像素
        
        while count > 0:
            if dst_pos >= len(src):
                break
            
            value = src[dst_pos]
            dst_pos += 1
            
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            count_val = (value & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    if dst_pos < len(src):
                        fill_val = src[dst_pos]
                        dst_pos += 1
                        for _ in range(count_val):
                            if count > 0:
                                # 这里需要映射到正确的dst位置
                                count -= 1
                else:
                    # SKIP
                    count -= count_val
            else:
                if bit6 == 0:
                    # COPY
                    if dst_pos + count_val <= len(src):
                        for i in range(count_val):
                            if count > 0:
                                count -= 1
                                dst_pos += 1
                    else:
                        break
                else:
                    # SKIP
                    count -= count_val
    
    return []

# 测试索引1
print('=== 测试索引1 (24x24) ===')
res1 = data[offsets[1]:offsets[2]]
w, h = struct.unpack('<HH', res1[:4])
print(f'w={w}, h={h}')

for header_size in [5, 8]:
    rle_data = res1[header_size:]
    decoded = decompress_rle_v1(rle_data, w, h)
    success = len(decoded)
    print(f'  头{header_size}字节: 解码{success}/{w*h}像素')
    
    if success == w * h:
        print('  OK! 图案:')
        for row in range(h):
            line = ''
            for col in range(w):
                v = decoded[row * w + col]
                line += '#' if v > 0 else '.'
            print(f'    {line}')

# 也测试其他tile
print('\n=== 测试其他tile资源 ===')
for idx in [11, 15, 55, 56]:
    res = data[offsets[idx]:offsets[idx+1]]
    w, h = struct.unpack('<HH', res[:4])
    
    for header_size in [5, 8]:
        if len(res) >= header_size:
            rle_data = res[header_size:]
            decoded = decompress_rle_v1(rle_data, w, h)
            status = 'OK' if len(decoded) == w * h else f'FAIL ({len(decoded)}/{w*h})'
            print(f'  索引{idx}: 头{header_size}字节 -> {status}')
