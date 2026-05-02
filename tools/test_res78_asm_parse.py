#!/usr/bin/env python3
"""
根据IDA汇编代码精确解析res78的内部结构。

从sub_25A96的汇编分析：
- arg_0 是缓冲区指针
- arg_4 是样本索引 (这里=1)
- 但v8 = arg_0 + 4*arg_4 = arg_0 + 4

等等！调用是 sub_25A96((int)_FDOTHER.DAT_, 0, 1)
这只有3个参数，对应 a1, a5?, a6?

看C调用: sub_25A96((int)_FDOTHER.DAT_, 0, 1)
汇编:
  push    1
  push    0
  push    [esp+2Ch+var_18]  ; _FDOTHER.DAT_
  call    sub_25A96

所以:
  arg_0 = _FDOTHER.DAT_ (缓冲区)
  arg_4 = 0
  arg_8 = 1

但代码中 a6 对应 arg_4 = 0
v8 = a5 + 4*a6 = a5 + 4*0 = a5 = _FDOTHER.DAT_

*(v8+6) = *(buffer+6) = 从缓冲区偏移6读取
*(v8+10) = *(buffer+10) = 从缓冲区偏移10读取

所以对于res78:
*(6) = bytes[6:10] = 0x00000000
*(10) = bytes[10:14] = 0x000018d7

样本起始 = 0
样本大小 = 0x18d7 - 0 = 6359
样本结束 = 0x18d7

但等等，这些值应该是**相对于缓冲区基址的偏移**。
所以样本数据在 buffer[0:0x18d7] = raw[0:6359]

但raw有6801字节，而6359 < 6801，所以后面442字节可能是其他数据。
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
    print(f"First 32 bytes:")
    for i in range(0, 32, 16):
        hex_str = raw[i:i+16].hex(' ')
        print(f"  {i:04x}: {hex_str}")
    
    # 根据IDA汇编
    v6 = struct.unpack_from('<I', raw, 6)[0]
    v10 = struct.unpack_from('<I', raw, 10)[0]
    sample_start = v6
    sample_size = v10 - v6
    sample_end = sample_start + sample_size
    
    print(f"\n--- IDA汇编解析 ---")
    print(f"*(6) = 0x{v6:x} ({v6})")
    print(f"*(10) = 0x{v10:x} ({v10})")
    print(f"样本起始: {sample_start}")
    print(f"样本大小: {sample_size}")
    print(f"样本结束: {sample_end}")
    
    if 0 <= sample_start < sample_end <= len(raw):
        sample_data = raw[sample_start:sample_end]
        print(f"样本数据: {len(sample_data)} bytes")
        print(f"前32字节: {sample_data[:32].hex(' ')}")
        
        output_dir = Path("output/sfx_wav/res078_asm_parse")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for sr in [5512, 8000, 11025, 16000, 22050]:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(1)
                wf.setframerate(sr)
                wf.writeframes(sample_data)
            (output_dir / f"asm_parse_8bit_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
        
        print(f"\nGenerated files in: {output_dir}")
    else:
        print(f"Invalid sample range!")


if __name__ == "__main__":
    main()
