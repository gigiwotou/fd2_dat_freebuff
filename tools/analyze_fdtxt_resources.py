#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析FDTXT.DAT资源索引结构
根据IDA分析: dword_53A79 = sub_111BA("FDTXT.DAT", ..., n17 + 1)
n17 = 关卡编号
需要找出各资源索引对应的内容
"""

import struct
import os

FDTXT_PATH = r"d:\testworkspace\fd2_dat_freebuff\game\FDTXT.DAT"

# 控制码定义
TEXT_END = -1
TEXT_NEWLINE = -2
TEXT_NEWLINE2 = -3
TEXT_PORTRAIT_F = -17
TEXT_PORTRAIT_S = -18
TEXT_CHAR_F = -19
TEXT_CHAR_S = -20

CONTROL_CODES = {
    TEXT_END: "END",
    TEXT_NEWLINE: "NL",
    TEXT_NEWLINE2: "NL2",
    TEXT_PORTRAIT_F: "PF",
    TEXT_PORTRAIT_S: "PS",
    TEXT_CHAR_F: "CF",
    TEXT_CHAR_S: "CS",
}

def analyze_fdtxt():
    with open(FDTXT_PATH, 'rb') as f:
        data = f.read()
    
    # 解析文件头
    magic = data[:6]
    resource_count = struct.unpack_from('<I', data, 6)[0]
    print(f"魔数: {magic}")
    print(f"资源总数: {resource_count}")
    
    # 解析资源偏移
    offsets = []
    for i in range(resource_count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    print(f"\n资源偏移表:")
    for i in range(min(50, len(offsets) - 1)):
        start = offsets[i]
        end = offsets[i + 1]
        size = end - start
        print(f"  资源{i}: 偏移={start}, 大小={size}字节")
    
    # 分析每个资源
    print(f"\n" + "="*80)
    print("各资源内容分析:")
    print("="*80)
    
    for res_idx in range(min(10, len(offsets) - 1)):
        start = offsets[res_idx]
        end = offsets[res_idx + 1]
        res_data = data[start:end]
        
        if len(res_data) < 2:
            print(f"\n资源{res_idx}: 数据太小")
            continue
        
        # 子项数量
        sub_count = struct.unpack_from('<h', res_data, 0)[0]
        print(f"\n资源{res_idx}: 大小={len(res_data)}, 子项数={sub_count}")
        
        if sub_count <= 0 or sub_count > 1000:
            print(f"  跳过(子项数异常)")
            continue
        
        # 分析前几个子项
        for sub_idx in range(min(3, sub_count)):
            sub_off = struct.unpack_from('<h', res_data, 2 + sub_idx * 2)[0]
            if sub_idx + 1 < sub_count:
                sub_end = struct.unpack_from('<h', res_data, 2 + (sub_idx + 1) * 2)[0]
            else:
                sub_end = len(res_data)
            
            if sub_off < 0 or sub_off >= len(res_data):
                continue
                
            sub_data = res_data[sub_off:sub_end]
            
            # 解析文本内容
            text_preview = []
            control_count = 0
            char_count = 0
            has_dialog = False
            
            pos = 0
            while pos + 2 <= len(sub_data) and pos < 200:
                word = struct.unpack_from('<h', sub_data, pos)[0]
                pos += 2
                
                if word == TEXT_END:
                    break
                elif word in CONTROL_CODES:
                    code = CONTROL_CODES[word]
                    text_preview.append(f"[{code}]")
                    control_count += 1
                    # 头像控制码后面有参数
                    if word in [TEXT_PORTRAIT_F, TEXT_PORTRAIT_S, TEXT_CHAR_F, TEXT_CHAR_S]:
                        if pos + 2 <= len(sub_data):
                            param = struct.unpack_from('<h', sub_data, pos)[0]
                            pos += 2
                            text_preview.append(f"({param})")
                            has_dialog = True
                else:
                    char_count += 1
            
            preview = " ".join(text_preview[:30])
            print(f"  子项{sub_idx}: 偏移={sub_off}, 大小={sub_end - sub_off}, "
                  f"控制码={control_count}, 字符={char_count}, 有对话框={'是' if has_dialog else '否'}")
            if preview:
                print(f"    预览: {preview}")

if __name__ == "__main__":
    analyze_fdtxt()
