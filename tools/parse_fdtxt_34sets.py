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

# 解析头部
magic = data[:6]
count = struct.unpack_from('<I', data, 6)[0]

print('=' * 80)
print('FDTXT.DAT 解析')
print('=' * 80)
print('文件大小: %d 字节' % file_size)
print('魔数: %s' % magic)
print('偏移表数量: %d' % count)

# 读取偏移表（每项4字节）
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 前34个偏移是有效的资源集偏移
# 第33个偏移（索引33）= 120502 = 文件大小（结束标记）
resource_set_count = 34

print('资源集数量: %d' % resource_set_count)
print()

# 解析每个资源集
with open('output/fdtxt_34_sets.txt', 'w', encoding='utf-8') as out:
    out.write('=' * 80 + '\n')
    out.write('FDTXT.DAT 34个资源集解析\n')
    out.write('=' * 80 + '\n\n')
    
    for i in range(resource_set_count):
        if i < len(offsets) - 1:
            start = offsets[i]
            end = offsets[i + 1] if (i + 1 < len(offsets) and offsets[i + 1] < file_size) else file_size
        else:
            start = offsets[i] if i < len(offsets) else 0
            end = file_size
        
        if start >= file_size:
            continue
        
        size = end - start
        res = data[start:end]
        
        out.write('=' * 80 + '\n')
        out.write('=== 资源集 %d ===\n' % i)
        out.write('=' * 80 + '\n')
        out.write('偏移: 0x%08X - 0x%08X\n' % (start, end))
        out.write('大小: %d 字节\n' % size)
        out.write('\n')
        
        # 解析资源集内的文本（WORD数组）
        text = []
        j = 0
        word_count = 0
        unk_count = 0
        
        while j + 2 <= len(res):
            word = struct.unpack_from('<h', res, j)[0]
            j += 2
            word_count += 1
            
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
                    unk_count += 1
        
        decoded_text = ''.join(text)
        
        out.write('WORD数量: %d\n' % word_count)
        out.write('UNK字符: %d\n' % unk_count)
        out.write('\n')
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')
        
        print('资源集 %2d: 大小=%d 字节, WORD=%d, UNK=%d' % (i, size, word_count, unk_count))

print()
print('解析结果已保存到: output/fdtxt_34_sets.txt')
