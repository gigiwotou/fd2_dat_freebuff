"""检查FDOTHER.DAT和FDTXT.DAT中的资源是否存在"""
import struct
from pathlib import Path

def analyze_dat_file(filepath):
    """分析DAT文件结构"""
    path = Path(filepath)
    if not path.exists():
        print(f"文件不存在: {filepath}")
        return None
    
    data = path.read_bytes()
    print(f"\n{'='*60}")
    print(f"文件: {filepath}")
    print(f"大小: {len(data)} bytes ({len(data)/1024:.2f} KB)")
    
    # 检查文件头
    header = data[0:6]
    print(f"文件头: {header.hex(' ')} ({header})")
    
    if header != b'LLLLLL':
        print("警告: 非标准DAT文件格式")
        return None
    
    # 解析索引表
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 4
        if len(offsets) > 5000:  # 安全限制
            break
    
    total_resources = len(offsets) - 1  # 最后一个offset是文件末尾
    print(f"索引数量: {len(offsets)}")
    print(f"资源数量: {total_resources}")
    
    # 检查特定索引
    check_indices = [201, 205]
    print(f"\n检查特定资源索引:")
    for idx in check_indices:
        if idx < total_resources:
            start = offsets[idx]
            end = offsets[idx + 1]
            size = end - start
            print(f"  索引 {idx}: 存在 (偏移={start}, 大小={size} bytes)")
            
            # 检查是否为图片格式
            if size >= 4:
                width = struct.unpack_from('<H', data, start)[0]
                height = struct.unpack_from('<H', data, start + 2)[0]
                if 0 < width < 1000 and 0 < height < 1000:
                    print(f"    可能是图片: {width}x{height}")
        else:
            print(f"  索引 {idx}: 不存在 (最大索引为 {total_resources - 1})")
    
    # 检查FDTXT.DAT的文本资源
    if 'FDTXT' in filepath.upper():
        print(f"\n检查文本资源索引:")
        text_indices = [514, 549, 550]
        for idx in text_indices:
            if idx < total_resources:
                start = offsets[idx]
                end = offsets[idx + 1]
                size = end - start
                print(f"  索引 {idx}: 存在 (偏移={start}, 大小={size} bytes)")
                
                # 尝试读取前几个字节作为文本
                if size > 0:
                    text_preview = data[start:start+min(50, size)]
                    # 尝试解码为文本（可能需要特殊编码）
                    try:
                        text_str = text_preview.decode('gbk', errors='replace')
                        print(f"    内容预览: {text_str}")
                    except:
                        print(f"    原始数据: {text_preview.hex(' ')}")
            else:
                print(f"  索引 {idx}: 不存在 (最大索引为 {total_resources - 1})")
    
    # 输出前20个资源的基本信息
    print(f"\n前20个资源概览:")
    for i in range(min(20, total_resources)):
        start = offsets[i]
        end = offsets[i + 1]
        size = end - start
        preview = data[start:start+min(10, size)]
        print(f"  [{i:3d}] 偏移={start:8d}, 大小={size:6d} bytes, 预览={preview.hex(' ')}")
    
    return {
        'total_resources': total_resources,
        'offsets': offsets,
        'data': data
    }

# 检查game目录下的DAT文件
game_dir = Path("d:/workspace/fd2_dat_freebuff/game")
if not game_dir.exists():
    # 尝试其他可能的位置
    game_dir = Path("d:/workspace/fd2_dat_freebuff")

print("搜索DAT文件...")
fdother_files = list(game_dir.glob("**/FDOTHER.DAT"))
fdtxt_files = list(game_dir.glob("**/FDTXT.DAT"))

if not fdother_files and not fdtxt_files:
    print(f"\n在 {game_dir} 及其子目录中未找到DAT文件")
    print("\n请提供DAT文件的路径，或创建game目录并放入DAT文件")
else:
    for f in fdother_files:
        analyze_dat_file(f)
    
    for f in fdtxt_files:
        analyze_dat_file(f)
