import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    # Parse DAT header
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    print(f'Magic: {magic}, Resource count: {count}')
    
    # Read offset table
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'\nFirst 10 resource offsets:')
    for i in range(min(10, count)):
        size = offsets[i+1] - offsets[i] if i+1 < count else 'unknown'
        print(f'  Resource {i}: offset={offsets[i]} (0x{offsets[i]:04X}), size={size}')
    
    # Check what's at offset 526 within the ENTIRE file
    f.seek(526)
    bytes_at_526 = f.read(8)
    val_at_526 = struct.unpack('<I', bytes_at_526[:4])[0]
    print(f'\nRaw file offset 526 bytes: {" ".join(f"{b:02X}" for b in bytes_at_526)}')
    print(f'Value at raw file offset 526 (uint32 LE): {val_at_526} (0x{val_at_526:04X})')
    
    # Check resource 0
    res0_start = offsets[0]
    res0_size = offsets[1] - res0_start if count > 1 else 'unknown'
    print(f'\nResource 0: file_offset={res0_start} (0x{res0_start:04X}), size={res0_size}')
    
    # Check offset 526 within resource 0
    res0_offset_526 = res0_start + 526
    f.seek(res0_offset_526)
    bytes_res0_526 = f.read(8)
    val_res0_526 = struct.unpack('<I', bytes_res0_526[:4])[0]
    print(f'Resource 0 + offset 526 = file offset {res0_offset_526} (0x{res0_offset_526:04X})')
    print(f'Bytes: {" ".join(f"{b:02X}" for b in bytes_res0_526)}')
    print(f'Value: {val_res0_526} (0x{val_res0_526:04X})')
    
    # Check what's at resource 0's offset 526 value
    if isinstance(res0_size, int) and val_res0_526 < res0_size:
        target = res0_start + val_res0_526
        f.seek(target)
        img_header = f.read(8)
        w = struct.unpack('<H', img_header[:2])[0]
        h = struct.unpack('<H', img_header[2:4])[0]
        print(f'\nImage at resource 0 + {val_res0_526} (file offset {target}): {w}x{h}')
        print(f'First 32 bytes: {" ".join(f"{b:02X}" for b in img_header + f.read(24))}')
