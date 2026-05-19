import struct
import sys

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(0)
magic = fd.read(6)
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

print(f'文件头: {magic}')
print(f'索引数: {count}')
print()

# 读取索引1
idx = 1
fd.seek(10 + idx * 4)
offset = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset

print(f'索引{idx}:')
print(f'  偏移: {offset}')
print(f'  大小: {size}')
print(f'  下一个偏移: {next_offset}')
print()

# 读取数据
fd.seek(offset)
data = fd.read(size)

print('前200字节内容:')
for i in range(min(200, len(data))):
    if i % 16 == 0:
        print(f'\n{offset + i:06X}: ', end='')
    print(f'{data[i]:02X} ', end='')
print()
print()

# 检查是否是嵌套的DAT文件
if data[0:6] == b'LLLLLL':
    print('索引1是嵌套的DAT文件!')
    nested_count = struct.unpack('<H', data[6:8])[0]
    print(f'嵌套DAT索引数: {nested_count}')
    
    # 读取嵌套DAT的资源
    for i in range(min(10, nested_count)):
        off = 10 + i * 4
        if off + 8 > len(data):
            break
        off_start = struct.unpack('<I', data[off:off+4])[0]
        off_end = struct.unpack('<I', data[off+4:off+8])[0]
        nested_size = off_end - off_start
        print(f'  嵌套索引{i}: 偏移{off_start}, 大小{nested_size}')
else:
    print('索引1不是嵌套DAT文件')
    print('前20字节是: ', data[:20])

fd.close()
