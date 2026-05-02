#!/usr/bin/env python3
"""
为res78尝试极低采样率和其他变体格式。
"""

import struct
import wave
import io
from pathlib import Path


def pcm8_to_wav(pcm_data, sample_rate):
    """Convert 8-bit unsigned PCM to WAV."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


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
    
    output_dir = Path("output/sfx_wav/res078_test_v3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Res78: {len(raw)} bytes")
    print(f"First 16 bytes: {raw[:16].hex(' ')}")
    
    # 解析头部
    c1, c2 = struct.unpack_from('<HH', raw, 0)
    print(f"count1={c1}, count2={c2}")
    
    # 尝试从偏移0开始（整个资源当作音频数据）
    for start in [0, 4, 8, 16]:
        if start >= len(raw):
            continue
        sample = raw[start:]
        print(f"\n--- From offset {start}: {len(sample)} bytes ---")
        
        # 极低采样率
        for sr in [250, 500, 750, 1000, 1500, 2000, 2500, 3000]:
            wav = pcm8_to_wav(sample, sr)
            duration = len(sample) / sr
            (output_dir / f"from{start}_raw8_{sr}hz.wav").write_bytes(wav)
            print(f"  from{start}_raw8_{sr}hz.wav ({duration:.2f}s)")
        
        # 尝试跳过前4字节
        if start + 4 < len(raw):
            skip4 = sample[4:]
            for sr in [250, 500, 1000, 2000, 4000]:
                wav = pcm8_to_wav(skip4, sr)
                duration = len(skip4) / sr
                (output_dir / f"from{start}_skip4_{sr}hz.wav").write_bytes(wav)
    
    print(f"\nGenerated files in: {output_dir}")
    print("\n请试听 from0_raw8_1000hz.wav 和 from0_raw8_2000hz.wav")
    print("如果这些也不像，说明数据格式可能不是简单的8-bit PCM")


if __name__ == "__main__":
    main()
