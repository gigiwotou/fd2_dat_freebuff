#!/usr/bin/env python3
"""
从IDA分析结果精确提取res78闪电音效。

IDA分析的关键发现：
1. sub_20421 播放动画音效时的流程：
   - 加载FDOTHER.DAT资源#78到缓冲区
   - 从ANI.DAT读取字节码指令
   - 调用sub_36FF4解释执行字节码
   - 调用sub_25A96播放音效

2. sub_25A96播放逻辑：
   - 缓冲区结构: [count1:2字节][count2:2字节][offset_table:count2*4字节][sample_data]
   - 偏移表每项4字节，指向sample_data的起始位置
   - 样本地址 = base + offset
   - 样本大小 = next_offset - current_offset

3. res78的结构：
   - 偏移0: count1=2, count2=2
   - 偏移4: offset[0]=0x4 (样本0起始)
   - 偏移8: offset[1]=0x1a94 (样本0结束/样本1起始)
   - 样本0: 0x4 ~ 0x1a94 (6800字节) = 闪电音效
   - 样本1: 0x1a94 ~ 0x1a98 (4字节) = 可能不是音频

关键：样本数据从偏移4开始，长度6800字节。
之前的问题是我们把整个资源(包括偏移表)都当作音频，导致杂音。
"""

import struct
import wave
import io
from pathlib import Path


def convert_to_be16_audio(data):
    """将原始数据转换为大端16位音频格式。"""
    if len(data) % 2 != 0:
        data = data[:-1]
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append(data[i + 1])
        result.append(data[i])
    return bytes(result)


def pcm16_to_wav(pcm_data, sample_rate=8000, channels=1):
    """将16位PCM数据转换为WAV格式。"""
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return wav_buffer.getvalue()


def extract_res78_precise(fdother_data):
    """根据IDA分析精确提取res78中的样本。"""
    count = struct.unpack_from('<I', fdother_data, 6)[0]
    offsets = []
    for i in range(count):
        off = struct.unpack_from('<I', fdother_data, 10 + i * 4)[0]
        offsets.append(off)
    
    res_idx = 78
    res_start = offsets[res_idx]
    res_end = offsets[res_idx + 1] if res_idx + 1 < len(offsets) else len(fdother_data)
    raw = fdother_data[res_start:res_end]
    
    # 解析头部
    count1 = struct.unpack_from('<H', raw, 0)[0]
    count2 = struct.unpack_from('<H', raw, 2)[0]
    
    # 读取偏移表
    internal_offsets = []
    for i in range(count2):
        pos = 4 + i * 4
        if pos + 4 <= len(raw):
            val = struct.unpack_from('<I', raw, pos)[0]
            internal_offsets.append(val)
    
    # 添加资源末尾作为最后一个偏移
    internal_offsets.append(len(raw))
    
    samples = []
    for i in range(len(internal_offsets) - 1):
        sample_start = internal_offsets[i]
        sample_end = internal_offsets[i + 1]
        if sample_start < len(raw) and sample_end <= len(raw) and sample_end > sample_start:
            sample_data = raw[sample_start:sample_end]
            samples.append(sample_data)
    
    return samples


def main():
    with open("game/FDOTHER.DAT", "rb") as f:
        data = f.read()
    
    output_dir = Path("output/sfx_wav/res078_lightning_precise")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    samples = extract_res78_precise(data)
    
    print(f"Res78 提取到 {len(samples)} 个样本")
    
    for i, sample in enumerate(samples):
        print(f"\n样本[{i}]: {len(sample)} 字节")
        print(f"  前32字节: {sample[:32].hex()}")
        
        # 尝试不同采样率
        for sr in [4000, 5512, 8000, 11025, 16000, 22050]:
            be16 = convert_to_be16_audio(sample)
            wav = pcm16_to_wav(be16, sr)
            (output_dir / f"sample{i}_{sr}hz.wav").write_bytes(wav)
            print(f"  生成 sample{i}_{sr}hz.wav ({len(be16)} bytes)")
    
    print(f"\n生成文件在: {output_dir}")


if __name__ == "__main__":
    main()
