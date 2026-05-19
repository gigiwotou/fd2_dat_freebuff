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

# 读取偏移表（每项4字节）
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

print('=' * 80)
print('FDTXT.DAT 解析结果')
print('=' * 80)
print('文件大小: %d 字节' % file_size)
print('偏移表数量: %d' % count)
print('资源集数量: 34个（索引0-33）')
print()
print('索引0: 名字、技能、职业、法术等词组')
print('索引1-32: 游戏各关卡的文字资源')
print('索引33: 开场第一个过场动画关卡的文字资源')
print()

# 解析34个资源集
with open('output/fdtxt_34_resources.txt', 'w', encoding='utf-8') as out:
    out.write('=' * 80 + '\n')
    out.write('FDTXT.DAT 34个资源集解析\n')
    out.write('=' * 80 + '\n\n')
    out.write('索引0: 名字、技能、职业、法术等词组\n')
    out.write('索引1-32: 游戏各关卡的文字资源\n')
    out.write('索引33: 开场第一个过场动画关卡的文字资源\n\n')
    
    for i in range(34):
        if i >= len(offsets):
            break
            
        start = offsets[i]
        if start >= file_size:
            print('资源集 %2d: 偏移超出文件范围' % i)
            continue
        
        # 计算结束位置
        if i + 1 < len(offsets) and offsets[i + 1] < file_size:
            end = offsets[i + 1]
        else:
            end = file_size
        
        size = end - start
        res = data[start:end]
        
        # 解析文本（WORD数组）
        text = []
        j = 0
        word_count = 0
        unk_count = 0
        unk_indexes = []
        
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
                    if word not in unk_indexes:
                        unk_indexes.append(word)
        
        decoded_text = ''.join(text)
        
        # 输出到文件
        out.write('=' * 80 + '\n')
        out.write('=== 资源集 %d ===\n' % i)
        out.write('=' * 80 + '\n')
        out.write('偏移: 0x%08X - 0x%08X\n' % (start, end))
        out.write('大小: %d 字节\n' % size)
        out.write('WORD数量: %d\n' % word_count)
        out.write('UNK字符: %d\n' % unk_count)
        if unk_indexes:
            out.write('UNK索引列表: %s\n' % str(unk_indexes))
        out.write('\n')
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')
        
        # 控制台输出
        print('资源集 %2d: 大小=%6d 字节, WORD=%d, UNK=%d' % (i, size, word_count, unk_count))

print()
print('解析结果已保存到: output/fdtxt_34_resources.txt')
print()
print('UNK索引汇总（所有资源集）:')

# 统计所有UNK索引
all_unk = set()
for i in range(34):
    if i >= len(offsets):
        break
    start = offsets[i]
    if start >= file_size:
        continue
    if i + 1 < len(offsets) and offsets[i + 1] < file_size:
        end = offsets[i + 1]
    else:
        end = file_size
    res = data[start:end]
    
    j = 0
    while j + 2 <= len(res):
        word = struct.unpack_from('<h', res, j)[0]
        j += 2
        if word > 0 and word >= len(font):
            all_unk.add(word)

print('不同UNK索引总数: %d' % len(all_unk))
print('UNK索引列表: %s' % sorted(list(all_unk)))
