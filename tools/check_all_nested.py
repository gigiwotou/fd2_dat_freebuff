"""分析所有 LLLL 嵌套资源的实际子资源数"""
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

    offsets = []
    for i in range(max_resources):
        offsets.append(struct.unpack('<I', data[6 + i*4:10 + i*4])[0])
    offsets.append(file_size)

    # 找出所有 LLLL 资源
    print('All LLLL nested DAT resources:')
    for i in range(max_resources):
        start = offsets[i]
        end = offsets[i+1]
        size = end - start
        if data[start:start+6] == b'LLLLLL':
            count = struct.unpack('<I', data[start+6:start+10])[0]
            # 找出实际有效子资源数 (按偏移表格式: 每项4字节, 偏移必须 < size)
            valid_count = 0
            for j in range(count):
                if 10 + j*4 + 4 > size:
                    break
                off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
                if off < 10 + count*4 or off > size:
                    break
                valid_count += 1
            print('  Viewer Res %2d: size=%6d, declared_count=%3d, valid_count=%2d' % (
                i, size, count, valid_count))

    # 详细看 viewer 资源 7
    print('\n\n=== Detailed Viewer Res 7 ===')
    start = offsets[7]
    end = offsets[8]
    size = end - start
    print('size=%d' % size)
    print('First 64 bytes: %s' % ' '.join('%02x' % b for b in data[start:start+64]))

    # 计算 count 字段后第一个有效偏移位置
    # 找第一个 offset 值 < size 且 >= 10+count*4
    count = struct.unpack('<I', data[start+6:start+10])[0]
    print('count=%d' % count)
    print('Offset table would be: +%d..+%d' % (10, 10 + count*4))
    for j in range(count):
        if 10 + j*4 + 4 > size:
            break
        off = struct.unpack('<I', data[start+10+j*4:start+14+j*4])[0]
        in_range = 10+count*4 <= off <= size
        print('  Off[%2d] = 0x%04x, in_offset_table_range=%s' % (j, off, in_range))
