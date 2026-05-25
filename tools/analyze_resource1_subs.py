#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析FDTXT.DAT资源1的子项0-5
关注对话结束控制码模式
"""

import struct
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FDTXT_PATH = 'game/FDTXT.DAT'

CONTROL_CODES = {
    -1: 'TEXT_END - 文本结束',
    -2: 'TEXT_NEWLINE - 换行',
    -3: 'TEXT_NEWLINE2 - 换行+模式切换',
    -4: 'TEXT_RECURSE_1',
    -5: 'TEXT_RECURSE_2',
    -6: 'TEXT_SHOW_NUMBER',
    -17: 'TEXT_DATO_LOAD_1832',
    -18: 'TEXT_DATO_LOAD_36887',
    -19: 'TEXT_CHAR_F',
    -20: 'TEXT_CHAR_S',
}

def analyze_resource1():
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    # 解析文件头
    count = struct.unpack_from('<I', data, 6)[0]
    print(f'FDTXT.DAT 文件大小: {len(data)} 字节')
    print(f'资源集数量: {count}')
    print()
    
    # 读取偏移表
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    if len(offsets) < 2:
        print('错误: 资源集数量不足')
        return
    
    # 读取资源1
    res1_start = offsets[1]
    res1_end = offsets[2] if len(offsets) > 2 else len(data)
    res1_data = data[res1_start:res1_end]
    
    print(f'=== 资源1 ===')
    print(f'文件偏移: 0x{res1_start:06X} - 0x{res1_end:06X}')
    print(f'大小: {res1_end - res1_start} 字节')
    print()
    
    # 子项数量
    sub_count = struct.unpack_from('<h', res1_data, 0)[0]
    print(f'子项数量: {sub_count}')
    print()
    
    # 分析子项0-5
    for sub_idx in range(min(6, sub_count)):
        sub_offset = struct.unpack_from('<h', res1_data, 2 + sub_idx * 2)[0]
        if sub_idx + 1 < sub_count:
            next_sub_offset = struct.unpack_from('<h', res1_data, 2 + (sub_idx + 1) * 2)[0]
        else:
            next_sub_offset = len(res1_data)
        
        sub_data = res1_data[sub_offset:next_sub_offset]
        
        print(f'{"="*80}')
        print(f'=== 资源1/子项{sub_idx} ===')
        print(f'相对偏移: {sub_offset} - {next_sub_offset}')
        print(f'大小: {next_sub_offset - sub_offset} 字节')
        print(f'{"="*80}')
        print()
        
        # 解析所有int16值（前50个）
        print(f'前50个int16值:')
        print(f'{"索引":<6} {"十进制":<8} {"十六进制":<8} {"描述"}')
        print(f'{"-"*60}')
        
        pos = 0
        for i in range(min(50, len(sub_data) // 2)):
            if pos + 2 > len(sub_data):
                break
            
            value = struct.unpack_from('<h', sub_data, pos)[0]
            pos += 2
            
            hex_val = f'0x{value & 0xFFFF:04X}'
            
            if value in CONTROL_CODES:
                desc = CONTROL_CODES[value]
            elif value < 0:
                desc = f'未知控制码'
            else:
                desc = f'字符/文本'
            
            print(f'[{i:<4}] {value:>6} {hex_val:>8} {desc}')
        
        print()
        
        # 分析对话结束模式
        print(f'对话结束模式分析:')
        print(f'{"-"*60}')
        
        # 重新解析完整序列
        pos = 0
        sentence_count = 0
        sentences = []
        current_sentence = []
        
        while pos + 2 <= len(sub_data):
            value = struct.unpack_from('<h', sub_data, pos)[0]
            pos += 2
            
            if value == -1:  # TEXT_END
                current_sentence.append('TEXT_END')
                sentences.append(current_sentence)
                break
            elif value == -2:  # TEXT_NEWLINE
                current_sentence.append('TEXT_NEWLINE')
            elif value == -3:  # TEXT_NEWLINE2
                current_sentence.append('TEXT_NEWLINE2')
                sentences.append(current_sentence)
                current_sentence = []
                sentence_count += 1
            elif value in CONTROL_CODES:
                current_sentence.append(CONTROL_CODES[value].split(' - ')[0])
            elif value >= 0:
                current_sentence.append(f'字符')
        
        # 输出每个句子的结束模式
        for i, sentence in enumerate(sentences):
            # 找出最后3个元素
            ending = sentence[-3:] if len(sentence) >= 3 else sentence
            text_len = sum(1 for x in sentence if x == '字符')
            ending_desc = ' -> '.join(ending)
            print(f'  句子{i+1}: 文本长度={text_len} 结尾=[{ending_desc}]')
        
        print()
        
        # 统计TEXT_NEWLINE和TEXT_NEWLINE2
        newline_count = sum(1 for s in sentences for x in s if x == 'TEXT_NEWLINE')
        newline2_count = sum(1 for s in sentences for x in s if x == 'TEXT_NEWLINE2')
        end_count = sum(1 for s in sentences for x in s if x == 'TEXT_END')
        
        print(f'统计:')
        print(f'  句子总数: {len(sentences)}')
        print(f'  TEXT_NEWLINE (-2) 出现: {newline_count} 次')
        print(f'  TEXT_NEWLINE2 (-3) 出现: {newline2_count} 次')
        print(f'  TEXT_END (-1) 出现: {end_count} 次')
        print()

if __name__ == '__main__':
    analyze_resource1()
