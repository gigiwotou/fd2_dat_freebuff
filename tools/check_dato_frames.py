import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

idx = 0
off_start = struct.unpack('<I', data[10 + idx * 4: 14 + idx * 4])[0]
off_end = struct.unpack('<I', data[10 + (idx + 1) * 4: 14 + (idx + 1) * 4])[0]
res_data = data[off_start:off_end]

header_size = struct.unpack('<I', res_data[0:4])[0]
frame0_off = struct.unpack('<I', res_data[4:8])[0]
frame1_off = struct.unpack('<I', res_data[8:12])[0]
frame2_off = struct.unpack('<I', res_data[12:16])[0]
width = struct.unpack('<H', res_data[16:18])[0]
height = struct.unpack('<H', res_data[18:20])[0]

print(f'Resource header: header_size={header_size}, frames=[{frame0_off},{frame1_off},{frame2_off}], {width}x{height}')

frames = [frame0_off, frame1_off, frame2_off]
for i, frame_off in enumerate(frames):
    next_off = frames[i+1] if i < 2 else len(res_data)
    frame_data = res_data[frame_off:next_off]
    f_w = struct.unpack('<H', frame_data[0:2])[0]
    f_h = struct.unpack('<H', frame_data[2:4])[0]
    pixel_data = frame_data[20:20+6400]
    print(f'Frame {i}: size={len(frame_data)}, {f_w}x{f_h}, pixels[{min(pixel_data)}..{max(pixel_data)}], unique={len(set(pixel_data))}')
