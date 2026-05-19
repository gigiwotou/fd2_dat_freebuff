#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FDTXT.DAT 文本索引扫描工具
扫描所有文本索引，找出职业名、道具名、法术名等的索引范围
"""

import struct
import os
import json
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_font_encoding(encoding_path):
    """加载字体编码表"""
    with open(encoding_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('font', [])

def read_dat(filepath):
    """读取DAT文件，返回数据和偏移表"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    if data[:6] != b'LLLLLL':
        raise ValueError("不是有效的DAT文件")
    
    offset_count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(offset_count):
        offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(offset)
    
    return data, offsets

def get_resource(data, offsets, index):
    """获取指定索引的资源"""
    if index < 0 or index >= len(offsets) - 1:
        return b''
    start = offsets[index]
    end = offsets[index + 1]
    return data[start:end]

def decode_text(data, offsets, index, font_encoding):
    """解码指定索引的文本"""
    res = get_resource(data, offsets, index)
    if not res:
        return None
    
    text = []
    i = 0
    while i + 2 <= len(res):
        word = struct.unpack_from('<h', res, i)[0]
        i += 2
        
        if word == -1:
            break
        elif word == -2 or word == -3:
            text.append('\n')
        elif word < 0:
            continue
        else:
            if word < len(font_encoding):
                text.append(font_encoding[word])
            else:
                text.append(f'[未知{word}]')
    
    return ''.join(text).strip()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='FDTXT.DAT文本索引扫描工具')
    parser.add_argument('fdtxt_path', help='FDTXT.DAT文件路径')
    parser.add_argument('--start', type=int, default=0, help='起始索引')
    parser.add_argument('--end', type=int, default=500, help='结束索引')
    parser.add_argument('--filter', type=str, default=None, help='过滤包含指定字符的文本')
    parser.add_argument('--export', '-e', type=str, default=None, help='导出到文件')
    parser.add_argument('--encoding', type=str, 
                        default='tools/font/encoding_cn.json', 
                        help='字符编码表路径')
    args = parser.parse_args()
    
    if not os.path.exists(args.fdtxt_path):
        print(f"错误：找不到 {args.fdtxt_path}")
        return
    
    if not os.path.exists(args.encoding):
        print(f"错误：找不到编码表 {args.encoding}")
        return
    
    font_encoding = load_font_encoding(args.encoding)
    print(f"编码表字符数: {len(font_encoding)}")
    
    data, offsets = read_dat(args.fdtxt_path)
    print(f"FDTXT.DAT 索引总数: {len(offsets) - 1}")
    print(f"扫描范围: {args.start} ~ {args.end}")
    print("-" * 80)
    
    results = []
    for i in range(args.start, min(args.end + 1, len(offsets) - 1)):
        text = decode_text(data, offsets, i, font_encoding)
        if text:
            if len(text) < 2:
                continue
            
            if args.filter and args.filter not in text:
                continue
            
            results.append((i, text))
    
    output_lines = []
    for idx, text in results:
        line = f"索引 {idx:4d}: {text[:100]}"
        print(line)
        output_lines.append(line)
    
    print(f"\n共找到 {len(results)} 条匹配的文本")
    
    if args.export:
        with open(args.export, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"已导出到: {args.export}")

if __name__ == '__main__':
    main()