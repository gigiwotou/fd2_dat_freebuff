#!/usr/bin/env python3
"""详细分析所有索引的TILE结构"""
import struct
import os

def main():
    dat_path = 'game/FDOTHER.DAT'
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # 解析索引表
    offsets = []
    offset = 6
    while offset + 4 <= len(data):
        off = struct.unpack_from('<I', data, offset)[0]
        if off == 0 or off >= len(data):
            break
        offsets.append(off)
        offset += 4
    offsets.append(len(data))
    
    print(f"总索引数: {len(offsets)-1}")
    
    # 分析前5个索引
    for idx in range(min(5, len(offsets)-1)):
        res_start = offsets[idx]
        res_end = offsets[idx+1]
        res_data = data[res_start:res_end]
        
        print(f"\n{'='*60}")
        print(f"索引{idx}: 偏移={res_start}, 大小={len(res_data)}")
        print(f"前32字节: {' '.join(f'{b:02X}' for b in res_data[:32])}")
        
        # 尝试解析头部
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        
        print(f"  解析头部: {w}x{h}")
        
        if w > 640 or h > 480 or w == 0 or h == 0:
            print(f"  -> 宽高异常，可能不是普通TILE")
        else:
            print(f"  -> 宽高合理，是普通TILE")
            
            # 检查头部大小
            if len(res_data) >= 8 and res_data[5] != 0:
                header_size = 8
                palette_window = struct.unpack_from('<H', res_data, 4)[0]
                print(f"  -> 8字节头，调色板窗口={palette_window}")
            else:
                header_size = 5
                palette_window = res_data[4]
                print(f"  -> 5字节头，调色板窗口={palette_window}")
            
            # RLE数据
            rle_data = res_data[header_size:]
            print(f"  -> RLE数据大小: {len(rle_data)}")
            print(f"  -> RLE前16字节: {' '.join(f'{b:02X}' for b in rle_data[:16])}")

if __name__ == '__main__':
    main()
