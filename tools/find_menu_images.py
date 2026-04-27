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
    
    print(f'Total resources: {count}')
    print(f'\nSearching for menu-related resources:')
    print(f'Looking for RLE images with reasonable dimensions...\n')
    
    menu_candidates = []
    
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        # Check for palette (768 bytes)
        if size == 768:
            f.seek(start)
            pal_data = f.read(768)
            # Check if first 16 entries are gradient red
            is_gradient = True
            for j in range(15):
                r1, g1, b1 = pal_data[j*3], pal_data[j*3+1], pal_data[j*3+2]
                r2, g2, b2 = pal_data[(j+1)*3], pal_data[(j+1)*3+1], pal_data[(j+1)*3+2]
                if not (r2 > r1 and g1 == 0 and b1 == 0):
                    is_gradient = False
                    break
            
            if is_gradient:
                print(f'Resource {i}: 768 bytes - GRADIENT PALETTE (likely for fade effects)')
            continue
        
        # Check for RLE images
        if size >= 4:
            f.seek(start)
            header = f.read(4)
            w = header[0] | (header[1] << 8)
            h = header[2] | (header[3] << 8)
            
            # Menu items are typically small (under 320x50)
            # Menu background is 320x200
            if w > 0 and w <= 320 and h > 0 and h <= 200:
                menu_candidates.append((i, w, h, size))
    
    # Print menu candidates sorted by size
    print(f'\nPotential menu image resources:')
    print(f'{"Index":<8} {"Width":<8} {"Height":<8} {"Size":<10}')
    print(f'{"-"*40}')
    for idx, w, h, size in sorted(menu_candidates, key=lambda x: x[3]):
        if h <= 20:
            tag = 'MENU ITEM?'
        elif h <= 100:
            tag = 'MEDIUM IMAGE'
        else:
            tag = 'LARGE IMAGE'
        print(f'{idx:<8} {w:<8} {h:<8} {size:<10} {tag}')
