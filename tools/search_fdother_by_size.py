#!/usr/bin/env python3
"""搜索FDOTHER.DAT中符合特定尺寸范围的资源"""

import struct
import sys

def search_fdother_by_size():
    """解析FDOTHER.DAT并搜索指定尺寸范围的资源"""
    
    with open('game/FDOTHER.DAT', 'rb') as f:
        data = f.read()
    
    print(f"FDOTHER.DAT 总大小: {len(data)} 字节")
    print()
    
    # 解析资源偏移表（从偏移6开始，每项4字节）
    print("=== 解析资源偏移表 ===")
    
    target_results = []
    all_valid_images = []
    
    for idx in range(500):  # 检查最多500个资源索引
        offset = 6 + idx * 4
        if offset + 4 > len(data):
            break
        
        rel_offset = struct.unpack('<I', data[offset:offset+4])[0]
        
        if rel_offset > 0 and rel_offset < len(data):
            # 尝试读取宽高
            if rel_offset + 4 <= len(data):
                w = struct.unpack('<H', data[rel_offset:rel_offset+2])[0]
                h = struct.unpack('<H', data[rel_offset+2:rel_offset+4])[0]
                
                # 记录所有看起来合理的图像资源
                if w > 0 and w < 2000 and h > 0 and h < 2000:
                    all_valid_images.append((idx, rel_offset, w, h))
                    
                    # 检查是否在目标范围内
                    if 300 <= w <= 320 and 80 <= h <= 100:
                        target_results.append((idx, rel_offset, w, h))
    
    print(f"总共找到 {len(all_valid_images)} 个有效的图像资源")
    print()
    
    # 输出目标范围内的资源
    print(f"=== 目标搜索结果：宽度300-320，高度80-100 ===")
    if target_results:
        for idx, offset, w, h in target_results:
            print(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}")
    else:
        print("未找到精确匹配的资源")
    
    print()
    
    # 输出所有宽度在300-320之间的资源
    print(f"=== 宽度在300-320之间的所有资源 ===")
    width_matches = [(idx, offset, w, h) for idx, offset, w, h in all_valid_images if 300 <= w <= 320]
    if width_matches:
        for idx, offset, w, h in width_matches:
            print(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}")
    else:
        print("未找到宽度在300-320之间的资源")
    
    print()
    
    # 输出接近310x86的资源（正负10像素误差）
    print(f"=== 接近310x86的资源（正负10像素） ===")
    close_matches = [(idx, offset, w, h) for idx, offset, w, h in all_valid_images 
                     if abs(w - 310) <= 10 and abs(h - 86) <= 10]
    if close_matches:
        for idx, offset, w, h in close_matches:
            print(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}")
    else:
        print("未找到接近310x86的资源")
    
    print()
    
    # 输出前30个有效资源作为参考
    print(f"=== 前30个有效资源参考 ===")
    for idx, offset, w, h in all_valid_images[:30]:
        print(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}")
    
    print()
    
    # 保存完整输出到文件
    output_file = 'output/parse_fdother_full.txt'
    import os
    os.makedirs('output', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"FDOTHER.DAT 解析完整输出\n")
        f.write(f"文件大小: {len(data)} 字节\n")
        f.write(f"有效图像资源总数: {len(all_valid_images)}\n\n")
        
        f.write(f"=== 所有有效图像资源 ===\n")
        for idx, offset, w, h in all_valid_images:
            f.write(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}\n")
        
        f.write(f"\n=== 目标搜索结果：宽度300-320，高度80-100 ===\n")
        if target_results:
            for idx, offset, w, h in target_results:
                f.write(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}\n")
        else:
            f.write("未找到精确匹配的资源\n")
        
        f.write(f"\n=== 宽度在300-320之间的所有资源 ===\n")
        if width_matches:
            for idx, offset, w, h in width_matches:
                f.write(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}\n")
        else:
            f.write("未找到宽度在300-320之间的资源\n")
        
        f.write(f"\n=== 接近310x86的资源（正负10像素） ===\n")
        if close_matches:
            for idx, offset, w, h in close_matches:
                f.write(f"资源索引 {idx:3d}: 偏移 {offset:6d} (0x{offset:06X}), 尺寸 {w}x{h}\n")
        else:
            f.write("未找到接近310x86的资源\n")
    
    print(f"完整输出已保存到: {output_file}")

if __name__ == '__main__':
    search_fdother_by_size()
