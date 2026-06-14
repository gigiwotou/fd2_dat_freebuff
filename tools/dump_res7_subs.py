"""详细分析 viewer 资源 7 的所有 38 个子资源偏移和大小"""
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
    offsets.append(file_size_total)

    # viewer 资源 7
    start = offsets[7]
    end = offsets[8]
    size = end - start
    f.seek(start)
    data = f.read(size)

    # LLLL: [magic:6][count:4][offsets: count*4]
    rc = struct.unpack('<I', data[6:10])[0]
    print('Resource count: %d' % rc)

    # 偏移表
    sub_offsets = []
    for i in range(rc):
        off = struct.unpack('<I', data[10 + i*4:14 + i*4])[0]
        sub_offsets.append(off)

    # 打印所有子资源的偏移和大小
    print('\nAll 38 sub-resources:')
    for i in range(rc):
        off = sub_offsets[i]
        if i + 1 < rc:
            next_off = sub_offsets[i+1]
        else:
            next_off = size  # 末尾
        sub_size = next_off - off
        # 读取 w, h
        w = struct.unpack('<H', data[off:off+2])[0]
        h = struct.unpack('<H', data[off+2:off+4])[0]
        valid = "OK" if off + sub_size <= size and w > 0 and w <= 640 and h > 0 and h <= 480 else "INVALID"
        print('  Sub %2d: offset=0x%04x, size=%3d, w=%3d, h=%3d %s' % (i, off, sub_size, w, h, valid))
