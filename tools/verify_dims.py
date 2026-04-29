import struct

data = open('game/FDFIELD.DAT', 'rb').read()
layout_start = 406
print(f'Real Map 0 layout at: {layout_start}')
print(f'Header bytes: {data[layout_start:layout_start+8].hex(" ")}')
w = struct.unpack_from('<H', data, layout_start)[0]
h = struct.unpack_from('<H', data, layout_start + 2)[0]
print(f'Dimensions: {w}x{h}')
print(f'Size of resource: {2714-406} bytes')
print(f'Expected tile data size: {w*h*4+4} bytes')
tile_data_size = (2714-406)-4
print(f'Actual tile data size: {tile_data_size} bytes')
print(f'Can fit {tile_data_size//4} tiles')
print(f'Expected {w*h} tiles')
print(f'Perfect match: {tile_data_size//4 == w*h}')