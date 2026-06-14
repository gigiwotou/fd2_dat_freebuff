"""打印 FDOTHER.DAT 的所有偏移"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count_dword = struct.unpack('<I', f.read(4))[0]
    print('count_dword in header: %d' % count_dword)

    # 实际偏移表项数
    f.seek(6)
    offset_count = 0
    zero_count = 0
    file_size_total = 0
    f.seek(0, 2)
    file_size_total = f.tell()
    f.seek(6)

    while True:
        off_data = f.read(4)
        if len(off_data) < 4:
            break
        off = struct.unpack('<I', off_data)[0]
        if off == 0:
            zero_count += 1
            if zero_count <= 5:
                print('  Zero offset at index %d, byte pos=0x%x' % (offset_count, 6 + offset_count*4))
        if off == 0 or off > file_size_total:
            break
        offset_count += 1

    print('Total offsets (till first zero or invalid): %d' % offset_count)
    print('First zero at byte pos 0x%x (index %d)' % (6 + offset_count*4, offset_count))

    # 打印所有 0 偏移
    f.seek(0, 2)
    file_size = f.tell()
    print('File size: %d' % file_size)
