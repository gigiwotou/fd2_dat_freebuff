"""
读取FDTXT.DAT资源0的子文本514、515、516的内容
打印原始int16值和对应的字符
"""
import struct
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
    """解析FDTXT.DAT文件，返回所有子文本"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    
    # 检查文件头
    header = data[0:6]
    if header != b'LLLLLL':
        print(f"错误: 非标准DAT格式，文件头: {header.hex(' ')}")
        return None
    
    # 解析索引表：从偏移6开始，每项4字节（DWORD）
    offsets = []
    pos = 6
    while pos + 4 <= file_size:
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset >= file_size or offset == 0:
            break
        offsets.append(offset)
        pos += 4
    
    total_resources = len(offsets) - 1
    print(f"总资源数: {total_resources}")
    
    if len(offsets) < 1:
        print("错误: 没有足够的资源")
        return None
    
    # 读取资源0
    start = offsets[0]
    end = offsets[1] if len(offsets) > 1 else file_size
    resource_size = end - start
    
    print(f"\n资源0: 偏移={start}, 大小={resource_size} bytes")
    
    # 读取资源0的WORD数据
    resource_data = data[start:end]
    word_count = resource_size // 2
    
    words = []
    for j in range(word_count):
        word = struct.unpack_from('<h', resource_data, j * 2)[0]  # 有符号int16
        words.append(word)
    
    # 分割子文本（以-1/0xFFFF为分隔符）
    sub_texts = []
    current_sub = []
    
    for word in words:
        if word == -1:  # 子文本结束标记
            sub_texts.append(current_sub)
            current_sub = []
        else:
            current_sub.append(word)
    
    # 如果还有剩余内容（最后一个子文本可能没有-1）
    if current_sub:
        sub_texts.append(current_sub)
    
    print(f"子文本总数: {len(sub_texts)}")
    
    return sub_texts


def print_sub_text(sub_index, words):
    """打印子文本内容"""
    print(f"\n{'='*70}")
    print(f"子文本 {sub_index}")
    print(f"{'='*70}")
    print(f"WORD数量: {len(words)}")
    print(f"\n原始int16值及对应字符:")
    print(f"{'索引':<8} {'int16值':<10} {'十六进制':<10} {'类型'}")
    print(f"{'-'*70}")
    
    for i, word in enumerate(words):
        hex_val = f"0x{word & 0xFFFF:04X}"
        
        if word == -1:
            char_type = "结束标记"
        elif word == -2:
            char_type = "换行"
        elif word == -3:
            char_type = "换行+模式"
        elif word == -4:
            char_type = "递归显示dword_53AD9"
        elif word == -5:
            char_type = "递归显示dword_53ADD"
        elif word == -6:
            char_type = "显示数字"
        elif word >= -20 and word < 0:
            char_type = f"控制码({word})"
        elif word >= 0 and word <= 1823:
            char_type = f"字符索引({word})"
        else:
            char_type = f"未知({word})"
        
        print(f"[{i:<5}] {word:<10} {hex_val:<10} {char_type}")


def main():
    filepath = find_fdtxt_dat()
    
    if not filepath:
        print("未找到FDTXT.DAT文件")
        print("请将文件放在以下目录之一:")
        print("  - d:/workspace/fd2_dat_freebuff/game")
        print("  - d:/workspace/fd2_dat_freebuff")
        print("  - d:/workspace/fd2_ida_hex/fd2")
        return
    
    print(f"找到文件: {filepath}\n")
    
    sub_texts = parse_fdtxt(filepath)
    
    if sub_texts is None:
        return
    
    # 打印子文本514、515、516
    target_indices = [514, 515, 516]
    
    for idx in target_indices:
        if idx < len(sub_texts):
            print_sub_text(idx, sub_texts[idx])
        else:
            print(f"\n错误: 子文本{idx}不存在（总共只有{len(sub_texts)}个子文本）")


if __name__ == '__main__':
    main()
