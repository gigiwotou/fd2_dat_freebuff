import struct
import os

dat_path = 'game/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    magic = f.read(6)
    count = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(count):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    
    print(f'Total resources: {count}')
    print(f'\nSearching for resource set (should be >768 bytes):\n')
    
    for i in range(7, 16):
        if i >= count:
            break
        start = offsets[i]
        end = offsets[i+1] if i+1 < count else os.path.getsize(dat_path)
        size = end - start
        
        print(f'Resource #{i}: size={size:8d} bytes', end='')
        
        if size > 768 and size < 100000:
            # Check if it has offset table structure
            f.seek(start)
            header = f.read(min(48, size))
            
            # Check for 3-byte offsets (14 offsets = 42 bytes)
            if size >= 42:
                # Try parsing as 14 x 3-byte offsets
                test_offsets = []
                valid = True
                for j in range(14):
                    pos = j * 3
                    if pos + 3 <= size:
                        val = header[pos] | (header[pos+1] << 8) | (header[pos+2] << 16)
                        test_offsets.append(val)
                        if val > size:
                            valid = False
                            break
                
                if valid and len(test_offsets) == 14:
                    print(f' -> POSSIBLE RESOURCE SET (14 3-byte offsets)')
                    print(f'    Offsets: {[hex(x) for x in test_offsets[:8]]}...')
                else:
                    # Check for 4-byte offsets
                    if size >= 56:  # 14 x 4 bytes
                        w = header[0] | (header[1] << 8)
                        h = header[2] | (header[3] << 8)
                        if w > 0 and w <= 320 and h > 0 and h <= 200:
                            print(f' -> RLE IMAGE {w}x{h}')
                        else:
                            print(f' -> OTHER (header={header[:8].hex()})')
                    else:
                        print(f' -> OTHER')
            else:
                print(f' -> TOO SMALL')
        elif size == 768:
            print(f' -> PALETTE')
        else:
            print(f' -> TOO SMALL or TOO LARGE')
