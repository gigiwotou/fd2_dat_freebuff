#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FD2 资源名字解析工具
将 FDFIELD.DAT 中的编号与 FDTXT.DAT 中的文本名字对应起来

资源关联关系：
- FDFIELD.DAT: 角色数据（职业ID、道具ID等）
- FDTXT.DAT: 文本数据（角色名、道具名等）
- FDOTHER.DAT: 字体资源
- encoding_cn.json: 字符编码映射表
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
    """解析FDTXT.DAT中的文本，使用字体编码表"""
    res = get_resource(data, offsets, index)
    if not res:
        return None
    
    text = []
    i = 0
    while i + 2 <= len(res):
        word = struct.unpack_from('<h', res, i)[0]
        i += 2
        
        if word == -1:  # 结束
            break
        elif word == -2 or word == -3:  # 换行
            text.append('\n')
        elif word < 0:  # 其他控制码
            continue
        else:
            # 使用字体编码表解码字符
            if word < len(font_encoding):
                text.append(font_encoding[word])
            else:
                text.append(f'[未知字符{word}]')
    
    return ''.join(text).strip()

def parse_fdfield_char_info(data, offsets, map_id):
    """解析FDFIELD.DAT中的角色信息"""
    map_index_offset = 6 + map_id * 12
    control_off = struct.unpack_from('<I', data, map_index_offset + 4)[0]
    charpos_off = struct.unpack_from('<I', data, map_index_offset + 8)[0]
    
    chars = []
    char_info_offset = 131
    
    total_units = data[control_off + 2]
    
    for i in range(total_units):
        offset = control_off + char_info_offset + i * 26
        
        char = {
            'index': i,
            'faction': data[offset],
            'portrait_id': data[offset + 1],
            'race_id': data[offset + 2],
            'job_id': data[offset + 3],
            'level': data[offset + 4],
            'items': list(data[offset + 5:offset + 13]),
            'spells': list(data[offset + 13:offset + 17]),
            'spawn_turn': data[offset + 17],
            'drop_type': data[offset + 18],
            'drop_content': list(data[offset + 19:offset + 22]),
        }
        chars.append(char)
    
    total_chars = struct.unpack_from('<H', data, charpos_off)[0]
    positions = []
    for i in range(total_chars):
        pos_offset = charpos_off + 2 + i * 6
        x = struct.unpack_from('<H', data, pos_offset)[0]
        y = struct.unpack_from('<H', data, pos_offset + 2)[0]
        portrait = struct.unpack_from('<H', data, pos_offset + 4)[0]
        positions.append({'x': x, 'y': y, 'portrait_id': portrait})
    
    return chars, positions

def main():
    import argparse
    parser = argparse.ArgumentParser(description='FD2资源名字解析工具')
    parser.add_argument('game_dir', help='游戏数据目录（包含DAT文件）')
    parser.add_argument('--map', type=int, default=0, help='地图ID（默认0）')
    parser.add_argument('--export', '-e', type=str, default=None, help='导出到文件')
    parser.add_argument('--encoding', type=str, 
                        default='tools/font/encoding_cn.json', 
                        help='字符编码表路径')
    args = parser.parse_args()
    
    game_dir = args.game_dir
    map_id = args.map
    
    fdfield_path = os.path.join(game_dir, 'FDFIELD.DAT')
    fdtxt_path = os.path.join(game_dir, 'FDTXT.DAT')
    
    if not os.path.exists(fdfield_path):
        print(f"错误：找不到 {fdfield_path}")
        return
    
    if not os.path.exists(fdtxt_path):
        print(f"错误：找不到 {fdtxt_path}")
        return
    
    if not os.path.exists(args.encoding):
        print(f"错误：找不到编码表 {args.encoding}")
        return
    
    print(f"正在加载字符编码表...")
    font_encoding = load_font_encoding(args.encoding)
    print(f"编码表字符数: {len(font_encoding)}")
    
    print(f"\n正在解析 FDFIELD.DAT 和 FDTXT.DAT...")
    print(f"地图ID: {map_id}")
    print("-" * 80)
    
    fdfield_data, fdfield_offsets = read_dat(fdfield_path)
    chars, positions = parse_fdfield_char_info(fdfield_data, fdfield_offsets, map_id)
    
    fdtxt_data, fdtxt_offsets = read_dat(fdtxt_path)
    
    output_lines = []
    output_lines.append(f"=== 地图 {map_id} 角色数据 ===")
    output_lines.append(f"敌友单位总数: {len(chars)}")
    output_lines.append(f"总角色数(含己方): {len(positions)}")
    output_lines.append("")
    
    # 尝试找出职业名字的索引范围
    print("尝试识别职业名索引范围...")
    for test_idx in range(0, 100):
        text = decode_text(fdtxt_data, fdtxt_offsets, test_idx, font_encoding)
        if text and len(text) <= 4:
            print(f"索引{test_idx}: {text}")
    
    print("\n" + "=" * 80 + "\n")
    
    for i, pos in enumerate(positions):
        matched_char = None
        for char in chars:
            if char['portrait_id'] == pos['portrait_id']:
                matched_char = char
                break
        
        output_lines.append(f"--- 角色 {i} ---")
        output_lines.append(f"位置: ({pos['x']}, {pos['y']})")
        output_lines.append(f"肖像ID: {pos['portrait_id']}")
        
        if matched_char:
            faction_names = {0: '敌军', 1: 'NPC', 2: '友军'}
            output_lines.append(f"阵营: {faction_names.get(matched_char['faction'], f'未知({matched_char['faction']})')}")
            output_lines.append(f"种族ID: {matched_char['race_id']}")
            output_lines.append(f"职业ID: {matched_char['job_id']}")
            output_lines.append(f"等级: {matched_char['level']}")
            output_lines.append(f"出场回合: {matched_char['spawn_turn'] if matched_char['spawn_turn'] != 0xFF else '增援'}")
            
            # 尝试获取职业名
            job_name = decode_text(fdtxt_data, fdtxt_offsets, matched_char['job_id'], font_encoding)
            if job_name and job_name != '[未知字符0]':
                output_lines.append(f"职业名: {job_name}")
            
            items_str = []
            for j, item_id in enumerate(matched_char['items']):
                if item_id != 0xFF:
                    item_name = decode_text(fdtxt_data, fdtxt_offsets, item_id + 100, font_encoding)
                    if item_name:
                        items_str.append(f"道具{j}: ID={item_id} ({item_name})")
                    else:
                        items_str.append(f"道具{j}: ID={item_id}")
                else:
                    items_str.append(f"道具{j}: 无")
            output_lines.append("物品: " + ", ".join(items_str))
            
            spells_str = []
            for j, spell_id in enumerate(matched_char['spells']):
                if spell_id != 0xFF:
                    spell_name = decode_text(fdtxt_data, fdtxt_offsets, spell_id + 200, font_encoding)
                    if spell_name:
                        spells_str.append(f"法术{j}: ID={spell_id} ({spell_name})")
                    else:
                        spells_str.append(f"法术{j}: ID={spell_id}")
                else:
                    spells_str.append(f"法术{j}: 无")
            output_lines.append("法术: " + ", ".join(spells_str))
        else:
            if pos['portrait_id'] == 0:
                output_lines.append("类型: 己方人物")
            else:
                output_lines.append("类型: 未匹配到角色数据")
        
        output_lines.append("")
    
    output_text = '\n'.join(output_lines)
    print(output_text)
    
    if args.export:
        with open(args.export, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"\n已导出到: {args.export}")

if __name__ == '__main__':
    main()