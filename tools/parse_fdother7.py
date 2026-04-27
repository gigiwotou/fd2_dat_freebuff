import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # Read header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read all offsets
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Resource #7
    start7 = offsets[7]
    end7 = offsets[8] if 8 < count else os.path.getsize(dat_path)
    size7 = end7 - start7
    
    print(f'Resource #7: offset={start7}, size={size7} bytes')
    
    f.seek(start7)
    data = f.read(size7)
    
    # FDOTHER #7 structure:
    # Bytes 0-43: 14 x 3-byte LE offsets (7 pairs)
    # Bytes 44+: RLE image data for 7 sub-resources
    
    print(f'\n14 sub-resource offsets (3-byte LE):')
    sub_offsets = []
    for i in range(14):
        pos = i * 3
        val = data[pos] | (data[pos+1] << 8) | (data[pos+2] << 16)
        sub_offsets.append(val)
        print(f'  [{i}] = 0x{val:04x} ({val})')
    
    print(f'\n7 sub-resource images:')
    for i in range(7):
        img_start = sub_offsets[i*2]
        img_end = sub_offsets[i*2+1]
        img_size = img_end - img_start
        
        print(f'\n  Image {i}: offset 0x{img_start:04x}-0x{img_end:04x}, size={img_size} bytes')
        
        if img_size >= 4:
            # RLE image header: width(2) + height(2) in little-endian
            w = data[img_start] | (data[img_start+1] << 8)
            h = data[img_start+2] | (data[img_start+3] << 8)
            print(f'    Dimensions: {w}x{h}')
            print(f'    First 16 bytes: {data[img_start:img_start+16].hex()}')
