import struct
import json
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('game/FDTXT.DAT', 'rb') as f:
    data = f.read()

with open('tools/font/encoding_cn.json', 'r', encoding='utf-8') as f:
    font_data = json.load(f)
font = font_data['font']

file_size = len(data)
count = struct.unpack_from('<I', data, 6)[0]

offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 找出实际有效的资源数量
actual_count = 0
for i, offset in enumerate(offsets):
    if offset >= file_size:
        actual_count = i
        break
else:
    actual_count = len(offsets)

print('实际资源数量:', actual_count)

# 解码所有文本
with open('output/fdtxt_final.txt', 'w', encoding='utf-8') as out:
    for i in range(actual_count):
        start = offsets[i]
        end = offsets[i+1] if (i+1 < len(offsets) and offsets[i+1] < file_size) else file_size
        res = data[start:end]
        
        text = []
        unk_count = 0
        j = 0
        while j + 2 <= len(res):
            word = struct.unpack_from('<h', res, j)[0]
            j += 2
            
            if word == -1:
                break
            elif word == -2 or word == -3:
                text.append('\n')
            elif word < 0:
                text.append('[CMD%d]' % word)
            else:
                if word < len(font):
                    text.append(font[word])
                else:
                    text.append('[UNK%d]' % word)
                    unk_count += 1
        
        decoded_text = ''.join(text)
        
        print('索引 %2d: 大小=%d 字节, UNK字符数=%d' % (i, len(res), unk_count))
        out.write('=== 索引 %d ===\n' % i)
        out.write('大小: %d 字节\n' % len(res))
        out.write('UNK字符数: %d\n' % unk_count)
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')

print()
print('解码完成，已保存到 output/fdtxt_final.txt')
