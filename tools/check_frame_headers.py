import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

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

# Analyze resource 0 with 4-frame assumption
idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

header_size = struct.unpack('<I', r[0:4])[0]
num_offsets = (header_size - 4) // 4  # 16-4=12, 12/4=3
w = struct.unpack('<H', r[16:18])[0]
h = struct.unpack('<H', r[18:20])[0]

print(f'Resource 0: {len(r)} bytes, header_size={header_size}, num_offsets={num_offsets}, {w}x{h}')

# Parse frame offsets
frame_offs = []
for i in range(num_offsets):
    off = struct.unpack('<I', r[4 + i*4: 8 + i*4])[0]
    frame_offs.append(off)

print(f'Frame offsets: {frame_offs}')

# Decode each frame
frames_data = []
for i, foff in enumerate(frame_offs):
    next_off = frame_offs[i+1] if i+1 < len(frame_offs) else len(r)
    # Each frame: [w:2][h:2][unknown:16][compressed_pixels]
    # Skip 20 bytes frame header
    compressed = r[foff+20:next_off]
    decoded = decode_rle(compressed)
    frames_data.append(decoded)
    print(f'  Frame {i}: compressed={len(compressed)}, decoded={len(decoded)}')

# Now check if there's data for a 4th frame after the last offset
# Frame 3 (4th frame) should be after frame_offs[2] + its data
last_frame_off = frame_offs[-1]
# The 4th frame might start right after frame 2's data
# But we don't know where frame 2 ends since there's no offset[3]

# Check: is there a 4th frame header (20 bytes) + data after frame 2?
# Frame 2 starts at offset 9512, resource ends at 12665
# Frame 2 header = 20 bytes, compressed data = 12665-9512-20 = 3133 bytes
# If we decode frame 2 from offset 9512+20 to end: should get 6400 pixels

# Actually, let me check: what if the 4th frame is stored RAW (uncompressed) after all compressed data?
# Or what if there are actually 4 frame offsets but stored differently?

# Let me try: what if header_size=16 means 4 offsets (16/4=4) but the format is:
# [4] header_size [4] off0 [4] off1 [4] off2 [2] w [2] h = 20 bytes
# And the 4th offset is NOT stored, it's computed as end_of_resource?

# Or: what if each frame data block has its own header that includes next frame offset?
# Frame header: [w:2][h:2][next_frame_offset:4][padding:12] = 20 bytes

# Check frame headers for embedded offsets
for i, foff in enumerate(frame_offs):
    print(f'\nFrame {i} header at byte {foff}:')
    fh = r[foff:foff+20]
    fw = struct.unpack('<H', fh[0:2])[0]
    fh_h = struct.unpack('<H', fh[2:4])[0]
    f_next = struct.unpack('<I', fh[4:8])[0] if len(fh) >= 8 else 0
    print(f'  w={fw}, h={fh_h}, next_offset={f_next}')
    print(f'  bytes[4-19]: {fh[4:20].hex()}')

# What if bytes 4-7 of each frame header contain the NEXT frame's offset?
# Frame 0: next = bytes[4-7] of frame 0 data
# Frame 1: next = bytes[4-7] of frame 1 data
# Frame 2: next = bytes[4-7] of frame 2 data (or end of resource)
# Frame 3: would be after frame 2... but we only have 3 offsets in the resource header
