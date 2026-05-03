import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    # Parse header
    f.seek(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read offset table
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Resource 1
    res1_start = offsets[1]
    res1_size = offsets[2] - res1_start
    print(f"Resource 1: file_offset={res1_start} (0x{res1_start:04X}), size={res1_size}")
    
    # Read internal offset table (32-bit entries)
    f.seek(res1_start)
    res1_data = f.read(res1_size)
    
    # Count how many 32-bit offsets
    num_offsets = 0
    offset_list = []
    pos = 0
    while pos + 4 <= len(res1_data):
        off = struct.unpack('<I', res1_data[pos:pos+4])[0]
        if off >= res1_size:
            break
        offset_list.append(off)
        num_offsets += 1
        pos += 4
        if num_offsets >= 100:
            break
    
    print(f"Resource 1 has {num_offsets} internal 32-bit offsets")
    
    # Check each sub-resource for 24x24 dimensions
    print("\nSearching for 24x24 sub-resources:")
    for i, off in enumerate(offset_list[:20]):
        sub_data = res1_data[off:off+8]
        if len(sub_data) < 4:
            continue
        w = struct.unpack('<H', sub_data[0:2])[0]
        h = struct.unpack('<H', sub_data[2:4])[0]
        marker = " <-- FOUND!" if w == 24 and h == 24 else ""
        print(f"  Sub-resource {i}: offset={off} (0x{off:04X}), dimensions={w}x{h}{marker}")
    
    # Also check: what's at file offset 0x2300 (8960)?
    f.seek(0x2300)
    data_at_2300 = f.read(64)
    print(f"\nFile offset 0x2300 (8960) data (first 64 bytes):")
    print(' '.join(f'{b:02X}' for b in data_at_2300))
    
    # Check if this falls in Resource 1
    if res1_start <= 0x2300 < res1_start + res1_size:
        rel_off = 0x2300 - res1_start
        print(f"This is inside Resource 1, relative offset={rel_off} (0x{rel_off:04X})")
        
        # Check if it's one of the sub-resources
        for i, off in enumerate(offset_list):
            if off == rel_off:
                print(f"  -> This is sub-resource {i}!")
                w = struct.unpack('<H', data_at_2300[0:2])[0]
                h = struct.unpack('<H', data_at_2300[2:4])[0]
                print(f"  -> Dimensions: {w}x{h}")
                break
        
        # Also check nearby sub-resources for 24x24
        print("\nChecking all sub-resources for 24x24:")
        for i, off in enumerate(offset_list):
            abs_off = res1_start + off
            f.seek(abs_off)
            sub_header = f.read(4)
            if len(sub_header) < 4:
                continue
            w = struct.unpack('<H', sub_header[0:2])[0]
            h = struct.unpack('<H', sub_header[2:4])[0]
            if w == 24 and h == 24:
                print(f"  Sub-resource {i}: offset={off} (0x{off:04X}), file_offset={abs_off} (0x{abs_off:04X}), dimensions={w}x{h} <-- 24x24!")
                # Show first 32 bytes of RLE data
                f.seek(abs_off + 4)
                rle_data = f.read(32)
                print(f"    RLE data: {' '.join(f'{b:02X}' for b in rle_data)}")
