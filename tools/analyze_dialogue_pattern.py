#!/usr/bin/env python3
"""分析FDTXT中的控制码模式，找出双对话框交替逻辑"""

import struct
import sys

def analyze_dialogue_pattern(dat_path):
    with open(dat_path, 'rb') as f:
        data = f.read()
    
    # 解析头部
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = struct.unpack_from(f'<{count}I', data, 10)
    
    print(f"总资源集数: {count}")
    print("="*80)
    
    for res_idx in range(min(count, 20)):  # 只分析前20个
        rs = offsets[res_idx]
        re = offsets[res_idx + 1] if res_idx + 1 < count else len(data)
        
        rd = data[rs:re]
        sc = struct.unpack_from('<h', rd, 0)[0]
        offs = struct.unpack_from(f'<{sc}h', rd, 2)
        
        print(f"\n资源集 {res_idx} (偏移: {rs:#x}-{re:#x}, 子项数: {sc})")
        print("-"*80)
        
        for sub_idx in range(min(sc, 5)):  # 每个资源集只显示前5个子项
            byte_offset = offs[sub_idx]
            if byte_offset < 0 or byte_offset >= len(rd):
                print(f"  子项 {sub_idx}: 无效偏移 {byte_offset}")
                continue
            
            # 提取文本
            text_data = rd[byte_offset:]
            words = []
            i = 0
            while i < len(text_data) - 1:
                word = struct.unpack_from('<h', text_data, i)[0]
                words.append(word)
                i += 2
                if word == -1:  # TEXT_END
                    break
                if i > 1000:  # 安全限制
                    break
            
            # 分析控制码
            controls = []
            text_chars = []
            for w in words:
                if w < 0 and w >= -20:
                    controls.append(w)
                elif w >= 0:
                    text_chars.append(w)
            
            print(f"  子项 {sub_idx}: {len(words)} words, 控制码: {len(controls)}, 文本字符: {len(text_chars)}")
            
            # 显示控制码序列
            if controls:
                ctrl_names = []
                for c in controls:
                    if c == -1: ctrl_names.append("END")
                    elif c == -2: ctrl_names.append("NL")
                    elif c == -3: ctrl_names.append("NL2")
                    elif c == -4: ctrl_names.append("REC1")
                    elif c == -5: ctrl_names.append("REC2")
                    elif c == -6: ctrl_names.append("NUM")
                    elif c == -17: ctrl_names.append("PORTRAIT_F")
                    elif c == -18: ctrl_names.append("PORTRAIT_S")
                    elif c == -19: ctrl_names.append("CHAR_F")
                    elif c == -20: ctrl_names.append("CHAR_S")
                    else: ctrl_names.append(f"?({c})")
                
                print(f"    控制码: {', '.join(ctrl_names)}")
                
                # 检测对话框切换模式
                has_F = any(c in [-17, -19] for c in controls)
                has_S = any(c in [-18, -20] for c in controls)
                if has_F and has_S:
                    print(f"    ** 包含上下对话框切换 **")

if __name__ == '__main__':
    analyze_dialogue_pattern('game/FDTXT.DAT')
