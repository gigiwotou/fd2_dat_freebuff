"""打印 viewer 资源 7 的完整数据，重点关注 +10..+162 偏移表区域"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic

    f.seek(0, 2)
    file_size = f.tell()
    f.seek(0)
    data = f.read(file_size)

    # C 加载逻辑
    table_offset = 6
    max_resources = 0
    while table_offset + 4 <= file_size:
        res_offset = struct.unpack('<I', data[table_offset:table_offset+4])[0]
        if res_offset == 0 or res_offset > file_size:
            break
        max_resources += 1
        table_offset += 4

    # viewer 资源 7
    start = struct.unpack('<I', data[6 + 7*4:10 + 7*4])[0]
    end = struct.unpack('<I', data[6 + 8*4:10 + 8*4])[0]
    size = end - start
    sub_data = data[start:start+size]

    print('Viewer Res 7: offset=0x%x, size=%d' % (start, size))

    # 打印 +0..+170 字节
    print('Hex dump +0..+170:')
    for i in range(0, 170, 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in sub_data[i:i+16])))

    # LLLL 头 + count
    magic = sub_data[:6]
    count = struct.unpack('<I', sub_data[6:10])[0]
    print('Magic: %s, Count: %d' % (magic, count))

    # 偏移表 38 项 (从 +10 开始)
    print('\n38 offset entries:')
    for i in range(38):
        off = struct.unpack('<I', sub_data[10 + i*4:14 + i*4])[0]
        print('  Off[%2d] = 0x%04x' % (i, off))

    # 偏移表区域 +10..+161 的实际字节
    print('\nOffset table area (+10..+161) bytes:')
    print(' '.join('%02x' % b for b in sub_data[10:162]))
