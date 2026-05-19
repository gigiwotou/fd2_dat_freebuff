import json

with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    font_data = json.load(f)
font = font_data['font']

print('编码表总字符数:', len(font))
print()

# 编码表是按行组织的
# 查看编码表文件
with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析JSON
import re

# 找到font数组的所有行
lines = content.split('\n')
print('编码表文件行数:', len(lines))
print()

# 统计每行有多少个字符
char_counts = []
for i, line in enumerate(lines):
    # 数引号内的字符
    chars_in_line = line.count('"') // 2  # 每对引号之间一个字符
    if chars_in_line > 0:
        char_counts.append((i, chars_in_line, line[:60]))

print('编码表有效行数:', len(char_counts))
print()

# 查看分组
for idx, (line_num, count, preview) in enumerate(char_counts[:40]):
    print('行%3d: %3d 个字符 - %s' % (line_num, count, preview[:60]))
