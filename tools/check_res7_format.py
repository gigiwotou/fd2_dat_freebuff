"""检查 FDOTHER 索引 7 的格式"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count = struct.unpack('<I', f.read(4))[0]
    print(f'Resource count: {count}')
    offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(count)]

    # 读取资源7
    start = offsets[7]
    end = offsets[8] if 8 < count else None
    if end is None:
        f.seek(0, 2)
        file_size = f.tell()
        end = file_size

    size = end - start
    print(f'Resource 7: offset=0x{start:x}, size={size}')

    f.seek(start)
    data = f.read(size)
    print('First 64 bytes:')
    for i in range(0, 64, 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in data[i:i+16])))
    print('First 4 bytes ASCII:', data[:4])
    print('First 6 bytes ASCII:', data[:6])

    w = struct.unpack('<H', data[0:2])[0]
    h = struct.unpack('<H', data[2:4])[0]
    print('Width=%d, Height=%d' % (w, h))

    if len(data) >= 6:
        c = struct.unpack('<H', data[4:6])[0]
        print('Word at +4: %d' % c)
        # 看看tile_count附近的数据
        print('+4 to +10:', ' '.join('%02x' % b for b in data[4:10]))

    # 假设tile count=N, 偏移表从 +6 开始
    # 尝试两种可能
    # 方式1: [width:2][height:2][tile_count:2][tile_offsets: N*4]
    # 方式2: [width:2][height:2][tile_count:2] 没有tile_offsets, 紧接着是tile数据
    if len(data) >= 6:
        # 把+4的word当作 tile_count
        tile_count = struct.unpack('<H', data[4:6])[0]
        print('Tile count (treating +4 as count): %d' % tile_count)

        # 偏移表从 +6 开始, 每个 dword 4 字节
        if tile_count > 0 and tile_count < 10000:
            print('First 10 tile offsets (if count=%d):' % tile_count)
            for i in range(min(10, tile_count)):
                off = struct.unpack('<I', data[6 + i*4:10 + i*4])[0]
                if off < len(data):
                    tw = struct.unpack('<H', data[off:off+2])[0]
                    th = struct.unpack('<H', data[off+2:off+4])[0]
                    print('  Tile %d: offset=0x%x, w=%d, h=%d' % (i, off, tw, th))
                else:
                    print('  Tile %d: offset=0x%x (out of range)' % (i, off))

    # 顺便查看一下: 如果不通过 LLLL 头识别
    # 看看 ASCII 是否是 LLLLLL
    print('Is LLLLLL:', data[:6] == b'LLLLLL')
