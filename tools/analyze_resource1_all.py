#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FDTXT.DAT 资源1 完整控制码分析工具
分析资源1的所有子项，找出每个子项中所有控制码（负数）的位置和序列
特别关注：TEXT_END(-1), TEXT_NEWLINE2(-3), 以及其他未定义控制码
"""

import struct
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FDTXT_PATH = 'game/FDTXT.DAT'
OUTPUT_DIR = 'output'

# 已知控制码定义
KNOWN_CONTROL_CODES = {
    -1: 'TEXT_END',
    -2: 'TEXT_NEWLINE',
    -3: 'TEXT_NEWLINE2',
    -4: 'TEXT_RECURSE_1',
    -5: 'TEXT_RECURSE_2',
    -6: 'TEXT_SHOW_NUMBER',
    -7: 'TEXT_CMD_7',
    -8: 'TEXT_CMD_8',
    -9: 'TEXT_CMD_9',
    -10: 'TEXT_CMD_10',
    -11: 'TEXT_CMD_11',
    -12: 'TEXT_CMD_12',
    -13: 'TEXT_CMD_13',
    -14: 'TEXT_CMD_14',
    -15: 'TEXT_CMD_15',
    -16: 'TEXT_CMD_16',
    -17: 'TEXT_DATO_LOAD_1832',
    -18: 'TEXT_DATO_LOAD_36887',
    -19: 'TEXT_CHAR_F',
    -20: 'TEXT_CHAR_S',
}

# 带参数的控制码（后面跟着2字节参数）
PARAM_CODES = {-17, -18, -19, -20}

def parse_sub_item(sub_data, sub_idx):
    """解析单个子项的所有控制码"""
    control_codes = []  # [(位置索引, 控制码值, 控制码名, 参数值或None)]
    
    pos = 0
    word_idx = 0
    while pos + 2 <= len(sub_data):
        value = struct.unpack_from('<h', sub_data, pos)[0]
        pos += 2
        
        if value < 0:  # 控制码
            param = None
            if value in PARAM_CODES and pos + 2 <= len(sub_data):
                param = struct.unpack_from('<h', sub_data, pos)[0]
                pos += 2
            
            name = KNOWN_CONTROL_CODES.get(value, f'UNK_CODE_{value}')
            control_codes.append((word_idx, value, name, param))
        
        word_idx += 1
    
    return control_codes

def analyze_resource1():
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
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
    
    # 打开输出文件
    output_path = os.path.join(OUTPUT_DIR, 'fdtxt_resource1_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.write(f'FDTXT.DAT 资源1 完整控制码分析\n')
        out_file.write(f'文件大小: {len(data)} 字节\n')
        out_file.write(f'资源集数量: {count}\n')
        out_file.write(f'资源1大小: {res1_end - res1_start} 字节\n')
        out_file.write(f'子项数量: {sub_count}\n')
        out_file.write('=' * 100 + '\n\n')
        
        # 全局统计
        global_stats = {
            'total_subs': sub_count,
            'total_text_end': 0,
            'total_text_newline2': 0,
            'total_other_controls': {},
            'undefined_codes': set(),
        }
        
        # 分析所有子项
        for sub_idx in range(sub_count):
            sub_offset = struct.unpack_from('<h', res1_data, 2 + sub_idx * 2)[0]
            if sub_idx + 1 < sub_count:
                next_sub_offset = struct.unpack_from('<h', res1_data, 2 + (sub_idx + 1) * 2)[0]
            else:
                next_sub_offset = len(res1_data)
            
            sub_data = res1_data[sub_offset:next_sub_offset]
            
            # 解析控制码
            control_codes = parse_sub_item(sub_data, sub_idx)
            
            # 统计
            text_end_count = sum(1 for _, val, _, _ in control_codes if val == -1)
            text_newline2_count = sum(1 for _, val, _, _ in control_codes if val == -3)
            
            global_stats['total_text_end'] += text_end_count
            global_stats['total_text_newline2'] += text_newline2_count
            
            # 输出子项摘要
            line = f'子项{sub_idx}: 大小={len(sub_data)}字节, TEXT_END={text_end_count}, TEXT_NEWLINE2={text_newline2_count}, 总控制码={len(control_codes)}'
            print(line)
            out_file.write(line + '\n')
            
            # 输出完整控制码序列
            out_file.write(f'\n  完整控制码序列:\n')
            for word_idx, val, name, param in control_codes:
                if param is not None:
                    out_file.write(f'    [{word_idx:>4}] {val:>4} {name:<25} 参数={param}\n')
                else:
                    out_file.write(f'    [{word_idx:>4}] {val:>4} {name}\n')
                
                # 统计其他控制码
                if val not in (-1, -2, -3):
                    if val not in global_stats['total_other_controls']:
                        global_stats['total_other_controls'][val] = 0
                    global_stats['total_other_controls'][val] += 1
                
                # 记录未定义的控制码
                if val not in KNOWN_CONTROL_CODES:
                    global_stats['undefined_codes'].add(val)
            
            out_file.write('\n')
        
        # 输出全局统计
        out_file.write('\n' + '=' * 100 + '\n')
        out_file.write('全局统计\n')
        out_file.write('=' * 100 + '\n\n')
        
        out_file.write(f'子项总数: {sub_count}\n')
        out_file.write(f'TEXT_END(-1) 总出现次数: {global_stats["total_text_end"]}\n')
        out_file.write(f'TEXT_NEWLINE2(-3) 总出现次数: {global_stats["total_text_newline2"]}\n')
        out_file.write(f'\n')
        
        out_file.write('其他控制码统计:\n')
        for val, count in sorted(global_stats['total_other_controls'].items()):
            name = KNOWN_CONTROL_CODES.get(val, f'UNK_CODE_{val}')
            out_file.write(f'  {val:>4} {name:<25} 出现{count}次\n')
        
        out_file.write('\n')
        if global_stats['undefined_codes']:
            out_file.write('警告：发现未定义的控制码:\n')
            for val in sorted(global_stats['undefined_codes']):
                out_file.write(f'  {val} (0x{val & 0xFFFF:04X})\n')
        else:
            out_file.write('未发现未定义的控制码\n')
    
    print(f'\n详细分析结果已保存到: {output_path}')
    
    # 打印全局统计到控制台
    print(f'\n{"=" * 60}')
    print(f'全局统计')
    print(f'{"=" * 60}')
    print(f'子项总数: {sub_count}')
    print(f'TEXT_END(-1) 总出现次数: {global_stats["total_text_end"]}')
    print(f'TEXT_NEWLINE2(-3) 总出现次数: {global_stats["total_text_newline2"]}')
    print(f'\n其他控制码统计:')
    for val, count in sorted(global_stats['total_other_controls'].items()):
        name = KNOWN_CONTROL_CODES.get(val, f'UNK_CODE_{val}')
        print(f'  {val:>4} {name:<25} 出现{count}次')
    
    if global_stats['undefined_codes']:
        print(f'\n警告：发现未定义的控制码:')
        for val in sorted(global_stats['undefined_codes']):
            print(f'  {val} (0x{val & 0xFFFF:04X})')

if __name__ == '__main__':
    analyze_resource1()
