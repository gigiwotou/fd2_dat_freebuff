#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引5的数据结构
目标：
1. 确认魔术字节（LLLLLL还是LMI1）
2. 分析头部格式
3. 确定tile偏移表位置
4. 提取前10个tile的宽高数据
"""

import struct
import sys
import os


def hex_dump(data, offset=0, length=64):
    """打印十六进制转储"""
    end = min(offset + length, len(data))
    for i in range(offset, end, 16):
        hex_part = ' '.join(f'{b:02X}' for b in data[i:min(i+16, end)])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:min(i+16, end)])
        print(f"  {i:08X}  {hex_part:<48s}  {ascii_part}")


def analyze_fdother_index5(dat_path):
    print("="*80)
    print("FDOTHER.DAT 索引5 数据结构分析")
    print("="*80)
    
    if not os.path.exists(dat_path):
        print(f"错误: 文件不存在 - {dat_path}")
        return
    
    file_size = os.path.getsize(dat_path)
    print(f"\n文件: {dat_path}")
    print(f"文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)")
    
    with open(dat_path, 'rb') as f:
        # ==================== 1. 分析文件头部魔术字节 ====================
        print("\n" + "="*80)
        print("1. 魔术字节分析")
        print("="*80)
        
        header_bytes = f.read(6)
        print(f"前6字节(十六进制): {' '.join(f'{b:02X}' for b in header_bytes)}")
        print(f"前6字节(ASCII):    {header_bytes.decode('ascii', errors='replace')}")
        
        # 检查是否是LLLLLL
        if header_bytes == b'LLLLLL':
            print("[OK] 魔术字节: LLLLLL (6个L)")
            magic_type = 'LLLLLL'
        # 检查是否是LMI1（前4字节）
        elif header_bytes[:4] == b'LMI1':
            print("[OK] 魔术字节: LMI1 (前4字节) + 其他")
            magic_type = 'LMI1'
        else:
            print("[ERR] 魔术字节: 未知格式")
            magic_type = 'UNKNOWN'
        
        # 查看前32字节
        f.seek(0)
        first_32 = f.read(32)
        print(f"\n文件头部前32字节:")
        hex_dump(first_32, 0, 32)
        
        # ==================== 2. 读取资源数量 ====================
        print("\n" + "="*80)
        print("2. DAT文件头部格式")
        print("="*80)
        
        # 文件指针回到魔术字节后的位置（偏移6）
        f.seek(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        print(f"资源数量: {resource_count}")
        
        # 头部总大小 = 6字节魔术 + 4字节资源数 = 10字节
        header_size = 10
        print(f"DAT头部大小: {header_size} 字节 (6魔术 + 4资源数)")
        
        # ==================== 3. 读取偏移表 ====================
        print("\n" + "="*80)
        print("3. 资源偏移表")
        print("="*80)
        
        offsets = []
        print(f"{'索引':<6} {'偏移(十进制)':<15} {'偏移(十六进制)':<15} {'大小估算'}")
        print("-" * 60)
        
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
            
            if i < 15:
                if i + 1 < len(offsets):
                    size = offsets[i+1] - offset
                    size_str = f"{size} 字节"
                else:
                    size_str = "待定"
                print(f"{i:<6} {offset:<15} 0x{offset:<13X} {size_str}")
            elif i == 15:
                print("  ...")
        
        # ==================== 4. 分析索引5的数据 ====================
        print("\n" + "="*80)
        print("4. 索引5 数据区分析")
        print("="*80)
        
        if len(offsets) <= 5:
            print("错误: 资源数量不足，无法访问索引5")
            return
        
        start_offset = offsets[5]
        end_offset = offsets[6] if len(offsets) > 6 else file_size
        index5_size = end_offset - start_offset
        
        print(f"起始偏移: {start_offset} (0x{start_offset:X})")
        print(f"结束偏移: {end_offset} (0x{end_offset:X})")
        print(f"数据区大小: {index5_size} 字节")
        
        # 读取索引5的数据
        f.seek(start_offset)
        index5_data = f.read(index5_size)
        
        # 显示索引5数据的前128字节
        print(f"\n索引5数据前128字节:")
        hex_dump(index5_data, 0, 128)
        
        # ==================== 5. 分析索引5头部格式 ====================
        print("\n" + "="*80)
        print("5. 索引5头部格式")
        print("="*80)
        
        if len(index5_data) < 8:
            print("错误: 数据区太小，无法解析头部")
            return
        
        # 索引5的实际结构：
        # offset 0-3: 魔术字节 "LMI1"
        # offset 4-5: tile数量 (WORD)
        # offset 6+: 偏移表 (DWORD数组)
        
        index5_magic = index5_data[0:4]
        print(f"索引5魔术字节: {index5_magic.decode('ascii', errors='replace')}")
        print(f"索引5魔术字节(HEX): {' '.join(f'{b:02X}' for b in index5_magic)}")
        
        tile_count = struct.unpack('<H', index5_data[4:6])[0]
        print(f"Tile数量: {tile_count} (0x{tile_count:X})")
        
        # ==================== 6. Tile偏移表分析 ====================
        print("\n" + "="*80)
        print("6. Tile偏移表位置")
        print("="*80)
        
        offset_table_start = 6  # 从第6字节开始
        print(f"偏移表起始位置: {offset_table_start} (紧接头部之后)")
        print(f"每个偏移占用: 4字节 (DWORD)")
        print(f"偏移表总大小: {tile_count * 4} 字节")
        print(f"偏移表结束位置: {offset_table_start + tile_count * 4}")
        
        # 显示前几个偏移值
        print(f"\n偏移表内容:")
        print(f"{'Tile索引':<10} {'偏移表位置':<12} {'偏移值(十进制)':<15} {'偏移值(十六进制)':<15}")
        print("-" * 60)
        
        tile_offsets = []
        for i in range(min(tile_count, 20)):
            pos = offset_table_start + i * 4
            if pos + 4 > len(index5_data):
                print(f"  警告: 偏移表超出数据区范围")
                break
            
            tile_offset = struct.unpack('<I', index5_data[pos:pos+4])[0]
            tile_offsets.append(tile_offset)
            
            print(f"{i:<10} {pos:<12} {tile_offset:<15} 0x{tile_offset:<13X}")
        
        if tile_count > 20:
            print(f"  ... (共{tile_count}个tile，仅显示前20个)")
        
        # ==================== 7. 前10个Tile的宽高数据 ====================
        print("\n" + "="*80)
        print("7. 前10个Tile的宽高数据")
        print("="*80)
        
        print(f"{'Tile索引':<10} {'偏移':<8} {'宽度':<8} {'高度':<8} {'像素数':<10} {'数据大小':<10} {'压缩?'}")
        print("-" * 70)
        
        for i in range(min(10, len(tile_offsets))):
            tile_offset = tile_offsets[i]
            
            if tile_offset + 4 > len(index5_data):
                print(f"{i:<10} {tile_offset:<8} [超出数据区范围]")
                continue
            
            # 读取tile的宽高
            w = struct.unpack('<H', index5_data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', index5_data[tile_offset+2:tile_offset+4])[0]
            pixel_count = w * h
            
            # 计算tile数据大小（到下一个tile的距离）
            if i + 1 < len(tile_offsets):
                tile_data_size = tile_offsets[i+1] - tile_offset
            else:
                tile_data_size = len(index5_data) - tile_offset
            
            # 判断是否压缩
            pixel_data_size = tile_data_size - 4  # 减去4字节头部
            if pixel_data_size == pixel_count:
                compression = "否(原始)"
            elif pixel_data_size < pixel_count:
                compression = f"是({pixel_data_size}<{pixel_count})"
            else:
                compression = f"是({pixel_data_size}>{pixel_count})"
            
            print(f"{i:<10} {tile_offset:<8} {w:<8} {h:<8} {pixel_count:<10} {tile_data_size:<10} {compression}")
            
            # 显示tile头部的前16字节
            if tile_offset + 4 < len(index5_data):
                header_bytes = index5_data[tile_offset:tile_offset+20]
                print(f"           头部字节: {' '.join(f'{b:02X}' for b in header_bytes[:16])}")
        
        # ==================== 8. 详细分析前3个tile ====================
        print("\n" + "="*80)
        print("8. 前3个Tile详细分析")
        print("="*80)
        
        for i in range(min(3, len(tile_offsets))):
            tile_offset = tile_offsets[i]
            
            if tile_offset + 4 > len(index5_data):
                continue
            
            w = struct.unpack('<H', index5_data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', index5_data[tile_offset+2:tile_offset+4])[0]
            pixel_count = w * h
            
            if i + 1 < len(tile_offsets):
                tile_data_size = tile_offsets[i+1] - tile_offset
            else:
                tile_data_size = len(index5_data) - tile_offset
            
            pixel_data_size = tile_data_size - 4
            
            print(f"\nTile {i}:")
            print(f"  位置: 0x{tile_offset:X} ({tile_offset})")
            print(f"  宽度: {w}")
            print(f"  高度: {h}")
            print(f"  总像素: {pixel_count}")
            print(f"  数据大小: {tile_data_size} 字节")
            print(f"  像素数据: {pixel_data_size} 字节")
            
            if pixel_data_size == pixel_count:
                print(f"  压缩状态: 未压缩 (像素数据大小 = w*h)")
            else:
                compression_ratio = pixel_count / pixel_data_size if pixel_data_size > 0 else 0
                print(f"  压缩状态: RLE压缩 (压缩比: {compression_ratio:.2f}:1)")
            
            # 显示像素数据的前32字节
            pixel_start = tile_offset + 4
            pixel_end = min(pixel_start + 32, len(index5_data))
            pixel_bytes = index5_data[pixel_start:pixel_end]
            
            print(f"  像素数据前32字节:")
            for j in range(0, len(pixel_bytes), 16):
                chunk = pixel_bytes[j:j+16]
                hex_part = ' '.join(f'{b:02X}' for b in chunk)
                print(f"    +{j:3d}: {hex_part}")
        
        # ==================== 9. 总结 ====================
        print("\n" + "="*80)
        print("9. 分析总结")
        print("="*80)
        
        print(f"""
DAT文件结构:
  魔术字节: {magic_type}
  头部格式: 6字节魔术 + 4字节资源数量 + N*4字节偏移表
  
索引5结构:
  头部: 6字节
    - [0-3]: 魔术字节 "LMI1"
    - [4-5]: Tile数量 = {tile_count}
  
  Tile偏移表: 从偏移6开始，每个tile占用4字节(DWORD)
    - 共{tile_count}个tile
    - 偏移表范围: [6, {6 + tile_count * 4})
  
  Tile数据: 每个tile包含4字节头部(w,h) + RLE像素数据
    - 头部: 2字节宽度 + 2字节高度
    - RLE像素数据: 使用RLE压缩格式

前10个Tile尺寸:
""")
        
        for i in range(min(10, len(tile_offsets))):
            tile_offset = tile_offsets[i]
            if tile_offset + 4 > len(index5_data):
                continue
            w = struct.unpack('<H', index5_data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', index5_data[tile_offset+2:tile_offset+4])[0]
            print(f"  Tile {i}: {w} x {h}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    dat_path = 'bin/FDOTHER.DAT'
    if len(sys.argv) > 1:
        dat_path = sys.argv[1]
    
    if not os.path.exists(dat_path):
        print(f"错误: 文件不存在 - {dat_path}")
        sys.exit(1)
    
    analyze_fdother_index5(dat_path)
