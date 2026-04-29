import struct

data = open('game/FDFIELD.DAT', 'rb').read()
rc = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(rc):
    offsets.append(struct.unpack_from('<I', data, 10 + i * 4)[0])

layout_start = offsets[0]
print(f'Resource 0 (layout) starts at: {layout_start}')
print(f'Resource header bytes: {data[layout_start:layout_start+8].hex(" ")}')

w = struct.unpack_from('<H', data, layout_start)[0]
h = struct.unpack_from('<H', data, layout_start + 2)[0]
print(f'Direct read: w={w}, h={h}')
print(f'Expected map 0 should be 24x24 based on previous analysis')

print(f'\nResource 1 (control) starts at: {offsets[1]}')
control_start = offsets[1]
print(f'Control byte[0] (terrain_set_id): {data[control_start]}')
print(f'Control byte[1] (ally_max): {data[control_start+1]}')
print(f'Control byte[2] (enemy_total): {data[control_start+2]}')

print(f'\nResource size: {offsets[1]-layout_start} bytes')
print(f'Expected tile data size for 24x24: {24*24*4} bytes')

# Check if dimensions might be stored differently
# Try little-endian 16-bit at different offsets
for i in range(0, 8, 2):
    val = struct.unpack_from('<H', data, layout_start + i)[0]
    print(f'  Offset {i}: 0x{val:04x} = {val}')
