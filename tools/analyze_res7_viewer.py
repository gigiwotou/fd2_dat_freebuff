"""详细分析 viewer 资源 7 (LLLL 嵌套 DAT)"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count_dword = struct.unpack('<I', f.read(4))[0]

    # 实际有效的偏移 (C 代码逻辑)
    offsets = []
    file_size_total = 0
    f.seek(0, 2)
    file_size_total = f.tell()

    f.seek(6)
    while True:
        off_data = f.read(4)
        if len(off_data) < 4:
            break
        off = struct.unpack('<I', off_data)[0]
        if off == 0 or off > file_size_total:
            break
        offsets.append(off)
    offsets.append(file_size_total)  # 末尾

    # viewer 资源 7
    start = offsets[7]
    end = offsets[8]
    size = end - start
    print('Viewer Resource 7: start=0x%x, size=%d (0x%x)' % (start, size, size))

    f.seek(start)
    data = f.read(size)

    print('First 64 bytes:')
    for i in range(0, 64, 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in data[i:i+16])))
    print('First 6 bytes ASCII: %s' % repr(data[:6]))
    print('First 10 bytes:')
    for i in range(10):
        print('  +%02d: 0x%02x = %3d' % (i, data[i], data[i]))

    if data[:6] == b'LLLLLL':
        # 嵌套 DAT: [magic:6][count:4][offsets: count*4]
        if size < 10:
            print('Too small!')
        else:
            # count: 4 bytes after magic
            count = struct.unpack('<I', data[6:10])[0]
            print('Resource count: %d (0x%x)' % (count, count))

            # 偏移表
            print('First 10 sub-resource offsets:')
            for i in range(min(10, count)):
                off = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
                print('  Sub %d: offset=0x%x' % (i, off))

            # 第一个子资源的实际位置
            sub0_off = struct.unpack('<I', data[10:14])[0]
            sub1_off = struct.unpack('<I', data[14:18])[0]
            print('\nSub 0 start: 0x%x, Sub 1 start: 0x%x, size=%d' % (
                sub0_off, sub1_off, sub1_off - sub0_off))
            print('First 32 bytes of sub 0:')
            sub_data = data[sub0_off:sub0_off+32]
            for i in range(0, 32, 16):
                print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in sub_data[i:i+16])))

            # 检查 sub 0 是不是 4 字节 [w, h] 头
            w = struct.unpack('<H', data[sub0_off:sub0_off+2])[0]
            h = struct.unpack('<H', data[sub0_off+2:sub0_off+4])[0]
            print('Sub 0 first 4 bytes as w,h: w=%d, h=%d' % (w, h))
