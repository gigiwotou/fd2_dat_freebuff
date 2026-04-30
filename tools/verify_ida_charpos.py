#!/usr/bin/env python3
"""
验证IDA的角色位置数据解析逻辑

根据IDA sub_1088D：
  v4 = (_BYTE *)(dword_53A59 + 6 * dword_53BE3 + 2);
  
其中：
  dword_53A59 = 角色位置数据
  dword_53BE3 = control_data[2] = 敌人总数（total_units）
  
所以：v4指向 (角色位置数据 + 6 * total_units + 2)

但等等，这很奇怪。让我重新理解...

实际上IDA代码是：
  v4 = (_BYTE *)(dword_53A59 + 6 * dword_53BE3 + 2);
  
循环中：
  *v3 = *v4;           // byte[0]
  v3[1] = v4[2];       // byte[2]
  v4 += 6;             // 步进6字节
  
这说明角色位置数据格式是：
  偏移0: 总数（2字节）
  偏移2: 角色1数据
    +0: X坐标
    +1: ?（未使用）
    +2: Y坐标
    +3: portrait_id
    +4-5: ?
  偏移8: 角色2数据
  ...

但IDA使用 v4 = data + 6*total_units + 2，这是指向数组末尾！
然后循环中 v4 += 6，这是向后读取？

不对，让我重新看IDA代码...

v4初始化：v4 = char_pos_data + 6 * total_units + 2
循环：v4 += 6

这说明v4从末尾开始，向后读取？但这不合理...

让我用Python验证实际数据
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# 地图0
charpos_offset = 0x0E43
charpos_data = data[charpos_offset:]

# 读取总数
total = struct.unpack_from('<H', charpos_data, 0)[0]
print("地图0角色位置数据")
print("=" * 60)
print("总数: {}".format(total))
print()

# IDA逻辑：v4 = data + 6 * total_units + 2
# 但total_units是敌人总数（control_data[2]），不是角色总数
# 地图0的敌人总数 = 30

enemy_count = 30

# 计算v4偏移
v4_offset = 6 * enemy_count + 2
print("IDA计算：")
print("  v4偏移 = 6 * {} + 2 = {}".format(enemy_count, v4_offset))
print()

# 显示v4指向的数据
print("v4指向的数据（前60字节）:")
for i in range(10):
    offset = v4_offset + i * 6
    if offset + 6 > len(charpos_data):
        break
    
    bytes_data = charpos_data[offset:offset+6]
    x = bytes_data[0]
    unknown1 = bytes_data[1]
    y = bytes_data[2]
    portrait = bytes_data[3]
    unknown2 = bytes_data[4:6]
    
    print("  角色{:2d}: X={:3d}, ?={:3d}, Y={:3d}, Portrait={:3d}, ?={}".format(
        i, x, unknown1, y, portrait, ' '.join('{:02X}'.format(b) for b in unknown2)))

print()
print("=" * 60)
print("对比：正常解析（从偏移2开始）")
print("=" * 60)
print()

for i in range(10):
    offset = 2 + i * 6
    if offset + 6 > len(charpos_data):
        break
    
    bytes_data = charpos_data[offset:offset+6]
    x = bytes_data[0]
    unknown1 = bytes_data[1]
    y = bytes_data[2]
    portrait = bytes_data[3]
    unknown2 = bytes_data[4:6]
    
    print("  角色{:2d}: X={:3d}, ?={:3d}, Y={:3d}, Portrait={:3d}, ?={}".format(
        i, x, unknown1, y, portrait, ' '.join('{:02X}'.format(b) for b in unknown2)))
