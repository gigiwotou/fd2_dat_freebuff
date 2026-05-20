import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]

# Check different header sizes
for idx in range(200):
    off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
    off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
    if off_e > len(data) or off_s >= off_e:
        continue
    r = data[off_s:off_e]
    hs = struct.unpack('<I', r[0:4])[0]
    w = struct.unpack('<H', r[16:18])[0]
    h = struct.unpack('<H', r[18:20])[0]
    n = (hs - 4) // 4
    if n != 3 and n != 4:
        print(f'Resource {idx}: header_size={hs}, frames={n}, {w}x{h}')
        print(f'  First 20 bytes: {r[:20].hex()}')
        break

# Check if there's a pattern for 4 frames
# Maybe header_size=16 means: 4(DWORD) + 3*4(offsets) + 2(w) + 2(h) = 18 bytes header? No...
# Actually: header_size=16 could mean 16 bytes of frame offset table = 4 offsets
# Format: [header_size:4] [4 offsets: 16] [width:2] [height:2] = 24 bytes
# But then offsets start at byte 4, and offsets[3] would be at byte 16
# which is where we read width!

# Wait - what if header_size=16 means the offsets table is 16 bytes = 4 offsets?
# And the actual structure is:
# [4] header_size=16
# [4] offset0
# [4] offset1
# [4] offset2
# [4] offset3  <-- 4th frame!
# Then width/height at bytes 20-23?
# Let's check

idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

print(f'\n=== Try: 4 offsets at bytes 4,8,12,16, then w/h at 20,22 ===')
for i in range(4):
    off = struct.unpack('<I', r[4+i*4:8+i*4])[0]
    print(f'  offset[{i}] = {off}')
w = struct.unpack('<H', r[20:22])[0]
h = struct.unpack('<H', r[22:24])[0]
print(f'  width={w}, height={h} (at bytes 20,22)')

# But offset[3] at byte 16 = 0x00500050 = 5242960 which is way too large
# Unless it's not an offset but something else

# Let me try another interpretation:
# Maybe byte 16 = num_frames, bytes 17-19 = padding
print(f'\n=== Try: byte 16 = num_frames ===')
print(f'  byte[16] = {r[16]}')
print(f'  byte[17] = {r[17]}')
print(f'  bytes[18-19] = {struct.unpack("<H", r[18:20])[0]}')

# Hmm, byte 16 = 0x50 = 80 which is width
# Let me check if maybe the format has 4 offsets stored differently
# What if there are 4 frame offsets but they're WORDs (2 bytes) not DWORDs?
# [4] header_size
# [2] offset0_w, [2] offset0_h? No that doesn't make sense either

# Let me look at the actual bytes more carefully
print(f'\nRaw bytes 0-32:')
for i in range(0, 32, 4):
    d = struct.unpack('<I', r[i:i+4])[0]
    print(f'  [{i}] 0x{d:08X} = {d}')
