import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

idx = 0
off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
res_data = data[off_start:off_end]

header_size = struct.unpack('<I', res_data[0:4])[0]
width = struct.unpack('<H', res_data[16:18])[0]
height = struct.unpack('<H', res_data[18:20])[0]

num_frame_offsets = (header_size - 4) // 4
print(f'header_size={header_size}, num_frame_offsets={num_frame_offsets}, {width}x{height}')

frame_offs = []
for i in range(num_frame_offsets):
    off = struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0]
    frame_offs.append(off)

# Find 4th frame: it's after frame3's data ends
# Frame 3 starts at frame_offs[2], compressed data, need to find where it ends
# Scan backwards from resource end to find where frame 3's compressed data ends
# Or check if there's a frame offset at a specific position

# Let's check each resource's structure
print(f'\nFrame offsets: {frame_offs}')
print(f'Resource size: {len(res_data)}')

# Try: 4th frame might be at a fixed position
# Or maybe header_size doesn't mean what we think
# Let's try reading byte 16 as num_frames instead of width
num_frames_byte16 = res_data[16]
print(f'Byte 16 as num_frames: {num_frames_byte16}')

# Or maybe it's: [header_size:4] [offset1:4] [offset2:4] [offset3:4] [offset4:4] [width:2] [height:2]
# That would be header_size=20
# Let's try with offset table = header_size - 4 = 16 -> 4 offsets
# Wait, header_size=16, so (16-4)/4 = 3 offsets
# What if the format is actually [header_size:4] [4 offsets: 16 bytes] = 20 bytes header
# And header_size=16 means 16 bytes after the first 4 = 4 offsets

# Let's just try 4 frame offsets starting at byte 4
print(f'\nTrying 4 frame offsets (bytes 4, 8, 12, 16):')
for i in range(4):
    off = struct.unpack('<I', res_data[4 + i*4: 8 + i*4])[0]
    print(f'  frame[{i}] offset={off}')

# If frame[3] offset is 5242960 (0x500050), that's way beyond resource size
# So 4 offsets doesn't work with header_size=16

# Maybe the 4th frame is implicitly after frame 3's data
# Let's decode frame 3 and see where its data ends
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

print(f'\nDecoding 3 frames:')
for i in range(3):
    next_off = frame_offs[i+1] if i < 2 else len(res_data)
    compressed = res_data[frame_offs[i]+4:next_off]
    decoded = decode_rle(compressed)
    print(f'  frame[{i}]: compressed={len(compressed)} -> decoded={len(decoded)} (expected {width*height})')

# The 4th frame must be somewhere. Let me check the raw bytes after frame 3
# Frame 3 starts at 9512, ends at resource end (12665)
# Compressed data from 9512+4=9516 to 12665 = 3149 bytes
# If we decode this: should get 6400 pixels
# The remaining bytes after 6400 pixels worth of compressed data = ???

# Actually, let me check if there are exactly 4 frame offsets in ALL resources
# by checking a different resource
for test_idx in [1, 2, 10, 50, 100]:
    off_s = struct.unpack('<I', data[10 + test_idx * 4: 14 + test_idx * 4])[0]
    off_e = struct.unpack('<I', data[10 + (test_idx + 1) * 4: 14 + (test_idx + 1) * 4])[0]
    if off_e > len(data) or off_s >= off_e:
        continue
    r = data[off_s:off_e]
    hs = struct.unpack('<I', r[0:4])[0]
    n = (hs - 4) // 4
    print(f'\nResource {test_idx}: header_size={hs}, frame_offsets={n}')
    for i in range(min(n, 5)):
        off = struct.unpack('<I', r[4+i*4:8+i*4])[0]
        print(f'  frame[{i}] offset={off}')
