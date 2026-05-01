#!/usr/bin/env python3
"""
Extract audio samples from FDOTHER.DAT and convert to WAV.

From IDA analysis and audio testing:
1. sub_111BA loads resources using offset table (4*index + 6)
2. The loaded buffer contains multiple samples with their own offset table
3. Sample format: 16-bit PCM at 8000 Hz, mono (best quality verified by listening)
4. The buffer structure (from sub_25A96 analysis):
   - First 4 bytes: header/offset table entries
   - Sample data starts after 4-byte header
   - Sample data: 16-bit PCM (byte-swapped for WAV storage)

Key call chains:
- Resource #78 (0x4E): sub_20421 loads this, plays sample #0 (lightning)
- Resource #74 (0x4A): sub_1F894 loads this for scroll animation sounds
- Resource #7: menu sounds
"""

import struct
import wave
import io
from pathlib import Path

HEADER_SKIP = 4
SAMPLE_RATE = 8000


def pcm16_to_wav(pcm_data, sample_rate=SAMPLE_RATE, channels=1):
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


def convert_to_be16_audio(data):
    """Convert raw data to big-endian 16-bit audio format.
    
    The source data is stored as little-endian 16-bit PCM.
    We need to swap each pair of bytes to get big-endian format for WAV.
    """
    if len(data) % 2 != 0:
        data = data[:-1]
    
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])
        result.append(data[i])
    return bytes(result)


def read_fdother_resource(fdother_data, index):
    """Read a single resource from FDOTHER.DAT."""
    count = struct.unpack_from('<I', fdother_data, 6)[0]
    if index >= count:
        return None
    
    offset_table_start = 10
    start = struct.unpack_from('<I', fdother_data, offset_table_start + index * 4)[0]
    end = (struct.unpack_from('<I', fdother_data, offset_table_start + (index + 1) * 4)[0]
           if index + 1 < count else len(fdother_data))
    
    return fdother_data[start:end]


def extract_samples_from_buffer(raw_data, label=""):
    """
    Extract samples from a FDOTHER.DAT resource buffer.
    
    Based on IDA analysis of sub_25A96:
    - Buffer starts with offset table entries (4 bytes each)
    - Each entry points to sample data
    - Sample data is 16-bit PCM
    """
    samples = []
    
    if len(raw_data) < 8:
        return samples
    
    if raw_data[:2] != b'LL' and raw_data[:4] != b'LMI1':
        val1 = struct.unpack_from('<H', raw_data, 0)[0]
        val2 = struct.unpack_from('<H', raw_data, 2)[0]
        
        if val1 < 100 and val2 < 100 and val1 > 0:
            offset_start = 4 + val1 * 4
            if offset_start < len(raw_data):
                offsets = []
                for i in range(val2):
                    off_pos = 4 + i * 4
                    if off_pos + 4 > len(raw_data):
                        break
                    offset = struct.unpack_from('<I', raw_data, off_pos)[0]
                    offsets.append(offset)
                
                for i in range(len(offsets) - 1):
                    start = offsets[i]
                    end = offsets[i + 1]
                    if start < len(raw_data) and end <= len(raw_data) and start < end:
                        sample_data = raw_data[start:end]
                        samples.append(sample_data)
    
    if not samples and len(raw_data) > 50:
        if raw_data[:4] == b'\x40\x01\xc8\x00':
            samples.append(raw_data[4:])
        else:
            for header_size in [4, 6, 8, 12, 16]:
                if len(raw_data) > header_size + 50:
                    samples.append(raw_data[header_size:])
                    break
    
    return samples


def extract_all_sfx(fdother_path, output_dir):
    """Extract all sound effects from FDOTHER.DAT."""
    with open(fdother_path, 'rb') as f:
        fdother_data = f.read()
    
    count = struct.unpack_from('<I', fdother_data, 6)[0]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sfx_resources = list(range(count))
    
    for res_idx in sfx_resources:
        raw_data = read_fdother_resource(fdother_data, res_idx)
        if raw_data is None or len(raw_data) < 50:
            continue
        
        if len(raw_data) > 200000:
            continue
        
        samples = extract_samples_from_buffer(raw_data, f"res_{res_idx}")
        
        if samples:
            res_output_dir = output_dir / f"resource_{res_idx:03d}"
            res_output_dir.mkdir(parents=True, exist_ok=True)
            
            for i, sample_data in enumerate(samples):
                if len(sample_data) < 50:
                    continue
                
                be16_audio = convert_to_be16_audio(sample_data)
                
                wav_path = res_output_dir / f"sample_{i:02d}.wav"
                wav_path.write_bytes(pcm16_to_wav(be16_audio))
                
                raw_path = res_output_dir / f"sample_{i:02d}.pcm16"
                raw_path.write_bytes(sample_data)
                
                print(f"Resource [{res_idx:3d}] Sample [{i}]: "
                      f"pcm16={len(sample_data):5d} bytes -> {wav_path.name}")


def extract_key_sfx(fdother_path, output_dir):
    """Extract only the key sound effects identified from IDA analysis."""
    with open(fdother_path, 'rb') as f:
        fdother_data = f.read()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    key_resources = {
        78: "lightning_and_ani_sounds",
        74: "scroll_animation_sounds",
        7: "menu_sounds",
        8: "animation_sounds",
        9: "short_effect",
        15: "looping_tone",
        34: "tone_variant_1",
        39: "tone_variant_2",
    }
    
    for res_idx, description in key_resources.items():
        raw_data = read_fdother_resource(fdother_data, res_idx)
        if raw_data is None:
            print(f"Resource [{res_idx}] not found")
            continue
        
        print(f"\n{'='*60}")
        print(f"Resource [{res_idx}] - {description}")
        print(f"Size: {len(raw_data)} bytes")
        print(f"First 32 bytes: {raw_data[:32].hex()}")
        
        res_output_dir = output_dir / f"res{res_idx:03d}_{description}"
        res_output_dir.mkdir(parents=True, exist_ok=True)
        
        raw_path = res_output_dir / "raw_data.bin"
        raw_path.write_bytes(raw_data)
        
        if len(raw_data) > HEADER_SKIP + 50:
            raw_audio = raw_data[HEADER_SKIP:]
            be16_audio = convert_to_be16_audio(raw_audio)
            
            wav_path = res_output_dir / f"decoded.wav"
            wav_path.write_bytes(pcm16_to_wav(be16_audio))
            
            print(f"  Decoded (skip {HEADER_SKIP} bytes, {SAMPLE_RATE}Hz): "
                  f"raw={len(raw_audio)} -> be16={len(be16_audio)}")


if __name__ == "__main__":
    fdother_path = Path("game/FDOTHER.DAT")
    if not fdother_path.exists():
        print(f"Error: {fdother_path} not found")
        exit(1)
    
    output_dir = Path("output/sfx_wav")
    
    print("FDOTHER.DAT Sound Effect Extractor")
    print(f"Config: skip={HEADER_SKIP} bytes, sample_rate={SAMPLE_RATE}Hz")
    print("=" * 60)
    
    extract_key_sfx(fdother_path, output_dir / "key_sfx")
