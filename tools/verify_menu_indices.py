import struct

fdother_path = r"d:\testworkspace\fd2_dat_freebuff\bin\FDOTHER.DAT"

# Load FDOTHER.DAT
with open(fdother_path, 'rb') as f:
    fdother = f.read()

# Parse FDOTHER offset table (starts at byte 6)
def get_offset(idx):
    off = 6 + idx * 4
    return struct.unpack_from('<I', fdother, off)[0]

# Get resource 6 (nested DAT)
res6_offset = get_offset(6)
res6_size = get_offset(7) - res6_offset if 7 < 422 else len(fdother) - res6_offset
res6_data = fdother[res6_offset:res6_offset+res6_size]

print(f"Resource 6: offset={res6_offset}, size={res6_size}")

# Verify LLLLLL header
assert res6_data[0:6] == b'LLLLLL', f"Invalid magic: {res6_data[0:6]}"

# Parse count
count = struct.unpack_from('<I', res6_data, 6)[0]
print(f"Sub-resource count: {count}")

# Parse offset table (starts at byte 10)
offset_table = []
for i in range(count):
    off = struct.unpack_from('<I', res6_data, 10 + i*4)[0]
    offset_table.append(off)

print(f"\nOffset table verification:")
for i in range(min(8, count)):
    off = offset_table[i]
    if i+1 < count:
        next_off = offset_table[i+1]
        size = next_off - off
    else:
        size = res6_size - off
    
    # Check if offset is valid
    valid = "OK" if off < res6_size else "INVALID"
    print(f"  sub[{i}]: offset={off}, size={size}, {valid}")

# Check which sub-indices are used by sub_1FF79
print(f"\nSub-indices used by sub_1FF79:")
print(f"  Background (sel=0): sub_idx=2")
print(f"  Background (sel!=0): sub_idx=1")
print(f"  Item 0 (sel=0): sub_idx=4")
print(f"  Item 0 (sel!=0): sub_idx=3")
print(f"  Item 1 (sel=1): sub_idx=6")
print(f"  Item 1 (sel!=1): sub_idx=5")
print(f"  Item 2 (sel=2): sub_idx=? (not in first 8)")

# Check all offsets
print(f"\nAll valid sub-indices:")
for i in range(count):
    off = offset_table[i]
    if off >= res6_size:
        print(f"  sub[{i}]: INVALID offset={off}")
        break
    # Try to read width/height
    if off + 4 <= res6_size:
        w = struct.unpack_from('<H', res6_data, off)[0]
        h = struct.unpack_from('<H', res6_data, off+2)[0]
        print(f"  sub[{i}]: offset={off}, {w}x{h}")
