"""分析tile调色板 - 找出正确的颜色映射"""
import struct
from PIL import Image

FDOTHER_PATH = "game/FDOTHER.DAT"

# 6-bit调色板值转RGB
def pal6_to_rgb(v6):
    v8 = (v6 << 2) | (v6 >> 4)
    return (v8, v8, v8)

def analyze_tile_palette():
    with open(FDOTHER_PATH, 'rb') as f:
        f.seek(0)
        header = f.read(6)
        f.seek(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        # 索引5
        f.seek(10 + 5 * 4)
        offset = struct.unpack('<I', f.read(4))[0]
        end = struct.unpack('<I', f.read(4))[4]
        
        f.seek(offset)
        data = f.read(end - offset)
        
        # RLE解压
        rle_data = data[20:]
        pixel_count = 20 * 16 * 16
        decoded = bytearray()
        i, j = 0, 0
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
        
        # 统计调色板使用
        pal_used = set()
        for p in decoded:
            if p != 0:
                pal_used.add(p)
        
        print(f"使用的调色板索引: {sorted(pal_used)}")
        print(f"调色板数量: {len(pal_used)}")
        
        # 检查字体调色板中这些索引的颜色
        # 加载字体调色板 (FDOTHER索引98)
        f.seek(0)
        header = f.read(6)
        f.seek(6)
        count = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10 + 98 * 4)
        pal_off = struct.unpack('<I', f.read(4))[0]
        pal_end = struct.unpack('<I', f.read(4))[4]
        
        f.seek(pal_off)
        pal_data = f.read(pal_end - pal_off)
        
        print(f"\n字体调色板(索引98)中对应的颜色:")
        for idx in sorted(pal_used):
            if idx * 3 < len(pal_data):
                r6 = pal_data[idx * 3] & 0x3F
                g6 = pal_data[idx * 3 + 1] & 0x3F
                b6 = pal_data[idx * 3 + 2] & 0x3F
                r8 = (r6 << 2) | (r6 >> 4)
                g8 = (g6 << 2) | (g6 >> 4)
                b8 = (b6 << 2) | (b6 >> 4)
                print(f"  索引{idx}: RGB({r8}, {g8}, {b8})")
        
        # 尝试用不同的调色板渲染tile 0和tile 12（应该分别是角和填充）
        # 创建测试图像
        img = Image.new('RGB', (16 * 5, 16 * 4))
        for t in range(min(20, 20)):
            tx = t % 5
            ty = t // 5
            tile_data = decoded[t * 256:(t+1) * 256]
            for y in range(16):
                for x in range(16):
                    pal_idx = tile_data[y * 16 + x]
                    if pal_idx != 0 and pal_idx * 3 < len(pal_data):
                        r6 = pal_data[pal_idx * 3] & 0x3F
                        g6 = pal_data[pal_idx * 3 + 1] & 0x3F
                        b6 = pal_data[pal_idx * 3 + 2] & 0x3F
                        r8 = (r6 << 2) | (r6 >> 4)
                        g8 = (g6 << 2) | (g6 >> 4)
                        b8 = (b6 << 2) | (b6 >> 4)
                        img.putpixel((tx * 16 + x, ty * 16 + y), (r8, g8, b8))
                    else:
                        img.putpixel((tx * 16 + x, ty * 16 + y), (0, 0, 0))
        
        img.save('output/tile_with_font_palette.png')
        print(f"\n测试图像已保存: output/tile_with_font_palette.png")
        
        # 尝试用纯灰度调色板
        img2 = Image.new('RGB', (16 * 5, 16 * 4))
        for t in range(min(20, 20)):
            tx = t % 5
            ty = t // 5
            tile_data = decoded[t * 256:(t+1) * 256]
            for y in range(16):
                for x in range(16):
                    pal_idx = tile_data[y * 16 + x]
                    if pal_idx != 0:
                        v = pal_idx * 16  # 简单映射
                        img2.putpixel((tx * 16 + x, ty * 16 + y), (v, v, v))
                    else:
                        img2.putpixel((tx * 16 + x, ty * 16 + y), (0, 0, 0))
        
        img2.save('output/tile_with_gray_palette.png')
        print(f"灰度测试图像已保存: output/tile_with_gray_palette.png")

if __name__ == "__main__":
    analyze_tile_palette()
