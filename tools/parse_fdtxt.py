"""
解析FDTXT.DAT文件，查看资源0-34的内容
了解文本格式和ID映射方式

根据文档分析：
- 索引表从偏移0开始，每项2字节（WORD）
- 文本数据是WORD数组，以-1(0xFFFF)结束
- 控制码：-1结束，-2换行，-3换行+模式，-4/-5递归，-6数字，-17到-20对话框
- 正值是字符索引(0-1823)
"""
import struct
import os
from pathlib import Path

def find_fdtxt_dat():
    """查找FDTXT.DAT文件"""
    search_dirs = [
        Path("d:/workspace/fd2_dat_freebuff/game"),
        Path("d:/workspace/fd2_dat_freebuff"),
        Path("d:/workspace/fd2_ida_hex/fd2"),
        Path("d:/workspace/fd2_ida_hex"),
    ]
    
    for base_dir in search_dirs:
        if base_dir.exists():
            for f in base_dir.glob("**/FDTXT.DAT"):
                return str(f)
    
    return None

def parse_fdtxt(filepath):
    """解析FDTXT.DAT文件"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"{'='*70}")
    print(f"文件: {filepath}")
    print(f"大小: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    # 检查文件头
    header = data[0:6]
    print(f"文件头(前6字节): {header.hex(' ')} = '{header.decode('ascii', errors='replace')}'")
    
    if header != b'LLLLLL':
        print("警告: 非标准DAT文件格式，尝试其他格式解析")
        return parse_alternative_format(data, file_size)
    
    # 解析索引表：从偏移6开始，每项4字节（标准DAT格式）
    # 或者每项2字节（文本DAT格式）
    
    # 先尝试2字节索引（根据文档）
    print("\n尝试2字节索引格式（WORD数组）...")
    offsets_16 = []
    pos = 6
    while pos + 2 <= file_size:
        offset = struct.unpack_from('<H', data, pos)[0]
        if offset > file_size:
            break
        offsets_16.append(offset)
        pos += 2
    
    print(f"2字节索引数量: {len(offsets_16)}")
    
    # 也尝试4字节索引
    print("\n尝试4字节索引格式（DWORD数组）...")
    offsets_32 = []
    pos = 6
    while pos + 4 <= file_size:
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > file_size:
            break
        offsets_32.append(offset)
        pos += 4
    
    print(f"4字节索引数量: {len(offsets_32)}")
    
    # 判断使用哪种格式
    # 如果2字节索引的第一个值很小（<1000），说明可能是正确的
    if offsets_16 and offsets_16[0] < 1000:
        print("\n使用2字节索引格式")
        offsets = offsets_16
    else:
        print("\n使用4字节索引格式")
        offsets = offsets_32
    
    total_resources = len(offsets) - 1
    print(f"资源数量: {total_resources}")
    print(f"索引范围: 0 - {total_resources - 1}")
    
    # 输出索引表
    print(f"\n索引表:")
    for i, offset in enumerate(offsets[:20]):
        print(f"  索引{i}: 偏移 {offset} (0x{offset:X})")
    
    if len(offsets) > 20:
        print(f"  ... 还有 {len(offsets) - 20} 个索引")
    
    # 解析每个资源的内容
    print(f"\n{'='*70}")
    print("资源内容解析:")
    print(f"{'='*70}")
    
    for i in range(min(35, total_resources)):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else file_size
        size = end - start
        
        print(f"\n--- 资源 {i}: 偏移={start}, 大小={size} bytes ---")
        
        if size == 0:
            print("  (空资源)")
            continue
        
        # 读取资源数据
        resource_data = data[start:end]
        
        # 尝试解析为WORD数组
        word_count = size // 2
        words = []
        for j in range(word_count):
            word = struct.unpack_from('<h', resource_data, j * 2)[0]  # 有符号
            words.append(word)
        
        # 显示前50个WORD值
        print(f"  WORD数组 (前50个):")
        display_count = min(50, len(words))
        for j in range(display_count):
            word = words[j]
            if word == -1:
                print(f"    [{j}] = {word} (结束标记)")
                break
            elif word == -2:
                print(f"    [{j}] = {word} (换行)")
            elif word == -3:
                print(f"    [{j}] = {word} (换行+模式)")
            elif word == -4:
                print(f"    [{j}] = {word} (递归显示dword_53AD9)")
            elif word == -5:
                print(f"    [{j}] = {word} (递归显示dword_53ADD)")
            elif word == -6:
                print(f"    [{j}] = {word} (显示数字)")
            elif word >= -20 and word < 0:
                print(f"    [{j}] = {word} (控制码)")
            else:
                # 字符索引
                print(f"    [{j}] = {word} (字符索引)")
        
        if len(words) > 50:
            print(f"    ... 还有 {len(words) - 50} 个WORD")
        
        # 显示原始十六进制（前32字节）
        print(f"  原始数据 (前32字节):")
        hex_data = resource_data[:32].hex(' ')
        print(f"    {hex_data}")

def parse_alternative_format(data, file_size):
    """尝试其他格式解析"""
    # 可能没有LLLLLL文件头，直接从偏移0开始
    print("\n尝试无文件头格式...")
    
    # 尝试2字节索引
    offsets_16 = []
    pos = 0
    while pos + 2 <= file_size:
        offset = struct.unpack_from('<H', data, pos)[0]
        if offset > file_size or offset == 0:
            break
        offsets_16.append(offset)
        pos += 2
    
    if offsets_16 and offsets_16[0] < 1000:
        print(f"使用2字节索引，数量: {len(offsets_16)}")
        # 继续解析...
    else:
        print("无法识别的格式")

if __name__ == '__main__':
    filepath = find_fdtxt_dat()
    if filepath:
        parse_fdtxt(filepath)
    else:
        print("未找到FDTXT.DAT文件")
        print("请将文件放在以下目录之一:")
        print("  - d:/workspace/fd2_dat_freebuff/game")
        print("  - d:/workspace/fd2_dat_freebuff")
        print("  - d:/workspace/fd2_ida_hex/fd2")
