import struct

with open('game/FDTXT.DAT', 'rb') as f:
    fdtxt = f.read()

# 资源集0
rs = struct.unpack_from('<I', fdtxt, 10)[0]
re = struct.unpack_from('<I', fdtxt, 14)[0]
rd = fdtxt[rs:re]

sub_count = struct.unpack_from('<h', rd, 0)[0]

# 子项0
off = struct.unpack_from('<h', rd, 2)[0]
next_off = struct.unpack_from('<h', rd, 4)[0]
text_data = rd[off:next_off]

print(f'子项0: 偏移={off}-{next_off}, 长度={next_off - off}')
print(f'原始数据 (hex): {text_data[:150].hex()}')
print()

# 逐个字节分析
print('详细分析:')
i = 0
while i + 2 <= len(text_data):
    word = struct.unpack_from('<h', text_data, i)[0]
    word_hex = text_data[i:i+2].hex()
    
    if word == -1:
        print(f'  [{i:3d}] {word_hex} = {word:6d} : TEXT_END')
        break
    elif word == -2:
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            param_hex = text_data[i+2:i+4].hex()
            print(f'  [{i:3d}] {word_hex} {param_hex} = {word:6d},{param:6d} : TEXT_DELAY, delay={param}')
        else:
            print(f'  [{i:3d}] {word_hex} = {word:6d} : TEXT_DELAY (incomplete)')
        i += 4
    elif word == -19:
        if i + 4 <= len(text_data):
            param = struct.unpack_from('<h', text_data, i+2)[0]
            param_hex = text_data[i+2:i+4].hex()
            print(f'  [{i:3d}] {word_hex} {param_hex} = {word:6d},{param:6d} : TEXT_CHAR_F, char_db_index={param}')
        i += 4
    elif 0 <= word < 1000:
        # 可能是中文字符
        try:
            char = text_data[i:i+2].decode('big5')
            print(f'  [{i:3d}] {word_hex} = {word:6d} : 字符 "{char}" (Big5)')
        except:
            print(f'  [{i:3d}] {word_hex} = {word:6d} : 未知字符')
        i += 2
    else:
        print(f'  [{i:3d}] {word_hex} = {word:6d} : 未知')
        i += 2
