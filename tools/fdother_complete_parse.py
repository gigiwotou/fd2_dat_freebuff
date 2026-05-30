"""
FDOTHER.DAT 完整解析脚本 - 严格按MCP汇编代码实现
根据sub_111BA函数逻辑，从0开始逐一解析104个子资源

文件结构（根据sub_111BA）：
- [0-5字节]: "LLLLLL" 魔数 (6字节)
- [6字节起]: 索引表，每项4字节，存储资源起始偏移
- 资源大小 = offsets[index+1] - offsets[index]

资源识别规则：
1. 768字节 -> 调色板
2. 以"LMI1"开头 -> LMI1 tile集
3. 以"LLLLLL"开头 -> 嵌套DAT
4. 以"LLLL"开头（但不是LLLLLL）-> LLLL嵌套资源
5. [w:2][h:2][rle_data] -> Tile图像（w,h都>0且<320）
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

def identify_resource_type(data):
    """识别资源类型"""
    size = len(data)
    
    # 检查调色板
    if size == 768:
        return 'PALETTE', '调色板(768字节/256色)'
    
    # 检查LMI1
    if size >= 4 and data[0:4] == b'LMI1':
        return 'LMI1', 'LMI1 Tile集'
    
    # 检查嵌套DAT
    if size >= 6 and data[0:6] == b'LLLLLL':
        return 'NESTED_DAT', '嵌套DAT'
    
    # 检查LLLL（但不是LLLLLL）
    if size >= 4 and data[0:4] == b'LLLL' and (size < 6 or data[0:6] != b'LLLLLL'):
        return 'LLLL', 'LLLL嵌套资源'
    
    # 尝试解析为Tile图像 [w:2][h:2][rle_data...]
    if size >= 4:
        w, h = struct.unpack_from('<HH', data, 0)
        if 0 < w <= 320 and 0 < h <= 200:
            rle_sample = dump_hex(data, 4, 16)
            return 'TILE', f'Tile图像 {w}x{h}'
    
    return 'RAW', '原始数据'

def parse_lmi1_tileset(data):
    """解析LMI1格式的tile集"""
    result = []
    if len(data) < 6:
        return result
    
    # LMI1头部
    tile_count = struct.unpack_from('<H', data, 4)[0]
    result.append(f'  Tile数量: {tile_count}')
    
    if tile_count == 0 or tile_count > 500:
        result.append(f'  警告: tile数量异常')
        return result
    
    # 解析每个tile的偏移
    tiles_info = []
    for i in range(min(tile_count, 50)):  # 限制显示前50个
        offset_addr = 6 + i * 4
        if offset_addr + 4 > len(data):
            break
        
        tile_offset = struct.unpack_from('<I', data, offset_addr)[0]
        
        if tile_offset + 4 <= len(data):
            w, h = struct.unpack_from('<HH', data, tile_offset)
            if 0 < w <= 320 and 0 < h <= 200:
                tiles_info.append(f'    Tile[{i:3d}]: 偏移 {tile_offset:6d}, 尺寸 {w}x{h}')
            else:
                tiles_info.append(f'    Tile[{i:3d}]: 偏移 {tile_offset:6d}, 尺寸异常({w}x{h})')
        else:
            tiles_info.append(f'    Tile[{i:3d}]: 偏移 {tile_offset:6d} 超出范围')
    
    result.extend(tiles_info[:20])  # 只显示前20个
    if len(tiles_info) > 20:
        result.append(f'    ... 共{len(tiles_info)}个tile')
    
    return result

def parse_nested_dat(data):
    """解析嵌套DAT结构"""
    result = []
    
    # 检查魔数
    magic = data[0:6].decode('ascii', errors='replace')
    result.append(f'  魔数: {magic}')
    
    # 尝试读取索引数量（偏移6处4字节）
    if len(data) >= 10:
        count = struct.unpack_from('<I', data, 6)[0]
        result.append(f'  资源数量: {count}')
        
        if count > 0 and count < 300:
            # 解析前几个资源
            table_start = 10
            for i in range(min(count, 30)):
                offset_addr = table_start + i * 4
                if offset_addr + 4 > len(data):
                    break
                
                res_offset = struct.unpack_from('<I', data, offset_addr)[0]
                
                if res_offset > 0 and res_offset < len(data):
                    # 检查是否是tile
                    if res_offset + 4 <= len(data):
                        w, h = struct.unpack_from('<HH', data, res_offset)
                        if 0 < w <= 320 and 0 < h <= 200:
                            result.append(f'    资源[{i:3d}]: 偏移 {res_offset:6d}, Tile {w}x{h}')
                        elif w == 0 and h == 0:
                            result.append(f'    资源[{i:3d}]: 偏移 {res_offset:6d}')
                        else:
                            preview = dump_hex(data, res_offset, 12)
                            result.append(f'    资源[{i:3d}]: 偏移 {res_offset:6d}, 尺寸 {w}x{h}(可能异常)')
                            result.append(preview)
                    else:
                        result.append(f'    资源[{i:3d}]: 偏移 {res_offset:6d} 超出范围')
                else:
                    result.append(f'    资源[{i:3d}]: 偏移 {res_offset} (0x{res_offset:08X}) 无效')
            
            if count > 30:
                result.append(f'    ... 共{count}个资源')
    
    return result

def parse_tile_data(data):
    """解析单个tile数据"""
    result = []
    
    if len(data) < 4:
        return result
    
    w, h = struct.unpack_from('<HH', data, 0)
    result.append(f'  尺寸: {w}x{h}')
    
    # 检查是否有调色板窗口偏移（第5字节）
    if len(data) >= 5:
        palette_window = data[4]
        result.append(f'  调色板窗口偏移: {palette_window} (0x{palette_window:02X})')
    
    # RLE数据采样
    if len(data) > 5:
        result.append(f'  RLE数据前32字节:')
        result.append(dump_hex(data, 5, 32))
    
    # 估算非零像素
    rle_data = data[5:] if len(data) > 5 else b''
    nonzero = sum(1 for b in rle_data if b != 0)
    result.append(f'  RLE数据大小: {len(rle_data)} 字节，非零字节: {nonzero}')
    
    return result

def extract_resource_to_file(data, index, filepath, offset_start, offset_end, size, res_type, description):
    """导出资源到文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(data)
    return filepath

def parse_fdother():
    """完整解析FDOTHER.DAT"""
    
    filepath = 'game/FDOTHER.DAT'
    output_dir = 'output/fdother_104_resources'
    raw_dir = os.path.join(output_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f'FDOTHER.DAT 文件大小: {file_size} 字节 ({file_size/1024:.1f} KB)')
    print(f'文件魔数: {data[0:6]}')
    
    # 解析索引表（从偏移6开始，每项4字节）
    print('\n=== 解析索引表 ===')
    
    offsets = []
    table_start = 6
    
    # 扫描所有有效索引
    for i in range(200):
        offset_addr = table_start + i * 4
        if offset_addr + 4 > file_size:
            break
        
        offset_val = struct.unpack_from('<I', data, offset_addr)[0]
        
        if offset_val > file_size:
            print(f'索引 {i}: 偏移 {offset_val} 超出文件大小，停止')
            break
        
        if offset_val > 0:
            offsets.append((i, offset_val))
    
    # 添加文件末尾作为最后一个资源的结束
    if offsets:
        last_idx = offsets[-1][0]
        offsets.append((last_idx + 1, file_size))
    
    print(f'共找到 {len(offsets)-1} 个资源\n')
    
    # 生成报告
    report_lines = []
    report_lines.append('# FDOTHER.DAT 完整解析报告')
    report_lines.append(f'## 文件信息')
    report_lines.append(f'- 文件大小: {file_size} 字节')
    report_lines.append(f'- 资源数量: {len(offsets)-1}')
    report_lines.append(f'- 魔数: LLLLLL')
    report_lines.append('')
    report_lines.append('## 资源列表')
    report_lines.append('')
    
    # 逐个解析资源
    resource_summary = []
    
    for i in range(len(offsets) - 1):
        idx, start = offsets[i]
        _, end = offsets[i + 1]
        size = end - start
        
        if start >= file_size:
            break
        
        # 提取资源数据
        res_data = data[start:end]
        
        # 识别类型
        res_type, description = identify_resource_type(res_data)
        
        # 导出原始文件
        raw_file = os.path.join(raw_dir, f'resource_{idx:03d}.bin')
        extract_resource_to_file(res_data, idx, raw_file, start, end, size, res_type, description)
        
        # 解析详情
        details = []
        details.append(f'\n--- 资源 {idx} ---')
        details.append(f'偏移: {start} - {end} (0x{start:06X} - 0x{end:06X})')
        details.append(f'大小: {size} 字节')
        details.append(f'类型: {res_type} ({description})')
        details.append(f'文件: {raw_file}')
        details.append(f'数据预览:')
        details.append(dump_hex(res_data, 0, min(64, size)))
        
        # 根据类型深度解析
        if res_type == 'PALETTE':
            details.append(f'\n调色板分析:')
            # 显示前几个颜色
            for c in range(min(10, 256)):
                r = res_data[c*3]
                g = res_data[c*3+1]
                b = res_data[c*3+2]
                details.append(f'  颜色{c:3d}: RGB({r:3d}, {g:3d}, {b:3d}) [0x{r:02X}{g:02X}{b:02X}]')
            if 256 > 10:
                details.append(f'  ... 共256色')
        
        elif res_type == 'LMI1':
            details.append(f'\nLMI1 Tile集分析:')
            lmi1_info = parse_lmi1_tileset(res_data)
            details.extend(lmi1_info)
        
        elif res_type == 'NESTED_DAT':
            details.append(f'\n嵌套DAT分析:')
            nested_info = parse_nested_dat(res_data)
            details.extend(nested_info)
        
        elif res_type == 'TILE':
            details.append(f'\nTile图像分析:')
            tile_info = parse_tile_data(res_data)
            details.extend(tile_info)
        
        elif res_type == 'LLLL':
            details.append(f'\nLLLL嵌套资源分析:')
            details.append(f'头部: {res_data[0:8].hex(" ")}')
            if len(res_data) > 8:
                details.append(dump_hex(res_data, 8, 32))
        
        else:  # RAW
            details.append(f'\n原始数据分析:')
            if size > 64:
                details.append(dump_hex(res_data, 64, 64))
        
        # 输出到控制台
        print('\n'.join(details))
        print()
        
        # 添加到报告
        report_lines.append(f'### 资源 {idx}')
        report_lines.append(f'- 偏移: {start} - {end}')
        report_lines.append(f'- 大小: {size} 字节')
        report_lines.append(f'- 类型: {res_type}')
        report_lines.append(f'- 描述: {description}')
        report_lines.append(f'- 文件: `{raw_file}`')
        report_lines.append('')
        
        # 摘要
        resource_summary.append({
            'index': idx,
            'start': start,
            'end': end,
            'size': size,
            'type': res_type,
            'description': description
        })
    
    # 保存报告
    report_file = os.path.join(output_dir, 'fdother_complete_report.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    # 保存CSV摘要
    csv_file = os.path.join(output_dir, 'fdother_resource_summary.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('索引,起始偏移,结束偏移,大小,类型,描述\n')
        for res in resource_summary:
            f.write(f'{res["index"]},{res["start"]},{res["end"]},{res["size"]},{res["type"]},{res["description"]}\n')
    
    # 打印摘要表格
    print('\n' + '='*80)
    print('资源摘要:')
    print(f'{"索引":<6} {"大小":<8} {"类型":<12} {"描述"}')
    print('-'*80)
    for res in resource_summary:
        print(f'{res["index"]:<6} {res["size"]:<8} {res["type"]:<12} {res["description"]}')
    print('-'*80)
    print(f'总计: {len(resource_summary)} 个资源')
    print(f'报告已保存到: {report_file}')
    print(f'CSV已保存到: {csv_file}')
    print(f'原始资源已保存到: {raw_dir}')

if __name__ == '__main__':
    parse_fdother()
