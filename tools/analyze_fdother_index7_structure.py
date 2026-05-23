#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引7的tile数据结构

目标：
1. 确认魔术字节
2. 确认tile数量
3. 分析前20个tile的宽高
4. 确认是否未压缩
5. 特别关注tile 1-17（窗口边框用）的宽高是否接近16x16

根据已有分析：
- 索引7数据大小: 768字节
- 前42字节可能是3字节LE偏移表（14个偏移，定义7个image）
- 偏移6开始有3字节LE值：08, 0D, 11, 16, 1A, 1F...
"""

import struct
import sys
import os

def analyze_fdother_index7(dat_path, output_dir):
    """分析FDOTHER.DAT索引7的数据结构"""
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "fdother_index7_analysis.txt")
    
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    
    lines = []
    
    def log(msg=""):
        print(msg)
        lines.append(msg)
    
    log("="*80)
    log("FDOTHER.DAT 索引7 数据结构详细分析")
    log("="*80)
    
    # 1. 验证DAT文件头
    log("\n【1. DAT文件头验证】")
    magic = dat_data[0:6]
    log(f"文件魔术字节: {magic} ({' '.join(f'{b:02X}' for b in magic)})")
    
    resource_count = struct.unpack('<I', dat_data[6:10])[0]
    log(f"资源数量: {resource_count}")
    
    # 2. 读取索引7的偏移
    log("\n【2. 索引7偏移信息】")
    offset_table_start = 10
    index7_offset = struct.unpack('<I', dat_data[offset_table_start + 7*4:offset_table_start + 7*4 + 4])[0]
    
    if 8 < resource_count:
        index8_offset = struct.unpack('<I', dat_data[offset_table_start + 8*4:offset_table_start + 8*4 + 4])[0]
        index7_size = index8_offset - index7_offset
    else:
        index7_size = len(dat_data) - index7_offset
    
    log(f"索引7起始偏移: {index7_offset} (0x{index7_offset:X})")
    log(f"索引7数据大小: {index7_size} 字节")
    
    # 3. 读取索引7数据并完整hex dump
    index7_data = dat_data[index7_offset:index7_offset + index7_size]
    
    log("\n【3. 索引7完整数据(hex dump前128字节)】")
    for i in range(0, min(128, len(index7_data)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in index7_data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in index7_data[i:i+16])
        log(f"  {i:04X}: {hex_str:<48s}  {ascii_str}")
    
    # 4. 尝试不同格式解析
    log("\n【4. 多种格式解析尝试】")
    
    # 假设1: 3字节偏移表从偏移0开始（14个偏移定义7个image）
    log("\n假设1: 3字节偏移表从偏移0开始")
    offsets_3byte_0 = []
    for i in range(14):
        pos = i * 3
        if pos + 3 <= len(index7_data):
            offset = index7_data[pos] | (index7_data[pos+1] << 8) | (index7_data[pos+2] << 16)
            offsets_3byte_0.append(offset)
            log(f"  偏移[{i:2d}] = {offset:5d} (0x{offset:04X})")
    
    # 检查image对
    log("\n  Image对(start, end, size):")
    images_1 = []
    for i in range(7):
        start = offsets_3byte_0[i*2]
        end = offsets_3byte_0[i*2+1] if i*2+1 < len(offsets_3byte_0) else len(index7_data)
        size = end - start
        images_1.append((start, end, size))
        log(f"    Image {i}: start={start:3d}, end={end:3d}, size={size:3d}")
        
        # 解析image数据
        if start < len(index7_data) and end <= len(index7_data) and size > 0:
            img_data = index7_data[start:end]
            log(f"      数据(hex): {' '.join(f'{b:02X}' for b in img_data[:min(20, len(img_data))])}")
            
            # 尝试不同宽高解析
            if len(img_data) >= 4:
                w_le16 = struct.unpack('<H', img_data[0:2])[0]
                h_le16 = struct.unpack('<H', img_data[2:4])[0]
                log(f"      作为[WORD宽,WORD高](LE): 宽={w_le16}, 高={h_le16}, 预期像素={w_le16*h_le16}")
                
                # 尝试[BYTE宽, BYTE高]
                w_u8 = img_data[0]
                h_u8 = img_data[1]
                log(f"      作为[BYTE宽,BYTE高]: 宽={w_u8}, 高={h_u8}, 预期像素={w_u8*h_u8}")
                
                # 检查是否是RLE压缩
                if len(img_data) > 4:
                    pixel_data = img_data[4:]
                    log(f"      像素数据({len(pixel_data)}字节): {list(pixel_data[:20])}")
    
    # 假设2: 偏移表从偏移6开始（跳过前6字节头部）
    log("\n假设2: 3字节偏移表从偏移6开始")
    offsets_3byte_6 = []
    for i in range(12):
        pos = 6 + i * 3
        if pos + 3 <= len(index7_data):
            offset = index7_data[pos] | (index7_data[pos+1] << 8) | (index7_data[pos+2] << 16)
            offsets_3byte_6.append(offset)
            log(f"  偏移[{i:2d}] = {offset:5d} (0x{offset:04X})")
    
    # 假设3: 4字节偏移表（根据IDA公式：*(DWORD *)(FDOTHER_DAT__7 + 4*tile_index + 6)）
    log("\n假设3: 4字节DWORD偏移表从偏移6开始")
    offsets_4byte_6 = []
    for i in range(10):
        pos = 6 + i * 4
        if pos + 4 <= len(index7_data):
            offset = struct.unpack('<I', index7_data[pos:pos+4])[0]
            offsets_4byte_6.append(offset)
            log(f"  偏移[{i:2d}] = {offset:10d} (0x{offset:08X})")
    
    # 假设4: 2字节偏移表
    log("\n假设4: 2字节WORD偏移表从偏移6开始")
    offsets_2byte_6 = []
    for i in range(20):
        pos = 6 + i * 2
        if pos + 2 <= len(index7_data):
            offset = struct.unpack('<H', index7_data[pos:pos+2])[0]
            offsets_2byte_6.append(offset)
            log(f"  偏移[{i:2d}] = {offset:5d} (0x{offset:04X})")
    
    # 5. 分析前6字节的含义
    log("\n【5. 前6字节分析】")
    log(f"  字节0-5: {' '.join(f'{b:02X}' for b in index7_data[0:6])}")
    log(f"  作为2个WORD: {struct.unpack('<H', index7_data[0:2])[0]}, {struct.unpack('<H', index7_data[2:4])[0]}")
    log(f"  字节4-5作为WORD: {struct.unpack('<H', index7_data[4:6])[0]}")
    log(f"  作为3个WORD: {struct.unpack('<H', index7_data[0:2])[0]}, {struct.unpack('<H', index7_data[2:4])[0]}, {struct.unpack('<H', index7_data[4:6])[0]}")
    
    # 6. 对比其他已知索引的格式
    log("\n【6. 与其他索引格式对比】")
    
    # 检查索引4（字体，已知格式）
    if resource_count > 4:
        index4_offset = struct.unpack('<I', dat_data[offset_table_start + 4*4:offset_table_start + 4*4 + 4])[0]
        index5_offset = struct.unpack('<I', dat_data[offset_table_start + 5*4:offset_table_start + 5*4 + 4])[0]
        index4_size = index5_offset - index4_offset
        index4_data = dat_data[index4_offset:index4_offset + index4_size]
        
        log(f"  索引4（字体）: 偏移={index4_offset}, 大小={index4_size}字节")
        log(f"    前16字节: {' '.join(f'{b:02X}' for b in index4_data[:16])}")
    
    # 检查索引5
    if resource_count > 5:
        index6_offset = struct.unpack('<I', dat_data[offset_table_start + 6*4:offset_table_start + 6*4 + 4])[0]
        index5_size = index6_offset - index5_offset
        index5_data = dat_data[index5_offset:index5_offset + index5_size]
        
        log(f"  索引5: 偏移={index5_offset}, 大小={index5_size}字节")
        log(f"    前16字节: {' '.join(f'{b:02X}' for b in index5_data[:16])}")
    
    # 7. 尝试解析为tile集（使用假设1的偏移）
    log("\n【7. Tile解析（使用假设1的7个image）】")
    
    tile_info = []
    for i, (start, end, size) in enumerate(images_1):
        if start >= len(index7_data) or end > len(index7_data) or size < 4:
            log(f"  Tile {i}: 数据不足 (start={start}, end={end}, size={size})")
            continue
        
        # 尝试解析宽高
        w_le16 = struct.unpack('<H', index7_data[start:start+2])[0]
        h_le16 = struct.unpack('<H', index7_data[start+2:start+4])[0]
        
        expected_pixels = w_le16 * h_le16
        actual_pixels = size - 4
        
        is_valid = (expected_pixels == actual_pixels or expected_pixels == 0)
        
        tile_info.append({
            'index': i,
            'offset': start,
            'width': w_le16,
            'height': h_le16,
            'size': size,
            'expected_pixels': expected_pixels,
            'actual_pixels': actual_pixels,
            'is_valid': is_valid
        })
        
        log(f"  Tile {i}: 偏移={start:3d}, 宽={w_le16:5d}, 高={h_le16:5d}, "
            f"数据={size:3d}字节, 预期像素={expected_pixels:6d}, 实际像素={actual_pixels:3d}, "
            f"有效={is_valid}")
        
        # 显示像素数据
        if size > 4:
            pixel_data = index7_data[start+4:end]
            log(f"    像素数据({len(pixel_data)}字节): {list(pixel_data[:20])}")
    
    # 8. 总结
    log("\n【8. 分析总结】")
    log(f"1. 魔术字节: 索引7没有独立的魔术字节")
    log(f"2. Tile数量: {len(images_1)} 个（根据3字节偏移表假设）")
    log(f"3. 数据大小: {index7_size} 字节（非常小，不可能是17个16x16未压缩tile）")
    log(f"4. Tile宽高: 解析结果异常，可能需要不同的格式解释")
    log(f"5. 压缩状态: 数据量太小，可能是RLE压缩或其他格式")
    log(f"6. 关键发现: 768字节无法容纳17个16x16的未压缩tile（需要17*260=4420字节）")
    log(f"   - 如果是16x16 tile，必须使用RLE压缩")
    log(f"   - 或者tile尺寸远小于16x16")
    log(f"   - 或者窗口边框tile在其他索引中")
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    log(f"\n分析结果已保存到: {output_file}")


if __name__ == '__main__':
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"文件不存在: {dat_path}")
        sys.exit(1)
    
    output_dir = 'output'
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    analyze_fdother_index7(dat_path, output_dir)
