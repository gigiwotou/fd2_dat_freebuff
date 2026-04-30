import struct

with open('game/FDFIELD.DAT', 'rb') as f:
    data = f.read()

# Parse index table
count = (len(data) - 6) // 4
offsets = []
for i in range(count):
    pos = 6 + i * 4
    offset = struct.unpack_from('<I', data, pos)[0]
    offsets.append(offset)

# Map 32
map_id = 32
charpos_idx = 3 * map_id + 2

charpos_start = offsets[charpos_idx]
charpos_end = offsets[charpos_idx + 1]
charpos_data = data[charpos_start:charpos_end]

total_chars = struct.unpack_from('<H', charpos_data, 0)[0]

# Parse character positions
positions = []
for i in range(total_chars):
    offset = 2 + i * 6
    if offset + 6 > len(charpos_data):
        break
    
    x = charpos_data[offset]
    y = charpos_data[offset + 2]
    portrait = charpos_data[offset + 4]
    
    if x != 0 or y != 0:
        positions.append((x, y, portrait, i))

print(f"Map 32: {len(positions)} valid characters out of {total_chars}")
print()

# Find bounding box
min_x = min(p[0] for p in positions)
min_y = min(p[1] for p in positions)
max_x = max(p[0] for p in positions)
max_y = max(p[1] for p in positions)

center_tile_x = (min_x + max_x) // 2
center_tile_y = (min_y + max_y) // 2

MAP_TILE_SIZE = 24
SCREEN_W = 320
SCREEN_H = 200

camera_x = center_tile_x * MAP_TILE_SIZE - SCREEN_W // 2
camera_y = center_tile_y * MAP_TILE_SIZE - SCREEN_H // 2

# Map 32: 18x51 tiles
map_width = 18
map_height = 51
map_pixel_width = map_width * MAP_TILE_SIZE
map_pixel_height = map_height * MAP_TILE_SIZE

max_cam_x = map_pixel_width - SCREEN_W
max_cam_y = map_pixel_height - SCREEN_H
if max_cam_x < 0: max_cam_x = 0
if max_cam_y < 0: max_cam_y = 0
if camera_x < 0: camera_x = 0
if camera_y < 0: camera_y = 0
if camera_x > max_cam_x: camera_x = max_cam_x
if camera_y > max_cam_y: camera_y = max_cam_y

print(f"Character positions:")
for x, y, portrait, i in positions:
    screen_x = x * MAP_TILE_SIZE - camera_x
    screen_y = y * MAP_TILE_SIZE - camera_y
    on_screen = (0 <= screen_x < SCREEN_W and 0 <= screen_y < SCREEN_H)
    print(f"  Char {i:2d}: tile=({x:2d},{y:2d}), portrait={portrait:3d} -> screen=({screen_x:4d},{screen_y:4d}) {'ON' if on_screen else 'OFF'} screen")

print()
print(f"Bounding box: ({min_x},{min_y}) to ({max_x},{max_y})")
print(f"Center tile: ({center_tile_x},{center_tile_y})")
print(f"Camera: ({camera_x},{camera_y})")
print(f"Map size: {map_pixel_width}x{map_pixel_height} pixels")
print(f"Screen size: {SCREEN_W}x{SCREEN_H} pixels")
print(f"Max camera: ({max_cam_x},{max_cam_y})")
print()

# Count visible characters
visible = 0
for x, y, portrait, i in positions:
    screen_x = x * MAP_TILE_SIZE - camera_x
    screen_y = y * MAP_TILE_SIZE - camera_y
    if 0 <= screen_x < SCREEN_W and 0 <= screen_y < SCREEN_H:
        visible += 1

print(f"Characters visible on screen: {visible}/{len(positions)}")
