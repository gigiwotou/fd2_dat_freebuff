#!/usr/bin/env python3
"""
Verify Map 32 sprite rendering and camera positioning.
Simulates the exact C code logic to find why only 1 sprite is visible.
"""

import struct

# Read FDFIELD.DAT
with open('game/FDFIELD.DAT', 'rb') as f:
    fdfield_data = f.read()

# Parse index table
count = (len(fdfield_data) - 6) // 4
fdfield_offsets = []
for i in range(count):
    pos = 6 + i * 4
    offset = struct.unpack_from('<I', fdfield_data, pos)[0]
    fdfield_offsets.append(offset)

# Map 32
map_id = 32
layout_idx = 3 * map_id
control_idx = 3 * map_id + 1
charpos_idx = 3 * map_id + 2

# Get control data
control_start = fdfield_offsets[control_idx]
control_end = fdfield_offsets[control_idx + 1]
control_data = fdfield_data[control_start:control_end]

# Parse control data
max_friendly = control_data[1]
total_units = control_data[2]

# Get char pos data
charpos_start = fdfield_offsets[charpos_idx]
charpos_end = fdfield_offsets[charpos_idx + 1]
charpos_data = fdfield_data[charpos_start:charpos_end]

# Parse character positions
total_chars = struct.unpack_from('<H', charpos_data, 0)[0]
char_positions = []
for i in range(total_chars):
    offset = 2 + i * 6
    if offset + 6 > len(charpos_data):
        break
    x = charpos_data[offset]
    y = charpos_data[offset + 2]
    portrait = charpos_data[offset + 4]
    char_positions.append({'x': x, 'y': y, 'portrait': portrait, 'index': i})

print("Map 32 Character Analysis")
print("=" * 70)
print(f"Map dimensions: 18x51 tiles")
print(f"Total characters: {total_chars}")
print(f"max_friendly: {max_friendly}")
print(f"total_units: {total_units}")
print()

# Simulate C code camera centering
valid_chars = [c for c in char_positions if c['x'] != 0 or c['y'] != 0]

if valid_chars:
    min_x = min(c['x'] for c in valid_chars)
    min_y = min(c['y'] for c in valid_chars)
    max_x = max(c['x'] for c in valid_chars)
    max_y = max(c['y'] for c in valid_chars)
    
    center_tile_x = (min_x + max_x) // 2
    center_tile_y = (min_y + max_y) // 2
    
    MAP_TILE_SIZE = 24
    SCREEN_W = 320
    SCREEN_H = 200
    
    camera_x = center_tile_x * MAP_TILE_SIZE - SCREEN_W // 2
    camera_y = center_tile_y * MAP_TILE_SIZE - SCREEN_H // 2
    
    map_pixel_width = 18 * MAP_TILE_SIZE
    map_pixel_height = 51 * MAP_TILE_SIZE
    
    max_cam_x = map_pixel_width - SCREEN_W
    max_cam_y = map_pixel_height - SCREEN_H
    if max_cam_x < 0: max_cam_x = 0
    if max_cam_y < 0: max_cam_y = 0
    if camera_x < 0: camera_x = 0
    if camera_y < 0: camera_y = 0
    if camera_x > max_cam_x: camera_x = max_cam_x
    if camera_y > max_cam_y: camera_y = max_cam_y
    
    print("Camera Centering Result:")
    print(f"  Bounding box: ({min_x},{min_y}) to ({max_x},{max_y})")
    print(f"  Center tile: ({center_tile_x},{center_tile_y})")
    print(f"  Camera: ({camera_x},{camera_y})")
    print(f"  Max camera: ({max_cam_x},{max_cam_y})")
    print()
    
    # Calculate visible tile range
    visible_tile_x_start = camera_x // MAP_TILE_SIZE
    visible_tile_y_start = camera_y // MAP_TILE_SIZE
    visible_tile_x_end = (camera_x + SCREEN_W) // MAP_TILE_SIZE
    visible_tile_y_end = (camera_y + SCREEN_H) // MAP_TILE_SIZE
    
    print(f"Visible tile range: X[{visible_tile_x_start}-{visible_tile_x_end}], Y[{visible_tile_y_start}-{visible_tile_y_end}]")
    print()
    
    # Check each character
    print("Character Visibility Analysis:")
    print("-" * 70)
    visible_count = 0
    for c in valid_chars:
        screen_x = c['x'] * MAP_TILE_SIZE - camera_x
        screen_y = c['y'] * MAP_TILE_SIZE - camera_y
        
        is_visible = (screen_x >= 0 and screen_x < SCREEN_W and 
                     screen_y >= 0 and screen_y < SCREEN_H)
        
        if is_visible:
            visible_count += 1
            status = "VISIBLE"
        else:
            status = "OFFSCREEN"
        
        print(f"  Char {c['index']:2d}: tile=({c['x']:2d},{c['y']:2d}) "
              f"portrait={c['portrait']:3d} -> screen=({screen_x:4d},{screen_y:4d}) {status}")
    
    print()
    print(f"Total visible characters: {visible_count}/{len(valid_chars)}")
    print()
    
    # Check character_icon position
    char_icon_x = 5
    char_icon_y = 5
    char_icon_screen_x = char_icon_x * MAP_TILE_SIZE - camera_x
    char_icon_screen_y = char_icon_y * MAP_TILE_SIZE - camera_y
    char_icon_visible = (char_icon_screen_x >= 0 and char_icon_screen_x < SCREEN_W and
                        char_icon_screen_y >= 0 and char_icon_screen_y < SCREEN_H)
    
    print(f"character_icon at tile ({char_icon_x},{char_icon_y}):")
    print(f"  Screen position: ({char_icon_screen_x},{char_icon_screen_y})")
    print(f"  Visible: {'YES' if char_icon_visible else 'NO'}")
    print()
    
    # What the user sees
    print("What user should see on screen:")
    if char_icon_visible:
        print(f"  - character_icon (hardcoded) at screen ({char_icon_screen_x},{char_icon_screen_y})")
    for c in valid_chars:
        screen_x = c['x'] * MAP_TILE_SIZE - camera_x
        screen_y = c['y'] * MAP_TILE_SIZE - camera_y
        if screen_x >= 0 and screen_x < SCREEN_W and screen_y >= 0 and screen_y < SCREEN_H:
            print(f"  - Enemy {c['index']} at screen ({screen_x},{screen_y})")
