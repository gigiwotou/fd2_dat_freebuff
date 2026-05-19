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

print('FDTXT.DAT 实际资源数量:', actual_count)
print('编码表字符数:', len(font))
print()

# 解码所有文本
with open('output/fdtxt_correct_final.txt', 'w', encoding='utf-8') as out:
    for i in range(actual_count):
        start = offsets[i]
        end = offsets[i+1] if (i+1 < len(offsets) and offsets[i+1] < file_size) else file_size
        res = data[start:end]
        
        # 第一个WORD是字符数量
        if len(res) < 2:
            continue
        
        char_count = struct.unpack_from('<H', res, 0)[0]
        
        text = []
        unk_count = 0
        known_count = 0
        cmd_count = 0
        j = 2  # 跳过第一个WORD
        
        while j < len(res):
            word = struct.unpack_from('<h', res, j)[0]
            j += 2
            
            if word == -1:  # 文本结束
                break
            elif word == -2 or word == -3:  # 换行
                text.append('\n')
            elif word < 0:  # 控制码
                text.append('[CMD%d]' % word)
                cmd_count += 1
            else:  # 字符索引
                if word < len(font):
                    text.append(font[word])
                    known_count += 1
                else:
                    text.append('[UNK%d]' % word)
                    unk_count += 1
        
        decoded_text = ''.join(text)
        
        print('索引 %2d: 声明字符数=%d, 已知=%d, UNK=%d, CMD=%d' % (i, char_count, known_count, unk_count, cmd_count))
        out.write('=== 索引 %d ===\n' % i)
        out.write('大小: %d 字节\n' % len(res))
        out.write('声明字符数: %d\n' % char_count)
        out.write('实际解析: 已知=%d, UNK=%d, CMD=%d\n' % (known_count, unk_count, cmd_count))
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')

print()
print('解码完成，已保存到 output/fdtxt_correct_final.txt')
print('总UNK索引值（需要补充到编码表）:')
