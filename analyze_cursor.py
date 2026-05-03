import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    # Check what's at file offset 8960 (0x2300)
    f.seek(8960)
    data = f.read(64)
    print(f'File offset 8960 (0x2300) bytes (first 64):')
    print(' '.join(f'{b:02X}' for b in data))
    
    # Try to parse as image header
    if len(data) >= 4:
        w = struct.unpack('<H', data[:2])[0]
        h = struct.unpack('<H', data[2:4])[0]
        print(f'As uint16 width: {w}, height: {h}')
    
    # Check what resource this offset falls into
    f.seek(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    for i in range(len(offsets)-1):
        if offsets[i] <= 8960 < offsets[i+1]:
            print(f'\nOffset 8960 falls within Resource {i}')
            print(f'Resource {i}: file_offset={offsets[i]} (0x{offsets[i]:04X})')
            print(f'Offset 8960 is {8960 - offsets[i]} bytes into Resource {i}')
            break
    else:
        if 8960 >= offsets[-1]:
            print(f'\nOffset 8960 falls within Resource {len(offsets)-1} or beyond')
        else:
            print(f'\nOffset 8960 is before first resource')
    
    # Also check: what if dword_53A81 points to Resource 1?
    res1_start = offsets[1]
    res1_offset_526 = res1_start + 526
    f.seek(res1_offset_526)
    bytes_res1_526 = f.read(8)
    val_res1_526 = struct.unpack('<I', bytes_res1_526[:4])[0]
    print(f'\n\nIf dword_53A81 = Resource 1 data (offset {res1_start}):')
    print(f'Resource 1 + offset 526 = file offset {res1_offset_526} (0x{res1_offset_526:04X})')
    print(f'Bytes: {" ".join(f"{b:02X}" for b in bytes_res1_526)}')
    print(f'Value: {val_res1_526} (0x{val_res1_526:04X})')
    
    # Check Resource 0 internal structure
    res0_start = offsets[0]
    res0_size = offsets[1] - res0_start
    f.seek(res0_start)
    res0_data = f.read(res0_size)
    print(f'\n\nResource 0 (size {res0_size}) first 32 bytes:')
    print(' '.join(f'{b:02X}' for b in res0_data[:32]))
    
    # Check if Resource 0 has an internal offset table
    # If first 4 bytes are an offset...
    if res0_size >= 4:
        internal_off = struct.unpack('<I', res0_data[:4])[0]
        print(f'First 4 bytes as uint32: {internal_off} (0x{internal_off:04X})')
        if internal_off < res0_size:
            print(f'This could be an internal offset pointing to {internal_off} within Resource 0')
            target = res0_start + internal_off
            f.seek(target)
            target_data = f.read(32)
            print(f'Data at file offset {target} (0x{target:04X}):')
            print(' '.join(f'{b:02X}' for b in target_data))
            w = struct.unpack('<H', target_data[:2])[0]
            h = struct.unpack('<H', target_data[2:4])[0]
            print(f'As dimensions: {w}x{h}')
