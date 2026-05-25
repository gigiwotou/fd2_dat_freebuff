"""验证FDOTHER.DAT索引5的tile数据是否正确"""
import struct

FDOTHER_PATH = "game/FDOTHER.DAT"

def verify_tile():
    with open(FDOTHER_PATH, 'rb') as f:
        f.seek(0)
        header = f.read(6)
        f.seek(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        # 索引5
        f.seek(10 + 5 * 4)
        offset = struct.unpack('<I', f.read(4))[0]
        end = struct.unpack('<I', f.read(4))[0]
        
        f.seek(offset)
        data = f.read(end - offset)
        
        print(f"FDOTHER.DAT索引5:")
        print(f"  偏移: {offset}, 大小: {len(data)} 字节")
        print(f"  前20字节hex: {data[:20].hex()}")
        
        # RLE解压
        rle_data = data[20:]
        pixel_count = 20 * 16 * 16
        decoded = bytearray()
        i = 0
        j = 0
        while i < len(rle_data) and j < pixel_count:
            byte = rle_data[i]
            i += 1
            if byte >= 0xC0:
                if i < len(rle_data):
                    count_val = byte & 0x3F
                    if count_val == 0: count_val = 64
                    value = rle_data[i]
                    i += 1
                    for _ in range(count_val):
                        if j < pixel_count:
                            decoded.append(value)
                            j += 1
            else:
                decoded.append(byte)
                j += 1
        
        print(f"\nRLE解压结果:")
        print(f"  解码像素: {len(decoded)} (期望 {pixel_count})")
        
        # 分析调色板使用情况
        palette_counts = {}
        for p in decoded:
            palette_counts[p] = palette_counts.get(p, 0) + 1
        
        print(f"  唯一调色板索引: {len(palette_counts)}")
        print(f"  调色板统计:")
        for pal, count in sorted(palette_counts.items()):
            if count > 10:
                print(f"    索引{pal}: {count}像素")
        
        # 检查每个tile的调色板分布
        print(f"\n每个tile的调色板分析:")
        for t in range(20):
            tile_data = decoded[t * 256:(t+1) * 256]
            tile_pals = {}
            for p in tile_data:
                tile_pals[p] = tile_pals.get(p, 0) + 1
            non_zero = sum(v for k, v in tile_pals.items() if k != 0)
            total_nonzero = sum(1 for k in tile_pals if k != 0)
            print(f"  Tile {t}: {total_nonzero}种颜色, {non_zero}个非零像素")

if __name__ == "__main__":
    verify_tile()
