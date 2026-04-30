#!/usr/bin/env python3
"""
根据文档截图和IDA分析，验证26字节角色结构

地图0:
- 控制数据大小: 0x3A9 = 937字节
- 前缀: 3 + 48 + 32 + 48 = 131字节
- 角色信息区: 937 - 131 = 806字节
- 敌人总数: 30

如果26字节/单位: 30 * 26 = 780字节，余26字节
这26字节可能是友军信息？

或者敌人总数实际上包含友军？
最大友军: 4
敌人: 30
总人物: 34

34 * 26 = 884字节 > 806字节  不匹配

让我检查实际数据...
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

control_offset = 0x0A9A
control_size = 0x3A9  # 937

# 地图信息
enemy_count = data[control_offset + 2]
max_friendly = data[control_offset + 1]

print("验证角色信息结构")
print("=" * 60)
print("敌人总数: {}".format(enemy_count))
print("最大友军: {}".format(max_friendly))
print()

# 前缀
prefix_size = 3 + 48 + 32 + 48  # 131字节
char_info_start = control_offset + prefix_size
char_info_size = control_size - prefix_size

print("角色信息区:")
print("  起始偏移: 0x{:04X} ({})".format(char_info_start - control_offset, char_info_start - control_offset))
print("  总大小: {}字节".format(char_info_size))
print()

# 显示实际十六进制数据
print("角色信息区前64字节:")
for addr in range(char_info_start, char_info_start + 64, 16):
    hex_bytes = data[addr:addr+16]
    hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
    print("  0x{:04X}: {}".format(addr - control_offset, hex_str))

print()
print("=" * 60)
print("尝试用26字节解析")
print("=" * 60)
print()

unit_size = 26
num_units = char_info_size // unit_size
remainder = char_info_size % unit_size

print("解析: {}字节 / {}字节 = {}单位，余{}字节".format(
    char_info_size, unit_size, num_units, remainder))
print()

# 解析前5个角色
for i in range(min(5, num_units)):
    off = char_info_start + i * unit_size
    
    faction = data[off]
    portrait = data[off + 1]
    race = data[off + 2]
    job = data[off + 3]
    level = data[off + 4]
    items = data[off + 5:off + 13]
    spells = data[off + 13:off + 17]  # 4字节
    spawn_turn = data[off + 17]
    drop_type = data[off + 18]
    drop_content_3 = data[off + 19:off + 22]  # 3字节
    drop_content = struct.unpack_from('<I', b'\x00' + drop_content_3, 0)[0]
    
    faction_str = {0: "敌军", 1: "NPC", 2: "友军"}.get(faction, "未知")
    
    print("角色{:2d}:".format(i))
    print("  阵营: {} ({})".format(faction_str, faction))
    print("  头像: {}, 种族: {}, 职业: {}, 等级: {}".format(portrait, race, job, level))
    print("  物品: {}".format(' '.join('{:02X}'.format(x) for x in items)))
    print("  法术: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
    print("  出场回合: {}".format(spawn_turn))
    print("  掉落: 类型={}, 内容=0x{:06X}".format(drop_type, drop_content))
    print()

# 剩余的字节
if remainder > 0:
    print("剩余{}字节:".format(remainder))
    hex_bytes = data[char_info_start + num_units * unit_size:char_info_start + char_info_size]
    hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
    print("  " + hex_str)
