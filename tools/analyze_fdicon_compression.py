"""Deep analysis of FDICON.B24 compression format."""

import struct

def analyze_compression(fdicon_path):
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    # Analyze icon 0, segment 0 in detail
    icon_id = 0
    seg_idx = 0
    
    icon_start = offsets[icon_id * 12]
    seg_start = offsets[icon_id * 12 + seg_idx]
    seg_end = offsets[icon_id * 12 + seg_idx + 1]
    seg_data = data[seg_start:seg_end]
    
    print(f"\nIcon {icon_id}, Segment {seg_idx}")
    print(f"Segment size: {len(seg_data)} bytes")
    print(f"\nFull segment data (hex):")
    for i in range(0, len(seg_data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in seg_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in seg_data[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")
    
    # Analyze byte frequency
    print(f"\nByte frequency analysis:")
    freq = {}
    for b in seg_data:
        freq[b] = freq.get(b, 0) + 1
    
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    print(f"Top 20 most frequent bytes:")
    for byte, count in sorted_freq[:20]:
        pct = count * 100.0 / len(seg_data)
        print(f"  0x{byte:02x} ({byte:3d}): {count:4d} times ({pct:5.1f}%)")
    
    # Analyze bit patterns
    print(f"\nBit pattern analysis:")
    bit7_set = sum(1 for b in seg_data if b & 0x80)
    bit6_set = sum(1 for b in seg_data if b & 0x40)
    bit5_set = sum(1 for b in seg_data if b & 0x20)
    
    print(f"  Bit 7 (0x80) set: {bit7_set}/{len(seg_data)} ({bit7_set*100.0/len(seg_data):.1f}%)")
    print(f"  Bit 6 (0x40) set: {bit6_set}/{len(seg_data)} ({bit6_set*100.0/len(seg_data):.1f}%)")
    print(f"  Bit 5 (0x20) set: {bit5_set}/{len(seg_data)} ({bit5_set*100.0/len(seg_data):.1f}%)")
    
    # Analyze high nibble patterns
    print(f"\nHigh nibble (4-bit) distribution:")
    high_nibble_freq = {}
    for b in seg_data:
        nibble = b >> 4
        high_nibble_freq[nibble] = high_nibble_freq.get(nibble, 0) + 1
    
    for nibble in range(16):
        count = high_nibble_freq.get(nibble, 0)
        if count > 0:
            pct = count * 100.0 / len(seg_data)
            start_val = nibble * 16
            end_val = nibble * 16 + 15
            print(f"  0x{start_val:02x}-0x{end_val:02x}: {count:4d} times ({pct:5.1f}%)")
    
    # Try to find pattern: look for 0xfe sequences
    print(f"\n0xfe byte positions (first 20):")
    fe_positions = [i for i, b in enumerate(seg_data) if b == 0xfe][:20]
    print(f"  {fe_positions}")
    
    # Analyze bytes before and after 0xfe
    print(f"\nContext around 0xfe bytes:")
    for pos in fe_positions[:10]:
        before = seg_data[pos-1] if pos > 0 else None
        after = seg_data[pos+1] if pos < len(seg_data) - 1 else None
        if before is not None and after is not None:
            print(f"  Position {pos:3d}: ... 0x{before:02x} [0xfe] 0x{after:02x} ...")
    
    # Try RLE decode with different algorithms
    print(f"\n{'='*60}")
    print("Testing RLE decode algorithms...")
    print(f"{'='*60}")
    
    # Algorithm 1: Check if first bytes are header
    print(f"\nAlgorithm: Check header structure")
    print(f"  First 4 bytes: {seg_data[0]:02x} {seg_data[1]:02x} {seg_data[2]:02x} {seg_data[3]:02x}")
    print(f"  As DWORD: 0x{struct.unpack('<I', seg_data[0:4])[0]:08x}")
    print(f"  As WORDs: 0x{struct.unpack('<H', seg_data[0:2])[0]:04x} 0x{struct.unpack('<H', seg_data[2:4])[0]:04x}")
    
    # Algorithm 2: Try RLE with 0xfe as transparent
    print(f"\nAlgorithm 2: RLE with 0xfe as transparent marker")
    ptr = 0
    pixel_count = 0
    while ptr < len(seg_data) and pixel_count < 600:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            pixel_count += 1  # Skip 1 pixel
        elif cmd & 0x80:
            # High bit set: run-length command
            if cmd & 0x40:
                # 0xC0+: fill with value
                count = (cmd & 0x3F) + 1
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    if value != 0xfe:
                        pixel_count += count
                    else:
                        pixel_count += count
            else:
                # 0x80-0xBF: copy raw bytes
                count = (cmd & 0x3F) + 1
                ptr += count
                pixel_count += count
        else:
            # Single pixel
            pixel_count += 1
    
    print(f"  Decoded {pixel_count} pixels")
    if pixel_count == 576:
        print(f"  ✓ PERFECT MATCH! 24x24 = 576 pixels")
    
    # Algorithm 3: Analyze command patterns more carefully
    print(f"\nAlgorithm 3: Detailed command analysis")
    ptr = 0
    commands = []
    while ptr < len(seg_data) and ptr < 100:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            if cmd & 0x40:
                # Fill command
                count = (cmd & 0x3F) + 1
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    commands.append(('FILL', count, value))
            else:
                # Copy command
                count = (cmd & 0x3F) + 1
                commands.append(('COPY', count, None))
                ptr += count
        else:
            commands.append(('PIXEL', 1, cmd))
    
    print(f"  First 20 commands:")
    for i, (cmd_type, count, value) in enumerate(commands[:20]):
        if cmd_type == 'FILL':
            print(f"    {i:2d}: {cmd_type} count={count}, value=0x{value:02x}")
        elif cmd_type == 'COPY':
            print(f"    {i:2d}: {cmd_type} count={count}")
        else:
            print(f"    {i:2d}: {cmd_type} value=0x{value:02x}")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    analyze_compression(fdicon_path)
