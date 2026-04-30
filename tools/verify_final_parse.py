#!/usr/bin/env python3
"""
最终验证：用26字节/单位解析地图0角色信息，并对比文档截图
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

control_offset = 0x0A9A
control_size = 0x3A9  # 937字节

print("地图0角色信息最终验证（26字节/单位）")
print("=" * 70)

# 前缀
prefix_size = 3 + 48 + 32 + 48  # 131字节
char_info_start = control_offset + prefix_size
char_info_size = control_size - prefix_size

print("角色信息区: 0x{:04X} ~ 0x{:04X}".format(
    char_info_start - control_offset, char_info_start + char_info_size - 1 - control_offset))
print("总大小: {}字节".format(char_info_size))
print()

# 敌人总数
enemy_count = data[control_offset + 2]
print("敌人总数: {}".format(enemy_count))

# 计算
num_units = char_info_size // 26
remainder = char_info_size % 26
print("按26字节/单位: {}单位，余{}字节".format(num_units, remainder))
print()

if num_units != enemy_count:
    print("[WARNING] 解析单位数({})与敌人总数({})不匹配!".format(num_units, enemy_count))
    print("  差值: {}字节".format(char_info_size - enemy_count * 26))
    print()

# 显示前几个角色的十六进制
print("角色信息区前78字节（3个角色）:")
for addr in range(char_info_start, char_info_start + 78, 16):
    hex_bytes = data[addr:addr+16]
    hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
    print("  0x{:04X}: {}".format(addr - control_offset, hex_str))

print()
print("=" * 70)
print("解析角色信息（26字节结构）")
print("=" * 70)
print()

for i in range(min(5, enemy_count)):
    off = char_info_start + i * 26
    
    faction = data[off]
    portrait = data[off + 1]
    race = data[off + 2]
    job = data[off + 3]
    level = data[off + 4]
    items = data[off + 5:off + 13]
    spells = data[off + 13:off + 17]  # 4字节
    spawn_turn = data[off + 17]
    drop_type = data[off + 18]
    drop_content_bytes = data[off + 19:off + 22]  # 3字节
    drop_content = struct.unpack_from('<I', b'\x00' + drop_content_bytes, 0)[0]
    reserved = data[off + 22:off + 26]
    
    faction_str = {0: "敌军", 1: "NPC", 2: "友军"}.get(faction, "未知")
    
    print("角色{:2d}:".format(i))
    print("  阵营: {} ({:2d})".format(faction_str, faction))
    print("  头像: {}, 种族: {}, 职业: {}, 等级: {}".format(portrait, race, job, level))
    print("  物品: {}".format(' '.join('{:02X}'.format(x) for x in items)))
    print("  法术: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
    print("  出场回合: {}".format(spawn_turn))
    print("  掉落: 类型={}, 内容=0x{:06X} ({}物品/{}金钱)".format(
        drop_type, drop_content, 
        "物品#" if drop_type == 0 else "",
        drop_content if drop_type == 1 else 0))
    print("  保留: {}".format(' '.join('{:02X}'.format(x) for x in reserved)))
    print()
