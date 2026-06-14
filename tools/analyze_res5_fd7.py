"""详细分析 FDOTHER 文件索引 5 (FDOTHER_DAT__7 实际指向)"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count = struct.unpack('<I', f.read(4))[0]
    offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(count)]

    # 读取资源 5 (FDOTHER_DAT__7 实际指向)
    start = offsets[5]
    end = offsets[6] if 6 < count else None
    if end is None:
        f.seek(0, 2)
        file_size = f.tell()
        end = file_size
    size = end - start
    print('Resource 5: offset=0x%x, size=%d (0x%x)' % (start, size, size))

    f.seek(start)
    data = f.read(size)

    # 查看前 128 字节
    print('First 128 bytes hex:')
    for i in range(0, 128, 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in data[i:i+16])))
    print('First 8 bytes ASCII: %s' % repr(data[:8]))

    # 检查是否是 LMI1 或 LLLL
    is_lmi1 = data[:4] == b'LMI1'
    is_llll = data[:6] == b'LLLLLL'
    print('Is LMI1: %s' % is_lmi1)
    print('Is LLLLLL: %s' % is_llll)

    if is_lmi1:
        tile_count = struct.unpack('<H', data[4:6])[0]
        print('LMI1 tile count: %d' % tile_count)
        # 显示前 5 个 tile 偏移
        for i in range(min(5, tile_count)):
            off = struct.unpack('<I', data[6 + i*4:10 + i*4])[0]
            print('  Tile %d: offset=0x%x' % (i, off))
            if off + 4 <= size:
                w = struct.unpack('<H', data[off:off+2])[0]
                h = struct.unpack('<H', data[off+2:off+4])[0]
                print('    Dimensions: %dx%d' % (w, h))

    if is_llll:
        # 嵌套 DAT 格式: LLLLLL + count:4 + offsets
        rc = struct.unpack('<I', data[6:10])[0]
        print('Nested DAT resource count: %d' % rc)
        for i in range(min(5, rc)):
            off = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
            print('  Resource %d: offset=0x%x' % (i, off))

    # 通用: 试解读 4 字节头为 (w, h)
    if len(data) >= 4:
        w = struct.unpack('<H', data[0:2])[0]
        h = struct.unpack('<H', data[2:4])[0]
        print('If w,h header: w=%d, h=%d' % (w, h))
