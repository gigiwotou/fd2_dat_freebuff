"""
紧急诊断：分析FDOTHER索引5的tile数据格式和RLE解压
直接查看前17个tile的原始数据和解压后数据
"""

import struct
import sys

def analyze_rle_control_byte(byte_val):
    """分析RLE控制字节"""
    if byte_val >= 0x80:
        count = byte_val & 0x7F
        return f"REPEAT: count={count}, pixel follows"
    else:
        return f"COPY: count={byte_val}"

def hex_dump(data, offset=0, length=64):
    """十六进制转储"""
    result = []
    for i in range(0, min(length, len(data)), 16):
        hex_part = ' '.join(f'{b:02X}' for b in data[offset+i:offset+i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset+i:offset+i+16])
        result.append(f"  {offset+i:04X}: {hex_part:<48} {ascii_part}")
    return '\n'.join(result)

def analyze_fdother_index5(fdother_path):
    with open(fdother_path, 'rb') as f:
        # 读取DAT头部
        magic = f.read(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        # 读取偏移表
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        if len(offsets) <= 5:
            print("索引5不存在")
            return
        
        # 获取索引5的数据
        start = offsets[5]
        end = offsets[6] if len(offsets) > 6 else None
        
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(start)
            data = f.read(file_size - start)
        
        print(f"FDOTHER索引5数据:")
        print(f"  大小: {len(data)} 字节")
        print(f"  头部前16字节: {hex_dump(data, 0, 16)}")
        
        # 解析头部
        if len(data) < 6:
            print("数据太小")
            return
        
        total_w = struct.unpack('<H', data[0:2])[0]
        total_h = struct.unpack('<H', data[2:4])[0]
        tile_count = struct.unpack('<H', data[4:6])[0]
        
        print(f"\nTile集头部:")
        print(f"  总宽度: {total_w}")
        print(f"  总高度: {total_h}")
        print(f"  Tile数量: {tile_count}")
        
        # 分析前17个tile
        print(f"\n=== 前17个Tile详细分析 ===\n")
        
        for i in range(min(17, tile_count)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                print(f"Tile {i}: 偏移表超出范围")
                break
            
            tile_offset = struct.unpack('<I', data[offset_addr:offset_addr+4])[0]
            print(f"\n--- Tile {i} ---")
            print(f"  偏移表位置: 0x{offset_addr:X}")
            print(f"  Tile数据偏移: 0x{tile_offset:X} ({tile_offset})")
            
            if tile_offset + 4 > len(data):
                print(f"  错误: tile偏移超出数据范围")
                continue
            
            # 读取tile头部
            w = struct.unpack('<H', data[tile_offset:tile_offset+2])[0]
            h = struct.unpack('<H', data[tile_offset+2:tile_offset+4])[0]
            
            print(f"  宽度: {w}")
            print(f"  高度: {h}")
            print(f"  预期解压大小: {w * h} 字节")
            
            # 计算压缩数据大小
            next_offset = struct.unpack('<I', data[offset_addr+4:offset_addr+8])[0] if i+1 < tile_count else len(data)
            compressed_size = next_offset - tile_offset
            pixel_data_size = compressed_size - 4
            
            print(f"  压缩数据大小: {compressed_size} 字节")
            print(f"  像素数据大小: {pixel_data_size} 字节")
            
            # 分析RLE控制字节
            if pixel_data_size > 0:
                pixel_start = tile_offset + 4
                print(f"\n  像素数据前32字节 (RLE压缩):")
                print(hex_dump(data, pixel_start, 32))
                
                print(f"\n  RLE控制字节分析:")
                pos = pixel_start
                count = 0
                while pos < pixel_start + 32 and pos < len(data) and count < 10:
                    control = data[pos]
                    print(f"    0x{pos-tile_offset-4:02X}: {analyze_rle_control_byte(control)}")
                    pos += 1
                    if control >= 0x80:
                        pos += 1  # 跳过像素值
                    else:
                        pos += control  # 跳过复制的字节
                    count += 1
                
                # 尝试简单RLE解压前几个字节
                print(f"\n  尝试RLE解压前{w*h}字节:")
                try:
                    decompressed = bytearray()
                    pos = pixel_start
                    src_end = pixel_start + pixel_data_size
                    while pos < src_end and len(decompressed) < w * h:
                        if pos >= len(data):
                            break
                        control = data[pos]
                        pos += 1
                        
                        if control >= 0x80:
                            # REPEAT
                            count = control & 0x7F
                            if pos >= len(data):
                                break
                            pixel = data[pos]
                            pos += 1
                            decompressed.extend([pixel] * count)
                        else:
                            # COPY
                            count = control
                            if pos + count > len(data):
                                count = len(data) - pos
                            decompressed.extend(data[pos:pos+count])
                            pos += count
                    
                    print(f"    解压成功: {len(decompressed)} 字节")
                    print(f"    前16字节: {' '.join(f'{b:02X}' for b in decompressed[:16])}")
                    
                    # 检查是否有明显的图案
                    unique_colors = set(decompressed[:min(64, len(decompressed))])
                    print(f"    前64字节中的独特颜色: {len(unique_colors)} 种")
                    print(f"    颜色值: {sorted(list(unique_colors))[:10]}")
                    
                except Exception as e:
                    print(f"    解压失败: {e}")
            
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    analyze_fdother_index5(sys.argv[1])
