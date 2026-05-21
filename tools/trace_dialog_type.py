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

# Parse with 2-byte TEXT_DELAY parameter
print('Parsing (TEXT_DELAY param = 2 bytes):')
i = 0
dialog_type = 'F'  # Initial value
char_count = 0
while i + 2 <= len(text_data):
    word = struct.unpack_from('<h', text_data, i)[0]
    
    if word == -1:  # TEXT_END
        print(f'  [{i:3d}] TEXT_END')
        break
    elif word == -2:  # TEXT_DELAY
        delay = struct.unpack_from('<h', text_data, i+2)[0]
        print(f'  [{i:3d}] TEXT_DELAY, delay={delay}')
        i += 4
    elif word == -19:  # TEXT_CHAR_F
        param = struct.unpack_from('<h', text_data, i+2)[0]
        print(f'  [{i:3d}] TEXT_CHAR_F, char_db_index={param} -> sets dialog to F')
        dialog_type = 'F'
        i += 4
    elif word == -20:  # TEXT_CHAR_S
        param = struct.unpack_from('<h', text_data, i+2)[0]
        print(f'  [{i:3d}] TEXT_CHAR_S, char_db_index={param} -> sets dialog to S')
        dialog_type = 'S'
        i += 4
    elif word == -17:  # TEXT_PORTRAIT_F
        param = struct.unpack_from('<h', text_data, i+2)[0]
        print(f'  [{i:3d}] TEXT_PORTRAIT_F, dato_idx={param} -> sets dialog to F')
        dialog_type = 'F'
        i += 4
    elif word == -18:  # TEXT_PORTRAIT_S
        param = struct.unpack_from('<h', text_data, i+2)[0]
        print(f'  [{i:3d}] TEXT_PORTRAIT_S, dato_idx={param} -> sets dialog to S')
        dialog_type = 'S'
        i += 4
    elif 0 <= word <= 65535:
        try:
            char = text_data[i:i+2].decode('big5')
            if char_count < 3:
                print(f'  [{i:3d}] char "{char}" (dialog={dialog_type})')
            char_count += 1
        except:
            pass
        i += 2
    else:
        i += 2

print(f'\nTotal characters: {char_count}')
print(f'Final dialog type: {dialog_type}')
