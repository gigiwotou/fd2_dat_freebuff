"""
重新解析FDTXT.DAT文件
根据IDA反编译代码：v15 = (__int16*)(*(__int16*)(arg0 + 2 * arg4) + arg0);
- 索引表在文件开头，每项2字节（WORD）
- 索引值是相对于文件开头的偏移
- 文本数据是WORD数组，以-1(0xFFFF)结束
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
    print(f"{'='*70}\n")
    
    # 查看前100字节的原始数据，帮助判断格式
    print("文件前100字节（十六进制）:")
    for i in range(0, min(100, file_size), 16):
        hex_str = data[i:i+16].hex(' ')
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    print(f"\n{'='*70}")
    print("尝试解析索引表（从偏移0开始，每项2字节）:")
    print(f"{'='*70}\n")
    
    # 解析2字节索引
    offsets = []
    pos = 0
    while pos + 2 <= file_size:
        offset = struct.unpack_from('<H', data, pos)[0]
        
        # 如果偏移超出文件范围或为0，可能是索引结束
        if offset >= file_size:
            break
        
        offsets.append(offset)
        pos += 2
        
        # 如果索引数量太多，可能解析错误
        if len(offsets) > 1000:
            break
    
    print(f"索引表位置: 偏移 0 - {pos-2}")
    print(f"索引项数量: {len(offsets)}")
    print(f"每项大小: 2字节")
    print(f"索引表总大小: {pos} 字节\n")
    
    # 输出前35个索引
    print("前35个索引:")
    for i, offset in enumerate(offsets[:35]):
        print(f"  索引[{i:2d}] = {offset:5d} (0x{offset:04X})")
    
    # 解析每个资源的内容
    print(f"\n{'='*70}")
    print("资源内容解析 (0-34):")
    print(f"{'='*70}\n")
    
    for i in range(min(35, len(offsets))):
        start = offsets[i]
        
        # 下一个资源的开始位置就是当前资源的结束
        if i + 1 < len(offsets):
            end = offsets[i + 1]
        else:
            end = file_size
        
        size = end - start
        
        if start >= file_size:
            print(f"--- 资源 {i}: 偏移超出范围 ---")
            continue
        
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
            print(f"  WORD数量: {actual_count} (无结束标记)")
        
        # 解析并显示内容
        print(f"  内容:")
        display_count = min(80, actual_count)
        
        line_text = "    "
        char_count = 0
        for j in range(display_count):
            word = words[j]
            
            if word == -1:
                line_text += "[-1结束] "
                print(line_text)
                line_text = "    "
                char_count = 0
                break
            elif word == -2:
                if line_text.strip():
                    print(line_text)
                line_text = "    [-2换行]"
                char_count = 0
            elif word == -3:
                if line_text.strip():
                    print(line_text)
                line_text = "    [-3换行+模式]"
                char_count = 0
            elif word == -4:
                line_text += "[-4递归AD9] "
            elif word == -5:
                line_text += "[-5递归ADD] "
            elif word == -6:
                line_text += "[-6数字] "
            elif word == -17:
                # 下一个WORD是参数
                if j + 1 < len(words):
                    line_text += f"[-17 DATO({words[j+1]})] "
                    j += 1  # 跳过参数
            elif word == -18:
                if j + 1 < len(words):
                    line_text += f"[-18 DATO({words[j+1]})] "
                    j += 1
            elif word == -19:
                if j + 1 < len(words):
                    line_text += f"[-19 图标DATO({words[j+1]})] "
                    j += 1
            elif word == -20:
                if j + 1 < len(words):
                    line_text += f"[-20 图标DATO({words[j+1]})] "
                    j += 1
            elif word < 0:
                line_text += f"[控制码{word}] "
            else:
                # 字符索引
                line_text += f"{word} "
                char_count += 1
            
            # 每行最多显示15个元素
            if char_count >= 15:
                print(line_text)
                line_text = "    "
                char_count = 0
        
        if line_text.strip() and line_text != "    ":
            print(line_text)
        
        if actual_count > 80:
            print(f"    ... (还有 {actual_count - 80} 个WORD)")

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
        print("  - d:/workspace/fd2_ida_hex")
