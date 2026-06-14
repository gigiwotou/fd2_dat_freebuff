"""详细分析 FDOTHER 索引 7 的结构"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count = struct.unpack('<I', f.read(4))[0]
    offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(count)]

    # 读取资源7
    start = offsets[7]
    end = offsets[8] if 8 < count else None
    if end is None:
        f.seek(0, 2)
        file_size = f.tell()
        end = file_size

    size = end - start
    print('Resource 7: offset=0x%x, size=%d (0x%x)' % (start, size, size))

    f.seek(start)
    data = f.read(size)

    # 看前 64 字节
    print('First 128 bytes hex:')
    for i in range(0, min(128, size), 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in data[i:i+16])))

    # 解析 6 字节头
    print('\nFirst 6 bytes (DWORD + WORD):')
    w0 = struct.unpack('<H', data[0:2])[0]
    w1 = struct.unpack('<H', data[2:4])[0]
    w2 = struct.unpack('<H', data[4:6])[0]
    print('  +0 (WORD): %d (0x%04x)' % (w0, w0))
    print('  +2 (WORD): %d (0x%04x)' % (w1, w1))
    print('  +4 (WORD): %d (0x%04x)' % (w2, w2))

    # 从 +6 开始, 试把数据当作 tile 偏移表
    print('\n试解析偏移表: 从 +6 开始, 每 4 字节一个 offset')
    print('找到所有 <= %d 的非零偏移:' % size)
    valid_offsets = []
    for i in range(min(200, size // 4)):
        off = struct.unpack('<I', data[6 + i*4:10 + i*4])[0]
        if off == 0 or off > size:
            # 打印位置 + 0 的位置
            if off == 0 and len(valid_offsets) > 0:
                print('  Offset[%d] = 0 (STOP at 0x%x)' % (i, 6 + i*4))
                break
            elif off > size:
                print('  Offset[%d] = 0x%x (out of range, STOP at 0x%x)' % (i, off, 6 + i*4))
                break
        else:
            # 读取该 tile 的 width, height
            tw = struct.unpack('<H', data[off:off+2])[0]
            th = struct.unpack('<H', data[off+2:off+4])[0]
            print('  Offset[%d] = 0x%x, w=%d, h=%d' % (i, off, tw, th))
            valid_offsets.append((off, tw, th))

    print('\n共 %d 个有效 tile 偏移' % len(valid_offsets))

    # 同时看是否是另一格式: 也许 4 字节宽, 高度 0 是中间记录?
    print('\n\n额外分析: 前 6 字节解读')
    print('W=%d, H=%d, T=%d' % (w0, w1, w2))

    # 也许头部是 [width:2][height:2][N:2] 然后偏移表? width=H*16, height=N?
    # 看 sub_168B6 调用时的 a5=tile_width, a6=tile_height
    # 看 a9=tile_height_count 等.
    # 也许头部 [width:2][height:2][tile_count:2] 是另一种 tile 集
    # 而 [palette_window:1] 在 [width:2] 前?

    # 看完整 768 字节的 3 字节分组 (按调色板格式读)
    print('\n\n按 3 字节调色板格式读前 30 字节:')
    for i in range(0, 30, 3):
        rgb = data[i:i+3]
        print('  +%02d: %02x %02x %02x' % (i, rgb[0], rgb[1], rgb[2]))
