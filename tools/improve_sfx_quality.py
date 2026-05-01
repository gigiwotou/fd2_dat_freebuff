#!/usr/bin/env python3
"""
改善 res9 音效的音质。尝试不同的参数组合。
"""

import struct
import wave
import io
from pathlib import Path


def convert_to_be16_audio(data):
    """Convert raw data to big-endian 16-bit audio format."""
    if len(data) % 2 != 0:
        data = data[:-1]
    
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])
        result.append(data[i])
    return bytes(result)


def pcm16_to_wav(pcm_data, sample_rate=16000, channels=1):
    """Convert 16-bit PCM data to WAV format."""
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def apply_low_pass_filter(data, threshold=128):
    """
    Simple noise reduction: clamp values that are too close to center (silence).
    This removes low-level noise while keeping significant audio content.
    """
    result = bytearray()
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            val = struct.unpack_from('>h', data, i)[0]
            if abs(val) < threshold:
                val = 0
            result.extend(struct.pack('>h', val))
    return bytes(result)


def amplify_audio(data, gain=2.0):
    """Amplify audio data by the given gain factor."""
    result = bytearray()
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            val = struct.unpack_from('>h', data, i)[0]
            val = int(val * gain)
            val = max(-32768, min(32767, val))
            result.extend(struct.pack('>h', val))
    return bytes(result)


def normalize_audio(data):
    """Normalize audio data to use full 16-bit range."""
    max_val = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            val = struct.unpack_from('>h', data, i)[0]
            max_val = max(max_val, abs(val))
    
    if max_val == 0:
        return data
    
    gain = 32767.0 / max_val
    return amplify_audio(data, gain)


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    output_dir = Path("output/sfx_wav_improved/res009_short_effect")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    res_idx = 9
    start = offsets[res_idx]
    end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(data)
    raw = data[start:end]
    
    print(f"Resource [{res_idx}] - {len(raw)} bytes")
    print(f"First 32 bytes: {raw[:32].hex()}")
    print()
    
    for hdr_skip in [0, 2, 4, 6, 8]:
        if len(raw) <= hdr_skip + 10:
            continue
        
        audio_data = raw[hdr_skip:]
        be16 = convert_to_be16_audio(audio_data)
        
        for sr in [8000, 11025, 16000, 22050]:
            wav = pcm16_to_wav(be16, sr)
            (output_dir / f"skip{hdr_skip}_{sr}hz.wav").write_bytes(wav)
        
        amplified = amplify_audio(be16, 2.0)
        wav = pcm16_to_wav(amplified, 16000)
        (output_dir / f"skip{hdr_skip}_16000hz_amplify2x.wav").write_bytes(wav)
        
        amplified4x = amplify_audio(be16, 4.0)
        wav = pcm16_to_wav(amplified4x, 16000)
        (output_dir / f"skip{hdr_skip}_16000hz_amplify4x.wav").write_bytes(wav)
        
        normalized = normalize_audio(be16)
        wav = pcm16_to_wav(normalized, 16000)
        (output_dir / f"skip{hdr_skip}_16000hz_normalized.wav").write_bytes(wav)
        
        filtered = apply_low_pass_filter(be16, threshold=64)
        wav = pcm16_to_wav(filtered, 16000)
        (output_dir / f"skip{hdr_skip}_16000hz_lowpass64.wav").write_bytes(wav)
        
        filtered_amplified = apply_low_pass_filter(amplified, threshold=64)
        wav = pcm16_to_wav(filtered_amplified, 16000)
        (output_dir / f"skip{hdr_skip}_16000hz_lowpass64_amplify2x.wav").write_bytes(wav)
    
    print(f"Generated WAV files in: {output_dir}")
    print("\n建议试听以下文件:")
    print("  skip4_16000hz.wav              - 原始 (skip 4 bytes)")
    print("  skip4_16000hz_amplify2x.wav    - 放大2倍")
    print("  skip4_16000hz_normalized.wav   - 标准化音量")
    print("  skip4_16000hz_lowpass64.wav    - 降噪处理")
    print("  skip4_11025hz.wav              - 较低采样率")


if __name__ == "__main__":
    main()
