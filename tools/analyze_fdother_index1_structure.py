#!/usr/bin/env python
"""分析FDOTHER.DAT索引1的2字节偏移表"""
import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    f.seek(0x46)  # 跳过DAT头部
    # 读取索引表
    idx_count = struct.unpack('<H', f.read(2))[0]
    print(f'索引数量: {idx_count}')
    
    # 读取索引表
    index_table = []
    for i in range(idx_count):
        offset = struct.unpack('<I', f.read(4))[0]
        size = struct.unpack('<I', f.read(4))[0]
        index_table.append((offset, size))
        if i < 5 or i == 12:  # 只打印前5个和第13个
            print(f'索引{i}: 偏移=0x{offset:08X}, 大小=0x{size:08X}')
    
    # 读取索引1
    idx1_offset, idx1_size = index_table[1]
    f.seek(idx1_offset)
    idx1_data = f.read(idx1_size)
    
    print(f'\n索引1数据:')
    print(f'  偏移: 0x{idx1_offset:08X}')
    print(f'  大小: {idx1_size} bytes')
    
    # 分析索引1的内部结构
    # 前4字节可能是资源数量
    if len(idx1_data) >= 4:
        res_count = struct.unpack('<I', idx1_data[0:4])[0]
        print(f'  资源数量: {res_count}')
        
        # 读取资源偏移表(每个4字节)
        offset_table_start = 4
        offset_table_end = offset_table_start + res_count * 4
        
        if offset_table_end <= len(idx1_data):
            print(f'\n资源偏移表:')
            for i in range(min(res_count, 20)):  # 只打印前20个
                off = offset_table_start + i * 4
                res_offset = struct.unpack('<I', idx1_data[off:off+4])[0]
                next_off = offset_table_start + (i+1) * 4
                if next_off < offset_table_end:
                    next_res_offset = struct.unpack('<I', idx1_data[next_off:next_off+4])[0]
                    res_size = next_res_offset - res_offset
                else:
                    res_size = len(idx1_data) - res_offset
                
                print(f'  资源{i}: 偏移=0x{res_offset:06X}, 大小={res_size}')
                
                # 如果是目标资源ID，保存内容
                if i in [201, 205, 514, 549, 550]:
                    if res_offset < len(idx1_data) and res_size > 0:
                        res_data = idx1_data[res_offset:res_offset+res_size]
                        output_path = os.path.join(os.path.dirname(__file__), '..', 'output', f'idx1_resource_{i}.bin')
                        with open(output_path, 'wb') as out_f:
                            out_f.write(res_data)
                        print(f'    已保存到: {output_path}')
                        
                        # 打印前32字节
                        print(f'    前32字节: {res_data[:32].hex()}')
