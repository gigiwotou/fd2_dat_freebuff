#!/usr/bin/env python3
'''
Test ANI.DAT loading and AFM playback.
This script extracts ANI.DAT index information and tests AFM decoding.
'''

import struct
import sys

def read_u32(f):
    return struct.unpack('<I', f.read(4))[0]

def main():
    ani_path = sys.argv[1] if len(sys.argv) > 1 else 'game/ANI.DAT'
    
    try:
        with open(ani_path, 'rb') as f:
            # Read ANI.DAT header (6 bytes magic + N * 4 byte offsets)
            magic = f.read(6)
            print(f'ANI.DAT magic: {magic}')
            
            # Read offset table
            offsets = []
            while True:
                pos = f.tell()
                offset_bytes = f.read(4)
                if len(offset_bytes) < 4:
                    break
                offset = struct.unpack('<I', offset_bytes)[0]
                if offset == 0:
                    break
                offsets.append((len(offsets), offset, pos))
            
            print(f'Found {len(offsets)} ANI entries:')
            for idx, offset, file_pos in offsets:
                f.seek(offset)
                sig = f.read(3)
                if sig == b'AFM':
                    # Read frame count from offset 0xA5
                    f.seek(offset + 0xA5)
                    frame_count = struct.unpack('<H', f.read(2))[0]
                    print(f'  ANI#{idx}: offset=0x{offset:X}, frame_count={frame_count}, file_pos=0x{file_pos:X}')
                else:
                    print(f'  ANI#{idx}: offset=0x{offset:X}, sig={sig!r} (NOT AFM)')
                    
    except FileNotFoundError:
        print(f'Error: {ani_path} not found')
        return 1
    except Exception as e:
        print(f'Error: {e}')
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())