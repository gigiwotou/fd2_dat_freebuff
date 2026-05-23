"""
查找所有FDOTHER资源，分析哪个是真正的窗口tile集
窗口tile集的特征：
1. tile尺寸应该是16x16或固定尺寸
2. tile数量应该在10-50之间（窗口边框+内容）
3. 应该有明显的图案（边框、角、背景等）
"""

import struct
import sys

def analyze_resource(fdother_path, index):
    """分析单个资源"""
    with open(fdother_path, 'rb') as f:
        # 读取DAT头部
        magic = f.read(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        if index >= resource_count:
            return None
        
        # 读取偏移表
        offsets = []
        for i in range(resource_count):
            offset = struct.unpack('<I', f.read(4))[0]
            offsets.append(offset)
        
        start = offsets[index]
        end = offsets[index + 1] if index + 1 < resource_count else None
        
        f.seek(start)
        if end:
            data = f.read(end - start)
        else:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(start)
            data = f.read(file_size - start)
        
        return data

def is_tile_set(data, name=""):
    """判断是否为tile集"""
    if not data or len(data) < 10:
        return False, "数据太小"
    
    # 检查常见tile集特征
    results = []
    
    # 特征1: 小尺寸tile (16x16, 8x8等)
    for tile_size in [8, 16, 24, 32]:
        if len(data) >= tile_size * tile_size:
            # 检查是否有重复图案
            chunk = data[:tile_size * tile_size]
            unique = len(set(chunk))
            if unique < tile_size * tile_size * 0.5:
                results.append(f"可能是{tile_size}x{tile_size} tile集 (独特颜色: {unique})")
    
    # 特征2: 16位头部 (宽度, 高度)
    if len(data) >= 4:
        w, h = struct.unpack('<HH', data[:4])
        if w <= 640 and h <= 480 and w > 0 and h > 0:
            if w % 8 == 0 and h % 8 == 0:
                results.append(f"可能是图像: {w}x{h}")
    
    # 特征3: 检查是否是RLE压缩数据
    if len(data) > 10:
        # RLE特征: 0x80以上字节表示重复
        high_bytes = sum(1 for b in data[:100] if b >= 0x80)
        if high_bytes > 20:
            results.append(f"可能是RLE压缩数据 (高字节比例: {high_bytes}/100)")
    
    # 特征4: 检查tile集头部格式
    if len(data) >= 6:
        # 尝试解析为tile集头部
        total_w = data[0] | (data[1] << 8)
        total_h = data[2] | (data[3] << 8)
        tile_count = data[4] | (data[5] << 8)
        
        if tile_count > 0 and tile_count < 500:
            if total_w > 0 and total_w < 2000:
                if total_h > 0 and total_h < 2000:
                    results.append(f"可能是tile集: {tile_count} tiles, 总尺寸{total_w}x{total_h}")
    
    if results:
        return True, "; ".join(results)
    return False, "不像是tile集"

def main(fdother_path):
    with open(fdother_path, 'rb') as f:
        magic = f.read(6)
        resource_count = struct.unpack('<I', f.read(4))[0]
        
        print(f"FDOTHER资源总数: {resource_count}\n")
        
        # 分析前50个资源
        for i in range(min(50, resource_count)):
            data = analyze_resource(fdother_path, i)
            if not data:
                continue
            
            is_tile, reason = is_tile_set(data, f"索引{i}")
            print(f"索引 {i:2d}: 大小={len(data):6d} 字节, {'是tile集' if is_tile else '不是tile集'}")
            if is_tile:
                print(f"       {reason}")
            
            # 显示前16字节
            hex_str = ' '.join(f'{b:02X}' for b in data[:16])
            print(f"       前16字节: {hex_str}")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <FDOTHER.DAT路径>")
        sys.exit(1)
    
    main(sys.argv[1])
