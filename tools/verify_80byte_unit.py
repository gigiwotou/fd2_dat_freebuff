#!/usr/bin/env python3
"""
根据IDA分析，角色信息结构是80字节

验证：
总控制大小 = 937字节
前缀 = 3 + 48 + 32 + 48 = 131字节
角色信息 = 937 - 131 = 806字节

如果每单位80字节：
806 / 80 = 10.075  这不合理

让我重新计算...

等等，IDA的sub_1088D显示：
- 角色位置数据：每条6字节（X, Y, portrait）
- 角色信息：memmove 80字节

但80字节可能是内存中的结构，不是文件中的结构。

让我重新检查控制数据的实际大小...

实际上，从Python验证结果看：
- 敌人总数 = 30
- 角色信息区大小 = 806字节
- 806 / 30 = 26.87 字节/单位

这仍然不匹配。让我检查文档是否有误...

或者，可能敌人总数不是30？
0x1E = 30

或者控制数据大小不是937？
0x3A9 = 937

让我检查实际解析的敌人数量...
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# 地图0控制数据
control_offset = 0x0A9A
control_size = 0x3A9  # 937字节

# 解析地图信息
map_number = data[control_offset]
max_friendly = data[control_offset + 1]
enemy_count = data[control_offset + 2]

print("地图0控制信息:")
print("  地图编号: {}".format(map_number))
print("  最大友军: {}".format(max_friendly))
print("  敌人总数: {} (0x{:02X})".format(enemy_count, enemy_count))
print()

# 文档说敌人总数30，但也许应该用其他字段？
# 或者敌人总数是包含友军的总数？

# 计算剩余空间
prefix_size = 3 + 48 + 32 + 48  # 131字节
remaining = control_size - prefix_size

print("前缀大小: {}字节".format(prefix_size))
print("剩余空间: {}字节".format(remaining))
print()

# 尝试不同的单位大小
for total_count in [enemy_count, max_friendly + enemy_count, max_friendly]:
    if total_count > 0:
        for unit_size in range(20, 35):
            if total_count * unit_size == remaining:
                print("[MATCH] 总数={}, {}字节/单位 = {}字节".format(
                    total_count, unit_size, remaining))

print()

# 如果敌人总数实际上是包含所有出场人物？
# 也许敌人总数是30，但实际只有部分有数据？

# 或者文档的敌人总数理解有误？
# 让我尝试用80字节解析前几个角色

print("尝试用80字节解析角色信息:")
print()

char_start = control_offset + prefix_size
for i in range(min(3, enemy_count)):
    off = char_start + i * 80
    if off + 80 > control_offset + control_size:
        break
    
    faction = data[off]
    portrait = data[off + 1]
    race = data[off + 2]
    job = data[off + 3]
    level = data[off + 4]
    items = data[off + 5:off + 13]
    spells = data[off + 13:off + 21]
    
    # 根据IDA，可能是80字节结构
    spawn_turn = data[off + 21] if off + 21 < control_offset + control_size else 0
    drop_type = data[off + 22] if off + 22 < control_offset + control_size else 0
    drop_content = struct.unpack_from('<H', data, off + 23)[0] if off + 25 < control_offset + control_size else 0
    
    faction_str = {0: "敌军", 1: "NPC", 2: "友军"}.get(faction, "未知")
    
    print("角色{:2d} (80字节结构):".format(i))
    print("  阵营: {} (0x{:02X})".format(faction_str, faction))
    print("  头像: {}".format(portrait))
    print("  等级: {}".format(level))
    print("  物品: {}".format(' '.join('{:02X}'.format(x) for x in items)))
    print("  法术: {}".format(' '.join('{:02X}'.format(x) for x in spells)))
    print("  出场回合: {}".format(spawn_turn))
    print("  掉落: 类型={}, 内容=0x{:04X}".format(drop_type, drop_content))
    print()
