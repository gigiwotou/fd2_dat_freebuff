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
    
    # Resource 6
    res6_offset = offsets[6]
    res7_offset = offsets[7]
    res6_size = res7_offset - res6_offset
    
    f.seek(res6_offset)
    res6 = f.read(res6_size)
    
    print(f"Resource 6: size={res6_size}")
    print(f"Magic: {res6[0:6]}")
    count = struct.unpack('<I', res6[6:10])[0]
    print(f"Count: {count}")
    
    # Check what's at offset 38
    print(f"\nAt offset 38:")
    print(f"  Bytes: {res6[38:46].hex()}")
    w = struct.unpack('<H', res6[38:40])[0]
    h = struct.unpack('<H', res6[40:42])[0]
    print(f"  Possible dimensions: {w}x{h}")
    
    # Check offset table entries
    print(f"\nOffset table (starting at byte 6):")
    for i in range(8):
        off_pos = 6 + i * 4
        offset = struct.unpack('<I', res6[off_pos:off_pos+4])[0]
        print(f"  [{i}] byte_pos={off_pos}: offset={offset}", end="")
        
        if offset < res6_size and offset > 10:
            w = struct.unpack('<H', res6[offset:offset+2])[0]
            h = struct.unpack('<H', res6[offset+2:offset+4])[0]
            print(f", {w}x{h}")
        else:
            print("")
