#!/usr/bin/env python3
"""
分析FDOTHER中哪些索引是调色板资源

根据之前的分析，已知调色板索引:
- 索引0: 主调色板 (768字节)
- 索引8: 调色板副本
- 索引57: 调色板副本
- 索引76: 标题画面调色板
- 索引99: 调色板副本
- 索引101: 调色板副本
- 索引102: 调色板副本

游戏可能:
1. 所有资源都使用索引0的主调色板
2. 某些资源使用特定的调色板（如全屏图像使用专用调色板）
3. 资源本身包含调色板信息（palette_window就是索引）
"""

import struct
import os

dat_path = 'bin/FDOTHER.DAT'

with open(dat_path, 'rb') as f:
    # 读取所有索引
    table_offset = 6
    resources = []
    
    while True:
        f.seek(table_offset)
        data = f.read(4)
        if len(data) < 4:
            break
        
        offset = struct.unpack('<I', data)[0]
        if offset == 0 or offset > os.path.getsize(dat_path):
            break
        
        # 读取下一个偏移
        f.seek(table_offset + 4)
        next_data = f.read(4)
        next_offset = struct.unpack('<I', next_data)[0] if len(next_data) >= 4 else os.path.getsize(dat_path)
        
        size = next_offset - offset
        
        # 读取资源头部
        f.seek(offset)
        header = f.read(min(size, 20))
        
        res_info = {
            'index': len(resources),
            'offset': offset,
            'size': size,
            'header': header
        }
        
        # 识别类型
        if size == 768:
            res_info['type'] = 'PALETTE'
        elif header[:4] == b'LMI1':
            res_info['type'] = 'LMI1'
        elif header[:6] == b'LLLLLL':
            res_info['type'] = 'NESTED'
        elif size >= 4:
            w = struct.unpack('<H', header[0:2])[0] if len(header) >= 2 else 0
            h = struct.unpack('<H', header[2:4])[0] if len(header) >= 4 else 0
            if w > 0 and w <= 640 and h > 0 and h <= 480:
                res_info['type'] = 'TILE'
                res_info['width'] = w
                res_info['height'] = h
                res_info['palette_window'] = header[4] if size >= 5 else 0
            else:
                res_info['type'] = 'RAW'
        else:
            res_info['type'] = 'RAW'
        
        resources.append(res_info)
        table_offset += 4
    
    print("="*70)
    print("调色板资源列表")
    print("="*70)
    
    for res in resources:
        if res['type'] == 'PALETTE':
            print(f"索引{res['index']}: PALETTE, 大小={res['size']}")
    
    print("\n" + "="*70)
    print("TILE资源的palette_window值分布")
    print("="*70)
    
    palette_windows = {}
    for res in resources:
        if res['type'] == 'TILE':
            pw = res['palette_window']
            if pw not in palette_windows:
                palette_windows[pw] = []
            palette_windows[pw].append(res['index'])
    
    for pw in sorted(palette_windows.keys()):
        indices = palette_windows[pw]
        print(f"\npalette_window={pw}: 共{len(indices)}个资源")
        print(f"  索引: {indices[:20]}{'...' if len(indices) > 20 else ''}")
    
    print("\n" + "="*70)
    print("分析：palette_window可能是调色板索引偏移")
    print("="*70)
    
    # 检查palette_window是否对应已知的调色板索引
    palette_indices = [res['index'] for res in resources if res['type'] == 'PALETTE']
    print(f"已知调色板索引: {palette_indices}")
    
    for pw in sorted(palette_windows.keys())[:10]:
        if pw in palette_indices:
            print(f"palette_window={pw} -> 直接使用调色板索引{pw}")
        else:
            # 检查是否是相对于索引0的偏移
            actual_pal_idx = pw
            if actual_pal_idx in palette_indices:
                print(f"palette_window={pw} -> 调色板索引{actual_pal_idx}")
            else:
                print(f"palette_window={pw} -> 不是调色板索引（可能只是颜色偏移值）")
