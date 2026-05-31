#!/usr/bin/env python
"""
简单分析索引1的原始字节结构
"""

import os

fdother_path = r"d:\workspace\fd2_dat_freebuff\game\FDOTHER.DAT"

if not os.path.exists(fdother_path):
    print(f"文件不存在: {fdother_path}")
    exit(1)

with open(fdother_path, 'rb') as f:
    data = f.read()

print(f"文件大小: {len(data)} bytes (0x{len(data):X})\n")

# 解析FDOTHER头部
# [0-3]: magic "FDOT"
# [4-7]: version
# [8+]: 资源索引表 (每个资源12字节)
#   [0-3]: offset
#   [4-7]: size
#   [8-11]: type

magic = data[0:4]
print(f"Magic: {magic}")

version = data[4] | (data[5] << 8) | (data[6] << 16) | (data[7] << 24)
print(f"Version: {version}\n")

# 找到索引1的资源信息
# 每个资源索引12字节
index1_entry_offset = 8 + 12 * 1  # 索引1
offset = data[index1_entry_offset] | (data[index1_entry_offset+1] << 8) | \
         (data[index1_entry_offset+2] << 16) | (data[index1_entry_offset+3] << 24)
size = data[index1_entry_offset+4] | (data[index1_entry_offset+5] << 8) | \
       (data[index1_entry_offset+6] << 16) | (data[index1_entry_offset+7] << 24)

print(f"索引1资源:")
print(f"  Offset: 0x{offset:X}")
print(f"  Size: 0x{size:X} ({size} bytes)\n")

# 读取资源数据
res_data = data[offset:offset+size]
print(f"资源前50字节:")
for i in range(0, min(50, len(res_data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
    print(f"  {i:04X}: {hex_str:<48s} {ascii_str}")

# 解析头部
if len(res_data) >= 10:
    width = res_data[0] | (res_data[1] << 8)
    height = res_data[2] | (res_data[3] << 8)
    palette_window = res_data[4]
    padding = res_data[5]
    
    print(f"\n头部解析:")
    print(f"  [0-1]: width = {width} (0x{width:X})")
    print(f"  [2-3]: height = {height} (0x{height:X})")
    print(f"  [4]: palette_window = {palette_window} (0x{palette_window:X})")
    print(f"  [5]: padding = {padding} (0x{padding:X})")
    
    # 解析偏移表（从偏移6开始，4字节每个）
    print(f"\n偏移表（前20个）:")
    offsets = []
    pos = 6
    for i in range(20):
        if pos + 4 > len(res_data):
            break
        off = res_data[pos] | (res_data[pos+1] << 8) | \
              (res_data[pos+2] << 16) | (res_data[pos+3] << 24)
        print(f"  [{pos}-{pos+3}]: offset = 0x{off:X} ({off} bytes)")
        offsets.append(off)
        pos += 4
        if off == 0 or off > size:
            break
    
    # 分析第一个图标的数据
    if len(offsets) >= 2 and offsets[0] > 0 and offsets[0] < size:
        icon0_offset = offsets[0]
        icon1_offset = offsets[1] if offsets[1] <= size else size
        icon0_size = icon1_offset - icon0_offset
        
        print(f"\n图标0:")
        print(f"  起始偏移: 0x{icon0_offset:X}")
        print(f"  大小: {icon0_size} bytes")
        print(f"  前30字节:")
        icon_data = res_data[icon0_offset:icon0_offset+min(30, icon0_size)]
        for i in range(0, len(icon_data), 16):
            hex_str = ' '.join(f'{b:02X}' for b in icon_data[i:i+16])
            print(f"    {i:04X}: {hex_str}")
        
        # 手动解码前几个字节
        print(f"\n手动解码前10个控制字节:")
        src_idx = 0
        for i in range(10):
            if src_idx >= len(icon_data):
                break
            value = icon_data[src_idx]
            bit7 = (value >> 7) & 1
            bit6 = (value >> 6) & 1
            lower6 = value & 0x3F
            mode = f"{bit7}{bit6}"
            
            if mode == "00":
                desc = "填充模式"
            elif mode == "01":
                desc = "交替模式"
            elif mode == "10":
                desc = "复制模式"
            elif mode == "11":
                desc = "跳过模式"
            
            print(f"  字节{i}: 0x{value:02X} = {mode}xxxxxx ({desc}), count={lower6}")
            src_idx += 1
