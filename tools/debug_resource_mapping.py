import struct

data = open('game/FDFIELD.DAT', 'rb').read()
rc = struct.unpack_from('<I', data, 6)[0]
print(f'Total resources claimed: {rc}')

# Read all resource offsets
resource_offsets = []
pos = 6
while pos < len(data) - 4 and len(resource_offsets) < rc:
    offset = struct.unpack_from("<I", data, pos)[0]
    if offset > pos and offset < len(data):
        resource_offsets.append(offset)
    else:
        break
    pos += 4

print(f'Actual resource offsets parsed: {len(resource_offsets)}')

max_maps = len(resource_offsets) // 3
print(f'Max possible maps: {max_maps}')

for map_id in range(min(5, max_maps)):  # Check first 5 maps
    layout_res_idx = map_id * 3
    layout_start = resource_offsets[layout_res_idx]
    control_start = resource_offsets[layout_res_idx + 1]
    spawn_start = resource_offsets[layout_res_idx + 2]
    
    w = struct.unpack_from("<H", data, layout_start)[0]
    h = struct.unpack_from("<H", data, layout_start + 2)[0]
    
    print(f'Map {map_id}:')
    print(f'  Layout resource: {layout_res_idx} (offset {layout_start})')
    print(f'  Control resource: {layout_res_idx + 1} (offset {control_start})')
    print(f'  Spawn resource: {layout_res_idx + 2} (offset {spawn_start})')
    print(f'  Raw dimensions: {w}x{h}')
    print(f'  Validated: {w > 0 and w <= 200 and h > 0 and h <= 200}')
    if w <= 0 or w > 200 or h <= 0 or h > 200:
        print(f'    -> Skipped due to size validation')
    else:
        print(f'    -> Will be processed')
        print(f'  Resource sizes: {control_start - layout_start}, {spawn_start - control_start}, ...')
    print()
