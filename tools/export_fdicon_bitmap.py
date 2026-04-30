"""Export FDICON.B24 icons using bitmap rendering algorithm from IDA sub_4ED7A."""

import struct
import os

def decode_icon_bitmap_16x16(bitmap_data, palette_idx1, palette_idx2):
    """
    Decode a 16x16 icon using bitmap algorithm from IDA sub_4ED7A.
    
    IDA logic:
    - 32 WORDs (16 rows x 2 WORDs per row)
    - Each row: WORD is byte-swapped
    - Each bit in the WORD controls a 2x2 pixel block
    - If bit is 1, fill with palette colors
    - If bit is 0, transparent
    
    The 32 WORDs are arranged as:
    - Row 0: WORD[0], WORD[1]
    - Row 1: WORD[2], WORD[3]
    - ...
    - Row 15: WORD[30], WORD[31]
    
    Each WORD is 16 bits, but only bits 0-7 are used (8 columns of 2px blocks = 16px width)
    """
    pixels = bytearray(32 * 32)  # 32x32 output (each 2x2 block = 1 bit)
    
    for row in range(16):
        for col_word in range(2):
            word_idx = row * 2 + col_word
            if word_idx * 2 + 1 >= len(bitmap_data):
                continue
            
            # Read WORD and byte-swap
            w = struct.unpack('<H', bitmap_data[word_idx*2:word_idx*2+2])[0]
            w = ((w >> 8) & 0xFF) | ((w & 0xFF) << 8)
            
            # Each bit represents a 2x2 pixel block
            for bit in range(16):
                if (w >> (15 - bit)) & 1:
                    # Fill 2x2 block with palette color
                    px = col_word * 16 + bit * 2
                    py = row * 2
                    
                    for dy in range(2):
                        for dx in range(2):
                            if px + dx < 32 and py + dy < 32:
                                pixels[(py + dy) * 32 + (px + dx)] = palette_idx1
    
    return bytes(pixels)

def export_icons_bitmap(fdicon_path, output_dir, max_icons=5):
    """Export icons treating segment data as 16x16 bitmap."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 size: {len(data)} bytes")
    
    # Read offsets
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    total_icons = len(offsets) // 12
    print(f"Total icons: {total_icons}")
    
    # Palette (grayscale for testing)
    palette = [(i, i, i) for i in range(256)]
    
    directions = ['Front', 'Left', 'Back', 'Right']
    frames = ['Frame0', 'Frame1', 'Frame2']
    
    for icon_id in range(min(max_icons, total_icons)):
        icon_dir = os.path.join(output_dir, f"icon_{icon_id:03d}")
        os.makedirs(icon_dir, exist_ok=True)
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        icon_data = data[data_start:data_end]
        
        print(f"\nIcon {icon_id}:")
        
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_data = icon_data[seg_start:seg_end]
            
            if len(seg_data) == 0:
                continue
            
            dir_name = directions[seg_idx // 3]
            frame_name = frames[seg_idx % 3]
            
            # Check if data is exactly 64 bytes (32 WORDs for 16x16 bitmap)
            if len(seg_data) == 64:
                # Exact bitmap size
                pixels = decode_icon_bitmap_16x16(seg_data, 15, 0)
                
                # Save as BMP
                from PIL import Image
                img = Image.new('P', (32, 32))
                img.putdata(pixels)
                pal = []
                for i in range(256):
                    pal.extend(palette[i] if i < len(palette) else (0,0,0))
                img.putpalette(pal)
                
                filename = f"{dir_name}_{frame_name}_bitmap_32x32.bmp"
                filepath = os.path.join(icon_dir, filename)
                img.save(filepath)
                
                non_trans = sum(1 for b in seg_data if b != 0)
                print(f"  {dir_name:5s} {frame_name:6s}: 64 bytes -> bitmap 32x32 ({non_trans} non-zero)")
            else:
                print(f"  {dir_name:5s} {frame_name:6s}: {len(seg_data):4d} bytes (not 64)")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    output_dir = 'd:\\testworkspace\\fd2_dat_freebuff\\output\\fdicon_icons'
    
    export_icons_bitmap(fdicon_path, output_dir, max_icons=3)
    print(f"\nDone! Check: {output_dir}")
