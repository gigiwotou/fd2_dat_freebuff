# Map 32 Sprite Rendering Analysis

## Problem
User sees only 1 character (needs to scroll to top-left), but logs show 4 characters were "DRAWN".

## Root Cause Analysis

### From Terminal Logs:
- 4 map characters were marked DRAWN (Char 9,10,17,18 with portrait=68/69)
- Screen positions: (112,52), (232,52), (112,148), (232,148) - ALL within 320x200 screen
- The hardcoded `character_icon` at tile(5,5) was NOT VISIBLE (screen=(88,-404))

### Python Export Results:
- Portrait 68: 464/576 pixels non-zero
- Portrait 69: 462/576 pixels non-zero
- Sprite data is VALID

### Possible Causes:
1. C code RLE decoding produces all zeros (but Python shows same algorithm works)
2. Rendering order - map overwrites sprites after they're drawn
3. Palette issue - indices don't map to visible colors

## Fix
Added debug output to check non-zero pixel count in C code after decoding.
The debug line will show: "Decoded pixels: X non-zero/576 total, first@Y"

## Next Step
Recompile and run game to see debug output. If pixel count is 0, the issue is in RLE decoding.
If pixel count is >400 (like Python shows), the issue is rendering order or palette.
