"""
直接搜索tile数据中的宽高信息
根据sub_2EB9F: v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
tile数据格式: [width:2][height:2][? :?][RLE数据]

但我们的tile数据前4字节是 32637 x 32384，这不合理。

让我尝试：tile数据可能是直接RLE压缩的像素数据，宽高是通过其他方式传递的。
查看sub_2EB9F的汇编调用:
  v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
  sub_4E98D(v9+9, *v9, v9[1], a7, a8, value)

这意味着:
- v9[0] = width (*v9)
- v9[1] = height (v9[1])
- v9+9 = RLE数据起始

但我们的tile数据前4字节作为width/height不合理，说明嵌套DAT的偏移表解析方式不对。

让我尝试另一种理解：嵌套DAT的偏移表后还有额外的tile元数据表。
"""
import struct
from PIL import Image
import os

fdother_path = r"D:\workspace\fd2_dat_freebuff\bin\FDOTHER.DAT"
output_dir = r"D:\workspace\fd2_dat_freebuff\output\fdother_7_tiles_v6\scene_0"
os.makedirs(output_dir, exist_ok=True)

def load_palette(fdother_path):
    with open(fdother_path, "rb") as f:
        f.read(6)
        count = struct.unpack("<I", f.read(4))[0]
        offsets = struct.unpack(f"<{count}I", f.read(count * 4))
        start = offsets[75]
        end = offsets[76] if 76 < count else None
        f.seek(start)
        pal_data = f.read(768) if end is None else f.read(end - start)
    
    palette_rgb = []
    for i in range(256):
        r = (pal_data[i * 3] << 2) | (pal_data[i * 3] >> 4)
        g = (pal_data[i * 3 + 1] << 2) | (pal_data[i * 3 + 1] >> 4)
        b = (pal_data[i * 3 + 2] << 2) | (pal_data[i * 3 + 2] >> 4)
        palette_rgb.append((r, g, b))
    
    return palette_rgb

def decompress_rle(src_data, width, height):
    output = bytearray(width * height)
    src_pos = 0
    dst_pos = 0
    src_end = len(src_data)
    
    for row in range(height):
        count = width
        while count > 0 and src_pos < src_end:
            ctrl = src_data[src_pos]
            src_pos += 1
            
            count_1 = (ctrl & 0x3F) + 1
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            
            if bit7 and bit6:
                dst_pos += count_1
                count -= count_1
            elif bit7 and not bit6:
                if src_pos + count_1 > src_end:
                    break
                for i in range(count_1):
                    output[dst_pos] = src_data[src_pos]
                    dst_pos += 1
                    src_pos += 1
                count -= count_1
            elif not bit7 and bit6:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos + 1] = fill
                    dst_pos += 2
                count = count - count_1 - count_1
            else:
                if src_pos >= src_end:
                    break
                fill = src_data[src_pos]
                src_pos += 1
                for i in range(count_1):
                    output[dst_pos] = fill
                    dst_pos += 1
                count -= count_1
        dst_pos = row * width + width
    
    return bytes(output)

palette_rgb = load_palette(fdother_path)

with open(fdother_path, "rb") as f:
    f.read(6)
    count = struct.unpack("<I", f.read(4))[0]
    offsets = struct.unpack(f"<{count}I", f.read(count * 4))
    
    index = 82
    start = offsets[index]
    end = offsets[index + 1]
    f.seek(start)
    resource_data = f.read(end - start)
    
    print(f"资源大小: {len(resource_data)}")
    offset_count = struct.unpack("<I", resource_data[6:10])[0]
    print(f"偏移数量字段: {offset_count}")
    
    # 根据sub_2EB9F的公式: v9 = *(DWORD *)(a5 + 4*a6 + 8) + a5
    # 这意味着从字节 8 开始存储的是tile数据的相对偏移
    # 但每个tile条目是 4 字节 (只是一个偏移值)
    
    # 嵌套DAT结构:
    # [magic:6][count:4][offset0:4][offset1:4][offset2:4][offset3:4]
    # offset3 = 文件末尾 (33848)
    # 但 offset_count=26 意味着有26个资源，不是3个tile
    
    # 等等！offset_count=26 可能是主DAT的资源数量，不是嵌套DAT的
    # 但嵌套DAT本身也是一个DAT，应该有自己的count和offsets
    
    # 重新理解：嵌套DAT的count=26，意味着有26个资源
    # 但只有前3个是tile数据，其余可能是其他资源
    
    # 让我尝试另一种方法：直接查找所有合理的宽高值
    print(f"\n搜索合理的宽高值 (width <= 320, height <= 200):")
    for i in range(114, len(resource_data) - 4, 2):
        w, h = struct.unpack("<HH", resource_data[i:i+4])
        if 0 < w <= 320 and 0 < h <= 200:
            # 检查这是否可能是tile头
            remaining = len(resource_data) - i - 10
            if remaining > 0 and remaining <= 320 * 200:
                print(f"  偏移 {i}: {w}x{h}, 剩余数据 {remaining} 字节")
                # 尝试解压缩
                if i + 10 <= len(resource_data):
                    rle_data = resource_data[i+10:]
                    if len(rle_data) >= w * h:
                        print(f"    尝试解压缩 {w}x{h}...")
                        try:
                            pixels = decompress_rle(rle_data[:w*h], w, h)
                            non_zero = sum(1 for p in pixels if p != 0)
                            total = w * h
                            ratio = non_zero / total if total > 0 else 0
                            print(f"    非零像素: {non_zero}/{total} ({ratio*100:.1f}%)")
                            
                            if 0.01 <= ratio <= 0.95:
                                img = Image.new("RGB", (w, h))
                                px = img.load()
                                for y in range(h):
                                    for x in range(w):
                                        idx = y * w + x
                                        pal_idx = pixels[idx]
                                        if pal_idx < len(palette_rgb):
                                            px[x, y] = palette_rgb[pal_idx]
                                
                                filepath = os.path.join(output_dir, f"found_{w}x{h}_at_{i}.png")
                                img.save(filepath)
                                print(f"    [OK] 已保存 {filepath}")
                        except Exception as e:
                            print(f"    错误: {e}")
