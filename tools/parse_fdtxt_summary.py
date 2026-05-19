"""
只输出FDTXT.DAT资源0-10的简要信息
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

def parse_fdtxt_summary(filepath):
    """简要解析FDTXT.DAT文件"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"文件: {filepath}")
    print(f"大小: {file_size} bytes ({file_size/1024:.2f} KB)\n")
    
    # 解析索引表：从偏移6开始，每项4字节（低2字节是偏移，高2字节是0）
    offsets = []
    pos = 6
    
    while pos + 4 <= file_size:
        offset_word = struct.unpack_from('<H', data, pos)[0]
        offset_dword = struct.unpack_from('<I', data, pos)[0]
        
        # 如果DWORD >= 文件大小，说明到达数据区
        if offset_dword >= file_size:
            break
        
        offsets.append(offset_word)
        pos += 4
    
    print(f"索引表: 偏移6到{pos-4}, 共{len(offsets)}个索引\n")
    
    # 输出所有索引
    print("所有索引:")
    for i, offset in enumerate(offsets):
        print(f"  [{i:3d}] = {offset:5d} (0x{offset:04X})")
    
    # 解析资源0-34
    print(f"\n{'='*70}")
    print("资源0-34内容:")
    print(f"{'='*70}\n")
    
    for i in range(min(35, len(offsets))):
        start = offsets[i]
        
        if start >= file_size or start == 0:
            print(f"资源{i}: 偏移无效({start})")
            continue
        
        if i + 1 < len(offsets):
            end = offsets[i + 1]
        else:
            end = file_size
        
        size = end - start
        
        if size <= 0:
            print(f"资源{i}: 偏移={start}, 空资源")
            continue
        
        resource_data = data[start:end]
        
        # 解析为WORD数组
        word_count = size // 2
        words = []
        for j in range(word_count):
            word = struct.unpack_from('<h', resource_data, j * 2)[0]
            words.append(word)
        
        # 找到-1结束标记
        end_pos = -1
        for j, word in enumerate(words):
            if word == -1:
                end_pos = j
                break
        
        if end_pos != -1:
            actual_count = end_pos + 1
        else:
            actual_count = len(words)
        
        # 简要显示
        print(f"\n资源{i}: 偏移={start}, WORD数={actual_count}")
        
        # 显示前20个WORD
        display = []
        j = 0
        while j < min(20, actual_count):
            word = words[j]
            if word == -1:
                display.append("[结束]")
                break
            elif word == -2:
                display.append("[换行]")
            elif word == -3:
                display.append("[换行+模式]")
            elif word == -4:
                display.append("[递归]")
            elif word == -5:
                display.append("[递归]")
            elif word == -6:
                display.append("[数字]")
            elif word == -17:
                if j + 1 < len(words):
                    display.append(f"[DATO({words[j+1]})]")
                    j += 1
            elif word == -18:
                if j + 1 < len(words):
                    display.append(f"[DATO36887({words[j+1]})]")
                    j += 1
            elif word == -19:
                if j + 1 < len(words):
                    display.append(f"[图标DATO({words[j+1]})]")
                    j += 1
            elif word == -20:
                if j + 1 < len(words):
                    display.append(f"[图标DATO36887({words[j+1]})]")
                    j += 1
            elif word < 0:
                display.append(f"[{word}]")
            else:
                display.append(str(word))
            j += 1
        
        print(f"  内容: {' '.join(display)}")
        if actual_count > 20:
            print(f"  ... (还有{actual_count - 20}个WORD)")

if __name__ == '__main__':
    filepath = find_fdtxt_dat()
    if filepath:
        parse_fdtxt_summary(filepath)
    else:
        print("未找到FDTXT.DAT文件")
