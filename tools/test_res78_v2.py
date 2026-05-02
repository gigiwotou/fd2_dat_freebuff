#!/usr/bin/env python3
"""
为res78尝试极低采样率和其他可能格式。

分析：字节值分布集中在96-127，是8-bit unsigned PCM特征。
沙沙声严重可能是因为采样率设置太高或太低。
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


def apply_lowpass_filter(data, cutoff=64):
    """将接近中心值(128)的字节视为静音，减少杂音。"""
    result = bytearray()
    for b in data:
        if abs(int(b) - 128) < cutoff:
            result.append(128)
        else:
            result.append(b)
    return bytes(result)


def smooth_data(data, window=3):
    """简单平滑滤波。"""
    result = bytearray()
    half = window // 2
    for i in range(len(data)):
        start = max(0, i - half)
        end = min(len(data), i + half + 1)
        avg = sum(data[start:end]) // (end - start)
        result.append(avg)
    return bytes(result)


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
    
    output_dir = Path("output/sfx_wav/res078_lightning_v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 从偏移16开始
    sample_data = raw[16:]
    
    print(f"Res78: {len(raw)} bytes")
    print(f"Sample data (from offset 16): {len(sample_data)} bytes")
    print(f"Expected duration at various sample rates:")
    for sr in [1000, 2000, 4000, 5512, 8000, 11025]:
        duration = len(sample_data) / sr
        print(f"  {sr} Hz -> {duration:.2f} seconds")
    
    # 尝试极低采样率
    print(f"\n--- 生成测试文件 ---")
    
    # 原始8-bit PCM
    for sr in [1000, 2000, 3000, 4000, 5000, 5512, 6000, 7000, 8000]:
        wav = pcm8_to_wav(sample_data, sr)
        (output_dir / f"raw8_{sr}hz.wav").write_bytes(wav)
        print(f"  raw8_{sr}hz.wav")
    
    # 应用低通滤波
    filtered = apply_lowpass_filter(sample_data, cutoff=32)
    for sr in [1000, 2000, 4000, 5512, 8000]:
        wav = pcm8_to_wav(filtered, sr)
        (output_dir / f"filtered32_{sr}hz.wav").write_bytes(wav)
        print(f"  filtered32_{sr}hz.wav")
    
    filtered64 = apply_lowpass_filter(sample_data, cutoff=64)
    for sr in [1000, 2000, 4000, 5512, 8000]:
        wav = pcm8_to_wav(filtered64, sr)
        (output_dir / f"filtered64_{sr}hz.wav").write_bytes(wav)
        print(f"  filtered64_{sr}hz.wav")
    
    # 平滑处理
    smoothed = smooth_data(sample_data, window=3)
    for sr in [1000, 2000, 4000, 5512, 8000]:
        wav = pcm8_to_wav(smoothed, sr)
        (output_dir / f"smoothed3_{sr}hz.wav").write_bytes(wav)
        print(f"  smoothed3_{sr}hz.wav")
    
    # 平滑+滤波
    smoothed_filtered = apply_lowpass_filter(smoothed, cutoff=32)
    for sr in [1000, 2000, 4000, 5512, 8000]:
        wav = pcm8_to_wav(smoothed_filtered, sr)
        (output_dir / f"smoothed3_filtered32_{sr}hz.wav").write_bytes(wav)
        print(f"  smoothed3_filtered32_{sr}hz.wav")
    
    print(f"\nGenerated files in: {output_dir}")
    print("\n请试听 raw8_4000hz.wav 和 raw8_5512hz.wav，看沙沙声是否减少")


if __name__ == "__main__":
    main()
