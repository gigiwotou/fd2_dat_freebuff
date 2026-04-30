"""Analyze FDICON.B24 segment data to determine if it's compressed or raw pixel data."""

import struct

def analyze_segments(fdicon_path):
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
    
    total_icons = len(offsets) // 12
    print(f"Total icons: {total_icons}")
    print(f"Total offsets: {len(offsets)}")
    
    # Analyze first 5 icons
    for icon_id in range(min(5, total_icons)):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        total_size = data_end - data_start
        
        print(f"Total icon data size: {total_size} bytes")
        
        # Analyze each segment
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_size = seg_end - seg_start
            
            dir_name = ['Front', 'Left', 'Back', 'Right'][seg_idx // 3]
            frame_name = ['Frame0', 'Frame1', 'Frame2'][seg_idx % 3]
            
            print(f"\n  Segment {seg_idx:2d} ({dir_name:5s} {frame_name:6s}): {seg_size:4d} bytes")
            
            if seg_size == 0:
                continue
            
            seg_data = data[icon_offsets[seg_idx]:icon_offsets[seg_idx + 1]]
            
            # Print first 50 bytes
            print(f"    First 50 bytes: {' '.join(f'{b:02x}' for b in seg_data[:50])}")
            
            # Analyze byte distribution
            byte_freq = {}
            for b in seg_data[:200]:
                byte_freq[b] = byte_freq.get(b, 0) + 1
            
            sorted_bytes = sorted(byte_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"    Top 5 bytes: {', '.join(f'0x{b:02x}({c}x)' for b, c in sorted_bytes)}")
            
            # Check if size matches 24x24 = 576 pixels
            if seg_size == 576:
                print(f"    -> Size matches 24x24 = 576 pixels (UNCOMPRESSED!)")
            elif seg_size == 256:
                print(f"    -> Size matches 16x16 = 256 pixels (UNCOMPRESSED!)")
            elif seg_size == 1024:
                print(f"    -> Size matches 32x32 = 1024 pixels (UNCOMPRESSED!)")
            else:
                # Check if it's close to any common size
                for w, h in [(24, 24), (16, 16), (32, 32), (20, 20)]:
                    if seg_size == w * h:
                        print(f"    -> Size matches {w}x{h} = {w*h} pixels (UNCOMPRESSED!)")
                        break

def test_raw_pixel_data(fdicon_path):
    """Test treating segment data as raw pixel data."""
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*60}")
    print("Testing RAW pixel data interpretation")
    print(f"{'='*60}")
    
    # Read first segment
    offset = struct.unpack('<I', data[6:10])[0]
    next_offset = struct.unpack('<I', data[10:14])[0]
    seg_data = data[offset:next_offset]
    
    print(f"First segment size: {len(seg_data)} bytes")
    print(f"First 100 bytes: {' '.join(f'{b:02x}' for b in seg_data[:100])}")
    
    # Check common sizes
    for width, height in [(24, 24), (16, 16), (32, 32), (20, 20), (24, 20)]:
        if len(seg_data) == width * height:
            print(f"✓ Matches {width}x{height} = {width*height} pixels")
            print(f"  This is likely RAW pixel data!")
            return width, height
    
    # Check if it's compressed
    unique_bytes = len(set(seg_data))
    print(f"Unique bytes in segment: {unique_bytes}")
    print(f"Average byte value: {sum(seg_data[:100]) / len(seg_data[:100]):.1f}")
    
    return None, None

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    analyze_segments(fdicon_path)
    test_raw_pixel_data(fdicon_path)
