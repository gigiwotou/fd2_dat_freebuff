#!/usr/bin/env python3
"""
分析sub_4E98D的palette window应用方式

根据反编译代码，value_1参数有三种模式:
1. value_1 == -1: 不应用palette，直接写入原始像素值
2. value_1 <= 0xFF: 使用value_1作为固定填充色（忽略src数据）
3. value_1 > 0xFF: 应用palette window变换

第3种模式的公式:
  value = value_1 + ((BYTE1(value_1) + src_byte) & 7)
  
其中value_1的格式可能是: (param << 8) | base_palette
"""

import struct
from pathlib import Path
from PIL import Image

FDOTHER_PATH = Path("game/FDOTHER.DAT")

def decode_rle_with_palette_transform(rle_data, w, h, base_pal, param):
    """使用palette transform模式解码RLE（value_1 > 0xFF分支）"""
    dst = bytearray(w * h)
    dst_idx = 0
    src_idx = 0
    
    for row in range(h):
        remaining = w
        
        while remaining > 0 and src_idx < len(rle_data):
            ctrl = rle_data[src_idx]
            src_idx += 1
            
            bit7 = (ctrl >> 7) & 1
            bit6 = (ctrl >> 6) & 1
            count = (ctrl & 0x3F) + 1
            
            if bit7 == 0:
                if bit6 == 0:
                    # FILL
                    actual_count = min(count, remaining)
                    if src_idx < len(rle_data):
                        src_byte = rle_data[src_idx]
                        src_idx += 1
                        # 应用palette transform
                        fill_val = base_pal + ((param + src_byte) & 7)
                        for i in range(actual_count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = fill_val
                                dst_idx += 1
                    remaining -= actual_count
                else:
                    # COPY_SPEC
                    total_consume = count * 2
                    actual_count = count
                    if total_consume > remaining:
                        actual_count = remaining // 2
                        total_consume = actual_count * 2
                    if src_idx < len(rle_data):
                        src_byte = rle_data[src_idx]
                        src_idx += 1
                        val = base_pal + ((param + src_byte) & 7)
                        for i in range(actual_count):
                            if dst_idx < len(dst):
                                dst[dst_idx] = val
                                dst_idx += 2
                    remaining -= total_consume
            else:
                if bit6 == 0:
                    # COPY_STD
                    actual_count = min(count, remaining, len(rle_data) - src_idx)
                    for i in range(actual_count):
                        if dst_idx < len(dst) and src_idx < len(rle_data):
                            src_byte = rle_data[src_idx]
                            src_idx += 1
                            dst[dst_idx] = base_pal + ((param + src_byte) & 7)
                            dst_idx += 1
                    remaining -= actual_count
                else:
                    # SKIP
                    actual_count = min(count, remaining)
                    dst_idx += actual_count
                    remaining -= actual_count
    
    return dst

def test_palette_transform():
    """测试不同的palette transform参数"""
    with open(FDOTHER_PATH, 'rb') as f:
        data = f.read()
    
    # 读取索引表
    offsets = []
    table_offset = 6
    while table_offset + 4 <= len(data):
        res_offset = struct.unpack_from('<I', data, table_offset)[0]
        if res_offset == 0 or res_offset > len(data):
            break
        offsets.append(res_offset)
        table_offset += 4
    
    # 索引0调色板
    idx0_data = data[offsets[0]:offsets[1]]
    
    # 索引1数据
    idx1_data = data[offsets[1]:offsets[2]]
    w = struct.unpack_from('<H', idx1_data, 0)[0]
    h = struct.unpack_from('<H', idx1_data, 2)[0]
    pw = idx1_data[4]
    
    print(f"索引1: {w}x{h}, palette_window={pw}")
    
    # RLE数据
    rle_data = idx1_data[5:]
    
    # 测试不同的base_pal和param组合
    print(f"\n测试palette transform:")
    print(f"{'='*60}")
    
    results = []
    
    for base_pal in [0, 16, 32, 48, 64, 96, 128, 160, 192, 224]:
        for param in [0, 16, 20, 32, 48, 64, 96, 128]:
            decoded = decode_rle_with_palette_transform(rle_data, w, h, base_pal, param)
            
            # 统计唯一值
            unique_vals = sorted(set(decoded))
            color_count = len(unique_vals)
            
            # 渲染
            img = Image.new('RGB', (w, h))
            for y in range(h):
                for x in range(w):
                    idx = y * w + x
                    pal_idx = decoded[idx]
                    if pal_idx < 256:
                        r = idx0_data[pal_idx * 3]
                        g = idx0_data[pal_idx * 3 + 1]
                        b = idx0_data[pal_idx * 3 + 2]
                        img.putpixel((x, y), (r, g, b))
            
            results.append({
                'base_pal': base_pal,
                'param': param,
                'img': img,
                'unique_count': color_count,
                'unique_vals': unique_vals,
            })
    
    # 按颜色数量排序（越少越好，图标通常颜色少）
    results.sort(key=lambda x: x['unique_count'])
    
    for i, result in enumerate(results[:10]):
        print(f"\n排名 {i+1}: base_pal={result['base_pal']}, param={result['param']}, 颜色数={result['unique_count']}")
        print(f"  颜色值: {result['unique_vals']}")
        
        filename = f'output/idx1_transform_pal{result["base_pal"]}_param{result["param"]}.png'
        result['img'].save(filename)
        print(f"  已保存: {filename}")

if __name__ == '__main__':
    test_palette_transform()
