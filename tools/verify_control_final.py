#!/usr/bin/env python3
"""
验证地图0控制数据结构（根据文档截图）

文档标注：
- 0x0A9A: 00 = 地图编号
- 0x0A9B: 04 = 最大友军数
- 0x0A9C: 1E = 敌人总数（30）
- 0x0A9D~0x0ACC: 回合事件（16组×3字节=48字节）
- 之后: 保留数据（16组×2字节=32字节）
- 之后: 宝箱数据（16组×3字节=48字节）
- 之后: 角色信息（每单位19字节）

文档说"前0x83个字节是地图的控制信息"
0x83 = 131 = 3 + 48 + 32 + 48 ✓
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

control_offset = 0x0A9A
control_size = 0x3A9

print("=" * 70)
print("地图0控制数据验证（基于文档截图）")
print("=" * 70)
print()

# 显示关键区域的十六进制
print("控制数据关键区域:")
for addr in [0x0A9A, 0x0A9D, 0x0AA9, 0x0AB9, 0x0AC9, 0x0AD9, 0x0AE9, 0x0AF9, 0x0B09, 0x0B19]:
    if addr < control_offset + control_size:
        hex_bytes = data[addr:addr+16]
        hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
        print("  0x{:04X}: {}".format(addr, hex_str))

print()
print("=" * 70)
print("解析控制数据结构")
print("=" * 70)
print()

control_data = data[control_offset:control_offset + control_size]

# 地图信息（3字节）
map_number = control_data[0]
max_friendly = control_data[1]
total_units = control_data[2]

print("地图信息:")
print("  地图编号: {}".format(map_number))
print("  最大友军: {}".format(max_friendly))
print("  敌人总数: {} (0x{:02X})".format(total_units, total_units))
print()

# 回合事件（48字节 = 16组×3字节）
turn_offset = 3
turn_size = 48
print("回合事件（偏移0x{:02X}~0x{:02X}，{}字节）:".format(turn_offset, turn_offset + turn_size - 1, turn_size))
for i in range(16):
    off = turn_offset + i * 3
    turn = control_data[off]
    event = struct.unpack_from('<H', control_data, off + 1)[0]
    if turn != 0xFF or event != 0xFFFF:
        print("  组{:2d}: 回合={:2d}, 事件=0x{:04X}".format(i, turn, event))
print()

# 保留数据（32字节 = 16组×2字节）
reserved_offset = turn_offset + turn_size
reserved_size = 32
print("保留数据（偏移0x{:02X}~0x{:02X}，{}字节）:".format(reserved_offset, reserved_offset + reserved_size - 1, reserved_size))
for i in range(16):
    off = reserved_offset + i * 2
    val = struct.unpack_from('<H', control_data, off)[0]
    if val != 0xFF00:
        print("  组{:2d}: 0x{:04X}".format(i, val))
print("  (文档说应该全是FF 00)")
print()

# 宝箱数据（48字节 = 16组×3字节）
treasure_offset = reserved_offset + reserved_size
treasure_size = 48
print("宝箱数据（偏移0x{:02X}~0x{:02X}，{}字节）:".format(treasure_offset, treasure_offset + treasure_size - 1, treasure_size))
for i in range(16):
    off = treasure_offset + i * 3
    box_type = control_data[off]
    content = struct.unpack_from('<H', control_data, off + 1)[0]
    if box_type != 0xFF:
        if box_type == 0x00:
            desc = "物品#{}".format(content)
        elif box_type == 0x01:
            desc = "金钱{}".format(content)
        else:
            desc = "未知"
        print("  组{:2d}: 类型={}, 内容={} ({})".format(i, box_type, content, desc))
print()

# 计算前缀大小
prefix_size = 3 + 48 + 32 + 48
print("前缀总计: {}字节 (0x{:02X})".format(prefix_size, prefix_size))
print("文档说前0x83字节，0x83 = {}".format(0x83))
print()

# 角色信息
char_offset = prefix_size
char_size = control_size - prefix_size
print("角色信息:")
print("  起始偏移: 0x{:02X} ({})".format(char_offset, char_offset))
print("  总大小: {}字节".format(char_size))
print("  敌人总数: {}".format(total_units))
print()

# 测试不同单位大小
for unit_size in range(15, 35):
    expected = total_units * unit_size
    if expected == char_size:
        print("  [MATCH] {}字节/单位 × {}单位 = {}字节".format(unit_size, total_units, char_size))
    elif abs(expected - char_size) <= 5:
        print("  {}字节/单位 × {}单位 = {}字节 (差{}字节)".format(
            unit_size, total_units, expected, char_size - expected))

# 尝试用19字节解析
print()
print("=" * 70)
print("用19字节/单位解析角色信息")
print("=" * 70)
print()

unit_size = 19
num_units = char_size // unit_size
remainder = char_size % unit_size

print("解析: {}字节  {}字节/单位 = {}单位，余{}字节".format(
    char_size, unit_size, num_units, remainder))
print()

for i in range(min(5, num_units)):
    off = char_offset + i * unit_size
    
    faction = control_data[off]
    portrait = control_data[off + 1]
    race = control_data[off + 2] if unit_size > 2 else 0
    job = control_data[off + 3] if unit_size > 3 else 0
    level = control_data[off + 4] if unit_size > 4 else 0
    items = control_data[off + 5:off + 13] if unit_size > 5 else b''
    spells = control_data[off + 13:off + 17] if unit_size > 13 else b''
    spawn_turn = control_data[off + 17] if unit_size > 17 else 0
    drop_type = control_data[off + 18] if unit_size > 18 else 0
    
    faction_str = {0: "敌军", 1: "NPC", 2: "友军"}.get(faction, "未知")
    
    print("角色{:2d}:".format(i))
    print("  阵营: {} (0x{:02X})".format(faction_str, faction))
    print("  头像: {}".format(portrait))
    print("  等级: {}".format(level))
    print("  物品: {}".format(' '.join('{:02X}'.format(x) for x in items)))
    print("  法术: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
    print("  出场回合: {}".format(spawn_turn))
    print("  掉落类型: 0x{:02X}".format(drop_type))
    print()
