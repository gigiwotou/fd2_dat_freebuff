#!/usr/bin/env python3
"""
为 res78 闪电音效尝试不同的解码参数来去除沙沙声。
"""

import struct
import wave
import io
from pathlib import Path


def convert_to_be16_audio(data):
    if len(data) % 2 != 0:
        data = data[:-1]
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])
        result.append(data[i])
    return bytes(result)


def pcm16_to_wav(pcm_data, sample_rate=8000, channels=1):
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
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
    start = offsets[res_idx]
    end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[start:end]
    
    output_dir = Path("output/sfx_wav/res078_lightning_test2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Resource [{res_idx}] - {len(raw)} bytes")
    print(f"First 64 bytes: {raw[:64].hex()}")
    
    print(f"\n--- 分析头部结构 ---")
    val1 = struct.unpack_from('<H', raw, 0)[0]
    val2 = struct.unpack_from('<H', raw, 2)[0]
    print(f"  val1 = {val1}, val2 = {val2}")
    
    if val1 > 0 and val1 < 50:
        print(f"  假设 val1={val1} 是偏移表项数")
        for i in range(val1):
            pos = 4 + i * 4
            if pos + 4 <= len(raw):
                val = struct.unpack_from('<I', raw, pos)[0]
                print(f"    偏移[{i}] = 0x{val:x} ({val})")
    
    print(f"\n--- 尝试不同头部跳过大小 ---")
    for hdr_skip in [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 256]:
        if len(raw) <= hdr_skip + 100:
            continue
        
        audio = raw[hdr_skip:]
        be16 = convert_to_be16_audio(audio)
        
        for sr in [2000, 4000, 5512, 8000, 11025]:
            wav = pcm16_to_wav(be16, sr)
            (output_dir / f"skip{hdr_skip}_{sr}hz.wav").write_bytes(wav)
        
        print(f"  skip{hdr_skip}: {len(be16)} bytes audio")
    
    print(f"\n生成的测试文件在: {output_dir}")


if __name__ == "__main__":
    main()
