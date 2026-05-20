import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f'DATO.DAT: {count} resources, file size: {len(data)}')

# 分析资源0的详细结构
off0 = struct.unpack('<I', data[10:14])[0]
off1 = struct.unpack('<I', data[14:18])[0]
size0 = off1 - off0

print(f'\n=== Resource 0 at {hex(off0)}, size={size0} ===')

# 根据反编译代码，头像数据头部包含宽高信息
# v4 = *a2 (宽度)
# v5 = a2[1] (高度)
# 这些都是__int16类型

# 检查字节0-1 (可能是宽度)
w = struct.unpack('<h', data[off0:off0+2])[0]
h = struct.unpack('<h', data[off0+2:off0+4])[0]
print(f'Bytes 0-1 (width?): {w}')
print(f'Bytes 2-3 (height?): {h}')

# 检查字节4-5
val4 = struct.unpack('<h', data[off0+4:off0+6])[0]
print(f'Bytes 4-5: {val4}')

# 检查字节6-7
val6 = struct.unpack('<h', data[off0+6:off0+8])[0]
print(f'Bytes 6-7: {val6}')

# 如果 w 和 h 不是宽高，让我们尝试不同的解释
# 根据反编译：a2是资源数据指针，*a2和a2[1]是宽高
# 也许资源数据从某个偏移开始？

# 检查是否资源0有内部偏移表
print(f'\nChecking possible internal structure:')
print(f'First 20 WORDs:')
for i in range(20):
    val = struct.unpack('<h', data[off0+i*2:off0+i*2+2])[0]
    print(f'  [{i}] {val} (0x{val & 0xFFFF:04X})')

# 让我们检查资源0中是否有明显的图像数据模式
# 从字节48开始检查（假设前48字节是头部/偏移表）
print(f'\nChecking data starting from byte 48:')
for i in range(20):
    val = struct.unpack('<h', data[off0+48+i*2:off0+48+i*2+2])[0]
    print(f'  [{48+i*2}] {val}')
