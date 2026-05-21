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

# Parse all control codes
i = 0
dialog_type = 'NONE'
while i + 2 <= len(text_data):
    word = struct.unpack_from('<h', text_data, i)[0]
    
    if word == -1:  # TEXT_END
        print(f'  [{i:3d}] TEXT_END')
        break
    elif word == -2:  # TEXT_DELAY
        if i + 3 <= len(text_data):
            delay = text_data[i+2]
            print(f'  [{i:3d}] TEXT_DELAY, delay={delay}')
            i += 3
        else:
            i += 2
    elif word == -19:  # TEXT_CHAR_F
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_CHAR_F -> dialog=F, char_db_index={param}')
            dialog_type = 'F'
            i += 4
        else:
            i += 2
    elif word == -20:  # TEXT_CHAR_S
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_CHAR_S -> dialog=S, char_db_index={param}')
            dialog_type = 'S'
            i += 4
        else:
            i += 2
    elif word == -17:  # TEXT_PORTRAIT_F
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_PORTRAIT_F -> dialog=F, dato_idx={param}')
            dialog_type = 'F'
            i += 4
        else:
            i += 2
    elif word == -18:  # TEXT_PORTRAIT_S
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            print(f'  [{i:3d}] TEXT_PORTRAIT_S -> dialog=S, dato_idx={param}')
            dialog_type = 'S'
            i += 4
        else:
            i += 2
    elif word == -3:  # TEXT_PAGE
        print(f'  [{i:3d}] TEXT_PAGE -> dialog=NONE')
        dialog_type = 'NONE'
        i += 2
    elif word == -4:  # TEXT_NEWLINE
        print(f'  [{i:3d}] TEXT_NEWLINE')
        i += 2
    elif word == -5:  # TEXT_NEWLINE2
        print(f'  [{i:3d}] TEXT_NEWLINE2')
        i += 2
    elif 0 <= word <= 65535:
        try:
            char = text_data[i:i+2].decode('big5')
            print(f'  [{i:3d}] char "{char}" (dialog={dialog_type})')
        except:
            pass
        i += 2
    else:
        i += 2
