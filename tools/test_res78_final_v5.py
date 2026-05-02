#!/usr/bin/env python3
"""
根据IDA汇编代码精确解析res78。

从sub_25A96汇编:
- a1 = 缓冲区指针 (_FDOTHER.DAT_)
- a6 = 样本索引 (0)  
- a7 = 循环计数 (1)

关键代码:
v8 = a5 + 4 * a6   # a5=缓冲区, a6=0, 所以 v8=缓冲区
v13 = *(v8 + 6) + a5  # 从v8+6读取4字节，加上v8得到绝对地址
v12 = *(v8 + 10) - *(v8 + 6)  # 样本大小

所以对于res78:
*(6) = 0x00000000 (样本起始相对偏移)
*(10) = 0x000018d7 (样本结束相对偏移)
样本大小 = 0x18d7 - 0x0 = 6359字节
"""

import struct
import wave
import io
from pathlib import Path


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    res_idx = 78
    res_start = offsets[res_idx]
    res_end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[res_start:res_end]
    
    print(f"Res78: {len(raw)} bytes")
    
    # 根据IDA汇编精确解析
    # *(6) 是相对偏移，从缓冲区+6开始读取4字节
    # 但*(6)和*(10)应该是指向内部的偏移
    
    print(f"\n前32字节:")
    for i in range(0, 32, 16):
        hex_str = raw[i:i+16].hex(' ')
        print(f"  {i:04x}: {hex_str}")
    
    # 尝试不同解析方式
    print(f"\n--- 尝试不同字段解释 ---")
    
    # 假设头部结构:
    # 偏移0-3: 标志
    # 偏移4-7: count?
    # 偏移8-11: 起始偏移
    # 偏移12-15: 结束偏移
    
    v6 = struct.unpack_from('<I', raw, 6)[0]
    v10 = struct.unpack_from('<I', raw, 10)[0]
    print(f"*(6) as uint32: 0x{v6:x} ({v6})")
    print(f"*(10) as uint32: 0x{v10:x} ({v10})")
    
    # 另一种解析：假设偏移表在偏移4
    c1 = struct.unpack_from('<H', raw, 0)[0]
    c2 = struct.unpack_from('<H', raw, 2)[0]
    print(f"\n假设: count1={c1}, count2={c2}")
    
    if c2 == 2:
        # 2个偏移项
        for i in range(c2):
            pos = 4 + i * 4
            val = struct.unpack_from('<I', raw, pos)[0]
            print(f"  offset[{i}] at {pos}: 0x{val:x} ({val})")
        
        # 但这样只有2个偏移，可能结构是:
        # [4字节: count1, count2] [8字节: offset[0], offset[1]] [数据]
        # offset[0] = 0 (样本0起始)
        # offset[1] = 0x10 (样本1起始)
        # 但这样样本0只有16字节
        
        # 或者: [4字节: count1, count2] [8字节: 样本起始, 样本结束] [样本数据]
        start = struct.unpack_from('<I', raw, 4)[0]  # 0
        end = struct.unpack_from('<I', raw, 8)[0]    # 0x10
        print(f"\n假设: start=0x{start:x}, end=0x{end:x}")
        
        # 如果样本从0x10开始
        sample_start = 0x10
        sample_end = len(raw)
        sample_size = sample_end - sample_start
        print(f"样本: {sample_start} ~ {sample_end}, 大小={sample_size}")
        
        if sample_size > 0:
            sample_data = raw[sample_start:sample_end]
            print(f"样本前32字节: {sample_data[:32].hex(' ')}")
            
            # 尝试8-bit PCM
            output_dir = Path("output/sfx_wav/res078_final_v5")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for sr in [5512, 8000, 11025, 16000]:
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(1)
                    wf.setframerate(sr)
                    wf.writeframes(sample_data)
                (output_dir / f"from16_8bit_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
            
            print(f"\nGenerated files in: {output_dir}")


if __name__ == "__main__":
    main()
