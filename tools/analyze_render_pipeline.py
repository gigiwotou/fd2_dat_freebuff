#!/usr/bin/env python3
"""分析sub_25A96/sub_25B45使用的渲染管线"""
import struct

# 从sub_25A96反汇编:
# v13 = *(DWORD *)(v8 + 6) + a5  (tile数据地址)
# v12 = *(DWORD *)(v8 + 10) - *(DWORD *)(v8 + 6)  (tile数据大小)
# sub_39694(v9, dword_53EE4, v13, v12)
# 这里v13是数据地址，v12是数据大小

# 但嵌套DAT的偏移表中，每个条目是DWORD
# 所以 a5 应该是嵌套DAT资源基址
# a6 应该是tile索引

# v8 = a5 + 4*a6
# *(DWORD *)(v8 + 6) 是从偏移6开始的DWORD
# 但嵌套DAT偏移表从偏移10开始

# 这意味着嵌套DAT的元数据表可能从某个其他位置开始
# 或者 sub_25A96 使用不同的数据结构

# 让我检查嵌套DAT的完整结构
dat_path = r'D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offsets = []
for i in range(count):
    offset = struct.unpack_from('<I', data, 10 + i * 4)[0]
    offsets.append(offset)

# 场景0 (索引63)
res_start = offsets[63]
res_end = offsets[64] if 64 < len(offsets) else len(data)
res_data = data[res_start:res_end]

print(f"索引63完整结构分析:")
print(f"  大小: {len(res_data)} 字节")

# 查看完整数据的前256字节
print(f"\n前256字节:")
for i in range(0, 256, 16):
    hex_str = ' '.join(f'{b:02X}' for b in res_data[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_data[i:i+16])
    print(f"  {i:03d} (0x{i:03X}): {hex_str}  {ascii_str}")

# 解析
print(f"\n结构解析:")
print(f"  [0-5] magic: {res_data[:6]}")
print(f"  [6-9] 值: 0x{struct.unpack_from('<I', res_data, 6)[0]:08X} = {struct.unpack_from('<I', res_data, 6)[0]}")

# 检查偏移表
nested_count = struct.unpack_from('<I', res_data, 6)[0]
print(f"  偏移表条目数: {nested_count}")

# 每个条目可能不是4字节，而是更大
# 从sub_25A96使用 *(DWORD *)(v8 + 6) 和 *(DWORD *)(v8 + 10)
# 说明条目至少14字节

# 尝试不同的条目大小
for entry_size in [14, 16, 20, 24]:
    num_entries = (len(res_data) - 10) // entry_size
    if num_entries > 0 and num_entries <= 100:
        print(f"\n  尝试条目大小 {entry_size} 字节:")
        for i in range(min(3, num_entries)):
            offset = 10 + i * entry_size
            if offset + 14 <= len(res_data):
                val6 = struct.unpack_from('<I', res_data, offset + 6)[0]
                val10 = struct.unpack_from('<I', res_data, offset + 10)[0]
                print(f"    条目{i}: +6=0x{val6:08X} ({val6}), +10=0x{val10:08X} ({val10})")
                if val6 < len(res_data) and val10 <= len(res_data) and val10 > val6:
                    print(f"      -> 数据大小: {val10 - val6}")
