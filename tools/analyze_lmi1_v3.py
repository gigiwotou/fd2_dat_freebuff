"""
验证资源#8的LMI1菜单资源集结构
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
    
    print(f'Resource #8 (LMI1 menu set): size={size8} bytes\n')
    
    f.seek(start8)
    data = f.read(size8)
    
    # Structure:
    # Bytes 0-3: "LMI1" magic
    # Bytes 4-5: First sub-resource start offset (12)
    # Bytes 6-7: First sub-resource end offset (58)
    # Bytes 8-9: Second sub-resource end offset (132)
    # ... etc (7 pairs total)
    # Bytes 32+: Some metadata
    # Bytes 40+: Sub-resource data
    
    # Parse sub-resource boundaries
    sub_starts = [12]  # First starts at 12
    sub_ends = []
    
    for i in range(7):
        pos = 4 + (i+1) * 2  # 6, 8, 10, 12, 14, 16, 18
        end = struct.unpack('<H', data[pos:pos+2])[0]
        sub_ends.append(end)
        if i < 6:
            sub_starts.append(end)
    
    print(f'Sub-resource boundaries:')
    print(f'  Starts: {sub_starts}')
    print(f'  Ends:   {sub_ends}')
    print()
    
    # Now extract and analyze each sub-resource
    for i in range(7):
        start = sub_starts[i]
        end = sub_ends[i]
        size = end - start
        
        print(f'Sub-resource {i}: offset {start}-{end}, size={size} bytes')
        
        if size > 0 and end <= size8:
            # Check if it's an image with header
            # Format might be: width(2) + height(2) + pixel_data
            w = data[start] | (data[start+1] << 8)
            h = data[start+2] | (data[start+3] << 8)
            
            print(f'  Header: w={w}, h={h}')
            print(f'  Expected pixel size: {w*h} bytes')
            print(f'  Actual size: {size} bytes')
            
            # Print first 20 bytes
            print(f'  Data: {data[start:start+20].hex()}')
            print()
