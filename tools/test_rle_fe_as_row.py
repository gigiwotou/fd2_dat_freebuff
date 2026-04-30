"""Try treating 0xFE as regular pixel value, not special."""

import struct

def test_v14(seg_data):
    """0xFE is regular pixel, no special meaning. bit7=cmd, bit6=fill/copy, count=low6+1"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            count = (cmd & 0x3F) + 1
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
            # Single pixel (including 0xFE)
            pixels.append(cmd)
        
        if len(pixels) >= 600:
            break
    
    return pixels

def test_v15(seg_data):
    """count = low6, no +1"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            count = cmd & 0x3F
            if count == 0:
                count = 64
            if cmd & 0x40:
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    pixels.extend([value] * count)
            else:
                for _ in range(count):
                    if ptr < len(seg_data):
                        pixels.append(seg_data[ptr])
                        ptr += 1
        else:
            pixels.append(cmd)
        
        if len(pixels) >= 600:
            break
    
    return pixels

def test_v16(seg_data):
    """Try: 0xFE = row terminator, skip to next row"""
    pixels = []
    ptr = 0
    row = 0
    col = 0
    
    while ptr < len(seg_data) and row < 24:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            # End of row, skip to next
            col = 0
            row += 1
        elif cmd & 0x80:
            count = (cmd & 0x3F) + 1
            if cmd & 0x40:
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    for _ in range(count):
                        if row < 24 and col < 24:
                            pixels.append(value)
                            col += 1
                        if col >= 24:
                            col = 0
                            row += 1
            else:
                for _ in range(count):
                    if ptr < len(seg_data) and row < 24 and col < 24:
                        pixels.append(seg_data[ptr])
                        ptr += 1
                        col += 1
                    if col >= 24:
                        col = 0
                        row += 1
        else:
            if row < 24 and col < 24:
                pixels.append(cmd)
                col += 1
            if col >= 24:
                col = 0
                row += 1
    
    return pixels

def test_v17(seg_data):
    """0xFE = row terminator (v16) but count = low6, no +1"""
    pixels = []
    ptr = 0
    row = 0
    col = 0
    
    while ptr < len(seg_data) and row < 24:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            col = 0
            row += 1
        elif cmd & 0x80:
            count = cmd & 0x3F
            if count == 0:
                count = 64
            if cmd & 0x40:
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    for _ in range(count):
                        if row < 24 and col < 24:
                            pixels.append(value)
                            col += 1
                        if col >= 24:
                            col = 0
                            row += 1
            else:
                for _ in range(count):
                    if ptr < len(seg_data) and row < 24 and col < 24:
                        pixels.append(seg_data[ptr])
                        ptr += 1
                        col += 1
                    if col >= 24:
                        col = 0
                        row += 1
        else:
            if row < 24 and col < 24:
                pixels.append(cmd)
                col += 1
            if col >= 24:
                col = 0
                row += 1
    
    return pixels

def test_v18(seg_data):
    """0xFE = row terminator, but fill/copy respects row boundaries"""
    pixels = [0] * 576  # 24x24
    ptr = 0
    row = 0
    col = 0
    
    while ptr < len(seg_data) and row < 24:
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            # Skip to next row
            col = 0
            row += 1
        elif cmd & 0x80:
            count = (cmd & 0x3F) + 1
            if cmd & 0x40:
                if ptr < len(seg_data):
                    value = seg_data[ptr]
                    ptr += 1
                    for _ in range(count):
                        if row < 24 and col < 24:
                            pixels[row * 24 + col] = value
                            col += 1
                        if col >= 24:
                            col = 0
                            row += 1
                            if row >= 24:
                                break
            else:
                for _ in range(count):
                    if ptr < len(seg_data) and row < 24 and col < 24:
                        pixels[row * 24 + col] = seg_data[ptr]
                        ptr += 1
                        col += 1
                    if col >= 24:
                        col = 0
                        row += 1
                        if row >= 24:
                            break
        else:
            if row < 24 and col < 24:
                pixels[row * 24 + col] = cmd
                col += 1
            if col >= 24:
                col = 0
                row += 1
    
    return pixels

def main():
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    # Test first segment
    seg_data = data[offsets[0]:offsets[1]]
    
    print(f"Icon 0, Front Frame0 ({len(seg_data)} bytes)")
    print(f"First 30 bytes: {' '.join(f'{b:02x}' for b in seg_data[:30])}")
    
    for name, func in [("v14", test_v14), ("v15", test_v15),
                       ("v16", test_v16), ("v17", test_v17),
                       ("v18", test_v18)]:
        pixels = func(seg_data)
        status = "✓" if len(pixels) == 576 else " "
        print(f"  {status} {name}: {len(pixels)} pixels")
        
        if len(pixels) == 576:
            non_zero = sum(1 for p in pixels if p != 0)
            print(f"      Non-zero: {non_zero}")
            print(f"      First 2 rows:")
            for r in range(2):
                row = pixels[r*24:(r+1)*24]
                print(f"        Row {r}: {' '.join(f'{p:02x}' for p in row)}")

if __name__ == '__main__':
    main()
