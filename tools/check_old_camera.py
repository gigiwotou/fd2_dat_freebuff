"""
Check visibility with OLD camera position (0,0) - what user is currently seeing.
"""
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
    positions.append((x, y, portrait, i))

# Map parameters
MAP_TILE_SIZE = 24
SCREEN_W = 320
SCREEN_H = 200

# OLD camera position (0, 0)
camera_x = 0
camera_y = 0

print("OLD camera position: (0, 0)")
print()

sprite_width = 24
sprite_height = 24

print("Character rendering with OLD camera (0,0):")
print("=" * 100)

visible_count = 0
for x, y, portrait, i in positions:
    if x == 0 and y == 0:
        print(f"Char {i:2d}: tile=({x:2d},{y:2d}) -> SKIP (0,0)")
        continue
    
    # This is the EXACT calculation from fd2_game.c
    screen_x = x * MAP_TILE_SIZE - camera_x
    screen_y = y * MAP_TILE_SIZE - camera_y
    draw_x = screen_x - sprite_width // 2
    draw_y = screen_y - sprite_height // 2
    
    # Check visibility (is_sprite_visible)
    is_visible = (draw_x + sprite_width > 0 and 
                  draw_x < SCREEN_W and
                  draw_y + sprite_height > 0 and 
                  draw_y < SCREEN_H)
    
    if is_visible:
        visible_count += 1
        status = "VISIBLE"
    else:
        status = "OFFSCREEN"
    
    print(f"Char {i:2d}: tile=({x:2d},{y:2d}) portrait={portrait:3d} -> screen=({screen_x:4d},{screen_y:4d}) draw=({draw_x:4d},{draw_y:4d}) {status}")

print()
print(f"Visible characters with camera (0,0): {visible_count}")
