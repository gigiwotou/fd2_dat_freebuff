"""Test sprite decoder logic by decoding a FIGANI.DAT sprite and saving as BMP."""

import struct
import sys
from PIL import Image

def load_palette():
    """Load palette from FDSHAP.DAT or use default."""
    # For now, create a grayscale palette for visualization
    palette = []
    for i in range(256):
        palette.extend([i, i, i])
    return palette

def decode_rle(frame_data, width, height):
    """Decode RLE compressed sprite frame."""
    pixels = bytearray(width * height)
    src_ptr = 0
    src_end = len(frame_data)
    dst = 0
    
    for y in range(height):
        remaining = width
        
        while remaining > 0 and src_ptr < src_end:
            value = frame_data[src_ptr]
            src_ptr += 1
            
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            count = (value & 0x3F) + 1
            
            if count > remaining:
                count = remaining
            
            if bit7 and bit6:
                # 11: Skip (transparent)
                dst += count
                remaining -= count
            elif bit7 and not bit6:
                # 10: Copy from source
                if src_ptr + count > src_end:
                    return None
                for i in range(count):
                    if dst < len(pixels):
                        pixels[dst] = frame_data[src_ptr]
                    dst += 1
                    src_ptr += 1
                remaining -= count
            elif not bit7 and bit6:
                # 01: Fill
                if src_ptr >= src_end:
                    return None
                fill = frame_data[src_ptr]
                src_ptr += 1
                for i in range(count):
                    if dst < len(pixels):
                        pixels[dst] = fill
                    dst += 1
                    remaining -= 1
            else:
                # 00: Regular fill
                if src_ptr >= src_end:
                    return None
                fill = frame_data[src_ptr]
                src_ptr += 1
                for i in range(count):
                    if dst < len(pixels):
                        pixels[dst] = fill
                    dst += 1
                    remaining -= 1
        
        if y < height - 1:
            row_end = (y + 1) * width
            if dst < row_end:
                dst = row_end
    
    return bytes(pixels)

def save_as_bmp(pixels, width, height, palette, filename):
    """Save pixel data as BMP image with palette."""
    img = Image.new('P', (width, height))
    img.putdata(pixels)
    
    # Create palette
    pal = []
    for i in range(256):
        if i < len(palette) // 3:
            pal.extend(palette[i*3:i*3+3])
        else:
            pal.extend([0, 0, 0])
    img.putpalette(pal)
    
    img.save(filename)
    print(f"Saved {filename} ({width}x{height})")

def test_sprite_decode():
    """Test decoding sprites from FIGANI.DAT."""
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    
    with open(figani_path, 'rb') as f:
        data = f.read()
    
    # Parse Format 2
    if data[:6] != b'LLLLLL':
        print("Invalid magic")
        return
    
    resource_count = struct.unpack('<I', data[6:10])[0]
    print(f"Resource count: {resource_count}")
    
    # Parse offsets
    offsets = []
    pos = 10
    for i in range(resource_count):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        offsets.append(offset)
        pos += 4
    
    # Test first 5 valid sprites
    sprite_idx = 0
    for i in range(min(50, resource_count)):
        if sprite_idx >= 5:
            break
            
        start = offsets[i]
        end = offsets[i+1] if i < resource_count - 1 else len(data)
        size = end - start
        
        if size < 20:
            continue
        
        res_data = data[start:end]
        header = struct.unpack('<I', res_data[0:4])[0]
        
        if header != 0x00040004 and header != 0x40004:
            continue
        
        print(f"\nSprite {i} (size={size})")
        
        # Parse sprite
        height = struct.unpack('<I', res_data[8:12])[0] & 0xFFFF
        
        # Count frame offsets
        frame_offsets = []
        offset = 12
        while offset + 4 <= size:
            frame_off = struct.unpack('<I', res_data[offset:offset+4])[0]
            if frame_off >= size or frame_off < offset + 4:
                break
            frame_offsets.append(frame_off)
            offset += 4
        
        print(f"  Height: {height}, Frames: {len(frame_offsets)}")
        
        # Decode first frame
        if frame_offsets:
            frame_start = frame_offsets[0]
            frame_end = frame_offsets[1] if len(frame_offsets) > 1 else size
            frame_data = res_data[frame_start:frame_end]
            
            # Try different widths
            for width in [24, 32, 36, 48]:
                pixels = decode_rle(frame_data, width, height)
                if pixels:
                    non_zero = sum(1 for b in pixels if b != 0)
                    if non_zero > width * height * 0.1:  # At least 10% non-zero
                        print(f"  Decoded {width}x{height}: {non_zero} non-zero pixels")
                        
                        # Save as image
                        palette = load_palette()
                        filename = f"sprite_{i}_{width}x{height}.bmp"
                        save_as_bmp(pixels, width, height, palette, filename)
                        break
        
        sprite_idx += 1

if __name__ == '__main__':
    test_sprite_decode()
