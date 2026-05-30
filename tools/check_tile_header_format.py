import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

offsets = []
table_start = 6
for i in range(103):
    offset_addr = table_start + i * 4
    offset_val = struct.unpack_from('<I', data, offset_addr)[0]
    offsets.append(offset_val)

# 检查所有Tile资源的头格式
print('=== 检查所有Tile资源的头字节 ===')

tile_indices = [1, 10, 11, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 32, 33, 34, 
                37, 38, 39, 42, 43, 44, 45, 54, 55, 56, 58, 59, 60, 61, 62, 65, 66, 67, 68,
                69, 70, 71, 72, 73, 74, 75, 96, 97, 98, 100]

for idx in tile_indices:
    res = data[offsets[idx]:offsets[idx+1]]
    w, h = struct.unpack('<HH', res[:4])
    byte4 = res[4]
    byte5 = res[5] if len(res) > 5 else 0
    byte6 = res[6] if len(res) > 6 else 0
    byte7 = res[7] if len(res) > 7 else 0
    
    # 检查是否是合理的调色板窗口值
    # 单字节范围: 0-255
    # 双字节范围: 0-65535
    
    pal_win_1byte = byte4
    pal_win_2byte = byte4 | (byte5 << 8)
    
    # 判断哪种更合理
    # 如果byte5很小（< 32），可能是2字节调色板窗口
    # 如果byte5很大，可能是其他数据
    
    print(f'索引{idx:3d}: {w:4d}x{h:4d}, 字节4-7: {byte4:02x} {byte5:02x} {byte6:02x} {byte7:02x}, '
          f'pal_win(1B)={pal_win_1byte:3d}, pal_win(2B)={pal_win_2byte:5d}')
