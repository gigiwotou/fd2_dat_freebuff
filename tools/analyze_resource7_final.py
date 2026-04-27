"""
分析FDOTHER.DAT的资源#7结构
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
    
    print('FDOTHER.DAT: {} resources\n'.format(count))
    
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print('Resource #7:')
    print('  Position in file: {}'.format(start7))
    print('  Size: {} bytes'.format(size7))
    
    if size7 == 768:
        print('  This is exactly 256 colors * 3 bytes = PALETTE')
        print('\nPALETTE DATA (first 16 entries):')
        f.seek(start7)
        pal = f.read(768)
        for i in range(16):
            r, g, b = pal[i*3], pal[i*3+1], pal[i*3+2]
            print('  [{:2d}] = ({:3d}, {:3d}, {:3d})'.format(i, r, g, b))
        
        print('\nConclusion: Resource #7 is a PALETTE, not a resource set!')
        print('The user might be mistaken, or there is a different interpretation.')
