#!/usr/bin/env python3
"""
基于IDA精确分析的动画音频解码

IDA分析得出的完整流程：
1. sub_20421打开ANI.DAT
2. fseek(ANI.DAT, arg_0 * 4 + 6, 0) - 定位到资源偏移表
3. 读取8字节 → 获取数据起始偏移
4. fseek到该偏移
5. 读取173字节头
6. var_14 = [esi+0xA5] - 循环/块数量
7. 循环：
   a. 读取8字节头 → var_24(size), var_22(count)
   b. 读取var_24字节数据到缓冲区
   c. sub_36FF4(var_22, 缓冲区) - 解码音频
   d. 如果是第一块(arg_0==1 && esi==0)：调用sub_25A96播放res78
8. sub_25A96使用Miles AIL播放res78中的样本
"""
import struct
import os

ani_path = os.path.join('game', 'ANI.DAT')
dat_path = os.path.join('game', 'FDOTHER.DAT')

def load_ani_resource(index):
    """从ANI.DAT加载资源"""
    with open(ani_path, 'rb') as f:
        # 读取资源偏移
        f.seek(10 + index * 4)
        offset = struct.unpack('<I', f.read(4))[0]
        
        f.seek(10 + (index + 1) * 4)
        next_offset = struct.unpack('<I', f.read(4))[0]
        
        size = next_offset - offset
        f.seek(offset)
        data = f.read(size)
    
    return data, offset, size

def parse_ani_animation(data):
    """解析ANI.DAT动画数据结构"""
    print(f"ANI数据大小: {len(data)} bytes")
    print(f"前32字节: {data[:32].hex()}")
    
    # 根据IDA: 读取173字节头
    header = data[:173]
    print(f"\n头部173字节:")
    print(f"  *(0xA5) = {struct.unpack_from('<H', header, 0xA5)[0]}")  # 块数量
    print(f"  *(0xA4) = {struct.unpack_from('<B', header, 0xA4)[0]}")
    
    # 解析块
    pos = 173
    blocks = []
    
    while pos < len(data):
        # 读取8字节块头
        if pos + 8 > len(data):
            break
        
        chunk_header = data[pos:pos+8]
        size = struct.unpack_from('<H', chunk_header, 0)[0]  # var_24
        count = struct.unpack_from('<H', chunk_header, 2)[0]  # var_22
        
        print(f"\n块头 @ {pos}:")
        print(f"  size (var_24) = {size}")
        print(f"  count (var_22) = {count}")
        print(f"  块数据: {chunk_header[4:8].hex()}")
        
        pos += 8
        
        # 读取size字节数据
        if pos + size > len(data):
            break
        
        chunk_data = data[pos:pos+size]
        print(f"  数据前16字节: {chunk_data[:16].hex()}")
        
        blocks.append({
            'size': size,
            'count': count,
            'data': chunk_data
        })
        
        pos += size
    
    return blocks

# 解析动画0（闪电动画）
print("="*60)
print("解析ANI.DAT动画 #0")
print("="*60)

ani_data, offset, size = load_ani_resource(0)
blocks = parse_ani_animation(ani_data)

# 保存块数据
os.makedirs('output/sfx_wav/ani_decode', exist_ok=True)

for i, block in enumerate(blocks):
    with open(f'output/sfx_wav/ani_decode/block{i}_size{block["size"]}_count{block["count"]}.bin', 'wb') as f:
        f.write(block['data'])

print(f"\n共解析 {len(blocks)} 个块")
print(f"块数据已保存到 output/sfx_wav/ani_decode/")
