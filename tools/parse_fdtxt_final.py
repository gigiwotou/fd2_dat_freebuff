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

# 读取偏移表
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 找出有效资源数量
valid_count = 0
for i, off in enumerate(offsets):
    if off < file_size:
        valid_count = i + 1
    else:
        break

print('=' * 80)
print('FDTXT.DAT 解析结果')
print('=' * 80)
print('文件大小: %d 字节' % file_size)
print('魔数: %s' % magic)
print('偏移表数量: %d' % count)
print('有效资源数量: %d' % valid_count)
print('编码表字符数: %d' % len(font))
print()

# 解析所有资源
total_known = 0
total_unk = 0
total_cmd = 0
unk_index_set = set()

with open('output/fdtxt_parse_result.txt', 'w', encoding='utf-8') as out:
    out.write('=' * 80 + '\n')
    out.write('FDTXT.DAT 解析结果\n')
    out.write('=' * 80 + '\n')
    out.write('文件大小: %d 字节\n' % file_size)
    out.write('有效资源数量: %d\n' % valid_count)
    out.write('编码表字符数: %d\n' % len(font))
    out.write('\n')
    
    for i in range(valid_count):
        start = offsets[i]
        end = offsets[i+1] if (i+1 < len(offsets) and offsets[i+1] < file_size) else file_size
        res = data[start:end]
        
        text = []
        unk_count = 0
        known_count = 0
        cmd_count = 0
        j = 0
        
        while j + 2 <= len(res):
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
                    text.append('?')
                    unk_count += 1
                    unk_index_set.add(word)
        
        decoded_text = ''.join(text)
        total_known += known_count
        total_unk += unk_count
        total_cmd += cmd_count
        
        # 输出到文件
        out.write('=' * 80 + '\n')
        out.write('=== 资源索引 %d ===\n' % i)
        out.write('=' * 80 + '\n')
        out.write('文件大小: %d 字节\n' % len(res))
        out.write('偏移: 0x%08X - 0x%08X\n' % (start, end))
        out.write('字符统计: 已知=%d, UNK=%d, 控制码=%d\n' % (known_count, unk_count, cmd_count))
        out.write('\n')
        out.write('内容:\n')
        out.write(decoded_text)
        out.write('\n\n')
        
        # 控制台输出摘要
        print('资源 %2d: 大小=%d 字节, 已知=%d, UNK=%d, CMD=%d' % (i, len(res), known_count, unk_count, cmd_count))
    
    # 输出UNK索引统计
    out.write('\n' + '=' * 80 + '\n')
    out.write('UNK索引统计（超出编码表范围的索引）\n')
    out.write('=' * 80 + '\n')
    out.write('UNK索引总数: %d\n' % len(unk_index_set))
    out.write('UNK索引列表: %s\n' % sorted(list(unk_index_set)))
    out.write('\n')
    out.write('总体统计:\n')
    out.write('  已知字符总数: %d\n' % total_known)
    out.write('  UNK字符总数: %d\n' % total_unk)
    out.write('  控制码总数: %d\n' % total_cmd)

print()
print('=' * 80)
print('总体统计')
print('=' * 80)
print('已知字符总数: %d' % total_known)
print('UNK字符总数: %d' % total_unk)
print('控制码总数: %d' % total_cmd)
print('不同UNK索引数: %d' % len(unk_index_set))
print()
print('解析结果已保存到: output/fdtxt_parse_result.txt')
