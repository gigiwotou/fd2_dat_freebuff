#!/usr/bin/env python3
"""
FDTXT.DAT 控制码参数格式分析工具

重点分析以下控制码后面的参数格式：
- TEXT_CHAR_F(-19): 从dword_53A45加载角色头像(正面)
- TEXT_PORTRAIT_F(-17): 加载头像(正面)
- TEXT_PORTRAIT_S(-18): 加载头像(侧面)
- TEXT_CHAR_S(-20): 从dword_53A45加载角色头像(侧面)

功能：
1. 扫描所有资源集的所有子项
2. 找出包含上述控制码的文本项
3. 对于每个找到的文本项，输出：
   - 资源集索引和子项索引
   - 控制码位置
   - 控制码后面的5个值（用于分析参数格式）
   - 控制码之后的所有字符值

通过分析这些值来判断：
- 控制码后面是跟一个参数值，还是跟多个字符值
- 参数值的格式和范围
"""

import struct
from pathlib import Path

# 文件路径
FDTXT_PATH = "game/FDTXT.DAT"

# 目标控制码定义
TARGET_CONTROL_CODES = {
    -17: "TEXT_PORTRAIT_F",  # 加载头像(正面)
    -18: "TEXT_PORTRAIT_S",  # 加载头像(侧面)
    -19: "TEXT_CHAR_F",      # 从dword_53A45加载角色头像(正面)
    -20: "TEXT_CHAR_S",      # 从dword_53A45加载角色头像(侧面)
}

# 所有控制码定义（用于识别）
ALL_CONTROL_CODES = {
    -1: "TEXT_END",           # 文本结束
    -2: "TEXT_NEWLINE",       # 换行
    -3: "TEXT_NEWLINE2",      # 换行+清除状态
    -4: "TEXT_RECURSE1",      # 递归调用dword_53A7D
    -5: "TEXT_RECURSE2",      # 递归调用dword_53ADD
    -6: "TEXT_SHOW_NUM",      # 显示数值dword_53AE1
    -17: "TEXT_PORTRAIT_F",   # 加载头像(正面)
    -18: "TEXT_PORTRAIT_S",   # 加载头像(侧面)
    -19: "TEXT_CHAR_F",       # 从dword_53A45加载角色头像(正面)
    -20: "TEXT_CHAR_S",       # 从dword_53A45加载角色头像(侧面)
}


def parse_fdtxt(filepath):
    """解析FDTXT.DAT文件，返回所有资源集和子项"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 解析资源集偏移表（从字节6开始，每4字节一个偏移）
    offsets = []
    pos = 6
    while pos + 4 <= len(data):
        offset = struct.unpack_from('<I', data, pos)[0]
        if offset > len(data):
            break
        offsets.append(offset)
        pos += 4
    
    count = len(offsets)
    print(f"文件大小: {len(data)} 字节")
    print(f"资源集数量: {count}")
    print()
    
    # 解析所有资源集和子项
    results = []
    
    for res_idx in range(count):
        res_start = offsets[res_idx]
        res_end = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
        res_data = data[res_start:res_end]
        
        # 子项数量
        if len(res_data) < 2:
            continue
        
        sub_count = struct.unpack_from('<h', res_data, 0)[0]
        if sub_count <= 0:
            continue
        
        # 遍历所有子项
        for sub_idx in range(sub_count):
            sub_offset = struct.unpack_from('<h', res_data, 2 + sub_idx * 2)[0]
            if sub_idx + 1 < sub_count:
                next_sub_offset = struct.unpack_from('<h', res_data, 2 + (sub_idx + 1) * 2)[0]
            else:
                next_sub_offset = len(res_data)
            
            sub_data = res_data[sub_offset:next_sub_offset]
            
            # 解析子项中的int16_t值
            words = []
            i = 0
            while i + 2 <= len(sub_data):
                value = struct.unpack_from('<h', sub_data, i)[0]
                words.append(value)
                i += 2
            
            results.append({
                'res_idx': res_idx,
                'sub_idx': sub_idx,
                'words': words,
                'res_start': res_start,
                'sub_offset': sub_offset,
            })
    
    return results


def analyze_target_control_codes(all_items):
    """分析目标控制码后面的值"""
    
    found_count = 0
    control_code_stats = {-17: 0, -18: 0, -19: 0, -20: 0}
    
    print("=" * 120)
    print("扫描结果汇总")
    print("=" * 120)
    
    for item in all_items:
        res_idx = item['res_idx']
        sub_idx = item['sub_idx']
        words = item['words']
        
        # 查找目标控制码
        for word_idx, word in enumerate(words):
            if word in TARGET_CONTROL_CODES:
                found_count += 1
                control_code_stats[word] = control_code_stats.get(word, 0) + 1
                
                code_name = TARGET_CONTROL_CODES[word]
                
                print(f"\n{'=' * 120}")
                print(f"找到控制码: {code_name}({word})")
                print(f"位置: 资源集索引={res_idx}, 子项索引={sub_idx}, 控制码在文本中的位置={word_idx}")
                print(f"{'=' * 120}")
                
                # 获取控制码后面的值
                # 显示后面5个值
                next_values = words[word_idx + 1:word_idx + 6]
                
                print(f"\n控制码后面的5个值:")
                for i, val in enumerate(next_values):
                    if val == -1:
                        label = "TEXT_END (文本结束)"
                    elif val == -2:
                        label = "TEXT_NEWLINE (换行)"
                    elif val == -3:
                        label = "TEXT_NEWLINE2 (换行+清除)"
                    elif val == -4:
                        label = "TEXT_RECURSE1 (递归1)"
                    elif val == -5:
                        label = "TEXT_RECURSE2 (递归2)"
                    elif val == -6:
                        label = "TEXT_SHOW_NUM (显示数值)"
                    elif val in TARGET_CONTROL_CODES:
                        label = f"{TARGET_CONTROL_CODES[val]}({val})"
                    elif val < 0:
                        label = f"UNKNOWN({val})"
                    else:
                        label = f"CHAR({val}) - 字体索引"
                    print(f"  [{i+1}] 值={val:5d}  {label}")
                
                # 显示控制码之后的所有值（最多50个，避免输出太长）
                remaining = words[word_idx + 1:]
                max_show = 50
                
                print(f"\n控制码之后的所有值（共{len(remaining)}个，显示前{min(max_show, len(remaining))}个）:")
                for i, val in enumerate(remaining[:max_show]):
                    if val == -1:
                        label = "TEXT_END"
                        print(f"  [{i}] {val:5d}  {label} <-- 文本结束")
                        break  # 遇到结束标记就停止
                    elif val == -2:
                        label = "TEXT_NEWLINE"
                    elif val == -3:
                        label = "TEXT_NEWLINE2"
                    elif val == -4:
                        label = "TEXT_RECURSE1"
                    elif val == -5:
                        label = "TEXT_RECURSE2"
                    elif val == -6:
                        label = "TEXT_SHOW_NUM"
                    elif val in TARGET_CONTROL_CODES:
                        label = f"{TARGET_CONTROL_CODES[val]}({val})"
                    elif val < 0:
                        label = f"UNKNOWN({val})"
                    else:
                        label = f"CHAR({val})"
                    print(f"  [{i}] {val:5d}  {label}")
                
                if len(remaining) > max_show:
                    print(f"  ... (还有 {len(remaining) - max_show} 个值)")
                
                # 分析：判断第一个值是否是参数
                if len(next_values) > 0:
                    first_val = next_values[0]
                    print(f"\n分析:")
                    print(f"  第一个值: {first_val}")
                    
                    if first_val == -1:
                        print(f"  -> 控制码后立即遇到TEXT_END，可能没有参数")
                    elif first_val == -2 or first_val == -3:
                        print(f"  -> 控制码后立即换行，可能没有参数")
                    elif first_val < 0:
                        print(f"  -> 第一个值是负数(控制码)，可能控制码没有独立参数")
                    elif first_val < 100:
                        print(f"  -> 第一个值较小({first_val})，可能是参数索引")
                    elif first_val < 1824:
                        print(f"  -> 第一个值在字体索引范围内(0-1823)，可能是字符")
                    else:
                        print(f"  -> 第一个值超出字体索引范围(>1823)，可能是特殊参数")
                
                print()
    
    # 统计汇总
    print("\n" + "=" * 120)
    print("统计汇总")
    print("=" * 120)
    print(f"总共找到 {found_count} 个目标控制码:")
    for code, count in sorted(control_code_stats.items()):
        code_name = TARGET_CONTROL_CODES.get(code, f"UNKNOWN({code})")
        print(f"  {code_name}({code}): {count} 次")


def main():
    """主函数"""
    if not Path(FDTXT_PATH).exists():
        print(f"错误: 找不到文件 {FDTXT_PATH}")
        return
    
    print("开始解析FDTXT.DAT文件...")
    all_items = parse_fdtxt(FDTXT_PATH)
    print(f"共解析 {len(all_items)} 个文本项")
    print()
    
    print("开始分析目标控制码...")
    analyze_target_control_codes(all_items)


if __name__ == "__main__":
    main()
