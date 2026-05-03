import struct

f = open('game/FDMUS.DAT', 'rb')
h = f.read(10)
count = struct.unpack('<I', h[6:10])[0]

offsets = []
for i in range(count):
    offsets.append(struct.unpack('<I', f.read(4))[0])

# Analyze Track 11
track = 11
f.seek(offsets[track])
data = f.read(offsets[track+1] - offsets[track]) if track+1 < count else f.read()
f.close()

print(f'Track {track}: {len(data)} bytes')
print(f'First 50 bytes: {data[:50].hex()}')

# Quick XMIDI parse to find max tick
pos = 0
# Skip header metas
while pos < len(data) and data[pos] == 0xFF:
    mt = data[pos+1]
    # Parse var len
    lb = 0
    while data[pos+2+lb] & 0x80:
        lb += 1
    lb += 1
    length = 0
    for i in range(lb):
        length = (length << 7) | (data[pos+2+i] & 0x7F)
    length = length | (data[pos+2+lb-1] & 0x7F)  # This is wrong, let me just skip
    pos += 2 + lb
    # Actually let me use a simpler approach
    break  # Just analyze raw bytes

# Let me just count bytes that look like note events
note_count = 0
for i in range(len(data)):
    if data[i] >= 0x90 and data[i] <= 0x9F:
        note_count += 1
print(f'Note On events: {note_count}')
