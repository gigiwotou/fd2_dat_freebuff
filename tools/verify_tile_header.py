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

# 验证其他Tile资源是否也使用8字节头
print('=== 验证其他Tile资源头格式 ===')

for idx in [11, 15, 55, 56, 59, 60, 61, 62, 74, 75, 97, 100]:
    res_start = offsets[idx]
    res_end = offsets[idx + 1]
    res = data[res_start:res_end]
    
    if len(res) >= 8:
        w = struct.unpack('<H', res[0:2])[0]
        h = struct.unpack('<H', res[2:4])[0]
        pal_win = struct.unpack('<H', res[4:6])[0]
        extra = struct.unpack('<H', res[6:8])[0]
        rle_size = len(res) - 8
        
        # 尝试从偏移8解码RLE
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
        
        decoded = decode_rle(res[8:], w, h)
        success = 'OK' if len(decoded) == w * h else 'FAIL'
        print(f'  索引{idx:3d}: {w:4d}x{h:4d}, pal_win={pal_win:2d}, extra={extra:5d}, rle={rle_size:6d} -> {success} ({len(decoded)}/{w*h})')
