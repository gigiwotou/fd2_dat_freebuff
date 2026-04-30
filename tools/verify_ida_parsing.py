#!/usr/bin/env python3
"""
根据IDA sub_1088D反编译代码验证角色位置解析

IDA关键代码：
  v4 = (_BYTE *)(dword_53A59 + 6 * dword_53BE3 + 2);
  
  for (n6 = 0; n6 < ::n6; ++n6) {
      *v3 = *v4;        // 复制byte[0] → X坐标
      v3[1] = v4[2];    // 复制byte[2] → Y坐标
      v4 += 6;          // 步进6字节
      ...
  }

其中：
  dword_53A59 = char_pos_data（角色位置数据）
  dword_53BE3 = *(control_data + 2) = total_units（敌人总数）
  ::n6 = *(control_data + 1) = max_friendly（己方人数）

所以：
  v4初始 = char_pos_data + 6 * total_units + 2
  循环次数 = max_friendly
  每次步进 = 6字节
  
这意味从位置数据中读取max_friendly个角色的坐标
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# 地图0
control_offset = 0x0A9A
charpos_offset = 0x0E43

control_data = data[control_offset:]
charpos_data = data[charpos_offset:]

# 从控制数据读取参数（IDA逻辑）
terrain_set_id = control_data[0]
max_friendly = control_data[1]
total_units = control_data[2]

print("地图0 - 根据IDA sub_1088D解析")
print("=" * 70)
print("控制数据：")
print("  terrain_set_id = {}".format(terrain_set_id))
print("  max_friendly (::n6) = {}".format(max_friendly))
print("  total_units (dword_53BE3) = {}".format(total_units))
print()

# 角色位置总数
total_chars = struct.unpack_from('<H', charpos_data, 0)[0]
print("角色位置数据：")
print("  总数 = {}".format(total_chars))
print("  max_friendly + total_units = {} + {} = {}".format(
    max_friendly, total_units, max_friendly + total_units))
print()

# IDA逻辑：v4 = char_pos_data + 6 * total_units + 2
v4_base = 6 * total_units + 2
print("IDA计算v4初始位置：")
print("  v4 = char_pos_data + 6 * {} + 2 = {}".format(total_units, v4_base))
print()

# 循环max_friendly次
print("循环读取 {} 个角色位置（max_friendly）：".format(max_friendly))
print("{:<6} {:<6} {:<6} {:<12}".format("索引", "X", "Y", "Portrait"))
print("-" * 35)

for i in range(max_friendly):
    offset = v4_base + i * 6
    
    if offset + 6 > len(charpos_data):
        print("  数据不足！")
        break
    
    x = charpos_data[offset]
    unknown = charpos_data[offset + 1]
    y = charpos_data[offset + 2]
    portrait = charpos_data[offset + 3]
    extra = charpos_data[offset + 4:offset + 6]
    
    print("{:<6} {:<6} {:<6} {:<12}".format(i, x, y, portrait))

print()
print("=" * 70)
print("完整角色位置数据（所有{}个）：".format(total_chars))
print("=" * 70)
print()

print("{:<6} {:<6} {:<6} {:<6} {:<12}".format("索引", "X", "?", "Y", "Portrait"))
print("-" * 40)

for i in range(total_chars):
    offset = 2 + i * 6
    
    if offset + 6 > len(charpos_data):
        break
    
    x = charpos_data[offset]
    unknown1 = charpos_data[offset + 1]
    y = charpos_data[offset + 2]
    portrait = charpos_data[offset + 3]
    
    print("{:<6} {:<6} {:<6} {:<6} {:<12}".format(i, x, unknown1, y, portrait))
