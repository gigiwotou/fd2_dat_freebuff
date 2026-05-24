"""通用FDOTHER.DAT资源解析器 - 基于MCP汇编分析"""
import struct
import os
from PIL import Image

class FDOTHERParser:
    def __init__(self, dat_path):
        self.dat_path = dat_path
        self.offsets = None
        self._load_offsets()
    
    def _load_offsets(self):
        """加载FDOTHER.DAT的偏移表"""
        with open(self.dat_path, "rb") as f:
            # 读取头部
            magic = f.read(6)
            if magic != b"LLLLLL":
                raise ValueError(f"不是有效的FDOTHER.DAT文件，Magic: {magic}")
            
            count = struct.unpack("<I", f.read(4))[0]
            self.offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    def get_resource(self, index):
        """获取指定索引的原始资源数据"""
        if index >= len(self.offsets):
            raise IndexError(f"索引 {index} 超出范围，总数 {len(self.offsets)}")
        
        start = self.offsets[index]
        end = self.offsets[index + 1] if index + 1 < len(self.offsets) else None
        
        with open(self.dat_path, "rb") as f:
            f.seek(start)
            if end:
                data = f.read(end - start)
            else:
                f.seek(0, 2)  # EOF
                file_size = f.tell()
                data = f.read(file_size - start)
        
        return data
    
    def parse_lmi1_tileset(self, index):
        """解析LMI1格式的tile集"""
        data = self.get_resource(index)
        
        if len(data) < 6 or data[0:4] != b"LMI1":
            return None
        
        tile_count = struct.unpack("<H", data[4:6])[0]
        tiles = []
        
        for i in range(tile_count):
            offset_addr = 6 + i * 4
            if offset_addr + 4 > len(data):
                break
            
            tile_offset = struct.unpack("<I", data[offset_addr:offset_addr + 4])[0]
            if tile_offset + 4 > len(data):
                continue
            
            w = struct.unpack("<H", data[tile_offset:tile_offset + 2])[0]
            h = struct.unpack("<H", data[tile_offset + 2:tile_offset + 4])[0]
            
            if w > 0 and h > 0 and w <= 320 and h <= 200:
                pixel_size = w * h
                if tile_offset + 4 + pixel_size <= len(data):
                    pixel_data = data[tile_offset + 4:tile_offset + 4 + pixel_size]
                    tiles.append({
                        "index": i,
                        "width": w,
                        "height": h,
                        "pixel_data": pixel_data,
                        "size": pixel_size
                    })
        
        return tiles
    
    def parse_llll_resource(self, index):
        """解析LLLL格式的资源"""
        data = self.get_resource(index)
        
        if len(data) < 8 or data[0:4] != b"LLLL":
            return None
        
        sub_count = struct.unpack("<I", data[4:8])[0]
        if sub_count > 1000:  # 防止错误解析
            return None
        
        resources = []
        offset_table_start = 8
        
        if offset_table_start + sub_count * 4 > len(data):
            return None
        
        for i in range(sub_count):
            offset = struct.unpack("<I", data[offset_table_start + i * 4:offset_table_start + i * 4 + 4])[0]
            next_offset = struct.unpack("<I", data[offset_table_start + (i+1) * 4:offset_table_start + (i+1) * 4 + 4])[0] if i + 1 < sub_count else len(data)
            
            sub_data = data[offset:next_offset]
            
            # 尝试解析为tile数据
            if len(sub_data) >= 4:
                w = struct.unpack("<H", sub_data[0:2])[0]
                h = struct.unpack("<H", sub_data[2:4])[0]
                
                if 0 < w <= 320 and 0 < h <= 200:
                    pixel_size = w * h
                    if len(sub_data) >= 4 + pixel_size:
                        pixel_data = sub_data[4:4 + pixel_size]
                        resources.append({
                            "index": i,
                            "width": w,
                            "height": h,
                            "pixel_data": pixel_data,
                            "size": pixel_size
                        })
        
        return resources
    
    def load_palette(self, index, palette_size=768):
        """加载调色板"""
        data = self.get_resource(index)
        if len(data) != palette_size:
            raise ValueError(f"调色板大小不符: 期望{palette_size}, 实际{len(data)}")
        
        palette_rgb = []
        for i in range(256):
            # FD2使用6位颜色值，扩展到8位
            r = (data[i * 3] << 2) | (data[i * 3] >> 4)
            g = (data[i * 3 + 1] << 2) | (data[i * 3 + 1] >> 4)
            b = (data[i * 3 + 2] << 2) | (data[i * 3 + 2] >> 4)
            palette_rgb.append((r, g, b))
        
        return palette_rgb
    
    def create_image_from_tile(self, tile, palette_rgb):
        """从tile数据创建图像"""
        img = Image.new("RGB", (tile["width"], tile["height"]))
        pixels = img.load()
        
        for y in range(tile["height"]):
            for x in range(tile["width"]):
                idx = y * tile["width"] + x
                if idx < len(tile["pixel_data"]):
                    pal_idx = tile["pixel_data"][idx]
                    if pal_idx < len(palette_rgb):
                        pixels[x, y] = palette_rgb[pal_idx]
        
        return img

def demo_usage():
    """演示通用解析器的使用"""
    dat_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
    
    if not os.path.exists(dat_path):
        print(f"找不到文件: {dat_path}")
        return
    
    parser = FDOTHERParser(dat_path)
    
    print("FDOTHER.DAT 解析器演示")
    print("=" * 50)
    print(f"资源总数: {len(parser.offsets)}")
    
    # 解析索引4的LMI1 tile集
    print(f"\n解析索引4 (LMI1格式 - 窗口边框tile集):")
    tiles = parser.parse_lmi1_tileset(4)
    if tiles:
        print(f"  找到 {len(tiles)} 个tile")
        
        # 显示前10个tile的信息
        for i, tile in enumerate(tiles[:10]):
            print(f"  Tile {tile['index']}: {tile['width']}x{tile['height']}")
        
        # 创建调色板
        palette = parser.load_palette(75)
        
        # 导出前5个tile为图像
        output_dir = os.path.join(os.path.dirname(__file__), "output", "demo_tiles")
        os.makedirs(output_dir, exist_ok=True)
        
        for i, tile in enumerate(tiles[:5]):
            img = parser.create_image_from_tile(tile, palette)
            img_path = os.path.join(output_dir, f"tile_{tile['index']}_{tile['width']}x{tile['height']}.png")
            img.save(img_path)
            print(f"  已导出: {img_path}")
    
    # 解析索引0的LLLL资源
    print(f"\n解析索引0 (LLLL格式):")
    resources = parser.parse_llll_resource(0)
    if resources:
        print(f"  找到 {len(resources)} 个子资源")
        for i, res in enumerate(resources[:5]):
            print(f"  Resource {res['index']}: {res['width']}x{res['height']}")
    else:
        print("  未找到LLLL格式数据或不是LLLL格式")

if __name__ == "__main__":
    demo_usage()
