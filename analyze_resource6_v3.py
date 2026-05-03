#!/usr/bin/env python3
"""根据sub_111BA汇编分析资源6的正确结构"""

import struct

def analyze_sub_111ba_format():
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 大小: {len(data)}")
    
    # sub_111BA 解析（111ba-112a4）:
    # 11217: shl eax, 2          ; index * 4
    # 1121a: add eax, 6          ; + 6
    # 1121f: fseek               ; 定位到文件偏移
    # 1122c: fread(8 bytes)      ; 读取8字节：4字节起始偏移 + 4字节结束偏移
    # 11235: mov edi, [ebx]      ; edi = 起始偏移
    # 11237: mov eax, [ebx+4]    ; eax = 结束偏移
    # 1123a: sub eax, edi        ; 资源大小 = 结束 - 起始
    # 11250: malloc(资源大小)
    # 1127c: fseek(起始偏移)
    # 1128e: fread(资源数据)
    # 1129f: return 资源数据指针
    
    # 所以资源6的数据是直接从FDOTHER.DAT中提取的原始数据
    # 资源6表项: 偏移30-33 (6 + 6*4)
    resource6_start = struct.unpack('<I', data[30:34])[0]
    resource7_start = struct.unpack('<I', data[34:38])[0]
    resource6_size = resource7_start - resource6_start
    
    print(f"\n资源6: 起始={resource6_start}, 大小={resource6_size}")
    
    resource6_data = data[resource6_start:resource6_start+resource6_size]
    
    # 打印前50字节
    print(f"\n资源6前50字节:")
    for i in range(0, 50, 16):
        hex_str = ' '.join(f'{b:02X}' for b in resource6_data[i:i+16])
        print(f"  {i:04d}: {hex_str}")
    
    # 分析头部
    magic = resource6_data[0:4]
    print(f"\n魔数: {''.join(chr(b) if 32 <= b < 127 else '.' for b in magic)}")
    
    # 从偏移6开始可能是资源表
    print(f"\n=== 从偏移6开始解析为资源表 ===")
    table_data = resource6_data[6:]
    
    # 每个表项4字节
    for idx in range(0, 200):
        offset = idx * 4
        if offset + 4 > len(table_data):
            break
        
        entry = struct.unpack('<I', table_data[offset:offset+4])[0]
        
        # 如果entry < 资源6大小，可能是相对偏移
        if entry > 0 and entry < len(resource6_data):
            # 尝试解析为RLE图像
            w = struct.unpack('<H', resource6_data[entry:entry+2])[0]
            h = struct.unpack('<H', resource6_data[entry+2:entry+4])[0]
            
            if w > 0 and w < 256 and h > 0 and h < 256:
                print(f"  索引{idx:3d} (表内偏移{offset:4d}): entry={entry:6d} -> 图像 {w}x{h}")
                
                # 如果是索引130（战场光标）
                if idx == 130:
                    print(f"    *** 光标资源 ***")
                    print(f"    RLE前16字节: {' '.join(f'{b:02X}' for b in resource6_data[entry+4:entry+20])}")

if __name__ == '__main__':
    analyze_sub_111ba_format()
