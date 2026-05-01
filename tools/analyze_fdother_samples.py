#!/usr/bin/env python3
"""
Analyze FDOTHER.DAT to find audio sample data.

From IDA analysis:
- sub_111BA loads resources using: fseek(4*index + 6), read 8 bytes (offset, next_offset)
- sub_25A96 plays samples from FDOTHER.DAT with sample index passed as a6 parameter
- AIL sample struct: sample_rate=11025, default pan=64
- Sample #0 is used for lightning effect in sub_20421 (when a5==1)
"""

import struct
from pathlib import Path

def analyze_fdother_samples(fdother_path):
    with open(fdother_path, 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT size: {len(data)} bytes (0x{len(data):X})")
    print("=" * 80)
    
    # Check header
    header = data[:6]
    print(f"Header: {header}")
    
    # Read resource count at offset 6
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"Resource count: {count}")
    
    # Read all resource offsets
    offset_table_start = 10  # After header(6) + count(4)
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, offset_table_start + i * 4)[0]
        offsets.append(off)
    
    # Print first 50 resources with their sizes and content preview
    for i in range(min(count, 50)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        size = end - start
        
        # Read first bytes to check for known audio signatures
        sample = data[start:start+20]
        
        # Check for common audio file signatures
        sig = ""
        if sample[:4] == b'RIFF':
            sig = " [WAV]"
        elif sample[:4] == b'Creative' or sample[:4] == b'CT':
            sig = " [VOC]"
        elif sample[:4] == b'FORM':
            sig = " [IFF/8SVX]"
        elif sample[:2] == b'\x01\x00' and size < 500:
            sig = " [POSSIBLE_RAW_16LE]"
        elif sample[:2] == b'\x00\x00' and size < 500:
            sig = " [POSSIBLE_RAW_8BIT]"
        
        # Print resource info
        hex_preview = sample[:16].hex()
        print(f"  [{i:3d}] offset=0x{start:06X}, size={size:6d}, hex={hex_preview}{sig}")
    
    print("\n" + "=" * 80)
    print("All resources:")
    for i in range(count):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        size = end - start
        
        # For larger resources, look for audio-like patterns
        sample = data[start:start+50]
        
        # Check if this might be audio data
        # VOC files start with "Creative Voice File" or similar
        # WAV files start with "RIFF"
        # Raw PCM would just be sample data
        
        is_interesting = False
        reason = ""
        
        # Resources 0-20 are likely samples (used in sub_25A96 calls)
        if i <= 30:
            is_interesting = True
            reason = "potential sample resource"
        
        # Check for audio signatures anywhere in the data
        if b'RIFF' in sample:
            is_interesting = True
            reason = "contains RIFF signature"
        if b'VOC' in sample or b'Creative' in sample:
            is_interesting = True
            reason = "contains VOC signature"
        
        if is_interesting:
            hex_preview = sample[:32].hex()
            ascii_preview = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sample[:32])
            print(f"  [{i:3d}] offset=0x{start:06X}, size={size:6d} <-- {reason}")
            print(f"        HEX:    {hex_preview}")
            print(f"        ASCII:  {ascii_preview}")
    
    # Focus on resources 0-12 which are used as samples
    print("\n" + "=" * 80)
    print("Detailed analysis of resources 0-15 (potential audio samples):")
    
    for i in range(min(16, count)):
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else len(data)
        size = end - start
        
        print(f"\n--- Resource [{i}] ---")
        print(f"  Offset: 0x{start:06X}")
        print(f"  Size: {size} bytes")
        
        # Full hex dump of first 128 bytes
        sample = data[start:start+min(128, size)]
        print(f"  First 128 bytes (hex):")
        for j in range(0, len(sample), 16):
            hex_str = ' '.join(f'{b:02X}' for b in sample[j:j+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in sample[j:j+16])
            print(f"    {start+j:06X}: {hex_str:<48s} {ascii_str}")
        
        # Statistical analysis
        if size > 0:
            chunk = data[start:start+min(size, 1000)]
            non_zero = sum(1 for b in chunk if b != 0)
            avg_val = sum(chunk) / len(chunk)
            max_val = max(chunk)
            min_val = min(chunk)
            print(f"  Stats (first 1000 bytes): non-zero={non_zero}, avg={avg_val:.1f}, "
                  f"min={min_val}, max={max_val}")
            
            # If size is reasonable for a sound effect (100-50000 bytes)
            if 100 < size < 100000:
                print(f"  -> LIKELY AUDIO SAMPLE (size fits sound effect)")
                
                # Save this resource for further analysis
                out_path = Path("output/sfx") / f"resource_{i:03d}.raw"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(data[start:end])
                print(f"  -> Saved to {out_path}")

if __name__ == "__main__":
    fdother_path = Path("game/FDOTHER.DAT")
    analyze_fdother_samples(fdother_path)
