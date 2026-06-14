"""详细分析 viewer 资源 7 - 打印所有 38 个偏移表项"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count_dword = struct.unpack('<I', f.read(4))[0]

    # 实际有效的偏移
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
    offsets.append(file_size_total)

    # viewer 资源 7
    start = offsets[7]
    end = offsets[8]
    size = end - start
    f.seek(start)
    data = f.read(size)

    # LLLL: [magic:6][count:4][offsets: count*4]
    rc = struct.unpack('<I', data[6:10])[0]
    print('Viewer Resource 7: size=%d (0x%x)' % (size, size))
    print('Resource count: %d\n' % rc)

    # 偏移表项
    print('All 38 offset table entries:')
    for i in range(rc):
        off = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
        marker = "INVALID" if off > size or off < 10 + rc*4 else ""
        # 计算下一个有效偏移
        if i + 1 < rc:
            next_off = struct.unpack('<I', data[10 + (i+1)*4:14 + (i+1)*4])[0]
        else:
            next_off = size
        sub_size = next_off - off if off <= size else 0
        print('  Off[%2d] = 0x%04x, sub_size=%4d %s' % (i, off, sub_size, marker))
