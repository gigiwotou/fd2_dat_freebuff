"""
详细分析资源#8结构
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
    
    # Resource #8
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    
    print(f'Resource #8: size={size8} bytes\n')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Print full hex dump
    print(f'Full hex dump:')
    for i in range(0, min(size8, 200), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        print(f'  {i:04x}: {hex_str}')
    
    # Check if first 4 bytes after "LMI1" are 2-byte offsets
    print(f'\nParsing after "LMI1" as 2-byte LE offsets:')
    pos = 4
    offsets_2byte = []
    while pos + 2 <= min(size8, 100):
        val = struct.unpack('<H', data[pos:pos+2])[0]
        offsets_2byte.append(val)
        print(f'  [{len(offsets_2byte)-1}] offset 0x{pos:04x} = {val}')
        pos += 2
        if val > size8 and val != 0:
            break
    
    if len(offsets_2byte) > 2:
        print(f'\nFirst few offsets: {[hex(x) for x in offsets_2byte[:8]]}')
        # Check if these define sub-resources
        print(f'\nSub-resource sizes:')
        for i in range(min(7, len(offsets_2byte)-1)):
            start = offsets_2byte[i]
            end = offsets_2byte[i+1]
            if start < size8 and end <= size8:
                size = end - start
                print(f'  [{i}] offset 0x{start:04x}-0x{end:04x}, size={size}')
