#!/usr/bin/env python
"""分析FDOTHER.DAT索引1的UI资源，查看4字节表中的图形资源"""
import struct
import os

fdother_path = os.path.join(os.path.dirname(__file__), '..', 'game', 'FDOTHER.DAT')
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

with open(fdother_path, 'rb') as f:
    data = f.read()
    
    # FDOTHER.DAT索引1的位置
    # 从之前的分析知道索引1在偏移0xD61，大小41105字节
    idx1_offset = 0xD61
    idx1_size = 41105
    idx1_data = data[idx1_offset:idx1_offset+idx1_size]
    
    print('FDOTHER.DAT索引1分析')
    print(f'大小: {len(idx1_data)} bytes')
    
    # 前0x46字节是4字节偏移表
    print('\n4字节偏移表 (前0x46字节):')
    for i in range(0x46 // 4):
        off = i * 4
        val = struct.unpack('<I', idx1_data[off:off+4])[0]
        next_off = (i+1) * 4
        if next_off < 0x46:
            next_val = struct.unpack('<I', idx1_data[next_off:next_off+4])[0]
            size = next_val - val
        else:
            size = 0
        print(f'  [{i:2d}] 0x{val:06X} (大小{size})')
        
        # 提取并保存资源
        if i > 0 and i <= 18 and val < len(idx1_data):
            if size > 0 and val + size <= len(idx1_data):
                res_data = idx1_data[val:val+size]
                output_path = os.path.join(output_dir, f'idx1_4byte_res_{i}.bin')
                with open(output_path, 'wb') as out_f:
                    out_f.write(res_data)
                
                # 解析头部
                if len(res_data) >= 4:
                    w = struct.unpack('<H', res_data[0:2])[0]
                    h = struct.unpack('<H', res_data[2:4])[0]
                    print(f'       尺寸: {w}x{h}, 数据大小: {len(res_data)-4} bytes')
    
    # 查看资源201和205的位置
    print('\n资源201/205分析:')
    res_201_table_off = 0x46 + 201 * 2
    res_205_table_off = 0x46 + 205 * 2
    
    if res_201_table_off + 2 <= len(idx1_data):
        res_201_offset = struct.unpack('<H', idx1_data[res_201_table_off:res_201_table_off+2])[0]
        res_205_offset = struct.unpack('<H', idx1_data[res_205_table_off:res_205_table_off+2])[0]
        res_201_size = res_205_offset - res_201_offset
        
        print(f'  资源201偏移: 0x{res_201_offset:04X}')
        print(f'  资源201大小: {res_201_size}')
        
        # 查看这些数据是否是4字节表的索引
        # 资源201指向0x4A4A，这个位置的数据是什么？
        if res_201_offset < len(idx1_data):
            # 查看该位置的数据
            res_data = idx1_data[res_201_offset:res_201_offset+min(64, len(idx1_data)-res_201_offset)]
            print(f'  资源201前64字节: {res_data.hex()}')
            
            # 如果前4字节是宽度和高度
            if len(res_data) >= 4:
                w = struct.unpack('<H', res_data[0:2])[0]
                h = struct.unpack('<H', res_data[2:4])[0]
                print(f'  可能的尺寸: {w}x{h}')
                
                # 计算预期大小
                expected_size = 4 + (w * h + 1) // 2  # 假设是4bpp压缩
                print(f'  预期大小: {expected_size}')
