import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f'FDOTHER.DAT: {count} resources, file size: {len(data)}')

# 查找调色板资源（通常是768字节 = 256颜色 * 3）
print(f'\nSearching for palette resources (768 bytes):')
for i in range(count-1):
    off_start = struct.unpack('<I', data[10+i*4:14+i*4])[0]
    off_end = struct.unpack('<I', data[10+(i+1)*4:14+(i+1)*4])[0]
    size = off_end - off_start
    
    if size == 768:
        print(f'  [{i}] offset={off_start}, size=768 (PALETTE)')
    
    if i < 20:
        print(f'  [{i}] offset={off_start}, size={size}')
