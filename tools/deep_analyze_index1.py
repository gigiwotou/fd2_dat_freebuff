import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]
print(f'FDOTHER.DAT索引数: {count}\n')

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

print(f'索引1:')
print(f'  偏移: 0x{offset_idx1:06X} ({offset_idx1})')
print(f'  大小: {size} bytes\n')

fd.seek(offset_idx1)
data = fd.read(size)

# 分析前16字节
print('前16字节:')
for i in range(16):
    print(f'  [{i:2d}] 0x{data[i]:02X}', end='')
    if (i+1) % 4 == 0:
        dword_val = struct.unpack('<I', data[i-3:i+1])[0]
        print(f'  (dword={dword_val})')
    else:
        print()
print()

# 索引1是一个嵌套的DAT文件！
# 从sub_29BCB的代码看，它加载FDOTHER.DAT索引1到dword_53F66
# 然后通过dword_53F66 + 70获取某个偏移量

# 检查索引1是否是另一个DAT文件
print('检查索引1是否是嵌套DAT:')
if data[0:6] == b'LLLLLL':
    print('  YES - 索引1是嵌套DAT文件!')
    nested_count = struct.unpack('<H', data[6:8])[0]
    print(f'  嵌套DAT索引数: {nested_count}')
    
    # 显示嵌套DAT的前10个索引
    print('\n  嵌套DAT索引表 (前10项):')
    for i in range(min(10, nested_count)):
        idx_off = 10 + i * 4
        off_start = struct.unpack('<I', data[idx_off:idx_off+4])[0]
        if i + 1 < nested_count:
            off_end = struct.unpack('<I', data[idx_off+4:idx_off+8])[0]
        else:
            off_end = size
        res_size = off_end - off_start
        print(f'    [{i:3d}] 偏移0x{off_start:06X}, 大小{res_size:6d}')
        
        # 显示前16字节
        if off_start < size:
            chunk = data[off_start:off_start+min(16, res_size)]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'         内容: {hex_str}')
else:
    print('  NO - 索引1不是嵌套DAT')
    
    # 尝试解析为4字节索引表
    print('\n尝试作为4字节索引表:')
    num_entries = size // 4
    print(f'  条目数: {num_entries}')
    for i in range(min(10, num_entries)):
        val = struct.unpack('<I', data[i*4:i*4+4])[0]
        print(f'    [{i:3d}] = 0x{val:08X}')
print()

fd.close()
