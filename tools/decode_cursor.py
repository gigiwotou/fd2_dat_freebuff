import struct
from PIL import Image

with open('game/FDOTHER.DAT', 'rb') as f:
    # Parse DAT header
    f.seek(6)
    count = struct.unpack('<I', f.read(4))[0]
    
    # Read offset table
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0]))
    
    # Resource 0
    res0_start = offsets[0]
    res0_size = offsets[1] - res0_start
    f.seek(res0_start)
    res0_data = f.read(res0_size)
    
    w = struct.unpack('<H', res0_data[0:2])[0]
    h = struct.unpack('<H', res0_data[2:4])[0]
    frame0_off = struct.unpack('<H', res0_data[4:6])[0]
    
    print(f"Resource 0: {w}x{h}, frame0 RLE at offset {frame0_off}")
    
    # RLE data
    rle_data = res0_data[frame0_off:]
    print(f"RLE length: {len(rle_data)}")
    print(f"First 40 bytes: {' '.join(f'{b:02X}' for b in rle_data[:40])}")
    
    # Decode RLE with CORRECT mode mapping per IDA 4E98D.c
    # bit7=1,bit6=1 -> SKIP (0xC0+)
    # bit7=1,bit6=0 -> COPY (0x80-0xBF)
    # bit7=0,bit6=1 -> ALTERNATE (0x40-0x7F) - writes at odd positions (dst+1, dst+3...)
    # bit7=0,bit6=0 -> FILL (0x00-0x3F) - continuous fill
    
    pixels = [0] * (w * h)
    p = 0
    total_commands = 0
    for row in range(h):
        col = 0
        while col < w and p < len(rle_data):
            opcode = rle_data[p]
            p += 1
            count = (opcode & 0x3F) + 1
            total_commands += 1
            
            bit7 = (opcode >> 7) & 1
            bit6 = (opcode >> 6) & 1
            
            if bit7 and bit6:
                # SKIP
                col += count
            elif bit7 and not bit6:
                # COPY
                for i in range(count):
                    if col < w:
                        pixels[row * w + col] = rle_data[p]
                        p += 1
                        col += 1
            elif not bit7 and bit6:
                # ALTERNATE - write at odd positions
                color = rle_data[p]
                p += 1
                for i in range(count):
                    col += 1  # skip to odd
                    if col < w:
                        pixels[row * w + col] = color
                    col += 1  # advance past
            else:
                # FILL - continuous
                color = rle_data[p]
                p += 1
                for i in range(count):
                    if col < w:
                        pixels[row * w + col] = color
                    col += 1
    
    non_zero = sum(1 for px in pixels if px != 0)
    print(f"Non-zero pixels: {non_zero}/{w*h}")
    
    # Save image
    img = Image.new('P', (w, h))
    palette = []
    for i in range(256):
        palette.extend([i, i, i])
    img.putpalette(palette)
    img.putdata(pixels)
    img.save('cursor_correct.png')
    print("Saved cursor_correct.png")
    
    # Print rows
    print("\nPixel grid (0=transparent):")
    for row in range(h):
        row_pixels = pixels[row*w:(row+1)*w]
        print(f"  {row:2d}: {' '.join(f'{px:02X}' for px in row_pixels)}")
