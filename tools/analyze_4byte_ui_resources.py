#!/usr/bin/env python
"""查看4字节表中的18个图形资源，分析是否为存档槽位UI元素"""
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
    
    print('分析4字节偏移表中的18个图形资源')
    print('=' * 60)
    
    for i in range(1, 19):
        off = i * 4
        val = struct.unpack('<I', idx1_data[off:off+4])[0]
        next_off = (i+1) * 4
        if next_off < 0x46:
            next_val = struct.unpack('<I', idx1_data[next_off:next_off+4])[0]
            size = next_val - val
        else:
            size = 0
        
        if val < len(idx1_data) and size > 0:
            res_data = idx1_data[val:val+size]
            
            # 解析头部
            w = struct.unpack('<H', res_data[0:2])[0]
            h = struct.unpack('<H', res_data[2:4])[0]
            pixel_data = res_data[4:]
            
            print(f'\n资源{i}: 偏移0x{val:04X}, 尺寸{w}x{h}, 像素数据{len(pixel_data)} bytes')
            
            # 查看像素数据格式
            # 如果是8bpp，应该是w*h bytes
            # 如果是4bpp压缩，应该是(w*h+1)//2 bytes
            expected_8bpp = w * h
            expected_4bpp = (w * h + 1) // 2
            
            print(f'  预期8bpp: {expected_8bpp}, 4bpp: {expected_4bpp}, 实际: {len(pixel_data)}')
            
            # 打印前32字节
            print(f'  前32字节: {pixel_data[:32].hex()}')
            
            # 如果是24x20=480字节，可能是8bpp
            if len(pixel_data) == expected_8bpp:
                print(f'  -> 8bpp未压缩像素数据')
                # 保存到BMP或raw格式
                output_path = os.path.join(output_dir, f'ui_res_{i}_{w}x{h}_8bpp.raw')
                with open(output_path, 'wb') as out_f:
                    out_f.write(pixel_data)
            elif len(pixel_data) == expected_4bpp:
                print(f'  -> 4bpp压缩像素数据')
                output_path = os.path.join(output_dir, f'ui_res_{i}_{w}x{h}_4bpp.raw')
                with open(output_path, 'wb') as out_f:
                    out_f.write(pixel_data)
            else:
                print(f'  -> 未知格式')
