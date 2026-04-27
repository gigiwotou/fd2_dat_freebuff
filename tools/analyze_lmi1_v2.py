"""
分析资源#8的LMI1格式 - 使用4字节偏移
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
    
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    
    print(f'Resource #8 (LMI1): size={size8} bytes\n')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Header: LMI1 (4 bytes)
    # Then 7 x 4-byte offsets? Or 14 x 2-byte offsets?
    print('Trying 7 x 4-byte offsets at bytes 4-31:')
    four_byte_offsets = []
    for i in range(7):
        pos = 4 + i * 4
        val = struct.unpack('<I', data[pos:pos+4])[0]
        four_byte_offsets.append(val)
        print(f'  [{i}] = {val} (0x{val:08x})')
    
    print('\nTrying 14 x 2-byte offsets at bytes 4-31:')
    two_byte_offsets = []
    for i in range(14):
        pos = 4 + i * 2
        val = struct.unpack('<H', data[pos:pos+2])[0]
        two_byte_offsets.append(val)
        print(f'  [{i}] = {val} (0x{val:04x})')
    
    # Check if 2-byte offsets at even positions are 0
    print('\nChecking even vs odd 2-byte offsets:')
    even_offsets = [two_byte_offsets[i] for i in range(0, 14, 2)]
    odd_offsets = [two_byte_offsets[i] for i in range(1, 14, 2)]
    print(f'  Even: {even_offsets}')
    print(f'  Odd: {odd_offsets}')
    
    # Maybe structure is: header(4) + 7 images starting at specific positions
    # Check bytes 32+ for image data
    print(f'\nChecking bytes 36-60 for image data:')
    print(f'  Hex: {data[36:60].hex()}')
    
    # First image should start after offset table
    # If 7 images, maybe offset table ends at byte 4 + 7*2 = 18?
    # Let's try: offset table is 14 x 2-byte, but only odd entries are used
    
    # Or maybe structure is different. Let's check sub-resource headers
    print('\nSearching for sub-resource patterns:')
    for i in range(0, min(100, size8-4)):
        w = data[i]
        h = data[i+1]
        if w > 10 and w < 100 and h > 10 and h < 50:
            print(f'  Possible image header at offset {i}: {w}x{h}')
            print(f'    Bytes: {data[i:i+8].hex()}')
