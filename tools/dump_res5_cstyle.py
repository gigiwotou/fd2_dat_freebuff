"""模拟 C 加载逻辑 (viewer 实际使用的)"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic

    # C 加载逻辑: 读 4*a7 + 6 处的 8 字节 (起始 + 末尾偏移)
    # 但 fdother_load 中是先用 0 之前的有效偏移数确定 max_resources

    # 重现 C 的 fdother_load:
    f.seek(0, 2)
    file_size = f.tell()
    f.seek(0)
    data = f.read(file_size)

    table_offset = 6
    max_resources = 0
    while table_offset + 4 <= file_size:
        res_offset = struct.unpack('<I', data[table_offset:table_offset+4])[0]
        if res_offset == 0 or res_offset > file_size:
            break
        max_resources += 1
        table_offset += 4

    # 构建完整偏移表
    offsets = []
    for i in range(max_resources + 1):
        if i < max_resources:
            offsets.append(struct.unpack('<I', data[6 + i*4:10 + i*4])[0])
        else:
            offsets.append(file_size)

    print('C-style max_resources: %d' % max_resources)
    print('Last few offsets:')
    for i in range(max(0, max_resources-5), max_resources+1):
        print('  Off[%d] = 0x%x' % (i, offsets[i]))

    # 现在 viewer 资源 5
    start = offsets[5]
    end = offsets[6]
    size = end - start
    print('\nViewer Resource 5 (C-style): offset=0x%x, size=%d (0x%x)' % (start, size, size))
    print('First 16 bytes: %s' % ' '.join('%02x' % b for b in data[start:start+16]))

    # viewer 资源 6
    start = offsets[6]
    end = offsets[7]
    size = end - start
    print('\nViewer Resource 6 (C-style): offset=0x%x, size=%d (0x%x)' % (start, size, size))
    print('First 16 bytes: %s' % ' '.join('%02x' % b for b in data[start:start+16]))
