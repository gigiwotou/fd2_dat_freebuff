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

def decompress_rle_mcp(src, width, height, palette_window=-1):
    """
    根据MCP sub_4E98D精确实现
    控制字节:
    - bit7=0, bit6=0: FILL (value+1个像素，填充值为下一个字节)
    - bit7=0, bit6=1: SKIP (value+1个像素，用palette_window填充)
    - bit7=1, bit6=0: COPY (value+1个像素，从源复制)
    - bit7=1, bit6=1: SKIP (value+1个像素，跳过)
    """
    expected = width * height
    dst = [0] * expected
    dst_idx = 0
    src_idx = 0
    src_size = len(src)
    
    while dst_idx < expected and src_idx < src_size:
        byte = src[src_idx]
        src_idx += 1
        
        bit7 = (byte >> 7) & 1
        bit6 = (byte >> 6) & 1
        count = (byte & 0x3F) + 1
        
        if bit7 == 0:
            if bit6 == 0:
                # FILL: 填充count个像素，值为下一个字节
                if src_idx < src_size:
                    fill_val = src[src_idx]
                    src_idx += 1
                    if palette_window != -1:
                        fill_val = (palette_window + fill_val) & 0xFF
                    for _ in range(count):
                        if dst_idx < expected:
                            dst[dst_idx] = fill_val
                            dst_idx += 1
            else:
                # SKIP: 跳过count个像素（填充0）
                for _ in range(count):
                    if dst_idx < expected:
                        dst[dst_idx] = 0
                        dst_idx += 1
        else:
            if bit6 == 0:
                # COPY: 复制count个字节
                for _ in range(count):
                    if dst_idx < expected and src_idx < src_size:
                        val = src[src_idx]
                        src_idx += 1
                        if palette_window != -1:
                            val = (palette_window + val) & 0xFF
                        dst[dst_idx] = val
                        dst_idx += 1
            else:
                # SKIP: 跳过count个像素
                for _ in range(count):
                    if dst_idx < expected:
                        dst[dst_idx] = 0
                        dst_idx += 1
    
    return dst

# 测试索引1
print('=== 测试索引1 (24x24) ===')
res1 = data[offsets[1]:offsets[2]]
w, h = struct.unpack('<HH', res1[:4])
print(f'w={w}, h={h}')

for header_size in [5, 8]:
    rle_data = res1[header_size:]
    decoded = decompress_rle_mcp(rle_data, w, h, -1)
    success = sum(1 for p in decoded if p != 0)
    print(f'  头{header_size}字节: 解码像素={len(decoded)}/{w*h}, 非零={success}')
    
    if len(decoded) == w * h and success > 0:
        print('  OK! 图案:')
        for row in range(h):
            line = ''
            for col in range(w):
                v = decoded[row * w + col]
                line += '#' if v > 0 else '.'
            print(f'    {line}')

# 测试其他tile
print('\n=== 测试其他tile资源 ===')
for idx in [11, 15, 55, 56]:
    res = data[offsets[idx]:offsets[idx+1]]
    w, h = struct.unpack('<HH', res[:4])
    
    for header_size in [5, 8]:
        if len(res) >= header_size:
            rle_data = res[header_size:]
            decoded = decompress_rle_mcp(rle_data, w, h, -1)
            status = 'OK' if len(decoded) == w * h else f'FAIL ({len(decoded)}/{w*h})'
            print(f'  索引{idx}: 头{header_size}字节 -> {status}')
