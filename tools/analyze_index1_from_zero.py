#!/usr/bin/env python
"""
重新分析FDOTHER.DAT索引1的2字节偏移表
假设表从偏移0开始，而不是从0x46开始
"""
import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    data = f.read()
    
    # FDOTHER.DAT索引1的位置
    idx1_offset = 0xD61
    idx1_size = 41105
    idx1_data = data[idx1_offset:idx1_offset+idx1_size]
    
    print('FDOTHER.DAT索引1的2字节偏移表分析（从偏移0开始）')
    print('=' * 70)
    
    # 假设2字节偏移表从0开始
    for res_id in [0, 1, 201, 205, 514, 549, 550]:
        table_off = res_id * 2
        if table_off + 2 <= len(idx1_data):
            res_offset = struct.unpack('<H', idx1_data[table_off:table_off+2])[0]
            
            # 找下一个不同的偏移计算大小
            next_offset = None
            for next_id in range(res_id + 1, min(res_id + 200, 2000)):
                next_table_off = next_id * 2
                if next_table_off + 2 <= len(idx1_data):
                    next_val = struct.unpack('<H', idx1_data[next_table_off:next_table_off+2])[0]
                    if next_val != res_offset:
                        next_offset = next_val
                        break
            
            if next_offset:
                res_size = next_offset - res_offset
            else:
                res_size = len(idx1_data) - res_offset
            
            print(f'\n资源ID {res_id}:')
            print(f'  表位置: 0x{table_off:04X}')
            print(f'  偏移: 0x{res_offset:04X} ({res_offset})')
            print(f'  大小: {res_size} bytes')
            
            if res_offset < len(idx1_data) and res_size > 0 and res_size < 50000:
                res_data = idx1_data[res_offset:res_offset+min(64, res_size)]
                print(f'  前64字节: {res_data.hex()}')
