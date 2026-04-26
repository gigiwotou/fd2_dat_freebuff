#!/usr/bin/env python3
"""
Extract src__14 array from the game binary.
src__14 is at 0x5204e in the data segment.
"""
import struct
import sys

def find_src14(binary_path):
    """Try to find and extract the src__14 array from the binary."""
    with open(binary_path, 'rb') as f:
        data = f.read()
    
    # The game binary is likely a DOS executable or similar
    # The data segment offset varies based on the format
    # Let's try different approaches
    
    print(f"Binary size: {len(data)} bytes")
    
    # Try to find patterns that match the expected trigger values
    # Common values: 520 (0x208), 490 (0x1EA), etc.
    # Looking for sequence of 15 DWORDs
    
    # Search for common patterns in the data
    target_values = [520, 490, 460, 430, 400, 370, 340, 310, 280, 250, 220, 190, 160, 130, 100]
    
    print(f"Looking for pattern: {target_values}")
    
    # Try to find this pattern in the binary
    for i in range(len(data) - 60):
        try:
            values = struct.unpack('<15I', data[i:i+60])
            if values == tuple(target_values):
                print(f"Found src__14 at offset 0x{i:X}")
                return values
        except:
            continue
    
    print("Pattern not found in binary")
    return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_src14.py <game_binary>")
        sys.exit(1)
    
    find_src14(sys.argv[1])
