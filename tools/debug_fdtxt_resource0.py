import struct

with open('game/FDTXT.DAT', 'rb') as f:
    fdtxt = f.read()

fdtxt_count = struct.unpack_from('<I', fdtxt, 6)[0]

# 分析资源集0的前5个子项
print('=== 资源集0 分析 ===')
rs = struct.unpack_from('<I', fdtxt, 10)[0]
re = struct.unpack_from('<I', fdtxt, 14)[0]
rd = fdtxt[rs:re]

sub_count = struct.unpack_from('<h', rd, 0)[0]
print(f'子项数量: {sub_count}')

for sub_idx in range(min(sub_count, 5)):
    off = struct.unpack_from('<h', rd, 2 + sub_idx * 2)[0]
    next_off = struct.unpack_from('<h', rd, 2 + (sub_idx + 1) * 2)[0] if sub_idx + 1 < sub_count else len(rd)
    
    text_data = rd[off:next_off]
    
    print(f'\n--- 子项{sub_idx} ---')
    print(f'偏移: {off}-{next_off}, 长度: {next_off - off}')
    
    # 解析所有控制码和文字
    i = 0
    text_chars = []
    while i + 2 <= len(text_data):
        word = struct.unpack_from('<h', text_data, i)[0]
        if word == -1:
            print(f'  [{i}] TEXT_END (-1)')
            break
        elif word == -2:
            param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
            print(f'  [{i}] TEXT_DELAY (-2), param={param}')
            i += 4
        elif word == -3:
            print(f'  [{i}] TEXT_PAGE (-3)')
            i += 2
        elif word == -4:
            print(f'  [{i}] TEXT_NEWLINE (-4)')
            i += 2
        elif word == -17:
            param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
            print(f'  [{i}] TEXT_PORTRAIT_F (-17), dato_idx={param}')
            i += 4
        elif word == -18:
            param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
            print(f'  [{i}] TEXT_PORTRAIT_S (-18), dato_idx={param}')
            i += 4
        elif word == -19:
            param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
            print(f'  [{i}] TEXT_CHAR_F (-19), char_db_index={param}')
            i += 4
        elif word == -20:
            param = struct.unpack_from('<h', text_data, i + 2)[0] if i + 4 <= len(text_data) else 0
            print(f'  [{i}] TEXT_CHAR_S (-20), char_db_index={param}')
            i += 4
        elif 0 <= word < 0x10000:
            text_chars.append(chr(word))
            i += 2
        else:
            print(f'  [{i}] UNKNOWN: {word}')
            i += 2
    
    if text_chars:
        text = ''.join(text_chars)
        print(f'  文本: {text}')
