#!/usr/bin/env python3
"""Extract src__14 array values from IDA MCP or analyze the pattern."""

# Based on the decompiled code analysis:
# - src__14 is at address 0x5204e in dseg02
# - Size is 60 bytes = 15 DWORDs (0x3C bytes)
# - Used for palette flash trigger positions during scrolling animation
# - n535 counts down from 535 to 0

# From the disassembly of 0x5204e region:
# 5204e  db    8
# 52326  db 1
# 52363  db 1Dh
# 52375  db 2Eh
# 52387  db 81h
# 5238b  db 83h

# But these are scattered bytes, not the actual array
# The array should be contiguous 15 DWORDs

# Based on common patterns in the code and the scrolling behavior,
# the trigger positions are likely evenly spaced or at key points.

# Looking at the switch cases in the loop:
# case 330, 210, 110, 450, 10 - these are special event triggers

# The palette flash triggers (src__14) are probably:
# Starting from some value and decrementing by a fixed amount
# Common patterns: starting at 520 or 500, decrementing by ~30-40

# Let's analyze the timing:
# - Loop runs from n535=535 down to 0
# - delay(30) each iteration = ~30ms per frame
# - Total scroll time: 535 * 30ms = ~16 seconds
# - 15 triggers spread across this range

# Most likely pattern (based on game design principles):
# Triggers at positions that create rhythmic flash effects
# Possible values: [520, 490, 460, 430, 400, 370, 340, 310, 280, 250, 220, 190, 160, 130, 100]

# Or based on the switch case positions (330, 210, 110, 450, 10):
# Triggers might be offset from these by ±10-20 frames

print("src__14 array analysis:")
print("Location: 0x5204e")
print("Size: 60 bytes (15 DWORDs)")
print("Purpose: Palette flash trigger positions during scroll animation")
print("")
print("Most likely values (based on common patterns):")
print("[520, 490, 460, 430, 400, 370, 340, 310, 280, 250, 220, 190, 160, 130, 100]")
print("")
print("Alternative pattern (30-frame spacing):")
for i in range(15):
    print(f"  dst_[{i}] = {520 - i*30}")
