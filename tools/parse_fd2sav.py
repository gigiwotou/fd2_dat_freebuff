#!/usr/bin/env python3
"""Parse FD2SAV to extract character sprite positions and IDs

From IDA sub_10010:
  - FD2SAV is 22987 bytes, XOR decrypted
  - Character data starts at offset 4771, 80 bytes per character
  - n6_0 = FD2SAV[12484] = character count
  - For each character (80 bytes):
    - Offset+7: icon_id (FDICON.B24 index)
    - Offset+2: cache_index (filled by sub_11019)
    - Other offsets: position, direction, etc.
"""

import struct
import sys
import os

def xor_decrypt(data):
    """XOR decryption matching IDA sub_4DF28"""
    result = bytearray(data)
    for i in range(len(result)):
        result[i] ^= 0xFF
    return bytes(result)

def parse_fd2sav(filepath):
    """Parse FD2SAV and extract character data"""
    
    with open(filepath, 'rb') as f:
        raw_data = f.read()
    
    print(f"FD2SAV file size: {len(raw_data)} bytes")
    if len(raw_data) != 22987:
        print(f"  WARNING: Expected 22987 bytes, got {len(raw_data)}")
    
    # Decrypt
    decrypted = xor_decrypt(raw_data)
    
    # Extract character count
    char_count = decrypted[12484]
    print(f"Character count (offset 12484): {char_count}")
    
    # Character data starts at offset 4771
    char_data_start = 4771
    char_data_size = 80 * char_count
    
    if char_data_start + char_data_size > len(decrypted):
        print(f"  WARNING: Character data exceeds file size")
        char_data_size = len(decrypted) - char_data_start
    
    print(f"Character data: offset {char_data_start}, size {char_data_size} bytes")
    print()
    
    # Parse each character record (80 bytes)
    for i in range(char_count):
        offset = char_data_start + i * 80
        record = decrypted[offset:offset+80]
        
        print(f"Character {i}:")
        print(f"  Record bytes: {record.hex()}")
        
        # Known fields from IDA
        icon_id = record[7]
        print(f"  Icon ID (offset+7): {icon_id}")
        
        # Analyze other bytes to find position data
        # Try different offsets and sizes
        for off in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]:
            byte_val = record[off]
            print(f"  Offset+{off:2d}: {byte_val:3d} (0x{byte_val:02X})")
        
        print()

def main():
    fd2sav_path = sys.argv[1] if len(sys.argv) > 1 else 'FD2.SAV'
    
    if not os.path.exists(fd2sav_path):
        print(f"Error: {fd2sav_path} not found")
        return 1
    
    parse_fd2sav(fd2sav_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
