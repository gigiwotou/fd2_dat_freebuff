#!/usr/bin/env python
"""
分析FDOTHER.DAT索引1的资源偏移表结构
根据sub_29AB2代码:
  - 资源201/205: 存档槽边框(选中/未选中)
  - 资源514: 空存档提示
  - 资源549: 文本/脚本资源
  - 资源550: 场景编号字符
"""
import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

with open(fdother_path, 'rb') as f:
    data = f.read()
    
    # FDOTHER.DAT索引1的位置
    idx1_offset = 0xD61
    idx1_size = 41105
    idx1_data = data[idx1_offset:idx1_offset+idx1_size]
    
    print('FDOTHER.DAT索引1完整资源偏移表分析')
    print('=' * 70)
    
    # 从0x46开始的2字节偏移表
    table_start = 0x46
    
    # 查看资源201和205
    for res_id in [201, 205, 514, 549, 550]:
        table_off = table_start + res_id * 2
        if table_off + 2 <= len(idx1_data):
            res_offset = struct.unpack('<H', idx1_data[table_off:table_off+2])[0]
            
            # 查找下一个非零资源来计算大小
            next_res_offset = None
            for next_id in range(res_id + 1, min(res_id + 100, 1000)):
                next_table_off = table_start + next_id * 2
                if next_table_off + 2 <= len(idx1_data):
                    next_val = struct.unpack('<H', idx1_data[next_table_off:next_table_off+2])[0]
                    if next_val != res_offset and next_val != 0:
                        next_res_offset = next_val
                        break
            
            if next_res_offset:
                res_size = next_res_offset - res_offset
            else:
                res_size = len(idx1_data) - res_offset
            
            print(f'\n资源ID {res_id}:')
            print(f'  表位置: 0x{table_off:04X}')
            print(f'  偏移: 0x{res_offset:04X}')
            print(f'  大小: {res_size} bytes')
            
            if res_offset < len(idx1_data) and res_size > 0 and res_size < 100000:
                res_data = idx1_data[res_offset:res_offset+res_size]
                
                # 检查是否是图像(有宽高头部)
                if len(res_data) >= 4:
                    w = struct.unpack('<H', res_data[0:2])[0]
                    h = struct.unpack('<H', res_data[2:4])[0]
                    if w < 500 and h < 500 and w > 0 and h > 0:
                        pixel_data = res_data[4:]
                        expected_size = w * h
                        print(f'  图像: {w}x{h}, 像素数据: {len(pixel_data)} bytes')
                        if len(pixel_data) == expected_size:
                            print(f'  -> 8bpp图像')
                            output_path = os.path.join(output_dir, f'res_{res_id}_{w}x{h}.raw')
                            with open(output_path, 'wb') as out_f:
                                out_f.write(pixel_data)
                        elif len(pixel_data) == (expected_size + 1) // 2:
                            print(f'  -> 4bpp图像')
                    
                # 如果前4字节不是有效宽高，可能是脚本或其他数据
                else:
                    print(f'  前4字节: {res_data[:4].hex()}')
                    # 检查是否全是可打印字符或小数值
                    if all(b < 128 for b in res_data[:64]):
                        print(f'  -> 可能是ASCII/脚本数据')
