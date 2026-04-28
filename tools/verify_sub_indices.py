import struct

fdother_path = r"d:\testworkspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

with open(fdother_path, 'rb') as f:
    # Read FDOTHER header
    magic = f.read(6)
    entry_count = struct.unpack('<I', f.read(4))[0]
    
    # Read all offsets
    offsets = []
    for i in range(entry_count):
        off = struct.unpack('<I', f.read(4))[0]
        offsets.append(off)
    
    # Resource 6 is at offsets[6]
    res6_offset = offsets[6]
    res7_offset = offsets[7] if 7 < entry_count else len(open(fdother_path, 'rb').read())
    res6_size = res7_offset - res6_offset
    
    print(f"Resource 6: file_offset={res6_offset}, size={res6_size}")
    
    # Read resource 6
    f.seek(res6_offset)
    res6 = f.read(res6_size)
    
    print(f"Magic: {res6[0:6]}")
    count = struct.unpack('<I', res6[6:10])[0]
    print(f"Sub-resource count: {count}")
    
    # Offset table starts at byte 6 (matches IDA formula: a3 + 4*sub_idx + 6)
    print(f"\nSub-resources (using offset_table = dat + 6):")
    for sub_idx in range(1, 8):
        off_pos = 6 + sub_idx * 4
        if off_pos + 4 > res6_size:
            print(f"  sub[{sub_idx}]: offset position {off_pos} out of range")
            break
        offset = struct.unpack('<I', res6[off_pos:off_pos+4])[0]
        print(f"  sub[{sub_idx}]: offset={offset}", end="")
        
        if offset < res6_size:
            w = struct.unpack('<H', res6[offset:offset+2])[0]
            h = struct.unpack('<H', res6[offset+2:offset+4])[0]
            print(f", {w}x{h}")
        else:
            print(f", INVALID (>= {res6_size})")
