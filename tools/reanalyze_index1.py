import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

# 读取索引1
fd.seek(10 + 1 * 4)
offset_idx1 = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset_idx1

fd.seek(offset_idx1)
data = fd.read(size)

print('索引1结构重新分析')
print(f'大小: {size} bytes')
print()

# 假设是4字节索引表
print('作为4字节索引表 (前10项):')
for i in range(10):
    val = struct.unpack('<I', data[i*4:i*4+4])[0]
    print(f'  [{i}] = 0x{val:08X} ({val})')
print()

# 检查每个资源的大小
print('资源大小分析:')
for i in range(10):
    val = struct.unpack('<I', data[i*4:i*4+4])[0]
    if i + 1 < 10:
        next_val = struct.unpack('<I', data[(i+1)*4:(i+1)*4+4])[0]
    else:
        next_val = size
    res_size = next_val - val
    print(f'  资源{i}: 偏移0x{val:06X}, 大小{res_size} bytes')
print()

# 显示资源0的前64字节
print('资源0内容:')
res0_off = struct.unpack('<I', data[0:4])[0]
res1_off = struct.unpack('<I', data[4:8])[0]
res0_size = res1_off - res0_off
chunk = data[res0_off:res0_off+min(64, res0_size)]
for i in range(0, len(chunk), 16):
    hex_str = ' '.join(f'{chunk[i+j]:02X}' for j in range(min(16, len(chunk)-i)))
    print(f'  0x{res0_off+i:06X}: {hex_str}')
print()

fd.close()
