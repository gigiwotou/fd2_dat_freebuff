"""打印所有 C-style 偏移表项"""
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

    # 列出 viewer 资源 0-12 的偏移和大小
    print('C-style Viewer Resources 0-15:')
    for i in range(16):
        if i < max_resources:
            start = struct.unpack('<I', data[6 + i*4:10 + i*4])[0]
        if i + 1 < max_resources:
            end = struct.unpack('<I', data[6 + (i+1)*4:10 + (i+1)*4])[0]
        else:
            end = file_size
        size = end - start
        first = data[start:start+8]
        print('  Viewer Res %2d: offset=0x%06x, size=%5d, first 8: %s' % (
            i, start, size, ' '.join('%02x' % b for b in first)))
