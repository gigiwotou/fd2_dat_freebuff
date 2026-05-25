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
count = struct.unpack_from('<I', data, 6)[0]

# 读取偏移表
offsets = []
for i in range(count):
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 分析资源1
res_idx = 1
start = offsets[res_idx]
end = offsets[res_idx + 1] if (res_idx + 1 < len(offsets)) else file_size
res = data[start:end]

print('=' * 80)
print('资源 %d 分析 (偏移: 0x%08X - 0x%08X)' % (res_idx, start, end))
print('=' * 80)

# 子项数量
sub_count = struct.unpack_from('<h', res, 0)[0]
print('子项数量: %d' % sub_count)

# 子项偏移
sub_offs = []
for i in range(sub_count):
    off = struct.unpack_from('<h', res, 2 + i * 2)[0]
    sub_offs.append(off)
    print('  子项%d: 偏移=%d (0x%04X)' % (i, off, off))

print()
print('-' * 80)

# 分析每个子项的前几个控制码
for i in range(sub_count):
    sub_start = sub_offs[i]
    if i + 1 < sub_count:
        sub_end = sub_offs[i + 1]
    else:
        sub_end = len(res)
    
    sub_data = res[sub_start:sub_end]
    
    print('\n子项 %d (大小: %d 字节):' % (i, len(sub_data)))
    
    # 解析前20个WORD
    j = 0
    words = []
    while j + 2 <= len(sub_data) and j < 100:
        word = struct.unpack_from('<h', sub_data, j)[0]
        j += 2
        words.append(word)
        
        if word == -1:  # TEXT_END
            print('  [%d] TEXT_END' % (j // 2 - 1))
            break
        elif word == -2:
            print('  [%d] TEXT_NEWLINE' % (j // 2 - 1))
        elif word == -3:
            print('  [%d] TEXT_NEWLINE2' % (j // 2 - 1))
        elif word == -4:
            print('  [%d] TEXT_RECURSE1' % (j // 2 - 1))
        elif word == -5:
            print('  [%d] TEXT_RECURSE2' % (j // 2 - 1))
        elif word == -6:
            print('  [%d] TEXT_SHOW_NUM (需要额外参数)' % (j // 2 - 1))
        elif word == -17:
            pid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('  [%d] TEXT_PORTRAIT_F, 参数=%d' % (j // 2 - 2, pid))
        elif word == -18:
            pid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('  [%d] TEXT_PORTRAIT_S, 参数=%d' % (j // 2 - 2, pid))
        elif word == -19:
            cid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('  [%d] TEXT_CHAR_F, 参数=%d' % (j // 2 - 2, cid))
        elif word == -20:
            cid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('  [%d] TEXT_CHAR_S, 参数=%d' % (j // 2 - 2, cid))
        elif word >= 0:
            if word < len(font):
                print('  [%d] 字符="%s" (索引=%d)' % (j // 2 - 1, font[word], word))
            else:
                print('  [%d] 字符=? (索引=%d, 超出编码表)' % (j // 2 - 1, word))
