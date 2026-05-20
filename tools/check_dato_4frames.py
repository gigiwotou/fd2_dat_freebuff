import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

# Check header_size values across many resources
count = struct.unpack('<I', data[6:10])[0]
print(f'Total resources: {count}')

header_sizes = {}
for i in range(min(count-1, 200)):
    off_start = struct.unpack('<I', data[10 + i * 4: 14 + i * 4])[0]
    off_end = struct.unpack('<I', data[10 + (i + 1) * 4: 14 + (i + 1) * 4])[0]
    if off_start + 4 > len(data) or off_end > len(data) or off_start >= off_end:
        continue
    hs = struct.unpack('<I', data[off_start:off_start+4])[0]
    header_sizes[hs] = header_sizes.get(hs, 0) + 1

print(f'\nHeader size distribution (first 200 resources):')
for hs, cnt in sorted(header_sizes.items()):
    print(f'  header_size={hs}: {cnt} resources')

# Check resource 0 in detail with header_size=20 assumption
idx = 0
off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
res_data = data[off_start:off_end]

print(f'\n=== Resource 0 detail (header_size={struct.unpack("<I", res_data[0:4])[0]}) ===')
for i in range(5):
    offset = struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0]
    next_off = struct.unpack('<I', res_data[8 + i*4: 12 + i*4])[0] if i < 4 else len(res_data)
    print(f'  frame[{i}] offset={offset}, next={next_off}, span={next_off - offset}')

# Check if header_size=20 gives 4 frames
print(f'\n=== If header_size=20 (4 frame offsets): ===')
for i in range(4):
    offset = struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0]
    print(f'  frame[{i}] offset={offset}')

# Try to decode with 4 frames
print(f'\n=== Try 4-frame decode (skip 4-byte header per frame): ===')
frame_offs = [struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0] for i in range(4)]
for i in range(4):
    next_off = frame_offs[i+1] if i < 3 else len(res_data)
    compressed = res_data[frame_offs[i]+4:next_off]
    # Simple RLE decode
    decoded = []
    j = 0
    while j < len(compressed):
        byte = compressed[j]
        if byte >= 0xC0:
            if j + 1 < len(compressed):
                cnt = compressed[j] & 0x3F
                if cnt == 0: cnt = 64
                decoded.extend([compressed[j+1]] * cnt)
                j += 2
            else: break
        else:
            decoded.append(byte)
            j += 1
    print(f'  frame[{i}]: compressed={len(compressed)} -> decoded={len(decoded)} pixels')
