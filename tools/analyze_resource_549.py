#!/usr/bin/env python
"""直接分析FDOTHER.DAT中资源549的二进制内容"""
import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')

with open(fdother_path, 'rb') as f:
    data = f.read()
    print(f'FDOTHER.DAT 总大小: {len(data)} bytes')
    
    # FDOTHER.DAT头部结构
    # 0x00-0x03: 魔数或版本
    # 0x04-0x05: 资源数量
    # 0x06开始: 索引表
    
    magic = data[0:4]
    print(f'头部4字节: {magic.hex()}')
    
    res_count = struct.unpack('<H', data[4:6])[0]
    print(f'资源数量: {res_count}')
    
    # 每个索引项: 4字节偏移 + 4字节大小
    index_start = 6
    print(f'\n索引表 (从0x{index_start:04X}开始):')
    
    for i in range(min(res_count, 15)):
        off = index_start + i * 8
        res_offset = struct.unpack('<I', data[off:off+4])[0]
        res_size = struct.unpack('<I', data[off+4:off+8])[0]
        print(f'  索引{i}: 偏移=0x{res_offset:06X}, 大小={res_size} bytes')
        
        # 如果是索引1，详细分析
        if i == 1:
            print(f'\n  索引1详细内容:')
            if res_offset < len(data) and res_size > 0:
                idx1_data = data[res_offset:res_offset+res_size]
                
                # 分析索引1内部结构
                # 前0x46字节是4字节偏移表
                print(f'    前0x46字节(4字节偏移表):')
                for j in range(0x46 // 4):
                    table_off = j * 4
                    if table_off + 4 <= len(idx1_data):
                        val = struct.unpack('<I', idx1_data[table_off:table_off+4])[0]
                        next_off = (j+1) * 4
                        if next_off < 0x46:
                            next_val = struct.unpack('<I', idx1_data[next_off:next_off+4])[0]
                            size = next_val - val
                        else:
                            size = 0
                        print(f'      [{j:2d}] 0x{val:06X} (大小{size})')
                
                # 从0x46开始是2字节偏移表
                print(f'\n    从0x46开始的2字节偏移表:')
                table_2byte_start = 0x46
                for j in range(10):  # 打印前10个
                    entry_off = table_2byte_start + j * 2
                    if entry_off + 2 <= len(idx1_data):
                        val = struct.unpack('<H', idx1_data[entry_off:entry_off+2])[0]
                        print(f'      [{j:3d}] 0x{val:04X}')
                
                # 查看资源549
                # 资源ID 549在2字节表中的位置: 0x46 + 549*2 = 0x49A
                res_549_table_off = 0x46 + 549 * 2
                if res_549_table_off + 2 <= len(idx1_data):
                    res_549_offset = struct.unpack('<H', idx1_data[res_549_table_off:res_549_table_off+2])[0]
                    res_550_table_off = 0x46 + 550 * 2
                    if res_550_table_off + 2 <= len(idx1_data):
                        res_550_offset = struct.unpack('<H', idx1_data[res_550_table_off:res_550_table_off+2])[0]
                        res_549_size = res_550_offset - res_549_offset
                    else:
                        res_549_size = len(idx1_data) - res_549_offset
                    
                    print(f'\n    资源549:')
                    print(f'      表位置: 0x{res_549_table_off:04X}')
                    print(f'      偏移: 0x{res_549_offset:04X}')
                    print(f'      大小: {res_549_size} bytes')
                    
                    if res_549_offset < len(idx1_data) and res_549_size > 0:
                        res_549_data = idx1_data[res_549_offset:res_549_offset+res_549_size]
                        
                        # 将549数据当作int16数组解析
                        print(f'\n    资源549内容(前100个int16):')
                        for k in range(min(100, len(res_549_data)//2)):
                            val = struct.unpack('<h', res_549_data[k*2:k*2+2])[0]
                            print(f'      [{k:3d}] {val:6d} (0x{val:04X})')
                        
                        # 保存完整资源
                        output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'resource_549_script.bin')
                        with open(output_path, 'wb') as out_f:
                            out_f.write(res_549_data)
                        print(f'\n    已保存到: {output_path}')
