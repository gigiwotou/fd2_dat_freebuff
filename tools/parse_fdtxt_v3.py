"""
正确解析FDTXT.DAT文件

根据十六进制数据和IDA代码分析：
- 前6字节: 文件头 "LLLLLL"
- 偏移6开始: 索引表，每项4字节（DWORD），但高2字节都是0
- 或者每项2字节（WORD）

根据IDA代码: v15 = (__int16*)(*(__int16*)(arg0 + 2 * arg4) + arg0);
- 索引表从文件开头（arg0）开始
- 每项2字节（WORD）
- 索引值是相对文件开头的偏移

实际数据（从偏移6开始）:
  92 00 00 00 → 92 00 = 0x0092 = 146 (如果2字节)
  66 1e 00 00 → 66 1e = 0x1E66 = 7782
  6e 2f 00 00 → 6e 2f = 0x2F6E = 12142

所以应该从偏移6开始，每项4字节，取低2字节作为偏移
或者从偏移6开始，每2字节读取一次，跳过间隔的2字节0
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
    """解析FDTXT.DAT文件"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"{'='*70}")
    print(f"文件: {filepath}")
    print(f"大小: {file_size} bytes ({file_size/1024:.2f} KB)")
    print(f"{'='*70}\n")
    
    # 查看前100字节的原始数据
    print("文件前100字节（十六进制）:")
    for i in range(0, min(100, file_size), 16):
        hex_str = data[i:i+16].hex(' ')
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # 确认文件头
    header = data[0:6]
    print(f"\n文件头: {header.decode('ascii', errors='replace')}")
    
    if header != b'LLLLLL':
        print("警告: 非标准DAT文件格式")
        return
    
    # 解析索引表：从偏移6开始
    # 观察数据模式：每4字节中，低2字节是偏移，高2字节是0
    # 所以可以按4字节读取DWORD，或者按2字节读取WORD并跳过下一个2字节
    
    print(f"\n{'='*70}")
    print("解析索引表（从偏移6开始）:")
    print(f"{'='*70}\n")
    
    offsets = []
    pos = 6
    
    # 尝试4字节格式
    print("尝试4字节格式（DWORD）:")
    test_pos = 6
    while test_pos + 4 <= file_size:
        offset = struct.unpack_from('<I', data, test_pos)[0]
        if offset >= file_size or offset == 0:
            break
        print(f"  偏移{test_pos}: {offset} (0x{offset:04X})")
        test_pos += 4
        if len(offsets) >= 5:
            break
    
    # 尝试2字节格式（跳过每2字节后的2字节0）
    print("\n尝试2字节格式（每4字节块的低2字节）:")
    test_pos = 6
    while test_pos + 4 <= file_size:
        offset = struct.unpack_from('<H', data, test_pos)[0]
        print(f"  偏移{test_pos}: {offset} (0x{offset:04X})")
        test_pos += 4
        if len(offsets) >= 5:
            break
    
    # 根据观察，索引表是4字节每项，但实际偏移值在低2字节
    # 或者理解为每项2字节，但每隔2字节有2字节填充
    print(f"\n{'='*70}")
    print("按4字节每项解析索引表:")
    print(f"{'='*70}\n")
    
    pos = 6
    while pos + 4 <= file_size:
        offset_dword = struct.unpack_from('<I', data, pos)[0]
        offset_word = struct.unpack_from('<H', data, pos)[0]
        
        # 如果高2字节不为0，说明不是这种格式
        if offset_dword >= file_size:
            # 可能已经到达数据区
            break
        
        # 使用低2字节作为偏移
        offsets.append(offset_word)
        pos += 4
    
    print(f"索引表位置: 偏移 6 - {pos-4}")
    print(f"索引项数量: {len(offsets)}")
    print(f"每项大小: 4字节（低2字节是偏移，高2字节是0）")
    print(f"索引表总大小: {pos - 6} 字节\n")
    
    # 输出前35个索引
    print("前35个索引:")
    for i, offset in enumerate(offsets[:35]):
        print(f"  索引[{i:2d}] = {offset:5d} (0x{offset:04X})")
    
    # 验证：检查这些偏移位置的数据是否像文本
    print(f"\n{'='*70}")
    print("验证索引偏移位置的数据:")
    print(f"{'='*70}\n")
    
    for i in range(min(5, len(offsets))):
        offset = offsets[i]
        if offset > 0 and offset < file_size:
            print(f"索引{i} 偏移 {offset} (0x{offset:04X}):")
            # 显示该位置前16字节
            chunk = data[offset:offset+16]
            hex_str = chunk.hex(' ')
            print(f"  数据: {hex_str}")
            # 尝试解析为WORD
            if len(chunk) >= 4:
                w0 = struct.unpack_from('<H', chunk, 0)[0]
                w1 = struct.unpack_from('<H', chunk, 2)[0]
                print(f"  WORD[0]={w0}, WORD[1]={w1}")
            print()
    
    # 解析每个资源的内容
    print(f"{'='*70}")
    print("资源内容解析 (0-34):")
    print(f"{'='*70}\n")
    
    for i in range(min(35, len(offsets))):
        start = offsets[i]
        
        if start >= file_size or start == 0:
            print(f"--- 资源 {i}: 偏移无效 ({start}) ---")
            continue
        
        # 下一个资源的开始位置就是当前资源的结束
        if i + 1 < len(offsets):
            end = offsets[i + 1]
        else:
            end = file_size
        
        size = end - start
        
        print(f"\n{'─' * 70}")
        print(f"资源 {i}: 文件偏移={start} (0x{start:04X}), 大小={size} bytes")
        print(f"{'─' * 70}")
        
        if size <= 0:
            print("  (空资源)")
            continue
        
        # 读取资源数据
        resource_data = data[start:end]
        
        # 解析为有符号WORD数组
        word_count = size // 2
        words = []
        for j in range(word_count):
            word = struct.unpack_from('<h', resource_data, j * 2)[0]  # 有符号16位
            words.append(word)
        
        # 找到-1结束标记的位置
        end_marker_pos = -1
        for j, word in enumerate(words):
            if word == -1:
                end_marker_pos = j
                break
        
        if end_marker_pos != -1:
            actual_count = end_marker_pos + 1  # 包含结束标记
            print(f"  WORD数量: {actual_count} (包含结束标记-1)")
        else:
            actual_count = len(words)
            print(f"  WORD数量: {actual_count} (无结束标记，可能不是文本数据)")
        
        # 解析并显示内容
        print(f"  内容:")
        display_count = min(100, actual_count)
        
        line_text = "    "
        char_count = 0
        j = 0
        while j < display_count:
            word = words[j]
            
            if word == -1:
                line_text += "[结束] "
                print(line_text)
                line_text = "    "
                char_count = 0
                break
            elif word == -2:
                if line_text.strip():
                    print(line_text)
                line_text = "    [换行]"
                char_count = 0
            elif word == -3:
                if line_text.strip():
                    print(line_text)
                line_text = "    [换行+模式]"
                char_count = 0
            elif word == -4:
                line_text += "[递归AD9] "
            elif word == -5:
                line_text += "[递归ADD] "
            elif word == -6:
                line_text += "[数字] "
            elif word == -17:
                # 下一个WORD是参数
                if j + 1 < len(words):
                    line_text += f"[DATO({words[j+1]})] "
                    j += 1  # 跳过参数
            elif word == -18:
                if j + 1 < len(words):
                    line_text += f"[DATO36887({words[j+1]})] "
                    j += 1
            elif word == -19:
                if j + 1 < len(words):
                    line_text += f"[图标DATO({words[j+1]})] "
                    j += 1
            elif word == -20:
                if j + 1 < len(words):
                    line_text += f"[图标DATO36887({words[j+1]})] "
                    j += 1
            elif word < 0:
                line_text += f"[控制码{word}] "
            else:
                # 字符索引
                line_text += f"字符{word} "
                char_count += 1
            
            # 每行最多显示10个元素
            if char_count >= 10:
                print(line_text)
                line_text = "    "
                char_count = 0
            
            j += 1
        
        if line_text.strip() and line_text != "    ":
            print(line_text)
        
        if actual_count > 100:
            print(f"    ... (还有 {actual_count - 100} 个WORD)")

if __name__ == '__main__':
    filepath = find_fdtxt_dat()
    if filepath:
        parse_fdtxt(filepath)
    else:
        print("未找到FDTXT.DAT文件")
