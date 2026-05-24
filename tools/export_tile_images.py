"""
导出索引4的tile为PNG图片，检查tile是否有内容
"""
import struct
import os
from PIL import Image

data_dir = r"d:\workspace\fd2_dat_freebuff\bin"
dat_path = os.path.join(data_dir, "FDOTHER.DAT")
output_dir = r"d:\workspace\fd2_dat_freebuff\output\tiles"
os.makedirs(output_dir, exist_ok=True)

def rle_decompress(src_data, width, height):
    """RLE解压 - 根据MCP汇编分析"""
    dst = bytearray(width * height)
    src_idx = 0
    dst_idx = 0
    row_count = height
    
    while row_count > 0:
        remaining = width
        
        while remaining > 0:
            if src_idx >= len(src_data):
                break
                
            value = src_data[src_idx]
            src_idx += 1
            
            if value & 0x80:
                if value & 0x40:
                    # SKIP: 跳过count个像素
                    count = (value & 0x3F) + 1
                    dst_idx += count
                    remaining -= count
                else:
                    # COPY: 复制count个像素
                    count = (value & 0x3F) + 1
                    for i in range(count):
                        if src_idx < len(src_data):
                            dst[dst_idx] = src_data[src_idx]
                            dst_idx += 1
                            src_idx += 1
                        remaining -= 1
            else:
                if value & 0x40:
                    # FILL隔行: 隔行填充
                    count = (value & 0x3F) + 1
                    if src_idx < len(src_data):
                        fill_value = src_data[src_idx]
                        src_idx += 1
                        for i in range(count):
                            dst[dst_idx + 1] = fill_value
                            dst_idx += 2
                        remaining -= count * 2
                else:
                    # FILL: 填充count个相同像素
                    count = (value & 0x3F) + 1
                    if src_idx < len(src_data):
                        fill_value = src_data[src_idx]
                        src_idx += 1
                        for i in range(count):
                            dst[dst_idx] = fill_value
                            dst_idx += 1
                        remaining -= count
        
        row_count -= 1
    
    return bytes(dst)

with open(dat_path, "rb") as f:
    f.read(10)  # 跳过magic和count
    offsets = []
    resource_count = struct.unpack("<I", f.read(4))[0]
    f.seek(10)
    for i in range(resource_count):
        offsets.append(struct.unpack("<I", f.read(4))[0])
    
    # 读取索引4
    f.seek(offsets[4])
    size = offsets[5] - offsets[4] if 5 < resource_count else 100000
    data = f.read(size)
    
    tile_count = struct.unpack("<H", data[4:6])[0]
    print(f"Tile count: {tile_count}")
    
    # 导出前20个tile
    for i in range(min(20, tile_count)):
        addr = struct.unpack("<I", data[6 + i*4 : 10 + i*4])[0]
        w, h = struct.unpack("<HH", data[addr:addr+4])
        
        # RLE压缩数据从addr+4开始，到下一个tile或文件结束
        compressed = data[addr+4:]
        if i + 1 < tile_count:
            next_addr = struct.unpack("<I", data[6 + (i+1)*4 : 10 + (i+1)*4])[0]
            compressed = data[addr+4:next_addr]
        
        # 解压
        try:
            pixels = rle_decompress(compressed, w, h)
            
            # 检查像素数据
            non_zero = sum(1 for p in pixels if p != 0)
            
            # 创建图片
            img = Image.new('P', (w, h))
            img.putdata(pixels)
            
            # 保存
            img.save(os.path.join(output_dir, f"tile_{i:03d}_{w}x{h}_nz{non_zero}.png"))
            
            print(f"Tile {i:3d}: {w:2d}x{h:2d}, 非零像素={non_zero:4d}, 保存=tile_{i:03d}_{w}x{h}_nz{non_zero}.png")
        except Exception as e:
            print(f"Tile {i:3d}: 解压失败 - {e}")

print(f"\n图片已保存到: {output_dir}")
