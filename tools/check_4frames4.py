import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]

# Check header_size values
hs_counts = {}
for i in range(min(count-1, 500)):
    off_s = struct.unpack('<I', data[10 + i * 4: 14 + i * 4])[0]
    if off_s + 4 > len(data): continue
    hs = struct.unpack('<I', data[off_s:off_s+4])[0]
    hs_counts[hs] = hs_counts.get(hs, 0) + 1

print('Header size distribution:')
for hs, cnt in sorted(hs_counts.items()):
    print(f'  {hs}: {cnt}')

# If ALL resources have header_size=16, then the structure is uniform
# Let's check what header_size=20, 24 etc would mean
# header_size=16: (16-4)/4 = 3 frame offsets

# Alternative theory: header_size is the size of the "offset table" portion
# header_size=16 means 16 bytes of offsets = 4 DWORD offsets
# Format: [4] header_size + [16] 4 offsets + [2] w + [2] h
# Total header = 24 bytes, but header_size only counts the offset table portion

# Let me check if offset[3] could be valid for ANY resource
print('\nChecking if any resource has a valid 4th offset:')
for i in range(10):
    off_s = struct.unpack('<I', data[10 + i * 4: 14 + i * 4])[0]
    off_e = struct.unpack('<I', data[10 + (i + 1) * 4: 14 + (i + 1) * 4])[0]
    if off_e > len(data) or off_s >= off_e: continue
    r = data[off_s:off_e]
    
    # Try 4 offsets at bytes 4, 8, 12, 16
    off3 = struct.unpack('<I', r[16:20])[0]
    if off3 > 0 and off3 < len(r):
        print(f'  Resource {i}: offset[3]={off3} (valid!)')
    else:
        print(f'  Resource {i}: offset[3]={off3} (invalid, size={len(r)})')

# Maybe the 4th frame is NOT in the offset table at all
# Maybe it's simply: frame data for frames 0,1,2 stored at offsets
# And frame 3 is always "the rest" after frame 2's data?
# But the RLE decode of frame 2 already gives ~6400 pixels...

# Let me check the actual game code logic more carefully
# sub_111BA loads a resource by index
# The decompiled code shows:
#   dword_53A85 = sub_111BA(..., n39)  // load DATO.DAT resource n39
#   a1 = *(unsigned __int8 *)dword_53A85 + dword_53A85  // get pixel data
#   sub_4EBFF(..., a1, 320)  // render with width=80, height=80

# So sub_4EBFF receives a pointer to pixel data directly
# a1 = *(uint8_t*)dword_53A85 + dword_53A85
# This means: first byte of resource + base address = pointer to pixels
# If first byte is 0x10 = 16, then pixels start at offset 16!

# But wait, the resource starts with: [16][3165][6328][9512][80][80]...
# If first byte = 16 (offset to pixels), then bytes 16 onwards = pixel data
# bytes[16] = 0x50 = 80, bytes[17] = 0x00
# That's width value, not pixel data

# Let me re-examine: *(uint8_t*)dword_53A85 means the FIRST BYTE of the loaded resource
# In the resource, first byte = 0x10 = 16 (low byte of header_size=16)
# So pixel data starts at byte 16 of the resource!
# bytes 16-19: 0x50 0x00 0x50 0x00 = width=80, height=80
# bytes 20+: RLE compressed pixel data

# But that means the offset table (bytes 4-15) is NOT used for pixel data
# The offsets must be for something else...

# Unless... the offsets are used for animation frames, and the "pixel data at offset 16" 
# is a DIFFERENT thing (maybe a static/default image)

# Let me check bytes 20+ as RLE compressed 80x80 image
print('\n=== Bytes 20+ as RLE compressed image: ===')
idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

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

compressed_20 = r[20:]
decoded_20 = decode_rle(compressed_20)
print(f'Compressed from byte 20: {len(compressed_20)} bytes')
print(f'Decoded: {len(decoded_20)} pixels (expected 6400)')

# Also try: maybe header_size=16 means "data starts at byte 16"
# And the offset table bytes 4-15 contain frame offsets
# But only 3 offsets... unless the 4th frame is the data at byte 16?

# Actually wait - re-reading the decompiled code:
# a1 = *(uint8_t*)dword_53A85 + dword_53A85
# This is: a1 = resource[0] + resource_base
# resource[0] = 0x10 = 16 (but this is the LOW byte of the DWORD 0x00000010)
# Actually in memory, 0x00000010 is stored as 10 00 00 00
# So resource[0] = 0x10 = 16
# a1 = resource_base + 16

# So pixel data IS at byte 16 of the resource
# And the offset table (bytes 4-15) is for something else (maybe animation?)

# The offset values 3165, 6328, 9512 - these are MUCH larger than 16
# They could be offsets to additional animation frames or data

# New theory:
# Bytes 0-3: header_size=16 (offset to main image data)
# Bytes 4-15: 3 animation frame offsets
# Bytes 16+: main image data (80x80 RLE compressed)
# Frames 0,1,2 from offset table are additional animation frames
# Frame 3 = main image at byte 16

print('\n=== Check if bytes 16+ is the 4th frame: ===')
w = struct.unpack('<H', r[16:18])[0]
h = struct.unpack('<H', r[18:20])[0]
print(f'Bytes 16-17 (width): {w}')
print(f'Bytes 18-19 (height): {h}')

# If bytes 16-19 contain w=80, h=80, then compressed data starts at byte 20
# Decode from byte 20:
compressed_main = r[20:]
decoded_main = decode_rle(compressed_main)
print(f'Main image compressed: {len(compressed_main)} bytes')
print(f'Main image decoded: {len(decoded_main)} pixels')
