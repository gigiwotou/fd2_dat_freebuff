import struct

with open('game/DATO.DAT', 'rb') as f:
    data = f.read()

# Check resource 0 internal structure
off0 = struct.unpack('<I', data[10:14])[0]
print(f'Resource 0 starts at: {hex(off0)}')

# Check if it has sub-structure
first_word = struct.unpack('<H', data[off0:off0+2])[0]
print(f'First WORD: {first_word} (0x{first_word:04X})')

# Maybe it's: [something: 4 bytes] [sub-count: 2 bytes] [sub-offsets: 4 bytes each?]
# Let's check the structure starting from byte 4
sub_count = struct.unpack('<H', data[off0+4:off0+6])[0]
print(f'WORD at byte 4: {sub_count}')

# If sub_count is valid, check sub-offset table
if sub_count > 0 and sub_count < 1000:
    print(f'Checking sub-offsets at byte 6 (if each offset is 4 bytes):')
    for i in range(min(5, sub_count)):
        pos = off0 + 6 + i * 4
        offset_val = struct.unpack('<I', data[pos:pos+4])[0]
        print(f'  sub[{i}] at byte {6+i*4}: {offset_val}')

# Or maybe sub-offsets are 2 bytes?
if sub_count > 0 and sub_count < 1000:
    print(f'\nChecking sub-offsets at byte 6 (if each offset is 2 bytes):')
    for i in range(min(10, sub_count)):
        pos = off0 + 6 + i * 2
        offset_val = struct.unpack('<H', data[pos:pos+2])[0]
        print(f'  sub[{i}] at byte {6+i*2}: {offset_val}')

# Let's look at the raw bytes
print(f'\nFirst 100 bytes of resource 0:')
for i in range(0, min(100, 12665), 4):
    val = struct.unpack('<I', data[off0+i:off0+i+4])[0]
    print(f'  [{i}] {val} (0x{val:08X})')
