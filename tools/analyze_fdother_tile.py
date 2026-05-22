"""分析FDOTHER.DAT索引5对话框tile资源"""
import struct
import sys

FDOTHER_PATH = "game/FDOTHER.DAT"

def load_resource(dat_path, index):
    """加载FDOTHER.DAT指定索引的资源"""
    with open(dat_path, 'rb') as f:
        f.seek(0)
        header = f.read(6)
        print(f"文件头: {header.hex()}")
        
        f.seek(6)
        count_bytes = f.read(4)
        count = struct.unpack('<I', count_bytes)[0]
        print(f"资源总数: {count}")
        
        offset_pos = 10 + index * 4
        f.seek(offset_pos)
        offset_bytes = f.read(4)
        offset = struct.unpack('<I', offset_bytes)[0]
        
        f.seek(offset_pos + 4)
        end_bytes = f.read(4)
        end_offset = struct.unpack('<I', end_bytes)[0]
        
        size = end_offset - offset
        print(f"\n索引{index}:")
        print(f"  偏移: {offset} (0x{offset:X})")
        print(f"  结束偏移: {end_offset} (0x{end_offset:X})")
        print(f"  大小: {size} 字节")
        
        f.seek(offset)
        data = f.read(size)
        return data

def rle_decode(data, max_pixels):
    """RLE解压FD2格式"""
    result = bytearray()
    i = 0
    j = 0
    
    while i < len(data) and j < max_pixels:
        byte = data[i]
        i += 1
        
        if byte >= 0xC0:
            if i < len(data):
                count = byte & 0x3F
                if count == 0:
                    count = 64
                value = data[i]
                i += 1
                for _ in range(count):
                    if j < max_pixels:
                        result.append(value)
                        j += 1
        else:
            result.append(byte)
            j += 1
    
    return bytes(result)

def analyze_tile_resource(data):
    """分析tile资源结构"""
    print(f"\n=== 分析tile资源结构 ===")
    print(f"资源大小: {len(data)} 字节")
    print(f"前64字节hex: {data[:64].hex()}")
    
    if len(data) > 20:
        print(f"\n检查前20字节:")
        for i in range(0, 20, 4):
            val = struct.unpack('<I', data[i:i+4])[0]
            print(f"  偏移{i}: 0x{val:X} ({val})")
        
        w = struct.unpack('<h', data[16:18])[0]
        h = struct.unpack('<h', data[18:20])[0]
        print(f"\n如果格式类似DATO (16-18=width, 18-20=height):")
        print(f"  宽度: {w}")
        print(f"  高度: {h}")
        
        # RLE解压像素数据
        pixel_data = data[20:]
        max_pixels = 256  # 16*16 = 256 (假设是tile集合)
        
        decoded = rle_decode(pixel_data, max_pixels * 20)  # 假设最多20个tile
        print(f"\nRLE解码结果: {len(decoded)} 像素")
        
        # 分析解码后的数据
        non_zero = sum(1 for b in decoded if b != 0)
        unique_values = len(set(decoded))
        print(f"  非零像素: {non_zero}")
        print(f"  唯一值数量: {unique_values}")
        print(f"  前32字节: {decoded[:32].hex()}")
        
        # 检查是否是多个tile
        if len(decoded) > 0:
            tile_count = len(decoded) // 256
            remaining = len(decoded) % 256
            print(f"\n  可能的tile数量: {tile_count} (剩余{remaining}像素)")
            
            # 如果是整数个tile
            if remaining == 0 and tile_count > 0:
                print(f"  确认是{tile_count}个16x16 tile")
                # 保存解码后的数据
                with open("output/fdother_index5_decoded.bin", "wb") as f:
                    f.write(decoded)
                print(f"  解码数据已保存: output/fdother_index5_decoded.bin")
                
                # 打印每个tile的前16字节
                for t in range(min(tile_count, 5)):
                    tile_start = t * 256
                    tile_preview = decoded[tile_start:tile_start+16]
                    print(f"  Tile {t}: {tile_preview.hex()}")

if __name__ == "__main__":
    try:
        print("分析FDOTHER.DAT索引5（对话框tile资源）")
        data = load_resource(FDOTHER_PATH, 5)
        analyze_tile_resource(data)
        
        with open("output/fdother_index5_raw.bin", "wb") as f:
            f.write(data)
        print(f"\n原始数据已保存: output/fdother_index5_raw.bin")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
