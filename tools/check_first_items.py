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
    off = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(off)

# 只分析资源1的前3个子项
res_idx = 1
start = offsets[res_idx]
end = offsets[res_idx + 1]
res = data[start:end]

sub_count = struct.unpack_from('<h', res, 0)[0]
print('资源1 子项数量: %d' % sub_count)

for i in range(min(3, sub_count)):
    sub_start = struct.unpack_from('<h', res, 2 + i * 2)[0]
    sub_end = struct.unpack_from('<h', res, 2 + (i + 1) * 2)[0] if (i + 1 < sub_count) else len(res)
    
    sub_data = res[sub_start:sub_end]
    
    print('\n' + '=' * 80)
    print('子项 %d (偏移: %d-%d, 大小: %d 字节)' % (i, sub_start, sub_end, len(sub_data)))
    print('=' * 80)
    
    # 解析前15个WORD
    j = 0
    while j + 2 <= len(sub_data) and j < 60:
        word = struct.unpack_from('<h', sub_data, j)[0]
        j += 2
        
        if word == -1:
            print('[%d] TEXT_END (-1)' % (j // 2 - 1))
            break
        elif word == -2:
            print('[%d] TEXT_NEWLINE (-2)' % (j // 2 - 1))
        elif word == -3:
            print('[%d] TEXT_NEWLINE2 (-3)' % (j // 2 - 1))
        elif word == -4:
            print('[%d] TEXT_RECURSE1 (-4)' % (j // 2 - 1))
        elif word == -5:
            print('[%d] TEXT_RECURSE2 (-5)' % (j // 2 - 1))
        elif word == -6:
            print('[%d] TEXT_SHOW_NUM (-6)' % (j // 2 - 1))
        elif word == -17:
            pid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('[%d] TEXT_PORTRAIT_F (-17), pid=%d' % (j // 2 - 2, pid))
        elif word == -18:
            pid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('[%d] TEXT_PORTRAIT_S (-18), pid=%d' % (j // 2 - 2, pid))
        elif word == -19:
            cid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('[%d] TEXT_CHAR_F (-19), cid=%d' % (j // 2 - 2, cid))
        elif word == -20:
            cid = struct.unpack_from('<h', sub_data, j)[0]
            j += 2
            print('[%d] TEXT_CHAR_S (-20), cid=%d' % (j // 2 - 2, cid))
        elif word >= 0:
            ch = font[word] if word < len(font) else '?'
            print('[%d] 字符="%s" (word=%d)' % (j // 2 - 1, ch, word))
