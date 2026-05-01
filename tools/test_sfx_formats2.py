#!/usr/bin/env python3
"""
Test multiple audio format variations to find the correct one.
User: hears rhythm but sound is sharp with noise.

Need to test:
1. Skip table header vs use all data as PCM
2. Different sample rates
3. Delta/ADPCM encoding
4. 4-bit packed audio
"""

import struct
import wave
import io
from pathlib import Path


def pcm8_to_wav(pcm_data, sample_rate=11025):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def decode_4bit_to_8bit(data):
    """Convert 4-bit nibbles to 8-bit by multiplying by 16."""
    output = []
    for byte in data:
        output.append((byte >> 4) * 16)
        output.append((byte & 0x0F) * 16)
    return bytes(output)


def decode_delta_pcm_8bit(data):
    """Decode as delta-encoded 8-bit PCM."""
    output = []
    current = 128  # start at center
    for byte in data:
        delta = byte - 128  # signed delta
        current += delta
        current = max(0, min(255, current))
        output.append(current)
    return bytes(output)


def decode_ulaw_8bit(data):
    """Simple mu-law like decompression."""
    output = []
    for byte in data:
        sign = byte & 0x80
        exp = (byte >> 4) & 0x07
        mantissa = byte & 0x0F
        
        sample = (mantissa << 3) + 8
        sample <<= exp
        
        if sign:
            output.append(255 - sample)
        else:
            output.append(sample)
    return bytes(output)


def resample_audio(data, factor):
    """Simple resample by duplicating/skipping samples."""
    if factor == 1:
        return data
    output = []
    for i in range(len(data)):
        output.append(data[i])
        if factor == 2:
            output.append(data[i])
        elif factor == 0.5 and i % 2 == 0:
            output.append(data[i])
    return bytes(output)


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    count = struct.unpack_from('<I', data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', data, 10 + i * 4)[0]
        offsets.append(off)
    
    output_dir = Path("output/sfx_format_test2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Focus on resource 9 (274 bytes, simple structure)
    res_idx = 9
    start = offsets[res_idx]
    end = offsets[res_idx + 1]
    raw = data[start:end]
    
    res_dir = output_dir / f"res{res_idx}"
    res_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Resource [{res_idx}] - {len(raw)} bytes")
    print(f"First 16: {raw[:16].hex()}")
    
    # Try different header skip sizes
    for hdr_skip in [0, 2, 4, 6, 8]:
        if len(raw) <= hdr_skip + 10:
            continue
        
        audio_data = raw[hdr_skip:]
        
        # 1. Direct 8-bit PCM at various sample rates
        for sr in [8000, 11025, 16000, 22050]:
            wav = pcm8_to_wav(audio_data, sr)
            (res_dir / f"skip{hdr_skip}_pcm8_{sr}hz.wav").write_bytes(wav)
        
        # 2. 4-bit unpacked to 8-bit
        unpacked = decode_4bit_to_8bit(audio_data)
        for sr in [8000, 11025, 16000, 22050]:
            wav = pcm8_to_wav(unpacked, sr)
            (res_dir / f"skip{hdr_skip}_4bit_{sr}hz.wav").write_bytes(wav)
        
        # 3. Delta PCM
        delta_pcm = decode_delta_pcm_8bit(audio_data)
        for sr in [8000, 11025, 16000, 22050]:
            wav = pcm8_to_wav(delta_pcm, sr)
            (res_dir / f"skip{hdr_skip}_delta8_{sr}hz.wav").write_bytes(wav)
        
        # 4. u-law
        ulaw_pcm = decode_ulaw_8bit(audio_data)
        for sr in [8000, 11025, 16000, 22050]:
            wav = pcm8_to_wav(ulaw_pcm, sr)
            (res_dir / f"skip{hdr_skip}_ulaw_{sr}hz.wav").write_bytes(wav)
        
        # 5. Resampled versions
        for factor in [2, 0.5]:
            resampled = resample_audio(audio_data, factor)
            sr = 11025
            wav = pcm8_to_wav(resampled, sr)
            (res_dir / f"skip{hdr_skip}_pcm8_{sr}hz_x{factor}.wav").write_bytes(wav)
    
    print(f"\nGenerated {len(list(res_dir.glob('*.wav')))} WAV files in {res_dir}")
    print("\nPlease test these files:")
    for f in sorted(res_dir.glob("*.wav")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
