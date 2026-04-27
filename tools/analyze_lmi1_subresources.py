"""
分析LMI1子资源的实际格式
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
    
    f.seek(start8)
    data = f.read(size8)
    
    # Sub-resource boundaries
    sub_starts = [12, 58, 132, 246, 378, 728, 1314]
    sub_ends = [58, 132, 246, 378, 728, 1314, 2209]
    
    print('Analyzing LMI1 sub-resource format:\n')
    
    for i in range(7):
        start = sub_starts[i]
        end = sub_ends[i]
        size = end - start
        
        print(f'Sub-resource {i}: offset {start}-{end}, size={size} bytes')
        
        # Print full hex dump
        print(f'  Full data:')
        chunk = data[start:end]
        for j in range(0, len(chunk), 16):
            hex_str = ' '.join(f'{b:02x}' for b in chunk[j:j+16])
            print(f'    {start+j:04x}: {hex_str}')
        
        # Try different interpretations
        print(f'  Interpretations:')
        
        # Format 1: w(1) + h(1) + pixels
        if size >= 2:
            w1, h1 = data[start], data[start+1]
            print(f'    w(1)+h(1): {w1}x{h1}, pixels={size-2}, expected={w1*h1}')
        
        # Format 2: w(2) + h(2) + pixels
        if size >= 4:
            w2 = data[start] | (data[start+1] << 8)
            h2 = data[start+2] | (data[start+3] << 8)
            print(f'    w(2)+h(2): {w2}x{h2}, pixels={size-4}, expected={w2*h2}')
        
        # Format 3: h(1) + w(1) + pixels
        if size >= 2:
            h3, w3 = data[start], data[start+1]
            print(f'    h(1)+w(1): {w3}x{h3}, pixels={size-2}, expected={w3*h3}')
        
        print()
