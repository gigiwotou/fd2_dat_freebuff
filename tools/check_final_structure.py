import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]

# Check if ALL resources have header_size=16
all_16 = True
for i in range(min(count-1, 100)):
    off_s = struct.unpack('<I', data[10 + i * 4: 14 + i * 4])[0]
    if off_s + 4 > len(data): continue
    hs = struct.unpack('<I', data[off_s:off_s+4])[0]
    if hs != 16:
        all_16 = False
        print(f'Resource {i} has header_size={hs}, not 16')

if all_16:
    print('All resources have header_size=16')

# Final theory: header_size=16 means:
# [4] header_size
# [4] offset0
# [4] offset1
# [4] offset2
# [2] width (=80)
# [2] height (=80)
# = 20 bytes header
# Pixel data at byte 16? No, byte 16 has width
# Pixel data at byte 20 (after w,h)

# But header_size=16 only accounts for bytes 0-15
# Bytes 16-19 (w,h) are NOT included in header_size

# So the structure is:
# Bytes 0-15: header (16 bytes)
# Bytes 16-19: width, height
# Bytes 20+: RLE compressed pixel data (80x80 = 6400 pixels)

# What about the 3 offsets? They point to additional frame data
# Each offset points to: [w:2][h:2][16 bytes padding?][compressed pixels]

# But where's the 4th frame? The user says 4 frames
# Let me check if maybe the structure is:
# Bytes 0-15: header with 3 offsets
# Bytes 16-19: width, height  
# Bytes 20-...: Frame 0 data
# Offset0: Frame 1 data
# Offset1: Frame 2 data
# Offset2: Frame 3 data

# Let's decode from byte 20 as Frame 0
def decode_rle(compressed):
    decoded = []
    i = 0
    while i < len(compressed):
        byte = compressed[i]
        if byte >= 0xC0:
            if i + 1 < len(compressed):
                count = byte & 0x3F
                if count == 0: count = 64
                decoded.extend([compressed[i+1]] * count)
                i += 2
            else: break
        else:
            decoded.append(byte)
            i += 1
    return decoded

idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

frame_offs = [
    struct.unpack('<I', r[4:8])[0],
    struct.unpack('<I', r[8:12])[0],
    struct.unpack('<I', r[12:16])[0]
]

print(f'\n4-frame theory: byte 20+ is frame 0, offsets are frames 1,2,3')
# Frame 0 at byte 20
compressed_0 = r[20:frame_offs[0]]  # from byte 20 to offset0
decoded_0 = decode_rle(compressed_0)
print(f'Frame 0 (byte 20 to {frame_offs[0]}): compressed={len(compressed_0)}, decoded={len(decoded_0)}')

# Frame 1 at offset0
compressed_1 = r[frame_offs[0]+4:frame_offs[1]]  # skip 4 bytes (w,h)
decoded_1 = decode_rle(compressed_1)
print(f'Frame 1 (offset {frame_offs[0]}+4 to {frame_offs[1]}): compressed={len(compressed_1)}, decoded={len(decoded_1)}')

# Frame 2 at offset1
compressed_2 = r[frame_offs[1]+4:frame_offs[2]]
decoded_2 = decode_rle(compressed_2)
print(f'Frame 2 (offset {frame_offs[1]}+4 to {frame_offs[2]}): compressed={len(compressed_2)}, decoded={len(decoded_2)}')

# Frame 3 at offset2
compressed_3 = r[frame_offs[2]+4:]
decoded_3 = decode_rle(compressed_3)
print(f'Frame 3 (offset {frame_offs[2]}+4 to end): compressed={len(compressed_3)}, decoded={len(decoded_3)}')
