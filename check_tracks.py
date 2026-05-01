import struct

f = open('game/FDMUS.DAT', 'rb')
h = f.read(10)
magic = h[:6]
count = struct.unpack('<I', h[6:10])[0]
print(f'Magic: {magic}, Count: {count}')

offsets = []
for i in range(count):
    offsets.append(struct.unpack('<I', f.read(4))[0])

for i in range(count):
    if i + 1 < count:
        size = offsets[i+1] - offsets[i]
    else:
        f.seek(0, 2)
        size = f.tell() - offsets[i]
    if size > 100:  # Only print valid tracks (more than 3 bytes)
        print(f'  Track {i}: offset={offsets[i]}, size={size} bytes')

f.close()
