#!/usr/bin/env python3
"""
验证IDA的索引逻辑：fseek(v3, 4 * a3 + 6, 0)

根据IDA sub_1088D：
  sub_111BA(FDFIELD.DAT, ..., 3 * map_id)       # 布局数据
  sub_111BA(FDFIELD.DAT, ..., 3 * map_id + 1)   # 控制数据
  sub_111BA(FDFIELD.DAT, ..., 3 * map_id + 2)   # 角色位置

所以索引表结构应该是：
  字节6 + 0: 地图0-布局数据偏移
  字节6 + 4: 地图0-控制数据偏移
  字节6 + 8: 地图0-角色位置偏移
  字节6 + 12: 地图1-布局数据偏移
  字节6 + 16: 地图1-控制数据偏移
  字节6 + 20: 地图1-角色位置偏移
  ...

即：每地图12字节（3个DWORD），但索引计算使用 4 * (3*map_id + part_index) + 6
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

print("FDFIELD.DAT - IDA索引逻辑验证")
print("=" * 70)
print()

# IDA逻辑：offset = 4 * index + 6
# 其中index = 3 * map_id + part_index (0=layout, 1=control, 2=charpos)

def ida_load_offset(map_id, part_index):
    """根据IDA逻辑计算索引位置"""
    index = 3 * map_id + part_index
    offset = 4 * index + 6
    return offset

# 验证地图0
print("地图0验证：")
layout_idx = ida_load_offset(0, 0)
control_idx = ida_load_offset(0, 1)
charpos_idx = ida_load_offset(0, 2)

print(f"  索引计算：")
print(f"    layout:  4 * (3*0 + 0) + 6 = {layout_idx}")
print(f"    control: 4 * (3*0 + 1) + 6 = {control_idx}")
print(f"    charpos: 4 * (3*0 + 2) + 6 = {charpos_idx}")
print()

layout_off = struct.unpack_from('<I', data, layout_idx)[0]
control_off = struct.unpack_from('<I', data, control_idx)[0]
charpos_off = struct.unpack_from('<I', data, charpos_idx)[0]

print(f"  读取结果：")
print(f"    layout  offset:  0x{layout_off:06X} ({layout_off})")
print(f"    control offset:  0x{control_off:06X} ({control_off})")
print(f"    charpos offset:  0x{charpos_off:06X} ({charpos_off})")
print()

# 验证地图0的十六进制
print("  索引表十六进制（字节6-17）：")
hex_data = data[6:18]
print(f"    {' '.join('{:02X}'.format(b) for b in hex_data)}")
print()

print("地图32验证：")
layout_idx_32 = ida_load_offset(32, 0)
control_idx_32 = ida_load_offset(32, 1)
charpos_idx_32 = ida_load_offset(32, 2)

print(f"  索引计算：")
print(f"    layout:  4 * (3*32 + 0) + 6 = {layout_idx_32}")
print(f"    control: 4 * (3*32 + 1) + 6 = {control_idx_32}")
print(f"    charpos: 4 * (3*32 + 2) + 6 = {charpos_idx_32}")
print()

layout_off_32 = struct.unpack_from('<I', data, layout_idx_32)[0]
control_off_32 = struct.unpack_from('<I', data, control_idx_32)[0]
charpos_off_32 = struct.unpack_from('<I', data, charpos_idx_32)[0]

print(f"  读取结果：")
print(f"    layout  offset:  0x{layout_off_32:06X} ({layout_off_32})")
print(f"    control offset:  0x{control_off_32:06X} ({control_off_32})")
print(f"    charpos offset:  0x{charpos_off_32:06X} ({charpos_off_32})")
print()

# 对比之前用12字节逻辑的结果
print("=" * 70)
print("对比：12字节/地图 vs IDA的4字节索引")
print("=" * 70)
print()

print("地图0:")
print("  12字节逻辑: layout={:6d} (0x{:06X})".format(
    struct.unpack_from('<I', data, 6 + 0*12)[0],
    struct.unpack_from('<I', data, 6 + 0*12)[0]))
print("  IDA逻辑:    layout={:6d} (0x{:06X})".format(layout_off, layout_off))
print()

print("地图32:")
print("  12字节逻辑: layout={:6d} (0x{:06X})".format(
    struct.unpack_from('<I', data, 6 + 32*12)[0],
    struct.unpack_from('<I', data, 6 + 32*12)[0]))
print("  IDA逻辑:    layout={:6d} (0x{:06X})".format(layout_off_32, layout_off_32))
print()

# 验证数据是否正确
print("=" * 70)
print("验证数据有效性")
print("=" * 70)
print()

for map_id, label in [(0, "地图0"), (32, "地图32")]:
    layout_idx = ida_load_offset(map_id, 0)
    control_idx = ida_load_offset(map_id, 1)
    charpos_idx = ida_load_offset(map_id, 2)
    
    layout_off = struct.unpack_from('<I', data, layout_idx)[0]
    control_off = struct.unpack_from('<I', data, control_idx)[0]
    charpos_off = struct.unpack_from('<I', data, charpos_idx)[0]
    
    print("{}:".format(label))
    
    # 验证布局数据（应该以width, height开头）
    if 0 < layout_off + 4 < len(data):
        width = struct.unpack_from('<H', data, layout_off)[0]
        height = struct.unpack_from('<H', data, layout_off + 2)[0]
        print("  布局数据: {}x{} 瓦片 (offset 0x{:06X})".format(width, height, layout_off))
    else:
        print("  布局数据: 无效偏移 0x{:06X}".format(layout_off))
    
    # 验证控制数据（前3字节应该是地图信息）
    if 0 < control_off + 3 < len(data):
        map_num = data[control_off]
        max_friendly = data[control_off + 1]
        total_units = data[control_off + 2]
        print("  控制数据: 地图{}, 友军{}, 敌人{} (offset 0x{:06X})".format(
            map_num, max_friendly, total_units, control_off))
    else:
        print("  控制数据: 无效偏移 0x{:06X}".format(control_off))
    
    # 验证角色位置（前2字节应该是总数）
    if 0 < charpos_off + 2 < len(data):
        total_chars = struct.unpack_from('<H', data, charpos_off)[0]
        print("  角色位置: 总数{} (offset 0x{:06X})".format(total_chars, charpos_off))
    else:
        print("  角色位置: 无效偏移 0x{:06X}".format(charpos_off))
    
    print()
