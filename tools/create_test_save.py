#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用的FD2.SAV存档文件
用于验证parse_fd2_save.py解析工具的正确性
"""

import struct
import os

# 与解析器相同的常量
SAVE_FILE_SIZE = 22987
OFFSET_CAMP_CHAR_DATA = 4771
OFFSET_CAMP_ICON_CACHE = 12451
OFFSET_CAMP_GAME_STATE = 12483
OFFSET_UNUSED = 12501
OFFSET_BATTLE_SLOTS = 12587
OFFSET_CHECKSUM = 22983
BATTLE_SLOT_SIZE = 2600

def rol16(value, shift):
    """16位循环左移"""
    value &= 0xFFFF
    return ((value << shift) | (value >> (16 - shift))) & 0xFFFF

def encrypt_decrypt(data: bytearray) -> bytearray:
    """XOR滚动加密/解密（同一算法）"""
    result = bytearray(len(data))
    key = 0xA5
    
    for i in range(len(data)):
        key = ((key - 0x7014) & 0xFFFF)
        key = rol16(key, 3)
        result[i] = data[i] ^ (key & 0xFF)
    
    return result

def calc_checksum(data: bytes) -> int:
    """计算校验和"""
    checksum = 0
    for i in range(OFFSET_CHECKSUM):
        checksum += data[i]
    return checksum & 0xFFFFFFFF

def create_test_save(filepath, map_id=0, char_count=4, has_battle_save=False):
    """创建测试存档文件"""
    
    # 创建22987字节的缓冲区，先填充0
    save_data = bytearray(SAVE_FILE_SIZE)
    
    # ========== 填充营地地图数据 (偏移0, 2211字节) ==========
    # 模拟一些地图数据
    for i in range(2211):
        save_data[i] = (i + map_id) % 256
    
    # ========== 填充营地战场队伍数据 (偏移2211, 2560字节) ==========
    for i in range(2560):
        save_data[2211 + i] = i % 256
    
    # ========== 填充角色数据 (偏移4771, 96个角色×80字节) ==========
    # 这里只填充前char_count个角色
    for char_idx in range(char_count):
        offset = OFFSET_CAMP_CHAR_DATA + char_idx * 80
        
        # 角色基础数据
        save_data[offset + 0] = char_idx % 24 + 1    # tile_x
        save_data[offset + 1] = char_idx % 16 + 1    # tile_y
        save_data[offset + 4] = 0 if char_idx < 2 else 1  # faction (0=己方, 1=敌方)
        save_data[offset + 5] = 0  # active_byte (0=存活)
        save_data[offset + 6] = 0  # char_type
        save_data[offset + 7] = char_idx + 100  # icon_id
        save_data[offset + 32] = char_idx + 100  # icon_id_alt
        save_data[offset + 33] = 2  # direction
        save_data[offset + 39] = 0  # death_flag (0=存活)
        save_data[offset + 70] = 5 + char_idx  # level/stats
        
        # 填充一些测试数据到padding区域
        for i in range(10, 25):
            save_data[offset + i] = char_idx + i
    
    # ========== 填充图标缓存 (偏移12451, 32字节) ==========
    for i in range(32):
        save_data[12451 + i] = i
    
    # ========== 填充营地游戏状态 (偏移12483, 18字节) ==========
    save_data[12483] = 0  # dword_53BEF
    save_data[12484] = char_count  # 角色数量
    save_data[12485] = map_id  # 当前地图ID
    save_data[12486] = 1  # n9
    save_data[12487] = 2  # n34
    save_data[12488] = 3  # n9_0
    save_data[12489] = 4  # n34_0
    save_data[12490] = 5  # n2_2
    save_data[12491] = 6  # n2_1
    save_data[12492] = 3  # 图标数量
    struct.pack_into('<I', save_data, 12493, 0x12345678)  # dword_53BF3
    save_data[12497] = 0xAA  # byte_53AF9
    save_data[12498] = 0xBB  # byte_51AAB
    save_data[12499] = 0xCC  # n127
    save_data[12500] = 0xDD  # byte_51E62
    
    # ========== 填充战场存档槽位 (偏移12587, 4个×2600字节) ==========
    if has_battle_save:
        for slot_idx in range(4):
            slot_offset = OFFSET_BATTLE_SLOTS + slot_idx * BATTLE_SLOT_SIZE
            
            # 战场数据
            for i in range(2560):
                save_data[slot_offset + i] = (i + slot_idx * 100) % 256
            
            # 槽位状态
            save_data[slot_offset + 2560] = map_id + slot_idx  # 地图ID
            save_data[slot_offset + 2561] = slot_idx + 1  # 图标数量
            struct.pack_into('<I', save_data, slot_offset + 2562, 0xAABB0000 + slot_idx)
            save_data[slot_offset + 2566] = 0x11
            save_data[slot_offset + 2567] = 0x22
            save_data[slot_offset + 2568] = 0x33
            save_data[slot_offset + 2569] = 0x44
    else:
        # 全部标记为空 (map_id = 0xFF)
        for slot_idx in range(4):
            slot_offset = OFFSET_BATTLE_SLOTS + slot_idx * BATTLE_SLOT_SIZE
            save_data[slot_offset + 2560] = 0xFF  # 无效地图ID
    
    # ========== 计算并写入校验和 ==========
    checksum = calc_checksum(save_data)
    struct.pack_into('<I', save_data, OFFSET_CHECKSUM, checksum)
    
    # ========== 加密整个文件 ==========
    encrypted_data = encrypt_decrypt(save_data)
    
    # 写入文件
    with open(filepath, 'wb') as f:
        f.write(encrypted_data)
    
    print(f"[成功] 创建测试存档: {filepath}")
    print(f"  文件大小: {len(encrypted_data)} 字节")
    print(f"  地图ID: {map_id}")
    print(f"  角色数量: {char_count}")
    print(f"  战场存档: {'有' if has_battle_save else '无'}")

if __name__ == '__main__':
    # 获取脚本所在目录的上级output目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建几个测试存档
    create_test_save(os.path.join(output_dir, 'test_save_1.sav'), map_id=0, char_count=4, has_battle_save=False)
    create_test_save(os.path.join(output_dir, 'test_save_2.sav'), map_id=5, char_count=8, has_battle_save=True)
    create_test_save(os.path.join(output_dir, 'test_save_3.sav'), map_id=10, char_count=16, has_battle_save=True)
    
    print(f"\n测试存档已创建到: {output_dir}")
    print("可以使用以下命令测试解析器:")
    print(f"  python parse_fd2_save.py {os.path.join(output_dir, 'test_save_1.sav')}")
    print(f"  python parse_fd2_save.py {os.path.join(output_dir, 'test_save_2.sav')} FDFIELD.DAT")
