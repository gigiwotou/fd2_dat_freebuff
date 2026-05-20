import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[6:10])[0]
print(f'DATO.DAT: {count} resources, file size: {len(data)}')

idx = 0
off_s = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_e = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
r = data[off_s:off_e]

print(f'\nResource 0: {len(r)} bytes')
print(f'header_size={struct.unpack("<I", r[0:4])[0]}')

# Structure:
# [4] header_size=16
# [4] offset0=3165
# [4] offset1=6328
# [4] offset2=9512
# [2] width=80
# [2] height=80
# [?] frame 0 data starting at byte 20

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

w = struct.unpack('<H', r[16:18])[0]
h = struct.unpack('<H', r[18:20])[0]
frame_offs = [struct.unpack('<I', r[4+i*4:8+i*4])[0] for i in range(3)]

print(f'{w}x{h}, frame offsets: {frame_offs}')

# Frame 0: bytes 20 to frame_offs[0]
compressed_0 = r[20:frame_offs[0]]
decoded_0 = decode_rle(compressed_0)
print(f'\nFrame 0: byte 20 to {frame_offs[0]}')
print(f'  compressed={len(compressed_0)}, decoded={len(decoded_0)} (expected {w*h}={w*h})')

# Frame 1: frame_offs[0]+4 to frame_offs[1] (skip 4 bytes w,h)
compressed_1 = r[frame_offs[0]+4:frame_offs[1]]
decoded_1 = decode_rle(compressed_1)
print(f'\nFrame 1: byte {frame_offs[0]+4} to {frame_offs[1]}')
print(f'  compressed={len(compressed_1)}, decoded={len(decoded_1)}')

# Frame 2: frame_offs[1]+4 to frame_offs[2]
compressed_2 = r[frame_offs[1]+4:frame_offs[2]]
decoded_2 = decode_rle(compressed_2)
print(f'\nFrame 2: byte {frame_offs[1]+4} to {frame_offs[2]}')
print(f'  compressed={len(compressed_2)}, decoded={len(decoded_2)}')

# Frame 3: frame_offs[2]+4 to end
compressed_3 = r[frame_offs[2]+4:]
decoded_3 = decode_rle(compressed_3)
print(f'\nFrame 3: byte {frame_offs[2]+4} to {len(r)}')
print(f'  compressed={len(compressed_3)}, decoded={len(decoded_3)}')

print(f'\n=== Summary ===')
total_pixels = len(decoded_0) + len(decoded_1) + len(decoded_2) + len(decoded_3)
print(f'Total decoded pixels: {total_pixels}')
print(f'Expected for 4 frames: {w*h*4} = {w*h*4}')
