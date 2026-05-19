"""
检查FDOTHER.DAT和FDTXT.DAT中特定资源是否存在
以及它们的嵌套结构和映射关系

目标资源:
- FDOTHER.DAT: 索引201和205 (slot边框图形)
- FDTXT.DAT: 索引514、549、550等 (存档选择界面文本)
"""
import struct
import os
from pathlib import Path

def parse_dat_file(filepath):
    """解析DAT文件，返回索引表和资源信息"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return None
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"\n{'='*70}")
    print(f"文件: {filepath}")
    print(f"大小: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    # 检查文件头
    header = data[0:6]
    print(f"文件头: {header.hex(' ')} = '{header.decode('ascii', errors='replace')}'")
    
    if header != b'LLLLLL':
        print("警告: 非标准DAT文件格式")
        # 尝试其他格式解析
        return parse_alternative_format(data, filepath)
    
    # 解析标准格式：索引从偏移6开始，每项4字节
    offsets = []
    pos = 6
    while pos + 4 <= file_size:
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > file_size:
            break
        offsets.append(offset)
        pos += 4
    
    total_resources = len(offsets) - 1  # 最后一个是文件末尾标记
    print(f"索引数量: {len(offsets)}")
    print(f"资源数量: {total_resources}")
    print(f"索引范围: 0 - {total_resources - 1}")
    
    return {
        'data': data,
        'offsets': offsets,
        'total_resources': total_resources,
        'file_size': file_size
    }

def parse_alternative_format(data, filepath):
    """尝试解析非标准格式的DAT文件"""
    print("\n尝试解析非标准格式...")
    
    # 尝试格式2：前4字节是资源数量
    if len(data) >= 10:
        count = struct.unpack_from('<I', data, 6)[0]
        print(f"假设格式2: 资源数量 = {count}")
        
        offsets = []
        pos = 10  # 偏移表从10开始
        for i in range(count):
            if pos + 4 > len(data):
                break
            offset = struct.unpack_from('<I', data, pos)[0]
            if offset > len(data):
                break
            offsets.append(offset)
            pos += 4
        
        print(f"解析到 {len(offsets)} 个偏移")
        
        return {
            'data': data,
            'offsets': offsets,
            'total_resources': len(offsets),
            'file_size': len(data)
        }
    
    return None

def check_fdother_resources(fdother_info):
    """检查FDOTHER.DAT中的资源201和205"""
    if not fdother_info:
        print("FDOTHER.DAT信息为空")
        return
    
    offsets = fdother_info['offsets']
    data = fdother_info['data']
    total = fdother_info['total_resources']
    
    print(f"\n{'='*70}")
    print("检查FDOTHER.DAT资源 201 和 205 (slot边框图形)")
    print(f"{'='*70}")
    
    # 直接检查索引201和205
    for idx in [201, 205]:
        print(f"\n索引 {idx}:")
        if idx < total:
            start = offsets[idx]
            end = offsets[idx + 1] if idx + 1 < len(offsets) else fdother_info['file_size']
            size = end - start
            print(f"  状态: 存在")
            print(f"  偏移: {start} (0x{start:X})")
            print(f"  大小: {size} bytes")
            
            # 检查是否为图片格式
            if size >= 4:
                width = struct.unpack_from('<H', data, start)[0]
                height = struct.unpack_from('<H', data, start + 2)[0]
                if 0 < width <= 1000 and 0 < height <= 1000:
                    print(f"  类型: 可能是图片 ({width}x{height})")
                else:
                    print(f"  类型: 二进制数据 (宽高不合理: {width}x{height})")
            
            # 显示前16字节
            preview = data[start:start+16]
            print(f"  预览: {preview.hex(' ')}")
        else:
            print(f"  状态: 不存在 (最大索引为 {total - 1})")
            print(f"  说明: 索引{idx}超出了直接索引范围")
    
    # 检查可能的嵌套DAT文件（索引7通常是嵌套DAT）
    print(f"\n检查嵌套DAT文件 (索引7):")
    if 7 < total:
        start = offsets[7]
        end = offsets[8] if 8 < len(offsets) else fdother_info['file_size']
        nested_data = data[start:end]
        
        print(f"  嵌套DAT大小: {len(nested_data)} bytes")
        print(f"  嵌套DAT文件头: {nested_data[0:6].hex(' ')}")
        
        if nested_data[0:6] == b'LLLLLL':
            print(f"  嵌套DAT格式: 标准DAT格式")
            
            # 解析嵌套DAT
            nested_offsets = []
            pos = 6
            while pos + 4 <= len(nested_data):
                offset = struct.unpack_from('<I', nested_data, pos)[0]
                if offset > len(nested_data):
                    break
                nested_offsets.append(offset)
                pos += 4
            
            nested_total = len(nested_offsets) - 1
            print(f"  嵌套DAT资源数量: {nested_total}")
            print(f"  嵌套DAT索引范围: 0 - {nested_total - 1}")
            
            # 检查嵌套DAT中的索引201和205
            for idx in [201, 205]:
                if idx < nested_total:
                    n_start = nested_offsets[idx]
                    n_end = nested_offsets[idx + 1] if idx + 1 < len(nested_offsets) else len(nested_data)
                    n_size = n_end - n_start
                    print(f"  嵌套索引 {idx}: 存在 (大小={n_size} bytes)")
                else:
                    print(f"  嵌套索引 {idx}: 不存在 (嵌套最大索引为 {nested_total - 1})")

def check_fdtxt_resources(fdtxt_info):
    """检查FDTXT.DAT中的文本资源"""
    if not fdtxt_info:
        print("FDTXT.DAT信息为空")
        return
    
    offsets = fdtxt_info['offsets']
    data = fdtxt_info['data']
    total = fdtxt_info['total_resources']
    
    print(f"\n{'='*70}")
    print("检查FDTXT.DAT文本资源 514, 549, 550等 (存档选择界面文本)")
    print(f"{'='*70}")
    
    # 根据文档，文本ID映射:
    # - 槽位号: 549 + n4 (n4=0,1,2,3)
    # - 空槽位: 514
    # - 场景名: 514 + n17
    # - 场景描述: 550 + n17
    
    text_ids = [514, 549, 550, 551, 552, 553]  # 549-553是槽位号1-5
    
    print(f"\n直接索引范围: 0 - {total - 1}")
    print(f"请求的文本ID: {text_ids}")
    
    # 检查这些文本ID是否在直接索引范围内
    for text_id in text_ids:
        print(f"\n文本ID {text_id}:")
        if text_id < total:
            start = offsets[text_id]
            end = offsets[text_id + 1] if text_id + 1 < len(offsets) else fdtxt_info['file_size']
            size = end - start
            print(f"  状态: 存在 (直接索引)")
            print(f"  偏移: {start}")
            print(f"  大小: {size} bytes")
            
            # 尝试读取文本内容
            if size > 0:
                text_data = data[start:start+min(100, size)]
                # 尝试GBK解码（中文游戏常用编码）
                try:
                    text_str = text_data.decode('gbk', errors='replace')
                    # 查找字符串结束位置
                    null_pos = text_str.find('\x00')
                    if null_pos != -1:
                        text_str = text_str[:null_pos]
                    print(f"  内容: {text_str}")
                except:
                    print(f"  原始数据: {text_data[:50].hex(' ')}")
        else:
            print(f"  状态: 不存在 (超出直接索引范围)")
            print(f"  说明: 文本ID {text_id} > 最大索引 {total - 1}")
    
    # 分析可能的索引映射
    print(f"\n可能的索引映射分析:")
    print(f"  FDTXT.DAT有 {total} 个直接索引")
    print(f"  如果文本ID是连续的，可能:")
    print(f"    - 文本ID 0-{total-1} 直接对应索引 0-{total-1}")
    print(f"    - 或者存在映射表将大ID映射到小索引")
    
    # 检查前20个文本资源的内容
    print(f"\n前20个文本资源内容预览:")
    for i in range(min(20, total)):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else fdtxt_info['file_size']
        size = end - start
        
        if size > 0:
            text_data = data[start:start+min(50, size)]
            try:
                text_str = text_data.decode('gbk', errors='replace')
                null_pos = text_str.find('\x00')
                if null_pos != -1:
                    text_str = text_str[:null_pos]
                print(f"  [{i:3d}] {text_str[:40]}")
            except:
                print(f"  [{i:3d}] (二进制数据)")

def main():
    print("FD2游戏资源检查工具")
    print("="*70)
    
    # 搜索DAT文件
    search_dirs = [
        Path("d:/workspace/fd2_dat_freebuff/game"),
        Path("d:/workspace/fd2_dat_freebuff"),
        Path("d:/workspace/fd2_dat_freebuff/data"),
        Path("d:/workspace/fd2_ida_hex/fd2"),
    ]
    
    fdother_path = None
    fdtxt_path = None
    
    for base_dir in search_dirs:
        if base_dir.exists():
            for f in base_dir.glob("**/FDOTHER.DAT"):
                fdother_path = f
                break
            for f in base_dir.glob("**/FDTXT.DAT"):
                fdtxt_path = f
                break
        if fdother_path and fdtxt_path:
            break
    
    if not fdother_path:
        print("\n未找到FDOTHER.DAT文件")
        print("请确保DAT文件在以下目录之一:")
        for d in search_dirs:
            print(f"  - {d}")
        return
    
    if not fdtxt_path:
        print("\n未找到FDTXT.DAT文件")
        print("请确保DAT文件在以下目录之一:")
        for d in search_dirs:
            print(f"  - {d}")
        return
    
    print(f"\n找到DAT文件:")
    print(f"  FDOTHER.DAT: {fdother_path}")
    print(f"  FDTXT.DAT: {fdtxt_path}")
    
    # 解析文件
    fdother_info = parse_dat_file(str(fdother_path))
    fdtxt_info = parse_dat_file(str(fdtxt_path))
    
    # 检查资源
    check_fdother_resources(fdother_info)
    check_fdtxt_resources(fdtxt_info)
    
    print(f"\n{'='*70}")
    print("检查完成")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
