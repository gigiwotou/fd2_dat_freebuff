"""Extract FIGANI.DAT sprite information and test decoding."""

import struct
import sys
import os

def parse_figani_dat(figani_path):
    """Parse FIGANI.DAT Format 2 structure."""
    with open(figani_path, 'rb') as f:
        data = f.read()
    
    print(f"FIGANI.DAT file size: {len(data)} bytes")
    
    # Verify magic
    if data[:6] != b'LLLLLL':
        print("ERROR: Invalid magic")
        return None
    
    # Format 2: offset table starts at byte 6
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    print(f"Resource count: {len(offsets)}")
    
    # Analyze resources
    sprites = []
    for i in range(len(offsets)):
        start = offsets[i]
        end = offsets[i + 1] if i < len(offsets) - 1 else len(data)
        size = end - start
        
        # Skip small resources (likely separators)
        if size < 16:
            sprites.append(None)
            continue
        
        res_data = data[start:end]
        
        # Parse header
        # Try to identify structure
        header_dword0 = struct.unpack('<I', res_data[0:4])[0]
        
        # Check if it looks like a valid sprite header
        if header_dword0 == 0x40004 or header_dword0 == 0x00040004:
            # Has header - parse dimensions and frames
            sprites.append({
                'index': i,
                'start': start,
                'size': size,
                'header': header_dword0,
                'data': res_data
            })
        else:
            sprites.append(None)
    
    valid_sprites = [s for s in sprites if s is not None]
    print(f"Valid sprites (with 0x40004 header): {len(valid_sprites)}")
    
    if valid_sprites:
        # Analyze first sprite in detail
        sprite = valid_sprites[0]
        print(f"\n{'='*60}")
        print(f"Analyzing sprite {sprite['index']} (size={sprite['size']})")
        print(f"{'='*60}")
        
        res_data = sprite['data']
        
        # Print first 100 bytes in hex
        print("First 100 bytes (hex):")
        for j in range(0, min(100, len(res_data)), 16):
            hex_str = ' '.join(f'{b:02X}' for b in res_data[j:j+16])
            print(f"  {j:04X}: {hex_str}")
        
        # Try different dimension parsing strategies
        print("\nTrying dimension parsing:")
        
        # Strategy 1: DWORD at 4 and 8
        if len(res_data) >= 12:
            dw1 = struct.unpack('<I', res_data[4:8])[0]
            dw2 = struct.unpack('<I', res_data[8:12])[0]
            print(f"  Strategy 1: DWORD[1]={dw1}, DWORD[2]={dw2}")
            if 0 < dw1 <= 200 and 0 < dw2 <= 200:
                print(f"    -> Valid dimensions: {dw1}x{dw2}")
        
        # Strategy 2: WORD at 4 and 6
        if len(res_data) >= 8:
            w1 = struct.unpack('<H', res_data[4:6])[0]
            w2 = struct.unpack('<H', res_data[6:8])[0]
            print(f"  Strategy 2: WORD[2]={w1}, WORD[3]={w2}")
            if 0 < w1 <= 200 and 0 < w2 <= 200:
                print(f"    -> Valid dimensions: {w1}x{w2}")
        
        # Strategy 3: Skip header, look for 2-byte width/height
        if len(res_data) >= 16:
            for offset in [4, 8, 12]:
                if offset + 4 <= len(res_data):
                    w = struct.unpack('<H', res_data[offset:offset+2])[0]
                    h = struct.unpack('<H', res_data[offset+2:offset+4])[0]
                    if 0 < w <= 200 and 0 < h <= 200:
                        print(f"  Strategy 3 (offset {offset}): {w}x{h}")
        
        # Try to find frame offsets
        print("\nSearching for frame offsets...")
        if len(res_data) >= 16:
            # Frame offsets typically start after some header bytes
            for start_offset in [12, 16, 20]:
                if start_offset + 8 <= len(res_data):
                    offsets_found = []
                    for j in range(start_offset, min(start_offset + 100, len(res_data) - 4), 4):
                        off = struct.unpack('<I', res_data[j:j+4])[0]
                        if off > start_offset and off < sprite['size']:
                            offsets_found.append((j, off))
                    
                    if offsets_found:
                        print(f"  From offset {start_offset}: {len(offsets_found)} possible frame offsets")
                        for pos, off in offsets_found[:5]:
                            print(f"    at {pos}: offset {off}")
    
    return data, offsets, sprites

def test_rle_decode(res_data, width, height, start_offset=0):
    """Test RLE decoding with given dimensions."""
    if width <= 0 or height <= 0 or width > 200 or height > 200:
        return None
    
    expected_size = width * height
    if expected_size > 100000:
        return None
    
    # Try to decode
    pixels = bytearray(expected_size)
    src = bytearray(res_data[start_offset:])
    src_ptr = 0
    dst = 0
    
    for y in range(height):
        remaining = width
        
        while remaining > 0 and src_ptr < len(src):
            value = src[src_ptr]
            src_ptr += 1
            
            # Check bits 7 and 6
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            
            count = (value & 0x3F) + 1
            
            if bit7 and bit6:
                # 11: skip (transparent)
                if count > remaining:
                    count = remaining
                dst += count
                remaining -= count
            elif bit7 and not bit6:
                # 10: copy from source
                if count > remaining:
                    count = remaining
                if src_ptr + count > len(src):
                    return None  # Not enough data
                for i in range(count):
                    if dst < expected_size:
                        pixels[dst] = src[src_ptr]
                    dst += 1
                    src_ptr += 1
                remaining -= count
            elif not bit7 and bit6:
                # 01: sparse fill
                if src_ptr >= len(src):
                    return None
                fill = src[src_ptr]
                src_ptr += 1
                
                if count > remaining:
                    count = remaining
                
                for i in range(count):
                    if remaining <= 0:
                        break
                    if dst < expected_size:
                        pixels[dst] = fill
                    dst += 1
                    remaining -= 1
                    if remaining > 0:
                        dst += 1
                        remaining -= 1
            else:
                # 00: regular fill
                if src_ptr >= len(src):
                    return None
                fill = src[src_ptr]
                src_ptr += 1
                
                if count > remaining:
                    count = remaining
                
                for i in range(count):
                    if dst < expected_size:
                        pixels[dst] = fill
                    dst += 1
                    remaining -= 1
        
        # Move to next row
        if y < height - 1:
            row_end = (y + 1) * width
            if dst < row_end:
                dst = row_end
    
    if src_ptr <= len(src):
        return bytes(pixels)
    return None

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    
    result = parse_figani_dat(figani_path)
    if result:
        data, offsets, sprites = result
        
        # Find first valid sprite
        for sprite in sprites:
            if sprite and sprite['size'] > 100:
                print(f"\n{'='*60}")
                print(f"Testing RLE decode for sprite {sprite['index']}")
                print(f"{'='*60}")
                
                # Try different dimension combinations
                test_dims = [(24, 24), (32, 32), (36, 36), (48, 48), (64, 64)]
                
                for width, height in test_dims:
                    # Try decoding from different offsets
                    for start in [4, 8, 12, 16]:
                        if start + 4 <= sprite['size']:
                            pixels = test_rle_decode(sprite['data'], width, height, start)
                            if pixels:
                                # Check if decoded successfully
                                non_zero = sum(1 for b in pixels if b != 0)
                                if non_zero > 0:
                                    print(f"  SUCCESS: {width}x{height} from offset {start}")
                                    print(f"    Non-zero pixels: {non_zero}/{width*height}")
                                    
                                    # Save as raw for verification
                                    out_path = f"sprite_{sprite['index']}_{width}x{height}.raw"
                                    with open(out_path, 'wb') as f:
                                        f.write(pixels)
                                    print(f"    Saved to {out_path}")
                                    break
                    else:
                        continue
                    break
                
                break
