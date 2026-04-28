import struct

fdother_path = r"d:\testworkspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

# Load FDOTHER.DAT header
with open(fdother_path, 'rb') as f:
    # FDOTHER has LLLLLL header at the start
    magic = f.read(6)
    print(f"FDOTHER.DAT magic: {magic}")
    
    # Read entry count
    entry_count_bytes = f.read(4)
    entry_count = struct.unpack('<I', entry_count_bytes)[0]
    print(f"Entry count: {entry_count}")
    
    # Read all offsets
    offsets = []
    for i in range(entry_count):
        off_bytes = f.read(4)
        off = struct.unpack('<I', off_bytes)[0]
        offsets.append(off)
    
    print(f"\nFirst 15 entries:")
    for i in range(min(15, entry_count)):
        off = offsets[i]
        if i+1 < entry_count:
            next_off = offsets[i+1]
            size = next_off - off
        else:
            size = -1
        
        # Read first few bytes to see the format
        f.seek(off)
        header = f.read(10)
        is_dat = header[0:6] == b'LLLLLL'
        is_lmi1 = header[0:4] == b'LMI1'
        
        fmt = ""
        if is_dat:
            fmt = "DAT"
            count = struct.unpack('<I', header[6:10])[0]
            fmt += f"(count={count})"
        elif is_lmi1:
            fmt = "LMI1"
        
        print(f"  idx={i}: offset={off}, size={size}, {fmt}")
