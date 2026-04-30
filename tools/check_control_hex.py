#!/usr/bin/env python3
"""
查看地图0控制数据实际内容，对比文档截图
"""

import struct

filepath = r'd:\testworkspace\fd2_dat_freebuff\bin\FDFIELD.DAT'

with open(filepath, 'rb') as f:
    data = f.read()

# 根据之前验证的偏移量
control_offset = 0x0A9A
control_size = 0x3A9

print("地图0控制数据十六进制转储 (0x{:04X} ~ 0x{:04X})".format(control_offset, control_offset + control_size - 1))
print("=" * 80)

# 显示从0x0A90到0x0B20的数据
start_addr = 0x0A90
end_addr = 0x0B20

for addr in range(start_addr, end_addr, 16):
    hex_bytes = data[addr:addr+16]
    hex_str = ' '.join('{:02X}'.format(b) for b in hex_bytes)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in hex_bytes)
    print("0x{:06X}: {:<48} {}".format(addr, hex_str, ascii_str))

print()
print("=" * 80)
print("根据文档标注解析控制数据头部")
print("=" * 80)
print()

# 文档截图显示从0x0A9A开始
print("0x0A9A处开始的字节:")
for i in range(32):
    addr = control_offset + i
    print("  0x{:04X}: 0x{:02X} ({:3d})".format(addr, data[addr], data[addr]))

print()
print("=" * 80)
print("解析地图信息（前3字节）")
print("=" * 80)
print()

control_data = data[control_offset:control_offset + control_size]

map_number = control_data[0]
max_friendly = control_data[1]  
total_units = control_data[2]

print("按26字节/单位计算:")
print("  Header: 3字节")
print("  Turn events: 16 * 3 = 48字节")
print("  Reserved: 16 * 2 = 32字节")  
print("  Treasure: 16 * 3 = 48字节")
print("  前缀总计: 3 + 48 + 32 + 48 = 131字节 (0x83)")
print()

char_info_start = 131
char_info_size = control_size - char_info_start

print("  角色信息区:")
print("  起始偏移: 0x{:02X} ({})".format(char_info_start, char_info_start))
print("  可用大小: {}字节".format(char_info_size))
print("  敌人/NPC总数: {}".format(total_units))
print("  如果每单位26字节: {} * 26 = {}字节".format(total_units, total_units * 26))
print("  如果每单位19字节: {} * 19 = {}字节".format(total_units, total_units * 19))
print()

# 尝试不同大小
for unit_size in [19, 20, 21, 22, 23, 24, 25, 26]:
    needed = total_units * unit_size
    if needed == char_info_size:
        print("  [MATCH] {}字节/单位 = {}字节".format(unit_size, needed))
    elif abs(needed - char_info_size) < 20:
        print("  {}字节/单位 = {}字节 (差{}字节)".format(unit_size, needed, char_info_size - needed))
