import struct

data = open('game/FDFIELD.DAT', 'rb').read()

# Get the actual resource offsets
rc = struct.unpack_from('<I', data, 6)[0]
resource_offsets = []
pos = 6
while pos < len(data) - 4 and len(resource_offsets) < rc:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        resource_offsets.append(offset)
    else:
        break
    pos += 4

print(f'Parsed {len(resource_offsets)} resource offsets')
print(f'First 5 offsets: {resource_offsets[:5]}')

# Map 0
map0_layout = resource_offsets[0]
map0_control = resource_offsets[1]
map0_spawn = resource_offsets[2]

print(f'\nMap 0:')
print(f'  Layout at: {map0_layout} (raw bytes: {data[map0_layout:map0_layout+8].hex(" ")})')
print(f'  Control at: {map0_control} (raw bytes: {data[map0_control:map0_control+16].hex(" ")})')
print(f'  Spawn at: {map0_spawn}')

# Parse control
terrain_set_id = data[map0_control]
ally_max = data[map0_control + 1]
enemy_total = data[map0_control + 2]

print(f'\nControl data:')
print(f'  terrain_set_id: {terrain_set_id}')
print(f'  ally_max: {ally_max}')
print(f'  enemy_total: {enemy_total}')
print(f'  Byte 3: {data[map0_control + 3]}')
print(f'  Byte 4: {data[map0_control + 4]}')
print(f'  Byte 5: {data[map0_control + 5]}')

# FDSHAP resources
fdshap = open('game/FDSHAP.DAT', 'rb').read()
fdshap_rc = struct.unpack_from('<I', fdshap, 6)[0]
fdshap_offsets = []
for i in range(fdshap_rc):
    fdshap_offsets.append(struct.unpack_from('<I', fdshap, 10 + i * 4)[0])

print(f'\nFDSHAP.DAT: {fdshap_rc} resources')
palette_res = terrain_set_id * 2
tile_res = terrain_set_id * 2 + 1

print(f'For terrain_set_id={terrain_set_id}:')
print(f'  Palette resource: {palette_res}')
print(f'  Tile resource: {tile_res}')

if palette_res < fdshap_rc:
    print(f'  Palette resource size: {fdshap_offsets[palette_res+1] - fdshap_offsets[palette_res]}')
if tile_res < fdshap_rc:
    print(f'  Tile resource size: {fdshap_offsets[tile_res+1] - fdshap_offsets[tile_res]}')
    tile_w = struct.unpack_from('<H', fdshap, fdshap_offsets[tile_res])[0]
    tile_h = struct.unpack_from('<H', fdshap, fdshap_offsets[tile_res] + 2)[0]
    print(f'  Tile dimensions: {tile_w}x{tile_h}')