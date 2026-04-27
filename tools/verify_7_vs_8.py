"""
验证FDOTHER.DAT偏移表中#7和#8的资源
"""
import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    print('Magic: {}'.format(magic))
    print('Resource count: {}\n'.format(count))
    
    # Read offset table
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Check resource #7
    print('Resource #7:')
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    print('  File offset: {}'.format(start7))
    print('  Size: {} bytes'.format(size7))
    
    f.seek(start7)
    data7 = f.read(min(32, size7))
    print('  Header: {}'.format(data7.hex()))
    if size7 == 768:
        print('  -> This is a 256-color PALETTE')
    print()
    
    # Check resource #8
    print('Resource #8:')
    start8 = offsets[8]
    end8 = offsets[9] if 9 < count else os.path.getsize(dat_path)
    size8 = end8 - start8
    print('  File offset: {}'.format(start8))
    print('  Size: {} bytes'.format(size8))
    
    f.seek(start8)
    data8 = f.read(min(64, size8))
    print('  Header: {}'.format(data8.hex()))
    print('  ASCII: {}'.format(data8[:4]))
    if size8 == 3999:
        print('  -> LMI1 format, likely a resource set')
    print()
    
    # Verify which one is the menu resource set
    print('Conclusion:')
    if size7 == 768 and size8 == 3999:
        print('  Resource #7 is a PALETTE (768 bytes = 256 colors * 3)')
        print('  Resource #8 is likely the MENU RESOURCE SET (3999 bytes, LMI1 format)')
        print('')
        print('  If "7号" means index 7 (0-based), then the menu set is #8.')
        print('  If "7号" means "7th resource" (1-based), then it would be #6.')
