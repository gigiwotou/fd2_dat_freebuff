#!/usr/bin/env python
"""分析FDOTHER.DAT索引1的资源549脚本数据"""
import struct
import os

output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
resource_549_path = os.path.join(output_dir, 'resource_549_script.bin')

if not os.path.exists(resource_549_path):
    print('资源549文件不存在')
    exit(1)

with open(resource_549_path, 'rb') as f:
    data = f.read()
    
print(f'资源549大小: {len(data)} bytes')
print(f'\n前200字节(hex):')
for i in range(0, min(200, len(data)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
    print(f'  {i:04X}: {hex_str}')

print(f'\n解析为int16数组(前100个):')
for i in range(min(100, len(data)//2)):
    val = struct.unpack('<h', data[i*2:i*2+2])[0]
    # 显示特殊值
    if val == -1:
        desc = '(END)'
    elif val == -2:
        desc = '(NEWLINE)'
    elif val == -3:
        desc = '(NEWLINE_WAIT)'
    elif val == -4:
        desc = '(CALL_205_76)'
    elif val == -5:
        desc = '(CALL_205_74)'
    elif val == -6:
        desc = '(PRINT_VAR)'
    elif val == -17:
        desc = '(LOAD_1832)'
    elif val == -18:
        desc = '(LOAD_36887)'
    elif val == -19:
        desc = '(LOAD_1832_80X)'
    elif val == -20:
        desc = '(LOAD_36887_80X)'
    else:
        desc = ''
    print(f'  [{i:3d}] {val:6d} (0x{val:04X}) {desc}')
