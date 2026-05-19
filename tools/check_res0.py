import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

# Read resource set 0 offset
res0 = struct.unpack('<I', data[10:14])[0]
print(f'Resource set 0 offset: {hex(res0)}')

# Read sub-count
sc = struct.unpack('<h', data[res0:res0+2])[0]
print(f'Sub count: {sc}')

# Read sub-offsets
offsets = []
for i in range(min(sc, 30)):
    off = struct.unpack('<h', data[res0+2+i*2:res0+4+i*2])[0]
    offsets.append(off)
    # Show first 2 bytes at each offset
    target = res0 + off
    if off >= 0 and target + 2 <= len(data):
        first_word = struct.unpack('<h', data[target:target+2])[0]
        print(f'  sub[{i}] offset={off}, first_word={first_word}')
    else:
        print(f'  sub[{i}] offset={off} (invalid)')

print(f'\nTotal sub-offsets: {len(offsets)}')
print(f'Offsets: {offsets}')
