"""Analyze FDICON.B24 segment compression format."""

import struct
import sys

def analyze_fdicon_segments(fdicon_path):
    with open(fdicon_path, 'rb') as f:
        data = f.read()
    
    print(f"FDICON.B24 file size: {len(data)} bytes")
    
    # Read offset table (starting at byte 6)
    offsets = []
    for i in range(140 * 12 + 4):
        offset = struct.unpack('<I', data[6 + i*4:6 + (i+1)*4])[0]
        offsets.append(offset)
    
    print(f"Total offsets in table: {len(offsets)}")
    print(f"First few offsets: {offsets[:15]}")
    
    # Analyze first 5 icons
    for icon_id in range(min(10, 140)):
        print(f"\n{'='*60}")
        print(f"Icon {icon_id}")
        print(f"{'='*60}")
        
        # Get 13 offsets for this icon
        icon_offsets = offsets[icon_id * 12 : icon_id * 12 + 13]
        data_start = icon_offsets[0]
        data_end = icon_offsets[12]
        data_size = data_end - data_start
        
        print(f"  Data range: {data_start} - {data_end}")
        print(f"  Data size: {data_size} bytes")
        
        # Extract icon data
        icon_data = data[data_start:data_end]
        
        # Analyze each segment
        for seg_idx in range(12):
            seg_start = icon_offsets[seg_idx] - data_start
            seg_end = icon_offsets[seg_idx + 1] - data_start
            seg_size = seg_end - seg_start
            
            if seg_size <= 0 or seg_start >= len(icon_data):
                print(f"  Segment {seg_idx:2d}: empty/invalid")
                continue
            
            seg_data = icon_data[seg_start:seg_end]
            
            # Print first 30 bytes
            hex_str = ' '.join(f'{b:02x}' for b in seg_data[:30])
            print(f"  Segment {seg_idx:2d}: size={seg_size:4d} bytes, first bytes: {hex_str}")
            
            # Analyze compression pattern
            if len(seg_data) >= 3:
                # Check for 3-byte pattern: CMD COUNT VALUE
                # Or other patterns
                byte_freq = {}
                for b in seg_data:
                    byte_freq[b] = byte_freq.get(b, 0) + 1
                
                # Most frequent bytes
                sorted_bytes = sorted(byte_freq.items(), key=lambda x: x[1], reverse=True)
                top_bytes = sorted_bytes[:5]
                print(f"    Top 5 bytes: {', '.join(f'0x{b:02x}({c}x)' for b, c in top_bytes)}")
                
                # Check if it follows RLE pattern (bit7: copy vs run)
                high_bit_count = sum(1 for b in seg_data if b & 0x80)
                low_bit_count = len(seg_data) - high_bit_count
                print(f"    Bit7 distribution: high={high_bit_count}, low={low_bit_count}")

if __name__ == '__main__':
    fdicon_path = 'd:\\testworkspace\\fd2_dat_freebuff\\bin\\FDICON.B24'
    analyze_fdicon_segments(fdicon_path)
