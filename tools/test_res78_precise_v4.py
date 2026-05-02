#!/usr/bin/env python3
"""
根据IDA代码重新解析res78的内部结构。

从sub_25A96的代码分析：
v8 = a5 + 4 * a6
v13 = *(v8 + 6) + a5    # 样本起始地址
v12 = *(v8 + 10) - *(v8 + 6)  # 样本大小

调用: sub_25A96((int)_FDOTHER.DAT_, 0, 1)
a5=0, a6=1, a7=1

但v8 = 0 + 4*1 = 4
v13 = *(4 + 6) + 0 = *(10)
v12 = *(4 + 10) - *(4 + 6) = *(14) - *(10)

这意味着：
- 从偏移10读取4字节作为样本起始偏移
- 从偏移14读取4字节作为样本结束偏移
- 样本大小 = end - start
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
    print(f"First 32 bytes hex:")
    for i in range(0, 32, 16):
        hex_str = raw[i:i+16].hex(' ')
        print(f"  {i:04x}: {hex_str}")
    
    print(f"\n--- 根据sub_25A96逻辑解析 ---")
    print(f"调用参数: a5=0, a6=1, a7=1")
    print(f"v8 = a5 + 4*a6 = {0 + 4*1}")
    
    # 从偏移10读取
    if len(raw) >= 18:
        start_offset = struct.unpack_from('<I', raw, 10)[0]
        end_offset = struct.unpack_from('<I', raw, 14)[0]
        sample_size = end_offset - start_offset
        
        print(f"*(10) = 0x{start_offset:x} ({start_offset})")
        print(f"*(14) = 0x{end_offset:x} ({end_offset})")
        print(f"sample_size = {sample_size}")
        
        if 0 < start_offset < end_offset <= len(raw) and sample_size > 0:
            sample_data = raw[start_offset:end_offset]
            print(f"样本数据: {len(sample_data)} bytes")
            print(f"前32字节: {sample_data[:32].hex(' ')}")
            
            # 尝试多种格式
            output_dir = Path("output/sfx_wav/res078_precise_v4")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for sr in [5512, 8000, 11025, 16000, 22050]:
                # 8-bit
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(1)
                    wf.setframerate(sr)
                    wf.writeframes(sample_data)
                (output_dir / f"precise_8bit_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
                
                # 16-bit LE
                if len(sample_data) % 2 == 0:
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sr)
                        wf.writeframes(sample_data)
                    (output_dir / f"precise_16le_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
            
            print(f"\nGenerated files in: {output_dir}")
        else:
            print(f"Invalid offsets: start={start_offset}, end={end_offset}")
    else:
        print(f"Resource too small: {len(raw)} bytes")


if __name__ == "__main__":
    main()
