import struct
import json
import sys
import io

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

# 实际有效的资源数量（偏移小于文件大小的）
actual_count = 0
for i, offset in enumerate(offsets):
    if offset < file_size:
        actual_count = i + 1
    else:
        break

print('FDTXT.DAT 资源数量:', actual_count)
print('编码表字符数:', len(font))
print()

with open('output/fdtxt_final_decode.txt', 'w', encoding='utf-8') as out:
    for i in range(actual_count):
        start = offsets[i]
        end = offsets[i+1] if (i+1 < len(offsets) and offsets[i+1] < file_size) else file_size
        res = data[start:end]
        
        text = []
        unk_indexes = []
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
                    text.append('?')
                    if word not in unk_indexes:
                        unk_indexes.append(word)
        
        decoded_text = ''.join(text)
        
        print('索引 %2d: 大小=%d 字节, UNK索引=%d个' % (i, len(res), len(unk_indexes)))
        out.write('=== 索引 %d ===\n' % i)
        out.write('大小: %d 字节\n' % len(res))
        if unk_indexes:
            out.write('UNK索引: %s\n' % str(unk_indexes))
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')

print()
print('解码完成，已保存到 output/fdtxt_final_decode.txt')
