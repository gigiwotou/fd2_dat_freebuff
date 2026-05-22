"""
分析FDTXT资源0的完整结构，找出所有子项的控制码
理解对话分段和精灵移动控制
"""
import struct

def analyze_all_subtexts():
    with open("game/FDTXT.DAT", "rb") as f:
        fdtxt = f.read()
    
    count = struct.unpack_from('<I', fdtxt, 6)[0]
    offsets = [struct.unpack_from('<I', fdtxt, 10 + i*4)[0] for i in range(count)]
    
    # 分析资源0的所有子项
    res_data = fdtxt[offsets[0]:offsets[1]]
    sub_count = struct.unpack_from('<h', res_data, 0)[0]
    sub_offsets = [struct.unpack_from('<h', res_data, 2 + i*2)[0] for i in range(sub_count)]
    
    print(f"=== FDTXT资源0: {sub_count}个子项 ===\n")
    
    for sub_idx in range(min(20, sub_count)):
        text_start = sub_offsets[sub_idx]
        text_end = sub_offsets[sub_idx + 1] if sub_idx + 1 < sub_count else len(res_data)
        
        print(f"\n--- 子项{sub_idx}: 偏移{text_start}-{text_end} ({text_end-text_start}字节) ---")
        
        pos = text_start
        controls = []
        chars = 0
        
        while pos < text_end:
            word = struct.unpack_from('<h', res_data, pos)[0]
            pos += 2
            
            if word == -1:
                controls.append("END")
                break
            elif word == -2:
                controls.append("NL")  # NEWLINE
            elif word == -3:
                controls.append("NL2")  # NEWLINE2 (wait)
            elif word == -19:
                cid = struct.unpack_from('<h', res_data, pos)[0]
                pos += 2
                controls.append(f"CHAR_F({cid})")
            elif word == -20:
                cid = struct.unpack_from('<h', res_data, pos)[0]
                pos += 2
                controls.append(f"CHAR_S({cid})")
            elif word == -17:
                pid = struct.unpack_from('<h', res_data, pos)[0]
                pos += 2
                controls.append(f"PORTRAIT_F({pid})")
            elif word == -18:
                pid = struct.unpack_from('<h', res_data, pos)[0]
                pos += 2
                controls.append(f"PORTRAIT_S({pid})")
            elif word == -4:
                controls.append("RECURSE1")
            elif word == -5:
                controls.append("RECURSE2")
            elif word == -6:
                val = struct.unpack_from('<h', res_data, pos)[0]
                pos += 2
                controls.append(f"NUM({val})")
            elif word >= 0:
                chars += 1
            else:
                controls.append(f"?({word})")
        
        print(f"  控制序列: {' -> '.join(controls)}")
        print(f"  字符数: {chars}")

if __name__ == "__main__":
    analyze_all_subtexts()
