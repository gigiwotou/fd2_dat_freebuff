#!/usr/bin/env python3
"""
根据MCP反汇编sub_111BA精确分析FDOTHER.DAT的索引结构

关键代码：
fseek(_rb_, 4 * a7 + 6, 0);  // 偏移到 4*index + 6
sub_373CA(v8, 1u, 8, _rb_);  // 读取8字节（2个dword）
v9 = *v8;                     // 第一个dword = 资源起始偏移
dword_53BFF = v8[1] - *v8;   // 第二个dword - 第一个dword = 资源大小

这意味着每个索引对应8字节：
- dword[0]: 资源起始偏移
- dword[1]: 下一个资源的偏移（相减得到大小）
"""

import struct

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    f.seek(0)
    magic = f.read(6)
    print(f"文件头: {magic}")
    print(f"文件头ASCII: {''.join(chr(b) for b in magic)}")
    
    # 读取前10个索引的偏移表
    print("\n" + "="*70)
    print("索引表分析 (每个索引8字节: 起始偏移 + 结束偏移)")
    print("="*70)
    
    for i in range(10):
        f.seek(4 * i + 6)
        data = f.read(8)
        if len(data) < 8:
            print(f"索引{i}: 数据不足")
            break
        
        start_offset = struct.unpack('<I', data[0:4])[0]
        end_offset = struct.unpack('<I', data[4:8])[0]
        size = end_offset - start_offset
        
        print(f"\n索引{i}: 偏移=0x{start_offset:08x}, 结束=0x{end_offset:08x}, 大小={size}")
        
        # 读取资源数据的前20字节用于分析
        f.seek(start_offset)
        res_data = f.read(min(size, 200))
        
        print(f"  前20字节: {' '.join(f'{b:02x}' for b in res_data[:20])}")
        
        # 尝试识别资源类型
        if size == 768:
            print(f"  -> 可能是调色板 (768字节)")
        elif res_data[:4] == b'LMI1':
            print(f"  -> LMI1 Tile集")
        elif res_data[:6] == b'LLLLLL':
            print(f"  -> 嵌套DAT结构")
        elif size >= 4:
            w = struct.unpack('<H', res_data[0:2])[0]
            h = struct.unpack('<H', res_data[2:4])[0]
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                print(f"  -> Tile图像: {w}x{h}")
                if size >= 5:
                    pal_window = res_data[4]
                    print(f"     palette_window={pal_window}")
        
        # 如果是索引2，进一步分析
        if i == 2:
            print(f"\n  索引2详细分析:")
            print(f"  大小={size}字节")
            
            # 尝试解析为偏移表
            if size >= 8:
                # 检查是否是78个偏移值
                if size >= 312:  # 78 * 4 = 312
                    print(f"  可能是78个偏移值的表")
                    
                    # 读取前10个偏移值
                    offsets = []
                    for j in range(min(10, size // 4)):
                        offset = struct.unpack('<I', res_data[j*4:j*4+4])[0]
                        offsets.append(offset)
                        print(f"    偏移[{j}] = 0x{offset:08x}")
                    
                    # 验证这些偏移是否合理
                    if offsets:
                        print(f"\n  验证偏移值:")
                        for j, off in enumerate(offsets[:5]):
                            if off < size:
                                print(f"    偏移[{j}] = 0x{off:08x} (在数据区内)")
                                # 读取该偏移的内容
                                f.seek(start_offset + off)
                                content = f.read(20)
                                print(f"      内容: {' '.join(f'{b:02x}' for b in content[:10])}")
                            else:
                                print(f"    偏移[{j}] = 0x{off:08x} (超出数据区)")
                
        # 如果是索引1，详细分析
        if i == 1:
            print(f"\n  索引1详细分析:")
            print(f"  大小={size}字节")
            
            # 尝试解析为Tile
            if size >= 5:
                w = struct.unpack('<H', res_data[0:2])[0]
                h = struct.unpack('<H', res_data[2:4])[0]
                pal_window = res_data[4]
                
                print(f"  Tile: {w}x{h}, palette_window={pal_window}")
                print(f"  预期像素={w*h}")
                print(f"  RLE数据大小={size-5}")
                
                # 分析RLE控制字节
                rle_data = res_data[5:]
                if len(rle_data) > 0:
                    print(f"  前10个RLE控制字节:")
                    for k in range(min(10, len(rle_data))):
                        ctrl = rle_data[k]
                        bit7 = (ctrl >> 7) & 1
                        bit6 = (ctrl >> 6) & 1
                        count = (ctrl & 0x3F) + 1
                        
                        if bit7 == 0 and bit6 == 0:
                            op = "FILL"
                        elif bit7 == 0 and bit6 == 1:
                            op = "COPY_SPEC"
                        elif bit7 == 1 and bit6 == 0:
                            op = "COPY_STD"
                        else:
                            op = "SKIP"
                        
                        print(f"    [{k}] 0x{ctrl:02x} ({op}, count={count})")
