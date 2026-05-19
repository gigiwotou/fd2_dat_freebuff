import json

with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    font_data = json.load(f)

font = font_data['font']
print('编码表总长度:', len(font))
print()

groups = [
    (0, 10, '数字0-9'),
    (10, 36, '字母A-Z'),
    (36, 93, '角色名字'),
    (93, 142, '职业/种族相关'),
    (142, 200, '职业名称'),
    (200, 300, '道具相关'),
]

for start, end, desc in groups:
    chars = font[start:end]
    char_str = ''.join(chars[:30])
    print('%4d-%4d (%-20s): %s...' % (start, end, desc, char_str))
    print()
