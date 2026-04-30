#!/usr/bin/env python3
"""
根据文档截图重新计算地图0控制数据结构

从文档截图标注：
- 0x0A9A: 00 (地图编号)
- 0x0A9B: 04 (最大友军)
- 0x0A9C: 1E (敌人总数 = 30)
- 0x0A9D ~ 0x0ACC: 回合事件（蓝色高亮）- 48字节 = 16组 * 3字节
- 0x0ACD ~ 0x0AEC: 未知保留（每2字节一组，共16组）- 32字节
- 0x0AED ~ 0x0B1C: 宝箱数据（绿色高亮）- 48字节 = 16组 * 3字节  
- 0x0B1D ~ ?: 角色信息

文档说"前0x83个字节是地图控制信息"
0x83 = 131字节
3 (header) + 48 (turn events) + 32 (reserved) + 48 (treasure) = 131 = 0x83 ✓

角色信息大小 = 总控制大小 - 0x83
总控制大小 = 0x3A9 = 937字节
角色信息 = 937 - 131 = 806字节
每单位 = 806 / 30 = 26.86...  这不合理！

让我检查文档是否说"前0x83字节"还是别的...
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

control_offset = 0x0A9A
control_size = 0x3A9

print("验证控制数据结构")
print("=" * 60)

# 前3字节
print("地图信息（3字节）:")
print("  0x{:04X}: {:02X} = 地图编号 {}".format(control_offset, data[control_offset], data[control_offset]))
print("  0x{:04X}: {:02X} = 最大友军 {}".format(control_offset+1, data[control_offset+1], data[control_offset+1]))
print("  0x{:04X}: {:02X} = 敌人总数 {}".format(control_offset+2, data[control_offset+2], data[control_offset+2]))
print()

total_units = data[control_offset+2]

# 回合事件 16*3 = 48字节
turn_start = control_offset + 3
turn_end = turn_start + 48

print("回合事件（48字节，0x{:04X}~0x{:04X}）:".format(turn_start, turn_end-1))
for i in range(16):
    addr = turn_start + i * 3
    turn = data[addr]
    event = struct.unpack_from('<H', data, addr+1)[0]
    print("  组{:2d}: 回合={:2d}, 事件={:04X}".format(i, turn, event))
print()

# 保留数据 16*2 = 32字节
reserved_start = turn_end
reserved_end = reserved_start + 32

print("保留数据（32字节，0x{:04X}~0x{:04X}）:".format(reserved_start, reserved_end-1))
for i in range(16):
    addr = reserved_start + i * 2
    val = struct.unpack_from('<H', data, addr)[0]
    if val != 0xFF00:
        print("  组{:2d}: 0x{:04X}".format(i, val))
print("  (应该是FF 00)")
print()

# 宝箱数据 16*3 = 48字节
treasure_start = reserved_end
treasure_end = treasure_start + 48

print("宝箱数据（48字节，0x{:04X}~0x{:04X}）:".format(treasure_start, treasure_end-1))
for i in range(16):
    addr = treasure_start + i * 3
    box_type = data[addr]
    content = struct.unpack_from('<H', data, addr+1)[0]
    if box_type != 0xFF:
        if box_type == 0x00:
            desc = "物品#{}".format(content)
        elif box_type == 0x01:
            desc = "金钱{}".format(content)
        else:
            desc = "未知类型{}".format(box_type)
        print("  组{:2d}: 类型={}, 内容={} ({})".format(i, box_type, content, desc))
print()

# 角色信息
char_start = treasure_end
char_size = control_size - (char_start - control_offset)

print("角色信息:")
print("  起始偏移: 0x{:04X} ({})".format(char_start - control_offset, char_start - control_offset))
print("  总大小: {}字节".format(char_size))
print("  敌人总数: {}".format(total_units))
print()

# 尝试找到正确的单位大小
for unit_size in range(15, 35):
    if total_units * unit_size == char_size:
        print("  [MATCH] {}字节/单位 * {}单位 = {}字节".format(unit_size, total_units, char_size))
        break
else:
    print("  [NO EXACT MATCH]")
    for unit_size in range(15, 35):
        diff = char_size - total_units * unit_size
        if abs(diff) < 10:
            print("  {}字节/单位: 需要{}字节，实际{}字节，差{}字节".format(
                unit_size, total_units * unit_size, char_size, diff))
