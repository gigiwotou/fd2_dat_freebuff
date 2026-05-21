import struct

with open('game/FDTXT.DAT', 'rb') as f:
    fdtxt = f.read()

# Resource set 0
rs = struct.unpack_from('<I', fdtxt, 10)[0]
re = struct.unpack_from('<I', fdtxt, 14)[0]
rd = fdtxt[rs:re]

# Sub-item 0
off = struct.unpack_from('<h', rd, 2)[0]
next_off = struct.unpack_from('<h', rd, 4)[0]
text_data = rd[off:next_off]

print(f'Sub-item 0: offset={off}-{next_off}, length={next_off - off}')
print()

# Correct parsing: TEXT_DELAY parameter is 1 byte (uint8_t), not 2 bytes (int16_t)
print('Correct parsing (TEXT_DELAY param = 1 byte):')
i = 0
while i + 2 <= len(text_data):
    word = struct.unpack_from('<h', text_data, i)[0]
    
    if word == -1:  # TEXT_END
        print(f'  [{i:3d}] TEXT_END')
        break
    elif word == -2:  # TEXT_DELAY
        if i + 3 <= len(text_data):
            delay = struct.unpack_from('<B', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_DELAY, delay={delay}')
            i += 3  # 2 bytes code + 1 byte param
        else:
            print(f'  [{i:3d}] TEXT_DELAY (incomplete)')
            i += 2
    elif word == -19:  # TEXT_CHAR_F
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_CHAR_F, char_db_index={param}')
            i += 4
        else:
            i += 2
    elif 0 <= word <= 65535:
        # Try Big5 encoding
        try:
            char = text_data[i:i+2].decode('big5')
            print(f'  [{i:3d}] char "{char}" (0x{text_data[i:i+2].hex()})')
        except:
            print(f'  [{i:3d}] 0x{text_data[i:i+2].hex()}')
        i += 2
    else:
        print(f'  [{i:3d}] UNKNOWN: {word}')
        i += 2
