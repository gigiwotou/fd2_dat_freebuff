"""
FDOTHER.DAT 逐个资源详细分析 - 用于游戏加载
从索引0开始，识别每个资源的：类型、尺寸、用途
"""

import struct
import os

def dump_hex(data, offset=0, length=32):
    """输出十六进制数据"""
    end = min(offset + length, len(data))
    result = []
    for i in range(offset, end, 16):
        hex_str = ' '.join(f'{b:02X}' for b in data[i:min(i+16, end)])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:min(i+16, end)])
        result.append(f'  {i:04X}: {hex_str:<48} {ascii_str}')
    return '\n'.join(result)

def parse_palette(data):
    """解析调色板数据"""
    colors = []
    for i in range(256):
        r, g, b = data[i*3], data[i*3+1], data[i*3+2]
        # 转换6位到8位
        r = (r << 2) | (r >> 4)
        g = (g << 2) | (g >> 4)
        b = (b << 2) | (b >> 4)
        colors.append((r, g, b))
    return colors

def parse_tile_info(data):
    """解析tile图像信息"""
    if len(data) < 4:
        return None
    w, h = struct.unpack_from('<HH', data, 0)
    if w == 0 or h == 0 or w > 640 or h > 480:
        return None
    return {'width': w, 'height': h}

def analyze_sound_format(data):
    """尝试分析音频格式"""
    # 检查常见音频格式标记
    if data[:4] == b'RIFF':
        return 'WAV'
    if data[:4] == b'MThd':
        return 'MIDI'
    if data[:4] == b'OggS':
        return 'OGG'
    if data[:2] == b'\xFF\xFB' or data[:2] == b'\xFF\xF3':
        return 'MP3'
    return None

def identify_resource(data, index):
    """识别资源详细信息"""
    size = len(data)
    result = {
        'index': index,
        'size': size,
        'type': 'UNKNOWN',
        'subtype': '',
        'description': '',
        'params': {}
    }
    
    # 1. 检查调色板（768字节 = 256色 * 3字节）
    if size == 768:
        result['type'] = 'PALETTE'
        result['description'] = '256色调色板'
        # 分析颜色特征
        avg_brightness = sum(data[i] for i in range(0, 768, 3)) / 256
        result['params']['avg_brightness'] = avg_brightness
        # 检查前几个颜色
        first_colors = []
        for i in range(min(10, 256)):
            r, g, b = data[i*3], data[i*3+1], data[i*3+2]
            first_colors.append(f'({r},{g},{b})')
        result['params']['first_colors'] = first_colors
        return result
    
    # 2. 检查LMI1 tile集
    if size >= 6 and data[:4] == b'LMI1':
        tile_count = struct.unpack_from('<H', data, 4)[0]
        result['type'] = 'LMI1'
        result['description'] = f'LMI1 Tile集 ({tile_count}个tile)'
        result['params']['tile_count'] = tile_count
        
        # 分析前几个tile
        tiles = []
        for i in range(min(tile_count, 10)):
            offset_addr = 6 + i * 4
            if offset_addr + 4 <= size:
                tile_offset = struct.unpack_from('<I', data, offset_addr)[0]
                if tile_offset + 4 <= size:
                    w, h = struct.unpack_from('<HH', data, tile_offset)
                    if w > 0 and h > 0 and w <= 640 and h <= 480:
                        tiles.append({'index': i, 'offset': tile_offset, 'width': w, 'height': h})
        result['params']['sample_tiles'] = tiles
        return result
    
    # 3. 检查嵌套DAT
    if size >= 10 and data[:6] == b'LLLLLL':
        result['type'] = 'NESTED_DAT'
        nested_count = struct.unpack_from('<I', data, 6)[0]
        result['description'] = f'嵌套DAT ({nested_count}个子资源)'
        result['params']['nested_count'] = nested_count
        
        # 分析嵌套资源的尺寸分布
        if 0 < nested_count < 200:
            table_start = 10
            nested_tiles = []
            for i in range(min(nested_count, 20)):
                offset_addr = table_start + i * 4
                if offset_addr + 4 <= size:
                    res_offset = struct.unpack_from('<I', data, offset_addr)[0]
                    if res_offset > 0 and res_offset + 4 <= size:
                        w, h = struct.unpack_from('<HH', data, res_offset)
                        if w > 0 and h > 0 and w <= 640 and h <= 480:
                            palette_window = data[res_offset + 4] if res_offset + 4 < size else 0
                            nested_tiles.append({
                                'index': i,
                                'offset': res_offset,
                                'width': w,
                                'height': h,
                                'palette_window': palette_window
                            })
            result['params']['sample_nested_tiles'] = nested_tiles
        return result
    
    # 4. 检查单个Tile图像 [w:2][h:2][data...]
    if size >= 4:
        tile_info = parse_tile_info(data)
        if tile_info:
            w, h = tile_info['width'], tile_info['height']
            result['type'] = 'TILE'
            result['description'] = f'Tile图像 {w}x{h}'
            result['params'] = tile_info
            
            # 检查是否有调色板窗口偏移（第5字节）
            if size >= 5:
                palette_window = data[4]
                result['params']['palette_window'] = palette_window
            
            # 分析RLE数据特征
            if size > 5:
                rle_data = data[5:]
                unique_values = len(set(rle_data))
                result['params']['rle_unique_values'] = unique_values
                result['params']['rle_size'] = len(rle_data)
                
                # 估算是否为音频
                if unique_values > 200 and w * h <= 10:  # 尺寸很小但数据很多样
                    result['type'] = 'AUDIO'
                    result['description'] = f'可能是音效数据 ({w}x{h}, 多样性{unique_values})'
            
            return result
    
    # 5. 检查是否为音频数据
    audio_format = analyze_sound_format(data)
    if audio_format:
        result['type'] = 'AUDIO'
        result['subtype'] = audio_format
        result['description'] = f'{audio_format}音频文件'
        return result
    
    # 6. 检查是否为特殊格式
    # 检查前几个字节是否有规律
    if size >= 8:
        header = data[:8].hex()
        # 检查是否有重复模式（可能是音频采样）
        if size > 100:
            # 计算数据熵
            from collections import Counter
            import math
            freq = Counter(data[:min(1000, size)])
            total = min(1000, size)
            entropy = 0
            for c in freq.values():
                if c > 0:
                    p = c / total
                    entropy -= p * math.log2(p)
            result['params']['entropy'] = entropy
            
            # 高熵值可能表示压缩数据或音频
            if entropy > 6.0:
                result['type'] = 'AUDIO'
                result['description'] = f'高熵数据 ({entropy:.2f} bits)，可能是音效'
    
    # 默认为RAW
    result['type'] = 'RAW'
    result['description'] = f'原始数据'
    return result

def main():
    """主分析函数"""
    filepath = 'game/FDOTHER.DAT'
    output_dir = 'output/fdother_detailed_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 解析索引表
    offsets = []
    table_start = 6
    for i in range(150):
        offset_addr = table_start + i * 4
        if offset_addr + 4 > len(data):
            break
        offset_val = struct.unpack_from('<I', data, offset_addr)[0]
        if offset_val > len(data):
            break
        if offset_val > 0:
            offsets.append((i, offset_val))
    
    # 添加文件末尾
    if offsets:
        last_idx = offsets[-1][0]
        offsets.append((last_idx + 1, len(data)))
    
    print(f'FDOTHER.DAT 资源详细分析')
    print(f'总资源数: {len(offsets)-1}\n')
    
    # 分析每个资源
    all_resources = []
    
    for i in range(len(offsets) - 1):
        idx, start = offsets[i]
        _, end = offsets[i + 1]
        size = end - start
        
        if start >= len(data):
            break
        
        res_data = data[start:end]
        info = identify_resource(res_data, idx)
        
        all_resources.append(info)
        
        # 打印详细信息
        print(f'\n{"="*80}')
        print(f'资源 {idx}')
        print(f'{"="*80}')
        print(f'偏移: {start} - {end}')
        print(f'大小: {size} 字节')
        print(f'类型: {info["type"]}')
        print(f'描述: {info["description"]}')
        
        # 根据类型输出详细信息
        if info['type'] == 'PALETTE':
            print(f'\n调色板详情:')
            print(f'  平均亮度: {info["params"]["avg_brightness"]:.1f}')
            print(f'  前10个颜色: {", ".join(info["params"]["first_colors"])}')
            
            # 导出调色板为C数组格式
            palette_file = os.path.join(output_dir, f'palette_{idx:03d}.h')
            with open(palette_file, 'w') as f:
                f.write(f'// 调色板 {idx} - 256色\n')
                f.write(f'const unsigned char palette_{idx:03d}[768] = {{\n')
                for j in range(256):
                    r, g, b = res_data[j*3], res_data[j*3+1], res_data[j*3+2]
                    f.write(f'  {r}, {g}, {b},')
                    if (j+1) % 8 == 0:
                        f.write('\n')
                f.write('};\n')
            print(f'  已导出为C头文件: {palette_file}')
        
        elif info['type'] == 'LMI1':
            print(f'\nLMI1 Tile集详情:')
            print(f'  Tile数量: {info["params"]["tile_count"]}')
            if info['params'].get('sample_tiles'):
                print(f'  前{len(info["params"]["sample_tiles"])}个tile:')
                for tile in info['params']['sample_tiles']:
                    print(f'    Tile[{tile["index"]}]: {tile["width"]}x{tile["height"]} @ 偏移{tile["offset"]}')
        
        elif info['type'] == 'NESTED_DAT':
            print(f'\n嵌套DAT详情:')
            print(f'  子资源数量: {info["params"]["nested_count"]}')
            if info['params'].get('sample_nested_tiles'):
                tiles = info['params']['sample_nested_tiles']
                print(f'  前{len(tiles)}个嵌套资源:')
                for tile in tiles:
                    print(f'    资源[{tile["index"]}]: {tile["width"]}x{tile["height"]}, 调色板窗口={tile["palette_window"]} @ 偏移{tile["offset"]}')
        
        elif info['type'] == 'TILE':
            print(f'\nTile图像详情:')
            print(f'  尺寸: {info["params"]["width"]}x{info["params"]["height"]}')
            if 'palette_window' in info['params']:
                print(f'  调色板窗口偏移: {info["params"]["palette_window"]} (0x{info["params"]["palette_window"]:02X})')
            if 'rle_unique_values' in info['params']:
                print(f'  RLE数据大小: {info["params"]["rle_size"]} 字节')
                print(f'  不同值数量: {info["params"]["rle_unique_values"]}')
        
        elif info['type'] == 'AUDIO':
            print(f'\n音效数据详情:')
            if 'entropy' in info['params']:
                print(f'  数据熵: {info["params"]["entropy"]:.2f} bits')
            if info.get('subtype'):
                print(f'  格式: {info["subtype"]}')
        
        # 导出原始文件
        raw_file = os.path.join(output_dir, f'resource_{idx:03d}.bin')
        with open(raw_file, 'wb') as f:
            f.write(res_data)
        
        # 打印数据预览
        print(f'\n数据预览 (前64字节):')
        print(dump_hex(res_data, 0, 64))
    
    # 生成汇总报告
    print(f'\n\n{"="*80}')
    print(f'资源类型汇总')
    print(f'{"="*80}')
    
    type_counts = {}
    for res in all_resources:
        t = res['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    for t, count in sorted(type_counts.items()):
        print(f'  {t}: {count}个')
    
    # 保存汇总CSV
    csv_file = os.path.join(output_dir, 'resource_summary.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('索引,大小,类型,描述,宽度,高度,调色板窗口,子资源数\n')
        for res in all_resources:
            width = res['params'].get('width', '')
            height = res['params'].get('height', '')
            palette_window = res['params'].get('palette_window', '')
            nested_count = res['params'].get('nested_count', '')
            tile_count = res['params'].get('tile_count', '')
            f.write(f'{res["index"]},{res["size"]},{res["type"]},{res["description"]},{width},{height},{palette_window},{nested_count or tile_count}\n')
    
    print(f'\n汇总报告已保存到: {csv_file}')
    print(f'所有资源已导出到: {output_dir}')

if __name__ == '__main__':
    main()
