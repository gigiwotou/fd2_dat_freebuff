"""Detailed FIGANI.DAT structure analysis."""

import struct

def analyze_deep(figani_path):
    with open(figani_path, 'rb') as f:
        data = f.read()
    
    # Parse Format 2
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack('<I', data[pos:pos+4])[0]
        if offset > len(data) or offset < 10:
            break
        offsets.append(offset)
        pos += 4
    
    print(f"Resource count: {len(offsets)}")
    
    # Analyze first 5 valid sprites
    sprite_count = 0
    for i in range(min(100, len(offsets))):
        if sprite_count >= 5:
            break
            
        start = offsets[i]
        end = offsets[i + 1] if i < len(offsets) - 1 else len(data)
        size = end - start
        
        if size < 20:
            continue
        
        res_data = data[start:end]
        header = struct.unpack('<I', res_data[0:4])[0]
        
        if header != 0x00040004 and header != 0x40004:
            continue
        
        sprite_count += 1
        
        print(f"\n{'='*60}")
        print(f"Sprite {i} (size={size})")
        print(f"{'='*60}")
        
        # Parse header
        dw0 = struct.unpack('<I', res_data[0:4])[0]
        dw1 = struct.unpack('<I', res_data[4:8])[0]
        dw2 = struct.unpack('<I', res_data[8:12])[0]
        
        print(f"  Header: 0x{dw0:08X}")
        print(f"  DWORD[1]: {dw1}")
        print(f"  DWORD[2]: {dw2}")
        
        # Parse frame offsets (starting at offset 12)
        frame_offsets = []
        pos = 12
        while pos + 4 <= min(100, size):
            off = struct.unpack('<I', res_data[pos:pos+4])[0]
            if off > pos and off < size:
                frame_offsets.append((pos, off))
                pos += 4
            else:
                break
        
        print(f"  Frame offsets: {len(frame_offsets)}")
        for idx, (pos, off) in enumerate(frame_offsets):
            frame_size = frame_offsets[idx+1][1] - off if idx+1 < len(frame_offsets) else size - off
            print(f"    Frame {idx}: offset {off}, size {frame_size}")
        
        # Analyze RLE data for first frame
        if frame_offsets:
            frame0_start = frame_offsets[0][1]
            frame0_end = frame_offsets[1][1] if len(frame_offsets) > 1 else size
            frame0_data = res_data[frame0_start:frame0_end]
            
            print(f"  Frame 0: offset={frame0_start}, size={len(frame0_data)}")
            print(f"  First 50 bytes: {' '.join(f'{b:02X}' for b in frame0_data[:50])}")
            
            # Count RLE command types
            if len(frame0_data) > 100:
                sample = frame0_data[:100]
                cmd_11 = sum(1 for b in sample if (b >> 6) == 3)  # 11xxxxxx
                cmd_10 = sum(1 for b in sample if (b >> 6) == 2)  # 10xxxxxx
                cmd_01 = sum(1 for b in sample if (b >> 6) == 1)  # 01xxxxxx
                cmd_00 = sum(1 for b in sample if (b >> 6) == 0)  # 00xxxxxx
                print(f"  RLE command distribution (first 100 bytes):")
                print(f"    11 (skip): {cmd_11}")
                print(f"    10 (copy): {cmd_10}")
                print(f"    01 (sparse): {cmd_01}")
                print(f"    00 (fill): {cmd_00}")

if __name__ == '__main__':
    figani_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FIGANI.DAT'
    analyze_deep(figani_path)
