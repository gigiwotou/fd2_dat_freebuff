import struct
from collections import Counter
import json

data = open('game/FDFIELD.DAT', 'rb').read()
rc = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(rc):
    offsets.append(struct.unpack_from('<I', data, 10 + i * 4)[0])

layout_start = offsets[0]
control_start = offsets[1]

# Parse layout with the IDA formula
w_raw = struct.unpack_from('<H', data, layout_start)[0]
h_raw = struct.unpack_from('<H', data, layout_start + 2)[0]
print(f'Raw dimensions: {w_raw}x{h_raw} (should be 1024x798)')

# Resource 0 size is 937 bytes (offsets[1] - offsets[0])
res0_size = offsets[1] - offsets[0]
print(f'Resource 0 size: {res0_size} bytes')

# The layout is: 4-byte header + tile_data
# But 937 - 4 = 933, which is not divisible by 4
# Maybe dimensions are stored as bytes, not 16-bit values?

# Let's try reading dimensions as individual bytes
b0 = data[layout_start]
b1 = data[layout_start + 1]
b2 = data[layout_start + 2]
b3 = data[layout_start + 3]
print(f'First 4 bytes: [{b0:02x} {b1:02x} {b2:02x} {b3:02x}]')

# If dimensions are stored differently...
# Try: width = b2, height = b3?
# width=0x1E=30, height=0x03=3... no
# Try: width = (b1 << 8) | b0 = 1024, height = (b3 << 8) | b2 = 798

# Actually, let me check what the working map_verify.py thinks
# It said Map 0 is 24x24. Where does that come from?

# The map_verify.py has this logic:
# if w <= 0 or w > 200 or h <= 0 or h > 200:
#     continue
# So 1024 and 798 would be filtered out!

# But we know map_verify.py found 24x24. Let me check where that comes from...

# Looking at the map_verify.py output:
# "Map 0: 24x24 tiles"

# This means the validation is working. So the raw dimensions ARE 1024x798,
# but they get filtered out... so where does 24x24 come from?

# Wait, let me re-read the map_verify.py code. It has:
# max_maps = resource_count // 3
# But the offset parsing might be wrong!

print(f'\nNumber of resources: {rc}')
print(f'Offsets count: {len(offsets)}')
print(f'Expected maps: {rc // 3}')

# Let me check resource 1 (control)
print(f'\nControl data (resource 1):')
for i in range(10):
    print(f'  Byte {i}: {data[control_start + i]:02x} = {data[control_start + i]}')

# terrain_set_id = data[control_start]
# Let me check if the map_verify.py is reading this correctly
