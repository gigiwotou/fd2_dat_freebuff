#!/usr/bin/env python3
"""
验证DATO.DAT头像加载机制

基于IDA Pro MCP分析结果:
1. 从FD2.SAV读取角色数据(偏移4771, 80字节/角色)
2. 提取每个角色的icon_id(角色数据偏移7)
3. 验证icon_id在DATO.DAT索引表中是否有效
4. 验证sub_111BA索引计算逻辑: file_offset = 4 * index + 6

IDA分析关键发现:
- 控制码-17/-18: 从dword_53BF7战场队伍数组查找角色,获取icon_id
- 控制码-19/-20: 直接从dword_53A45角色数组获取icon_id
- icon_id是单字节值(0-255),用作DATO.DAT的索引
- DATO.DAT文件头6字节,索引表从偏移10开始,每项4字节
"""

import struct
import sys
from pathlib import Path

# 配置
GAME_DIR = Path(__file__).parent.parent / "game"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

FD2SAV_PATH = GAME_DIR / "FD2.SAV"
DATO_PATH = GAME_DIR / "DATO.DAT"

# IDA分析的常量
SAVE_SIZE = 22987
SAVE_CHAR_DATA_OFFSET = 4771
SAVE_CHAR_COUNT_OFFSET = 12484
CHAR_DATA_SIZE = 80
CHAR_ICON_ID_OFFSET = 7

DATO_HEADER_SIZE = 6
DATO_INDEX_TABLE_OFFSET = 10


def decrypt_save(data: bytes) -> bytes:
    """
    解密FD2.SAV存档文件
    基于IDA sub_4DF28函数分析
    """
    result = bytearray(data)
    checksum = 0
    for i in range(SAVE_SIZE - 4):
        result[i] ^= 0x5A
        checksum += result[i]
    return bytes(result)


def load_dato_index_table(dato_data: bytes):
    """
    加载DATO.DAT索引表
    基于IDA sub_111BA函数分析
    """
    if len(dato_data) < 10:
        print("错误: DATO.DAT文件太小")
        return None, None
    
    # 读取索引数量 (偏移6, 4字节)
    count = struct.unpack('<I', dato_data[6:10])[0]
    print(f"DATO.DAT索引数量: {count}")
    print(f"DATO.DAT文件大小: {len(dato_data)} 字节")
    
    # 解析索引表
    index_table = []
    for i in range(count - 1):
        offset = DATO_INDEX_TABLE_OFFSET + i * 4
        if offset + 4 > len(dato_data):
            break
        start = struct.unpack('<I', dato_data[offset:offset+4])[0]
        end_offset = DATO_INDEX_TABLE_OFFSET + (i + 1) * 4
        if end_offset + 4 <= len(dato_data):
            end = struct.unpack('<I', dato_data[end_offset:end_offset+4])[0]
        else:
            end = len(dato_data)
        
        index_table.append({
            'index': i,
            'start': start,
            'end': end,
            'size': end - start,
            'valid': start < len(dato_data) and end <= len(dato_data)
        })
    
    return count, index_table


def load_save_characters(save_data: bytes):
    """
    从解密后的存档数据加载角色信息
    基于IDA sub_10010函数分析:
    - n6_0 = *(unsigned __int8 *)(v0 + 12484);
    - memmove(dword_53A45, v0 + 4771, 80 * n6_0);
    """
    char_count = save_data[SAVE_CHAR_COUNT_OFFSET]
    print(f"\n存档角色数量: {char_count}")
    
    characters = []
    for i in range(char_count):
        char_offset = SAVE_CHAR_DATA_OFFSET + i * CHAR_DATA_SIZE
        if char_offset + CHAR_DATA_SIZE > len(save_data):
            break
        
        char_data = save_data[char_offset:char_offset + CHAR_DATA_SIZE]
        icon_id = char_data[CHAR_ICON_ID_OFFSET]
        
        characters.append({
            'index': i,
            'icon_id': icon_id,
            'tile_x': char_data[0],
            'tile_y': char_data[1],
            'faction': char_data[4],
            'active_byte': char_data[5],
        })
    
    return char_count, characters


def validate_icon_ids(characters, count, index_table):
    """
    验证角色icon_id在DATO.DAT索引表中是否有效
    """
    print(f"\n{'='*60}")
    print(f"角色icon_id验证报告")
    print(f"{'='*60}")
    
    valid_count = 0
    invalid_count = 0
    invalid_icons = []
    icon_ids_used = set()
    
    for char in characters:
        icon_id = char['icon_id']
        icon_ids_used.add(icon_id)
        
        if icon_id < len(index_table):
            entry = index_table[icon_id]
            if entry['valid']:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_icons.append((char['index'], icon_id, "索引表条目无效"))
        else:
            invalid_count += 1
            invalid_icons.append((char['index'], icon_id, "索引超出范围"))
    
    print(f"有效icon_id: {valid_count}")
    print(f"无效icon_id: {invalid_count}")
    print(f"使用的唯一icon_id: {sorted(icon_ids_used)}")
    
    if invalid_icons:
        print(f"\n无效的icon_id详情:")
        for char_idx, icon_id, reason in invalid_icons:
            print(f"  角色{char_idx}: icon_id={icon_id} - {reason}")
    
    return valid_count, invalid_count, icon_ids_used


def analyze_dato_index_table(count, index_table, dato_size):
    """
    分析DATO.DAT索引表,找出有效和无效条目
    """
    print(f"\n{'='*60}")
    print(f"DATO.DAT索引表分析")
    print(f"{'='*60}")
    
    valid_entries = 0
    invalid_entries = 0
    last_valid_index = -1
    
    for entry in index_table:
        if entry['valid']:
            valid_entries += 1
            last_valid_index = entry['index']
        else:
            invalid_entries += 1
    
    print(f"总条目数: {len(index_table)}")
    print(f"有效条目: {valid_entries}")
    print(f"无效条目: {invalid_entries}")
    print(f"最后一个有效索引: {last_valid_index}")
    print(f"文件头声明数量: {count}")
    print(f"实际有效数量: {valid_entries}")
    
    # 显示前几个有效条目
    print(f"\n前10个有效索引条目:")
    for entry in index_table[:10]:
        if entry['valid']:
            print(f"  [{entry['index']:3d}] start={entry['start']:6d} end={entry['end']:6d} size={entry['size']:6d}")
    
    # 显示最后几个有效条目
    print(f"\n最后5个有效索引条目:")
    valid_entries_list = [e for e in index_table if e['valid']]
    for entry in valid_entries_list[-5:]:
        print(f"  [{entry['index']:3d}] start={entry['start']:6d} end={entry['end']:6d} size={entry['size']:6d}")
    
    return valid_entries


def main():
    print("="*60)
    print("DATO.DAT头像加载验证工具")
    print("基于IDA Pro MCP分析结果")
    print("="*60)
    
    # 加载DATO.DAT
    if not DATO_PATH.exists():
        print(f"错误: 找不到 {DATO_PATH}")
        return
    
    with open(DATO_PATH, 'rb') as f:
        dato_data = f.read()
    
    count, index_table = load_dato_index_table(dato_data)
    if count is None:
        return
    
    # 分析索引表
    valid_entries = analyze_dato_index_table(count, index_table, len(dato_data))
    
    # 加载存档角色数据
    if FD2SAV_PATH.exists():
        with open(FD2SAV_PATH, 'rb') as f:
            save_raw = f.read()
        
        save_data = decrypt_save(save_raw)
        char_count, characters = load_save_characters(save_data)
        
        # 验证icon_id
        validate_icon_ids(characters, count, index_table)
    else:
        print(f"\n警告: 找不到 {FD2SAV_PATH}, 跳过角色验证")
    
    print(f"\n{'='*60}")
    print(f"验证完成")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
