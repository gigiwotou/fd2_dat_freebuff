"""详细查看 FDOTHER 多个资源，确定索引7实际是什么"""
import struct

with open(r'D:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT', 'rb') as f:
    f.read(6)  # LLLLLL magic
    count = struct.unpack('<I', f.read(4))[0]
    offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(count)]

    # 看看 5-12 索引的偏移
    print('Resources 5-12 offsets and sizes:')
    for i in range(5, 13):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else None
        if end is None:
            f.seek(0, 2)
            file_size = f.tell()
            end = file_size
        size = end - start
        print('  Resource %d: offset=0x%x, size=%d (0x%x)' % (i, start, size, size))

    # 资源7的数据
    start = offsets[7]
    end = offsets[8] if 8 < count else None
    if end is None:
        f.seek(0, 2)
        file_size = f.tell()
        end = file_size
    size = end - start
    f.seek(start)
    data = f.read(size)

    print('\nResource 7: first 32 bytes:')
    for i in range(0, 32, 16):
        print('  +%04x: %s' % (i, ' '.join('%02x' % b for b in data[i:i+16])))

    # 现在按 3 字节 RGB 格式解读前 768 字节
    print('\n按 3 字节 RGB 格式: 前 30 个颜色')
    for i in range(0, 30*3, 3):
        r, g, b = data[i], data[i+1], data[i+2]
        print('  Color %d: (%2d, %2d, %2d)' % (i//3, r, g, b))

    # 注意：从原始 dump 看
    #   00 00 00 | 03 00 00 | 08 00 00 | 0d 00 00 ...
    # 看起来 R 通道是 0, 3, 8, 13, ..., 63, 63, 63, 60, 57, ...
    # G 通道是 0, 0, 0, 0, ...
    # B 通道全是 0
    # 所以这是 (R, 0, 0) 渐变
    # 这与 6bit -> 8bit 调色板格式很相似 (但只有 6bit)
