#!/usr/bin/env python3
"""在FDOTHER所有资源中搜索24x24的图像"""

import struct

def find_24x24_images():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    resource_count = struct.unpack('<I', data[6:10])[0]
    print(f"资源数量: {resource_count}")
    
    # 检查每个资源的头2-4字节是否为24x24
    found = []
    for idx in range(resource_count):
        offset = 10 + idx * 4
        if offset + 4 > len(data):
            break
        
        res_offset = struct.unpack('<I', data[offset:offset+4])[0]
        
        if res_offset > 0 and res_offset + 4 < len(data):
            w = struct.unpack('<H', data[res_offset:res_offset+2])[0]
            h = struct.unpack('<H', data[res_offset+2:res_offset+4])[0]
            
            if w == 24 and h == 24:
                found.append(idx)
                print(f"\n*** 找到24x24图像: 索引{idx}, 偏移{res_offset} ***")
                print(f"前32字节: {' '.join(f'{b:02X}' for b in data[res_offset:res_offset+32])}")
    
    print(f"\n共找到 {len(found)} 个24x24图像: 索引 {found}")
    
    # 同时检查资源5内部的资源表
    res5_offset = struct.unpack('<I', data[10+5*4:10+5*4+4])[0]
    res5_data = data[res5_offset:]
    res5_count = struct.unpack('<H', res5_data[4:6])[0]
    
    print(f"\n\n资源5内部资源数量: {res5_count}")
    found5 = []
    
    for idx in range(res5_count):
        table_offset = 6 + idx * 4
        if table_offset + 4 > len(res5_data):
            break
        
        entry_offset = struct.unpack('<I', res5_data[table_offset:table_offset+4])[0]
        
        if entry_offset > 0 and entry_offset + 4 < len(res5_data):
            w = struct.unpack('<H', res5_data[entry_offset:entry_offset+2])[0]
            h = struct.unpack('<H', res5_data[entry_offset+2:entry_offset+4])[0]
            
            if w == 24 and h == 24:
                found5.append(idx)
                print(f"  索引{idx}: 偏移{entry_offset}, RLE={ ' '.join(f'{b:02X}' for b in res5_data[entry_offset+4:entry_offset+20])}")
    
    print(f"\n资源5中找到 {len(found5)} 个24x24图像: 索引 {found5}")

if __name__ == '__main__':
    find_24x24_images()
