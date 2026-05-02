#!/usr/bin/env python3
"""
从IDA汇编代码精确提取res78样本并尝试各种解码方式。

从sub_25A96汇编:
- arg_0 = FDOTHER.DAT buffer
- arg_4 = 0 (sample index)
- arg_8 = 1 (loop count)

v8 = arg_0 + 4*0 = arg_0
edx = *(v8+6) = buffer[6:10]  # sample start offset
eax = *(v8+10) = buffer[10:14]  # sample end offset
sample_size = eax - edx

对于res78:
buffer[6:10] = 0x00000000
buffer[10:14] = 0x000018d7 = 6359

所以样本数据 = buffer[0:6359]
"""

import struct
import wave
import io
from pathlib import Path


def ima_adpcm_decode_16bit(adpcm_data, initial_predictor=0, initial_index=0):
    """Decode IMA ADPCM 4-bit data to 16-bit signed PCM."""
    IMA_STEP_TABLE = [
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34,
        37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
        157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494,
        544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
        1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
        4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487,
        12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086,
        29794, 32767
    ]
    IMA_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
    
    output = []
    predictor = initial_predictor
    index = initial_index
    
    for byte in adpcm_data:
        for nibble in [(byte >> 4) & 0x0F, byte & 0x0F]:
            step = IMA_STEP_TABLE[index]
            delta = 0
            if nibble & 0x04: delta += step
            if nibble & 0x02: delta += step >> 1
            if nibble & 0x01: delta += step >> 2
            delta += step >> 3
            
            if nibble & 0x08:
                predictor -= delta
            else:
                predictor += delta
            
            predictor = max(-32768, min(32767, predictor))
            output.append(struct.pack('<h', predictor))
            
            index += IMA_INDEX_TABLE[nibble]
            index = max(0, min(88, index))
    
    return b''.join(output)


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
    
    output_dir = Path("output/sfx_wav/res078_final")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Res78: {len(raw)} bytes")
    
    # 根据IDA汇编提取样本
    sample_start = struct.unpack_from('<I', raw, 6)[0]
    sample_end = struct.unpack_from('<I', raw, 10)[0]
    sample_size = sample_end - sample_start
    
    print(f"Sample: start={sample_start}, end={sample_end}, size={sample_size}")
    
    if 0 <= sample_start < sample_end <= len(raw):
        sample_data = raw[sample_start:sample_end]
        print(f"Sample data: {len(sample_data)} bytes")
        print(f"First 32 bytes: {sample_data[:32].hex(' ')}")
        
        # 尝试IMA ADPCM解码为16-bit
        for sr in [5512, 8000, 11025, 16000, 22050]:
            for pred in [0, 128, 1024]:
                decoded = ima_adpcm_decode_16bit(sample_data, pred, 0)
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sr)
                    wf.writeframes(decoded)
                (output_dir / f"adpcm16_p{pred}_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
        
        # 尝试8-bit PCM
        for sr in [5512, 8000, 11025, 16000, 22050]:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(1)
                wf.setframerate(sr)
                wf.writeframes(sample_data)
            (output_dir / f"pcm8_{sr}hz.wav").write_bytes(wav_buffer.getvalue())
        
        print(f"\nGenerated files in: {output_dir}")
    else:
        print(f"Invalid sample range!")


if __name__ == "__main__":
    main()
