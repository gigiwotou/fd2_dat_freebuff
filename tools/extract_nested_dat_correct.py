#!/usr/bin/env python3
"""
正确解析嵌套DAT并提取tile图像
根据IDA Pro MCP分析结果：DAT文件每次只读取2个DWORD
"""
import struct
from PIL import Image
import os

WORKSPACE = r"d:\workspace\fd2_dat_freebuff"
dat_path = f"{WORKSPACE}/bin/FDOTHER.DAT"
output_dir = f"{WORKSPACE}/output/nested_dat_tiles_v4"
os.makedirs(output_dir, exist_ok=True)

with open(dat_path, 'rb') as f:
    data = f.read()

# 正确的DAT读取方式：根据index定位，读取2个DWORD
def read_dat_resource(file_data, base_offset, index):
    """
    模拟sub_111BA的读取逻辑
    1. fseek(base + 4*index + 6)
    2. 读取2个DWORD (8字节)
    3. 大小 = offsets[1] - offsets[0]
    4. 定位到offsets[0]，读取数据
    """
    # 定位到索引表位置
    index_offset = base_offset + 4 * index + 6
    
    # 读取2个DWORD
    offset0 = struct.unpack_from('<I', file_data, index_offset)[0]
    offset1 = struct.unpack_from('<I', file_data, index_offset + 4)[0]
    
    # 计算大小
    size = offset1 - offset0
    
    if size <= 0 or offset0 >= len(file_data):
        return None, 0, 0
    
    # 读取资源数据
    if offset0 + size > len(file_data):
        size = len(file_data) - offset0
    
    resource_data = file_data[offset0:offset0 + size]
    return resource_data, offset0, size

# 读取主DAT的索引63
idx63_data, idx63_offset, idx63_size = read_dat_resource(data, 0, 63)

print(f"索引63:")
print(f"  偏移: 0x{idx63_offset:08X}")
print(f"  大小: {idx63_size}")

if idx63_data is None or len(idx63_data) < 10:
    print("错误：索引63数据无效")
    exit(1)

# 检查嵌套DAT头部
magic = idx63_data[:6]
print(f"  Magic: {magic}")

if magic != b"LLLLLL":
    print("错误：不是有效的嵌套DAT文件")
    exit(1)

# 嵌套DAT同样使用正确的读取方式
# 先读取索引0看看有多少资源
resource0_data, _, _ = read_dat_resource(idx63_data, 0, 0)
print(f"\n嵌套DAT索引0:")
print(f"  数据大小: {len(resource0_data) if resource0_data else 0}")
if resource0_data and len(resource0_data) > 4:
    first_4_bytes = struct.unpack_from('<I', resource0_data, 0)[0]
    print(f"  前4字节: {first_4_bytes} (可能是资源数量)")

# 尝试读取多个索引，看哪些是有效的
print(f"\n尝试读取嵌套DAT的前30个资源:")
valid_resources = []
for i in range(30):
    res_data, res_offset, res_size = read_dat_resource(idx63_data, 0, i)
    if res_data and len(res_data) > 4:
        # 尝试解析为tile数据
        w = struct.unpack_from('<H', res_data, 0)[0]
        h = struct.unpack_from('<H', res_data, 2)[0]
        if 0 < w <= 320 and 0 < h <= 200:
            valid_resources.append((i, res_data, w, h, res_offset, res_size))
            print(f"  [{i}] 偏移 {res_offset}: {w}x{h}, 大小 {res_size}")
        else:
            # 查看前16字节
            hex_str = ' '.join(f'{b:02X}' for b in res_data[:min(16, len(res_data))])
            print(f"  [{i}] 偏移 {res_offset}: 不是tile数据, 数据: {hex_str}")
    else:
        print(f"  [{i}] 无效或空")

# 提取有效的tile为图像
print(f"\n提取tile图像")
for i, (res_idx, res_data, w, h, res_offset, res_size) in enumerate(valid_resources):
    # 像素数据从偏移4开始
    if len(res_data) >= 4 + w * h:
        pixel_data = res_data[4:4 + w * h]
        
        # 创建图像（灰度图以便查看）
        img = Image.new('L', (w, h))
        for y in range(h):
            for x in range(w):
                px_idx = y * w + x
                if px_idx < len(pixel_data):
                    img.putpixel((x, y), pixel_data[px_idx])
        
        # 保存
        img_path = os.path.join(output_dir, f"tile_{res_idx}_{w}x{h}.png")
        img.save(img_path)
        print(f"  已保存: tile_{res_idx}_{w}x{h}.png")

print(f"\n完成！图像已保存到: {output_dir}")
