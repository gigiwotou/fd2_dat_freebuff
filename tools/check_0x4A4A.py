#!/usr/bin/env python
"""查看FDOTHER.DAT索引1中0x4A4A位置的实际数据"""
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
    
    # 查看0x4A4A位置的数据
    target_off = 0x4A4A
    print(f'索引1中0x{target_off:04X}位置的数据:')
    
    if target_off < len(idx1_data):
        res_data = idx1_data[target_off:target_off+256]
        print(f'前256字节: {res_data.hex()}')
        
        # 尝试解析为不同格式
        # 1. 尝试作为int16数组
        print('\n作为int16数组:')
        for i in range(min(50, len(res_data)//2)):
            val = struct.unpack('<h', res_data[i*2:i*2+2])[0]
            print(f'  [{i:3d}] {val:6d} (0x{val:04X})')
        
        # 2. 查看该位置之前的数据（看看是否是资源边界）
        print('\n0x4A00到0x4B00区域:')
        for off in range(0x4A00, 0x4B00, 16):
            chunk = idx1_data[off:off+16]
            print(f'  0x{off:04X}: {chunk.hex()}')
            
        # 3. 查看4字节表中是否有指向0x4A4A的条目
        print('\n检查4字节偏移表:')
        for i in range(0x46 // 4):
            off = i * 4
            val = struct.unpack('<I', idx1_data[off:off+4])[0]
            if val == 0x4A4A or (val <= 0x4A4A and val + 484 > 0x4A4A):
                print(f'  [{i}] 0x{val:06X} - 包含0x4A4A')
