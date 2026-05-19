import struct

fd = open('d:/workspace/fd2_dat_freebuff/game/FDOTHER.DAT', 'rb')

# 读取文件头
fd.seek(0)
magic = fd.read(6)
fd.seek(6)
count = struct.unpack('<H', fd.read(2))[0]

print(f'FDOTHER.DAT索引数: {count}')
print()

# 读取索引1
idx = 1
fd.seek(10 + idx * 4)
offset = struct.unpack('<I', fd.read(4))[0]
next_offset = struct.unpack('<I', fd.read(4))[0]
size = next_offset - offset

print(f'索引{idx}详细信息:')
print(f'  偏移: 0x{offset:06X} ({offset})')
print(f'  大小: {size} bytes')
print(f'  下一个偏移: 0x{next_offset:06X} ({next_offset})')
print()

# 读取索引1的数据
fd.seek(offset)
data = fd.read(size)

# 分析数据结构 - 查看前16字节
print('前16字节分析:')
for i in range(min(16, len(data))):
    print(f'  [{i:2d}] 0x{data[i]:02X} ({data[i]})')
print()

# 假设是偏移表，每个条目2字节或4字节
# 查看前10个2字节值
print('前20个2字节值 (小端序):')
for i in range(min(20, len(data) // 2)):
    val = struct.unpack('<H', data[i*2:i*2+2])[0]
    print(f'  [{i:2d}] offset=0x{val:04X} ({val})')
print()

# 查看前10个4字节值
print('前10个4字节值 (小端序):')
for i in range(min(10, len(data) // 4)):
    val = struct.unpack('<I', data[i*4:i*4+4])[0]
    print(f'  [{i:2d}] offset=0x{val:06X} ({val})')
print()

# 检查特定资源ID
print('检查资源ID对应的偏移:')
resource_ids = [201, 205, 514, 549, 550]
for rid in resource_ids:
    # 尝试2字节表
    if rid * 2 + 2 <= len(data):
        offset_2byte = struct.unpack('<H', data[rid*2:rid*2+2])[0]
        print(f'  资源ID {rid:3d}: 2字节表偏移=0x{offset_2byte:04X} ({offset_2byte})')
    
    # 尝试4字节表
    if rid * 4 + 4 <= len(data):
        offset_4byte = struct.unpack('<I', data[rid*4:rid*4+4])[0]
        print(f'  资源ID {rid:3d}: 4字节表偏移=0x{offset_4byte:06X} ({offset_4byte})')
print()

# 分析从0x388开始的区域（因为前面看到有0x388等偏移）
print('从偏移0x388开始的区域分析:')
start = 0x388
if start < len(data):
    for i in range(min(20, (len(data) - start) // 2)):
        val = struct.unpack('<H', data[start + i*2:start + i*2 + 2])[0]
        print(f'  [{start + i*2:04X}] 0x{val:04X} ({val})')
print()

# 尝试找到包含资源数据的区域
# 查找可能的资源起始标记
print('查找可能的资源标记:')
for i in range(0, min(1000, len(data)), 16):
    chunk = data[i:i+16]
    if any(b > 0 for b in chunk):
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'  偏移0x{i:04X}: {hex_str}')
print()

# 查看特定偏移位置的内容
print('查看特定偏移的内容:')
check_offsets = [0x388, 0x1C03, 0x500, 0x6E4, 0x8C8]
for co in check_offsets:
    if co < len(data):
        chunk = data[co:co+32]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'  偏移0x{co:04X}: {hex_str}')
        # 尝试作为文本显示
        try:
            text = chunk.decode('ascii', errors='ignore')
            printable = ''.join(c if 32 <= ord(c) < 127 else '.' for c in text)
            print(f'            文本: {printable}')
        except:
            pass
print()

fd.close()
