"""检查FDOTHER.DAT资源12和20"""
import struct
import os

def load_dat(dat_path):
    """加载DAT文件并解析资源"""
    with open(dat_path, 'rb') as f:
        magic = f.read(6)
        if magic != b'LLLLLL':
            raise ValueError(f"Invalid magic: {magic}")
        
        resource_count_bytes = f.read(4)
        resource_count = struct.unpack('<I', resource_count_bytes)[0]
        print(f"资源数量: {resource_count}")
        
        # 读取偏移表
        offsets = []
        for i in range(resource_count):
            offset_bytes = f.read(4)
            offset = struct.unpack('<I', offset_bytes)[0]
            offsets.append(offset)
        
        print(f"偏移表大小: {len(offsets)}")
        
        # 计算每个资源的大小
        resources = []
        for i in range(resource_count):
            start = offsets[i]
            if i + 1 < resource_count:
                end = offsets[i + 1]
            else:
                f.seek(0, 2)
                end = f.tell()
            
            size = end - start
            f.seek(start)
            data = f.read(size)
            resources.append({
                'index': i,
                'offset': start,
                'size': size,
                'data': data
            })
        
        return resources

# 检查资源12和20
resources = load_dat('game/FDOTHER.DAT')

for idx in [12, 20]:
    if idx < len(resources):
        res = resources[idx]
        print(f"\n资源 #{idx}:")
        print(f"  偏移: 0x{res['offset']:06x} ({res['offset']})")
        print(f"  大小: {res['size']} 字节")
        print(f"  前32字节: {res['data'][:32].hex(' ')}")
        
        # 检查是否是RLE图像
        if res['size'] > 4:
            w = struct.unpack('<H', res['data'][0:2])[0]
            h = struct.unpack('<H', res['data'][2:4])[0]
            print(f"  可能的尺寸: {w}x{h}")
            
            # 检查RLE标记
            if res['size'] > 6:
                rle_marker = struct.unpack('<H', res['data'][4:6])[0]
                print(f"  RLE标记: 0x{rle_marker:04x}")
