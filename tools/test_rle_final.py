"""Try more RLE algorithm variations to find 576 pixel match."""

import struct

def test_v9(seg_data):
    """count = cmd & 0x3F, no +1"""
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

def test_v10(seg_data):
    """count = (cmd >> 4) & 0x0F"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            count = (cmd >> 4) & 0x0F
            if count == 0:
                count = 16
            
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

def test_v11(seg_data):
    """count from lower nibble only"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd & 0x80:
            count = cmd & 0x0F
            if count == 0:
                count = 16
            
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

def test_v12(seg_data):
    """Special handling: 0xC0-0xCF = fill, 0x80-0x8F = copy, 0x90-0xBF = other"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd >= 0xC0:
            # Fill command
            count = cmd - 0xC0 + 1
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                pixels.extend([value] * count)
        elif cmd >= 0x80:
            # Copy command
            count = cmd - 0x80 + 1
            for _ in range(count):
                if ptr < len(seg_data):
                    pixels.append(seg_data[ptr])
                    ptr += 1
        else:
            pixels.append(cmd)
        
        if len(pixels) >= 600:
            break
    
    return pixels

def test_v13(seg_data):
    """0xfe = explicit skip of 1 pixel, 0xC0+=fill, 0x80-0xDF=copy"""
    pixels = []
    ptr = 0
    while ptr < len(seg_data):
        cmd = seg_data[ptr]
        ptr += 1
        
        if cmd == 0xfe:
            pixels.append(0)
        elif cmd >= 0xC0:
            count = cmd - 0xC0 + 1
            if ptr < len(seg_data):
                value = seg_data[ptr]
                ptr += 1
                if value == 0xfe:
                    pixels.extend([0] * count)
                else:
                    pixels.extend([value] * count)
        elif cmd >= 0x80:
            count = cmd - 0x80 + 1
            for _ in range(count):
                if ptr < len(seg_data):
                    val = seg_data[ptr]
                    ptr += 1
                    pixels.append(0 if val == 0xfe else val)
        else:
            pixels.append(cmd)
        
        if len(pixels) >= 600:
            break
    
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
    
    # Test first segment only
    seg_data = data[offsets[0]:offsets[1]]
    
    print(f"Icon 0, Front Frame0 ({len(seg_data)} bytes)")
    print(f"First 20 bytes: {' '.join(f'{b:02x}' for b in seg_data[:20])}")
    
    for name, func in [("v9", test_v9), ("v10", test_v10), 
                       ("v11", test_v11), ("v12", test_v12), ("v13", test_v13)]:
        pixels = func(seg_data)
        status = "✓" if len(pixels) == 576 else " "
        print(f"  {status} {name}: {len(pixels)} pixels")
        
        if len(pixels) == 576:
            non_zero = sum(1 for p in pixels if p != 0)
            print(f"      Non-zero: {non_zero}")
            print(f"      First row: {' '.join(f'{p:02x}' for p in pixels[:24])}")

if __name__ == '__main__':
    main()
