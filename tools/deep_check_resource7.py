import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Check resource #7 structure more carefully
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print(f'Resource #7: offset={start7}, size={size7}')
    print(f'Size 768 = 256 colors * 3 bytes = PALETTE')
    print(f'\nBut user says #7 is a resource set with 7 images...')
    print(f'Let me check if the data at offsets[7] points to actual image data')
    
    # The offset formula in sub_16886:
    # resource_address = *(DWORD*)(FDOTHER_ptr + 4*index + 6) + FDOTHER_ptr
    
    # For index=7:
    # offset_7 = *(DWORD*)(FDOTHER_ptr + 4*7 + 6) = *(DWORD*)(FDOTHER_ptr + 34)
    # resource_addr = offset_7 + FDOTHER_ptr
    
    # Let's check what offset_7 points to
    f.seek(6 + 4 + 7*4)  # Skip magic(6) + count(4) + 7 offsets
    offset_7 = struct.unpack('<I', f.read(4))[0]
    print(f'\nOffset for resource #7 from table: {offset_7}')
    print(f'Resource #7 actual position in file: {offsets[7]}')
    
    # They should match
    if offset_7 == offsets[7]:
        print(f'✓ Match!')
    
    # Now let's check if resource #7 might actually be a container
    f.seek(offsets[7])
    data = f.read(size7)
    
    print(f'\nFirst 48 bytes of resource #7:')
    for i in range(0, 48, 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f'  {i:04x}: {hex_str:<48s}  {ascii_str}')
    
    # Check if first 3 bytes might be an image dimension
    if size7 >= 4:
        w = data[0] | (data[1] << 8)
        h = data[2] | (data[3] << 8)
        print(f'\nIf interpreted as RLE header: w={w}, h={h}')
        
        # Check palette-like data
        if size7 == 768:
            print(f'\nThis is 768 bytes = 256 colors * 3 bytes')
            print(f'First 16 palette entries:')
            for i in range(16):
                r, g, b = data[i*3], data[i*3+1], data[i*3+2]
                print(f'  [{i:2d}] = ({r:3d}, {g:3d}, {b:3d})')
