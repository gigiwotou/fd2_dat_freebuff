#!/usr/bin/env python3
"""
对比两个工具生成的 be16 WAV 文件，找出差异。
"""

import wave
import struct
from pathlib import Path


def read_wav_data(wav_path):
    """读取 WAV 文件的数据部分。"""
    with wave.open(str(wav_path), 'rb') as wf:
        return {
            'channels': wf.getnchannels(),
            'sampwidth': wf.getsampwidth(),
            'framerate': wf.getframerate(),
            'nframes': wf.getnframes(),
            'data': wf.readframes(wf.getnframes())
        }


def compare_wav_files(file1, file2):
    """比较两个 WAV 文件的内容。"""
    wav1 = read_wav_data(file1)
    wav2 = read_wav_data(file2)
    
    print(f"\n比较: {file1.name} vs {file2.name}")
    print(f"  {file1.name}: {wav1['channels']}ch, {wav1['sampwidth']*8}bit, {wav1['framerate']}Hz, {wav1['nframes']}frames, {len(wav1['data'])}bytes")
    print(f"  {file2.name}: {wav2['channels']}ch, {wav2['sampwidth']*8}bit, {wav2['framerate']}Hz, {wav2['nframes']}frames, {len(wav2['data'])}bytes")
    
    if len(wav1['data']) != len(wav2['data']):
        print(f"  [WARN] 数据长度不同: {len(wav1['data'])} vs {len(wav2['data'])}")
        min_len = min(len(wav1['data']), len(wav2['data']))
    else:
        min_len = len(wav1['data'])
        print(f"  [OK] 数据长度相同: {min_len} bytes")
    
    if wav1['data'] == wav2['data']:
        print(f"  [OK] 数据完全相同！")
        return True
    else:
        diff_count = sum(1 for a, b in zip(wav1['data'][:min_len], wav2['data'][:min_len]) if a != b)
        print(f"  [DIFF] 数据不同: {diff_count}/{min_len} bytes 不同")
        
        if min_len <= 64:
            print(f"    file1: {wav1['data'][:min_len].hex()}")
            print(f"    file2: {wav2['data'][:min_len].hex()}")
        else:
            print(f"    file1 (前64字节): {wav1['data'][:64].hex()}")
            print(f"    file2 (前64字节): {wav2['data'][:64].hex()}")
        return False


def main():
    test3_dir = Path("output/sfx_format_test3/res9_274bytes")
    sfx_wav_dir = Path("output/sfx_wav/key_sfx/res009_short_effect")
    
    print("=" * 60)
    print("对比 comprehensive_audio_test.py 和 extract_sfx_wav.py 生成的文件")
    print("=" * 60)
    
    files_to_compare = []
    
    for skip in [0, 4, 6, 8, 12]:
        test3_file = test3_dir / f"skip{skip}_be16_16000hz.wav"
        sfx_file = sfx_wav_dir / f"decoded_skip{skip}.wav"
        
        if test3_file.exists() and sfx_file.exists():
            files_to_compare.append((test3_file, sfx_file))
    
    for test3_file, sfx_file in files_to_compare:
        compare_wav_files(test3_file, sfx_file)


if __name__ == "__main__":
    main()
