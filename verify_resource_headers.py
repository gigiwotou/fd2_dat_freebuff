#!/usr/bin/env python3
"""验证哪个资源的头部是 LLLLLL"""

import struct

def verify_resource_headers():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # FDOTHER.DAT格式：
    # 偏移0-5: 魔数 LLLLLL
    # 偏移6-9: 资源数量 (422)
    # 偏移10开始: 资源偏移表
    
    resource_count = struct.unpack('<I', data[6:10])[0]
    print(f"资源数量: {resource_count}")
    
    print(f"\n检查前20个资源的头部:")
    for i in range(20):
        offset = 10 + i * 4
        if offset + 4 > len(data):
            break
        
        res_offset = struct.unpack('<I', data[offset:offset+4])[0]
        
        # 读取该资源的前6字节
        res_header = data[res_offset:res_offset+6]
        header_hex = ' '.join(f'{b:02X}' for b in res_header)
        header_ascii = ''.join(chr(b) if 32 <= b < 127 else '.' for b in res_header)
        
        print(f"  资源{i}: 偏移={res_offset}, 头部={header_hex} ({header_ascii})")

if __name__ == '__main__':
    verify_resource_headers()
