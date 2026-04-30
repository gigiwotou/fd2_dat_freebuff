"""Test different RLE decoding algorithms with transparent pixel handling."""

import struct

def test_v4(seg_data):
    """0xfe = skip, other bytes: bit7=fill, bit6=raw, count+1"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            # Transparent/skip
            pixels.append(0)
        elif cmd & 0x80:
            count = (cmd & 0x7F) + 1
            if cmd & 0x40:
                # Fill
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    pixels.extend([value] * count)
            else:
                # Raw copy
                for _ in range(count):
                    if ptr < len(seg_data):
                        pixels.append(seg_data[ptr])
                        ptr += 1
        else:
            pixels.append(cmd)
        
        if len(pixels) > 600:
            break
    
    return pixels

def test_v5(seg_data):
    """0xfe = skip, others: bit7=cmd, bit6=type, count+1"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            pixels.append(0)
        elif cmd & 0x80:
            count = (cmd & 0x3F) + 1
            if cmd & 0x40:
                # 11 or 10: fill with next byte
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    pixels.extend([value] * count)
            else:
                # 01: copy next count bytes
                for _ in range(count):
                    if ptr < len(seg_data):
                        pixels.append(seg_data[ptr])
                        ptr += 1
        else:
            # 00: single pixel
            pixels.append(cmd)
        
        if len(pixels) > 600:
            break
    
    return pixels

def test_v6(seg_data):
    """Check if 0xfe is part of RLE command, not separate skip"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            count = (cmd & 0x7F)
            if count == 0:
                count = 128
            
            if cmd & 0x40:
                # Fill
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    if value == 0xfe:
                        # Transparent fill
                        pixels.extend([0] * count)
                    else:
                        pixels.extend([value] * count)
            else:
                # Raw
                for _ in range(count):
                    if ptr < len(seg_data):
                        val = seg_data[ptr]
                        ptr += 1
                        pixels.append(0 if val == 0xfe else val)
        else:
            pixels.append(cmd)
        
        if len(pixels) > 600:
            break
    
    return pixels

def test_v7(seg_data):
    """Try different count calculation"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            # Command byte
            if cmd & 0x40:
                # Fill: next byte is value, count from low 6 bits
                count = (cmd & 0x3F)
                if count == 0:
                    count = 64
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    pixels.extend([value] * count)
            else:
                # Raw copy
                count = (cmd & 0x3F)
                if count == 0:
                    count = 64
                for _ in range(count):
                    if ptr < len(seg_data):
                        pixels.append(seg_data[ptr])
                        ptr += 1
        else:
            pixels.append(cmd)
        
        if len(pixels) > 600:
            break
    
    return pixels

def test_v8(seg_data):
    """0xfe embedded as fill value in RLE"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            if cmd & 0x40:
                count = (cmd & 0x3F) + 1
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    # 0xfe = transparent
                    if value == 0xfe:
                        pixels.extend([0] * count)
                    else:
                        pixels.extend([value] * count)
            else:
                count = (cmd & 0x3F) + 1
                for _ in range(count):
                    if ptr < len(seg_data):
                        val = seg_data[ptr]
                        ptr += 1
                        pixels.append(0 if val == 0xfe else val)
        else:
            pixels.append(cmd)
        
        if len(pixels) > 600:
            break
    
    return pixels

def main():
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    # Read offsets
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    # Test all segments of icon 0
    for seg_idx in range(12):
        seg_data = data[offsets[seg_idx]:offsets[seg_idx + 1]]
        dir_name = ['Front', 'Left', 'Back', 'Right'][seg_idx // 3]
        frame_name = f'Frame{seg_idx % 3}'
        
        print(f"\n{'='*60}")
        print(f"Icon 0, {dir_name} {frame_name} ({len(seg_data)} bytes)")
        print(f"{'='*60}")
        
        for name, func in [("v4", test_v4), ("v5", test_v5), 
                           ("v6", test_v6), ("v7", test_v7), ("v8", test_v8)]:
            pixels = func(seg_data)
            status = "✓" if len(pixels) == 576 else " "
            print(f"  {status} {name}: {len(pixels)} pixels")
            
            if len(pixels) == 576:
                # Show first few rows
                non_zero = sum(1 for p in pixels if p != 0)
                print(f"      Non-zero: {non_zero}, First row: {' '.join(f'{p:02x}' for p in pixels[:24])}")

if __name__ == '__main__':
    main()
