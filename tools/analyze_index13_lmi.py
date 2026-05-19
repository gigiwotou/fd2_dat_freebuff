#!/usr/bin/env python3
"""
分析FDOTHER.DAT索引13的LMI1音频内部结构
找出音频块数量、各块偏移/大小
"""

import struct
from pathlib import Path

GAME_DIR = Path("game")
DAT_MAGIC = b"LLLLLL"

def analyze_lmi1_structure():
    fdother_path = GAME_DIR / "FDOTHER.DAT"
    if not fdother_path.exists():
        print(f"错误: 找不到 {fdother_path}")
        return
    
    data = fdother_path.read_bytes()
    file_size = len(data)
    
    # 解析主索引表
    res_count = struct.unpack_from("<I", data, 6)[0]
    offsets = []
    for i in range(res_count):
        off_pos = 10 + i * 4
        if off_pos + 4 > file_size:
            break
        offsets.append(struct.unpack_from("<I", data, off_pos)[0])
    
    print(f"FDOTHER.DAT - 索引13 (LMI1音频) 详细分析")
    print(f"{'='*80}")
    
    idx = 13
    start = offsets[idx]
    end = offsets[idx + 1] if (idx + 1) < len(offsets) else file_size
    res_data = data[start:end]
    
    print(f"\n索引13基本信息:")
    print(f"  主文件偏移: 0x{start:X} ({start:,} 字节)")
    print(f"  资源大小: {len(res_data):,} 字节")
    print(f"  格式: LMI1 (音频)")
    
    # LMI1结构分析
    # 根据已有的分析，LMI1格式可能是:
    # 0-3: "LMI1" 魔术头
    # 4-7: 未知（可能是采样率或块数量）
    # 8+: 音频块偏移表（每项4字节）
    
    print(f"\nLMI1文件头分析:")
    print(f"  魔术头: {res_data[:4]}")
    print(f"  字节4-7: {struct.unpack_from('<I', res_data, 4)[0]} (0x{struct.unpack_from('<I', res_data, 4)[0]:X})")
    
    # 尝试从字节8开始解析为偏移表
    # 先看看偏移表有多少项
    print(f"\n尝试解析音频块偏移表 (从字节8开始):")
    audio_offsets = []
    
    # LMI1的偏移表可能从字节8开始
    offset_table_start = 8
    max_possible_entries = (len(res_data) - offset_table_start) // 4
    
    print(f"  最多可能有 {max_possible_entries} 个条目")
    
    # 读取前20个偏移值，看看是否合理
    print(f"\n  前20个偏移值:")
    for i in range(min(20, max_possible_entries)):
        pos = offset_table_start + i * 4
        val = struct.unpack_from("<I", res_data, pos)[0]
        audio_offsets.append(val)
        print(f"    [{i}] 0x{val:X} ({val})")
    
    # 检查这些值是否像偏移（应该递增且在文件范围内）
    print(f"\n  偏移表验证:")
    valid_offsets = [off for off in audio_offsets if off < len(res_data)]
    print(f"    有效偏移: {len(valid_offsets)}/{len(audio_offsets)}")
    
    if valid_offsets:
        print(f"    最小偏移: {min(valid_offsets)}")
        print(f"    最大偏移: {max(valid_offsets)}")
        
        # 检查是否递增
        is_increasing = all(audio_offsets[i] <= audio_offsets[i+1] 
                           for i in range(len(audio_offsets)-1) 
                           if audio_offsets[i] < len(res_data) and audio_offsets[i+1] < len(res_data))
        print(f"    是否递增: {is_increasing}")
        
        # 如果偏移表有效，解析音频块
        if len(valid_offsets) > 1 and valid_offsets[0] > 20:  # 第一个偏移应该指向数据区
            print(f"\n  音频块分析:")
            print(f"  {'块索引':>6} {'偏移':>10} {'大小':>10}")
            print(f"  {'-'*30}")
            
            for i, offset in enumerate(valid_offsets):
                if i < len(valid_offsets) - 1:
                    next_offset = valid_offsets[i + 1]
                    if next_offset > offset and next_offset < len(res_data):
                        block_size = next_offset - offset
                        print(f"  [{i:>4}]  0x{offset:>7X} {block_size:>10,}")
                else:
                    # 最后一个块到文件末尾
                    block_size = len(res_data) - offset
                    print(f"  [{i:>4}]  0x{offset:>7X} {block_size:>10,}")

if __name__ == "__main__":
    analyze_lmi1_structure()
