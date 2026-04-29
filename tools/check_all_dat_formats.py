"""Check DAT file formats for all DAT files"""
import struct
from pathlib import Path

dat_dir = Path("game")

for dat_name in ["FDFIELD.DAT", "FDSHAP.DAT", "FDOTHER.DAT"]:
    dat_path = dat_dir / dat_name
    data = dat_path.read_bytes()
    
    print(f"\n{'='*60}")
    print(f"{dat_name} (size={len(data)})")
    print(f"{'='*60}")
    print(f"Magic (0-6): {data[0:6]}")
    
    # Format 1: count at byte 6
    count = struct.unpack_from('<I', data, 6)[0]
    print(f"\nFormat 1 interpretation:")
    print(f"  count (byte 6-9) = {count}")
    
    if count < 5000 and 10 + count * 4 <= len(data):
        print(f"  [OK] Valid count, checking offset table from byte 10...")
        offset0 = struct.unpack_from('<I', data, 10)[0]
        offset1 = struct.unpack_from('<I', data, 14)[0]
        print(f"  offset[0] = {offset0}")
        print(f"  offset[1] = {offset1}")
        
        # Verify offsets are within file
        if offset0 < len(data) and offset1 < len(data) and offset1 > offset0:
            print(f"  [OK] Offsets look valid")
            # Check resource at offset[0]
            size0 = offset1 - offset0
            print(f"  Resource 0 size: {size0}")
            print(f"  Resource 0 first 4 bytes: {data[offset0:offset0+4].hex(' ')}")
        else:
            print(f"  [ERROR] Offsets look invalid")
    else:
        print(f"  ❌ Invalid count or not enough data")
        
    # Format 2: offsets from byte 6
    print(f"\nFormat 2 interpretation (offsets from byte 6):")
    offset0_v2 = struct.unpack_from('<I', data, 6)[0]
    offset1_v2 = struct.unpack_from('<I', data, 10)[0]
    print(f"  offset[0] = {offset0_v2}")
    print(f"  offset[1] = {offset1_v2}")
    
    offsets_v2 = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > len(data):
            break
        offsets_v2.append(offset)
        pos += 4
    
    print(f"  Total offsets: {len(offsets_v2)}")
