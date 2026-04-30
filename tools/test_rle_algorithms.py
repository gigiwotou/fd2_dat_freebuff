"""Test different RLE decoding algorithms for FDICON.B24."""

import struct

def test_algorithm_v1(seg_data):
    """Algorithm v1: bit7=raw copy, bit6=fill, lower bits=count"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data) and len(pixels) < 600:
        cmd = seg_data[ptr]
        ptr += 1
        
        bit7 = (cmd >> 7) & 1
        bit6 = (cmd >> 6) & 1
        count = cmd & 0x3F
        
        if bit7 and bit6:
            # 11: fill with next byte
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                pixels.extend([value] * count)
        elif bit7 and not bit6:
            # 10: raw copy
            for _ in range(count):
                if ptr < len(seg_data):
                    pixels.append(seg_data[ptr])
                    ptr += 1
        elif not bit7 and bit6:
            # 01: fill with next byte
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                pixels.extend([value] * count)
        else:
            # 00: single pixel
            pixels.append(cmd)
    
    return pixels

def test_algorithm_v2(seg_data):
    """Algorithm v2: bit7=raw, bit6=fill, count+1"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data) and len(pixels) < 600:
        cmd = seg_data[ptr]
        ptr += 1
        
        bit7 = (cmd >> 7) & 1
        bit6 = (cmd >> 6) & 1
        count = (cmd & 0x3F) + 1
        
        if bit7 and bit6:
            # 11: fill with next byte
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                pixels.extend([value] * count)
        elif bit7 and not bit6:
            # 10: raw copy
            for _ in range(count):
                if ptr < len(seg_data):
                    pixels.append(seg_data[ptr])
                    ptr += 1
        elif not bit7 and bit6:
            # 01: fill with next byte
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                pixels.extend([value] * count)
        else:
            # 00: single pixel
            pixels.append(cmd)
    
    return pixels

def test_algorithm_v3(seg_data):
    """Algorithm v3: 0xfe = skip/transparent, others as v2"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data) and len(pixels) < 600:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            # Skip/transparent
            pixels.append(0)
        elif cmd & 0x80:
            if cmd & 0x40:
                # 11: fill
                count = (cmd & 0x3F) + 1
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    pixels.extend([value] * count)
            else:
                # 10: raw
                count = (cmd & 0x3F) + 1
                for _ in range(count):
                    if ptr < len(seg_data):
                        pixels.append(seg_data[ptr])
                        ptr += 1
        else:
            # Single pixel
            pixels.append(cmd)
    
    return pixels

def main():
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    # Read offset table
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    # Test on icon 0, segment 0
    seg_data = data[offsets[0]:offsets[1]]
    
    print(f"Segment 0 size: {len(seg_data)} bytes")
    print(f"First 20 bytes: {' '.join(f'{b:02x}' for b in seg_data[:20])}")
    
    # Test all algorithms
    for name, func in [("v1", test_algorithm_v1), 
                       ("v2", test_algorithm_v2), 
                       ("v3", test_algorithm_v3)]:
        pixels = func(seg_data)
        print(f"\nAlgorithm {name}: {len(pixels)} pixels")
        if len(pixels) == 576:
            print(f"  ✓ PERFECT! 24x24 = 576")
            # Show first row
            print(f"  First row (24 pixels): {' '.join(f'{p:02x}' for p in pixels[:24])}")
        elif 550 <= len(pixels) <= 580:
            print(f"  Close to 576!")

if __name__ == '__main__':
    main()
