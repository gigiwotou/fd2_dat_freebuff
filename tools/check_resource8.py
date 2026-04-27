"""
验证FDOTHER #8是否是资源集
"""
import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Check resource #8 in detail
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    
    print(f'Resource #8: offset={start8}, size={size8} bytes')
    
    f.seek(start8)
    data = f.read(min(1000, size8))
    
    print(f'\nFirst 64 bytes:')
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        print(f'  {i:04x}: {hex_str}')
    
    # Check header
    print(f'\nHeader analysis:')
    print(f'  Bytes 0-3: {data[0:4].hex()} = "{chr(data[0])}{chr(data[1])}{chr(data[2])}{chr(data[3])}"')
    
    # Check if it has RLE-like structure
    w = data[4] | (data[5] << 8)  # "0c00" = 12
    h = data[6] | (data[7] << 8)  # "3a00" = 58
    print(f'  Possible dims at offset 4: {w}x{h}')
    
    # If size is 3999, check what structure it has
    print(f'\nSize: {size8} bytes')
    if size8 == 3999:
        print(f'  3999 / 7 = {3999/7:.1f}')
        print(f'  3999 / 13 = {3999/13:.1f}')
