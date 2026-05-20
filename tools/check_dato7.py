import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

off0 = struct.unpack('<I', data[10:14])[0]
size0 = struct.unpack('<I', data[14:18])[0] - off0

print(f'Resource 0 size: {size0}')

# 根据反编译代码分析：
# sub_165AC(*a1, a1[1], n2) 中：
# *a1 = 宽度, a1[1] = 高度
# 这些是从资源数据头部读取的

# 检查字节16-19: 50005000
w = struct.unpack('<H', data[off0+16:off0+18])[0]
h = struct.unpack('<H', data[off0+18:off0+20])[0]
print(f'Bytes 16-17: {w} (0x{w:04X})')
print(f'Bytes 18-19: {h} (0x{h:04X})')

# 80x80可能是头像尺寸！
if w == 80 and h == 80:
    print(f'\n*** 80x80 is likely the portrait dimensions! ***')
    # 如果是80x80的8位索引图像，大小应该是 80*80 = 6400 字节
    # 加上头部信息，总大小应该接近 6400 + header_size
    
    # 检查资源0中从字节20开始的数据
    print(f'\nChecking pixel data starting from byte 20:')
    # 如果是8位索引图像，数据应该是0-255范围内的值
    pixel_data = data[off0+20:off0+20+100]
    unique_vals = set(pixel_data)
    print(f'  First 100 bytes: {pixel_data[:20].hex()}...')
    print(f'  Unique values in first 100 bytes: {len(unique_vals)}')
    print(f'  Min: {min(pixel_data)}, Max: {max(pixel_data)}')
    
    # 检查整个资源的数据分布
    all_data = data[off0+20:off0+size0]
    all_unique = set(all_data)
    print(f'\n  Full resource data stats:')
    print(f'  Total bytes: {len(all_data)}')
    print(f'  Expected for 80x80: {80*80} = 6400')
    print(f'  Unique values: {len(all_unique)}')
    print(f'  Min: {min(all_data)}, Max: {max(all_data)}')

# 让我们检查资源1是否也是80x80
off1 = struct.unpack('<I', data[14:18])[0]
off2 = struct.unpack('<I', data[18:22])[0]
size1 = off2 - off1

w1 = struct.unpack('<H', data[off1+16:off1+18])[0]
h1 = struct.unpack('<H', data[off1+18:off1+20])[0]
print(f'\nResource 1: width={w1}, height={h1}, size={size1}')

# 检查前10个资源的宽高
print(f'\nFirst 10 resources dimensions:')
for i in range(10):
    off = struct.unpack('<I', data[10+i*4:14+i*4])[0]
    end = struct.unpack('<I', data[10+(i+1)*4:14+(i+1)*4])[0]
    size = end - off
    
    w = struct.unpack('<H', data[off+16:off+18])[0]
    h = struct.unpack('<H', data[off+18:off+20])[0]
    print(f'  [{i}] {w}x{h}, size={size}')
