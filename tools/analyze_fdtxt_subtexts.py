"""
分析FDTXT.DAT文件中各资源的子文本数量
重点分析资源0-33，找出子文本数量达到514以上的资源
"""
import struct
from pathlib import Path

def find_fdtxt():
    """查找FDTXT.DAT文件"""
    paths = [
        Path("d:/workspace/fd2_dat_freebuff/game/FDTXT.DAT"),
        Path("d:/workspace/fd2_dat_freebuff/FDTXT.DAT"),
    ]
    for p in paths:
        if p.exists():
            return str(p)
    return None

def analyze_fdtxt(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"文件大小: {file_size} bytes")
    
    # 检查文件头
    header = data[0:6]
    print(f"文件头: {header}")
    
    if header != b'LLLLLL':
        print("错误: 非标准DAT格式")
        return
    
    # 解析索引表: 从偏移6开始，每项4字节(DWORD)
    # 根据IDA代码和实际数据，索引值是相对文件开头的偏移
    offsets = []
    pos = 6
    while pos + 4 <= file_size:
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset >= file_size or offset == 0:
            break
        offsets.append(offset)
        pos += 4
    
    total_resources = len(offsets) - 1
    print(f"\n总资源数: {total_resources}")
    print(f"索引表大小: {pos - 6} bytes\n")
    
    # 分析每个资源的子文本数量
    results = []
    
    for i in range(min(34, total_resources)):
        start = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else file_size
        resource_size = end - start
        
        if resource_size <= 0:
            results.append((i, 0, resource_size))
            continue
        
        # 读取资源数据
        resource_data = data[start:end]
        
        # 统计子文本数量
        # 子文本以-1(0xFFFF)分隔
        sub_count = 0
        word_count = resource_size // 2
        
        for j in range(word_count):
            word = struct.unpack_from('<H', resource_data, j * 2)[0]
            if word == 0xFFFF:  # -1 有符号
                sub_count += 1
        
        # 如果最后一个子文本没有-1结束符，也需要计算
        # 但通常应该都有结束符
        results.append((i, sub_count, resource_size))
    
    # 输出结果
    print("=" * 80)
    print("资源0-33子文本数量统计")
    print("=" * 80)
    print(f"{'资源编号':<10} {'子文本数量':<15} {'资源大小(bytes)':<15}")
    print("-" * 80)
    
    for res_idx, sub_count, res_size in results:
        print(f"{res_idx:<10} {sub_count:<15} {res_size:<15}")
    
    # 找出子文本数量>=514的资源
    print("\n" + "=" * 80)
    print("子文本数量>=514的资源:")
    print("=" * 80)
    
    found = False
    for res_idx, sub_count, res_size in results:
        if sub_count >= 514:
            print(f"  资源 {res_idx}: {sub_count} 个子文本, 大小 {res_size} bytes")
            found = True
    
    if not found:
        print("  无")
    
    # 统计信息
    print("\n" + "=" * 80)
    print("统计信息:")
    print("=" * 80)
    
    max_subs = max(results, key=lambda x: x[1])
    print(f"  最大子文本数: 资源 {max_subs[0]}, {max_subs[1]} 个子文本")
    
    total_subs = sum(r[1] for r in results)
    print(f"  资源0-33总子文本数: {total_subs}")
    
    avg_subs = total_subs / len(results) if results else 0
    print(f"  平均子文本数: {avg_subs:.1f}")

if __name__ == '__main__':
    filepath = find_fdtxt()
    if filepath:
        print(f"找到文件: {filepath}\n")
        analyze_fdtxt(filepath)
    else:
        print("未找到FDTXT.DAT文件")
