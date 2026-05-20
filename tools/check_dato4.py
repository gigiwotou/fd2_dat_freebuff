import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

off0 = struct.unpack('<I', data[10:14])[0]
print(f'Resource 0 starts at: {hex(off0)}')

# Structure: [16 (count?): 2B] [offset1: 2B] [offset2: 2B] ... [offset16: 2B] [data]
# First WORD at byte 0: 16
# Let's check if bytes 2-33 are 16 offsets (2 bytes each)
count = struct.unpack('<H', data[off0:off0+2])[0]
print(f'Count at byte 0: {count}')

print(f'\nChecking {count} sub-offsets at byte 2 (2 bytes each):')
sub_offsets_2b = []
for i in range(count):
    pos = off0 + 2 + i * 2
    offset_val = struct.unpack('<H', data[pos:pos+2])[0]
    sub_offsets_2b.append(offset_val)
    print(f'  sub[{i}] at byte {2+i*2}: {offset_val} (0x{offset_val:04X})')

# Check if sub_offsets are relative offsets within resource
# Last offset should point to end or near end
last_off = sub_offsets_2b[-1]
print(f'\nLast sub-offset: {last_off}')
print(f'Resource 0 size: {12665}')
print(f'If relative, last data starts at byte {last_off}')

# Check what's at the last offset position
if last_off < 12665:
    pos = off0 + last_off
    print(f'Data at last offset: {data[pos:pos+10].hex()}')

# Let's check if the structure is actually:
# [4 bytes: something] [16 sub-offsets: 4 bytes each] [data]
# First 4 bytes: 10 00 00 00
print(f'\nAlternative: 4-byte sub-offsets')
count_4 = struct.unpack('<I', data[off0:off0+4])[0]
print(f'First DWORD: {count_4}')
if count_4 == 16:
    print(f'16 sub-offsets at byte 4 (4 bytes each):')
    for i in range(16):
        pos = off0 + 4 + i * 4
        offset_val = struct.unpack('<I', data[pos:pos+4])[0]
        print(f'  sub[{i}] at byte {4+i*4}: {offset_val}')

# Or maybe first 4 bytes are just a marker, then [count: 2B] [offsets: 4B each]
# byte 0-3: 10 00 00 00 (maybe width/height or marker)
# byte 4-5: count
# byte 6+: offsets (4B each)
count_alt = struct.unpack('<H', data[off0+4:off0+6])[0]
print(f'\nAlternative 2: count at byte 4 = {count_alt}')
if count_alt > 0 and count_alt < 100:
    print(f'{count_alt} sub-offsets at byte 6 (4 bytes each):')
    for i in range(min(count_alt, 20)):
        pos = off0 + 6 + i * 4
        offset_val = struct.unpack('<I', data[pos:pos+4])[0]
        print(f'  sub[{i}] at byte {6+i*4}: {offset_val}')
