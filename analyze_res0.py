import struct

with open('game/FDOTHER.DAT', 'rb') as f:
    # Parse DAT header
    f.seek(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read offset table
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    # Resource 0
    res0_file_off = offsets[0]
    res0_size = offsets[1] - res0_file_off if len(offsets) > 1 else 10000
    
    f.seek(res0_file_off)
    res0_data = f.read(res0_size)
    
    print(f'Resource 0: file_offset={res0_file_off} (0x{res0_file_off:04X}), size={res0_size}')
    
    # Resource 0 header
    w = struct.unpack('<H', res0_data[0:2])[0]
    h = struct.unpack('<H', res0_data[2:4])[0]
    print(f'Header: width={w}, height={h}')
    
    # Internal offsets at positions 4, 6, 8... (16-bit)
    off_20 = struct.unpack('<H', res0_data[4:6])[0]  # 0x14 = 20
    off_86 = struct.unpack('<H', res0_data[6:8])[0]  # 0x56 = 86
    
    print(f'\nInternal offset 0: {off_20} (0x{off_20:02X})')
    print(f'Internal offset 1: {off_86} (0x{off_86:02X})')
    
    # Check data at internal offset 20
    f.seek(res0_file_off + off_20)
    data_at_20 = f.read(100)
    print(f'\nData at res0+{off_20} (file offset {res0_file_off + off_20}):')
    print(' '.join(f'{b:02X}' for b in data_at_20[:40]))
    
    # Maybe this is RLE data directly
    # Let's try to decode a few RLE commands
    print(f'\nTrying to decode RLE from offset {off_20}:')
    pos = 0
    total_pixels = 0
    for frame in range(3):
        frame_pos = pos
        row = 0
        while row < h and pos < len(data_at_20):
            opcode = data_at_20[pos]
            pos += 1
            bit7 = (opcode >> 7) & 1
            bit6 = (opcode >> 6) & 1
            cnt = (opcode & 0x3F) + 1
            
            if bit7 and bit6:
                # SKIP
                total_pixels += cnt
                print(f'  Frame {frame}, row {row}: SKIP {cnt}')
            elif bit7 and not bit6:
                # COPY
                total_pixels += cnt
                pos += cnt
                print(f'  Frame {frame}, row {row}: COPY {cnt}')
            elif not bit7 and bit6:
                # FILL
                color = data_at_20[pos]
                pos += 1
                total_pixels += cnt
                print(f'  Frame {frame}, row {row}: FILL {cnt} w/ 0x{color:02X}')
            else:
                # ALTERNATE
                color = data_at_20[pos]
                pos += 1
                total_pixels += cnt
                print(f'  Frame {frame}, row {row}: ALT {cnt} w/ 0x{color:02X}')
            
            row += 1
            if row >= h:
                break
        
        print(f'  Frame {frame}: consumed {pos - frame_pos} bytes, {total_pixels} pixels')
        if pos >= len(data_at_20):
            break
