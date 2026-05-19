import struct

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

file_size = len(data)
count = struct.unpack_from('<I', data, 6)[0]

print('FDTXT.DAT 文件大小:', file_size, '字节')
print('偏移表数量:', count)
print()

# 读取所有偏移
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 分析偏移值的模式
print('=== 分析偏移值模式 ===')
for i in range(min(40, count)):
    off = offsets[i]
    
    # 尝试解析为两个WORD
    if off > file_size:
        # 可能是两个WORD的组合
        word_low = off & 0xFFFF
        word_high = (off >> 16) & 0xFFFF
        print('偏移[%2d] = 0x%08X -> WORD_LOW=0x%04X (%d), WORD_HIGH=0x%04X (%d)' % (i, off, word_low, word_low, word_high, word_high))
    else:
        print('偏移[%2d] = 0x%08X (%d) - 有效偏移' % (i, off, off))

print()
print('=== 检查编码表的34个资源集对应关系 ===')

# 查看编码表
import json
with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    font_data = json.load(f)
font = font_data['font']

print('编码表总字符数:', len(font))
print()

# 检查编码表是否有34行的结构
with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 计算行数和每行字符数
lines = content.split('\n')
print('编码表文件行数:', len(lines))
print()

# 查看前几行
for i, line in enumerate(lines[:10]):
    # 计算这行的字符数
    chars = line.count('","') + 1
    if chars > 1 or i < 3:
        print('行%d: %d 个字符' % (i, chars))
