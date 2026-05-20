import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

print(f'Resource 0: {len(r)} bytes')
print(f'All DWORDs:')
for i in range(0, min(len(r), 32), 4):
    val = struct.unpack('<I', r[i:i+4])[0]
    print(f'  [{i}] 0x{val:08X} = {val}')

# Try: header_size=16 means [4] header_size + [12] 3 offsets = 16
# But what if it's [4] header_size + [12] 3 offsets + [4] 4th offset?
# That would be 20 bytes header, but header_size says 16...

# Alternative: what if header_size is something else entirely?
# Let's look at resource size vs header_size
# Resource 0: size=12665, header_size=16
# If header_size means "number of frame offsets in DWORDs", then 16 would be 16 offsets = way too many
# If header_size means "header size in bytes", then 16 = 4(D) + 3*4(offsets) + 2(w) + 2(h) = 18... no
# 4(D) + 3*4(offsets) = 16 ✓

# So the structure is:
# [4] header_size=16
# [4] offset0
# [4] offset1
# [4] offset2
# [2] width
# [2] height
# = 20 bytes total header, but header_size=16 means "frame offset table size"

# Now for the 4th frame: maybe it's NOT in the offset table
# Maybe the format uses "frame 0..N-2 stored, frame N-1 = remaining data"
# But we only have 3 offsets and the user says 4 frames

# Let me check: what if each resource actually has 4 offsets (16 bytes of offsets)?
# And header_size=16 means "16 bytes of offsets" = 4 offsets
# Format: [4] header_size + [16] 4 offsets + [2] w + [2] h = 24 bytes

# Try reading 4 offsets
print(f'\n=== 4-offset interpretation (16 bytes of offsets): ===')
for i in range(4):
    off = struct.unpack('<I', r[4+i*4:8+i*4])[0]
    print(f'  offset[{i}] = {off}')

# offset[3] = 5242960 which is way too big for a 12665-byte resource
# Unless it's stored as a WORD (2 bytes)?
print(f'\n=== Try 2-byte offsets: ===')
for i in range(8):
    off = struct.unpack('<H', r[4+i*2:6+i*2])[0]
    print(f'  offset[{i}] (2B) = {off}')

# offset[0]=0x0C5D=3165, offset[1]=0x18B8=6328, offset[2]=0x2528=9512
# offset[3]=0x0050=80 (this is width!)
# So with 2-byte offsets, offset[3] collides with width
# Unless there are only 3 offsets (6 bytes) + width/height at 10/12

print(f'\n=== 3 offsets as 2-byte words: ===')
for i in range(3):
    off = struct.unpack('<H', r[4+i*2:6+i*2])[0]
    print(f'  offset[{i}] = {off}')
w = struct.unpack('<H', r[10:12])[0]
h = struct.unpack('<H', r[12:14])[0]
print(f'  w={w}, h={h} (at bytes 10,12)')
print(f'  bytes[14-19]: {r[14:20].hex()}')

# w=0x0050=80, h=0x0050=80 - that works!
# But bytes 14-19 = 000000c54ac1 - this is RLE data starting early?
# That doesn't make sense if there are only 3 frames

# Let me try yet another interpretation:
# Maybe header_size=16 is actually a different field, not frame count
# What if the format is simply:
# [4] unknown (value=16)
# [4] offset0
# [4] offset1
# [4] offset2
# [2] width (=80)
# [2] height (=80)
# And there are exactly 3 frame offsets?
# The 4th frame could be: after frame 2's data, there's a 4th frame

# Let's decode frame 2 fully and see what's left
# Frame 2 starts at offset 9512
# Header: 20 bytes (w,h + 16 bytes)
# Compressed data starts at 9532
# Resource ends at 12665

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

# Decode all 3 frames
print(f'\n=== Full frame decode: ===')
frame_offs = [3165, 6328, 9512]
all_decoded_len = 0
for i, foff in enumerate(frame_offs):
    next_off = frame_offs[i+1] if i+1 < len(frame_offs) else len(r)
    compressed = r[foff+4:next_off]  # skip 4-byte frame header (w,h are in main header)
    decoded = decode_rle(compressed)
    all_decoded_len += len(decoded)
    print(f'  Frame {i}: compressed={len(compressed)}, decoded={len(decoded)}')

print(f'Total decoded pixels: {all_decoded_len}')
print(f'Expected for 3 frames: {80*80*3} = {80*80*3}')
print(f'Expected for 4 frames: {80*80*4} = {80*80*4}')

# Hmm, 3*6361 = 19083 pixels, but 3*6400 = 19200
# The RLE decode is giving 6361 instead of 6400 per frame
# Maybe the frame data includes 4 bytes that aren't pixel data

# Let me try: frame header is 4 bytes (w:2, h:2) + compressed data
# Skip 4 bytes per frame
print(f'\n=== Try skipping 4 bytes per frame: ===')
for i, foff in enumerate(frame_offs):
    next_off = frame_offs[i+1] if i+1 < len(frame_offs) else len(r)
    compressed = r[foff+4:next_off]
    decoded = decode_rle(compressed)
    print(f'  Frame {i}: compressed={len(compressed)}, decoded={len(decoded)}')
