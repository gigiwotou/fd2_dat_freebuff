import struct

with open('game/FDTXT.DAT', 'rb') as f:
    fdtxt = f.read()

# Resource set 0, sub-item 0
rs = struct.unpack_from('<I', fdtxt, 10)[0]
re = struct.unpack_from('<I', fdtxt, 14)[0]
rd = fdtxt[rs:re]

off = struct.unpack_from('<h', rd, 2)[0]
next_off = struct.unpack_from('<h', rd, 4)[0]
text_data = rd[off:next_off]

# First 50 bytes
print('Sub-item 0 first 100 bytes:')
for i in range(0, min(50, len(text_data)), 2):
    word = struct.unpack_from('<h', text_data, i)[0]
    raw = text_data[i:i+2].hex()
    print(f'  [{i:3d}] {raw} = {word:6d}', end='')
    if word == -1: print(' TEXT_END')
    elif word == -2: print(' TEXT_NEWLINE/DELAY')
    elif word == -17: print(' TEXT_PORTRAIT_F')
    elif word == -18: print(' TEXT_PORTRAIT_S')
    elif word == -19: print(' TEXT_CHAR_F')
    elif word == -20: print(' TEXT_CHAR_S')
    elif 32 <= word < 128: print(f' ASCII: {chr(word)}')
    else: print()
