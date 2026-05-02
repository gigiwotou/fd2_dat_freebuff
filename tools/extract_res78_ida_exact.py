#!/usr/bin/env python3
"""
基于IDA精确分析的闪电音效提取

从IDA分析得出的关键参数：
- sub_414E0初始化HSAMPLE结构体
- *(a1 + 0x3C) = 0x2B11 = 11025 (采样率)
- sub_25A96调用链:
  1. AIL_stop_sample (sub_39805)
  2. AIL_init_sample (sub_39521)
  3. AIL_set_sample_address (sub_39694) - 参数: (HSAMPLE, 音频数据指针, 样本大小)
  4. AIL_set_sample_loop_count (sub_39AAE) - 参数: (HSAMPLE, 循环次数)
  5. AIL_start_sample (sub_39798)

音频格式推断:
- Miles Sound System默认支持8-bit unsigned PCM
- 采样率: 11025 Hz
- 从res78偏移16开始，大小6343字节
"""
import struct
import os
import wave

# 加载FDOTHER.DAT
dat_path = os.path.join('game', 'FDOTHER.DAT')
with open(dat_path, 'rb') as f:
    data = f.read()

count = struct.unpack_from('<I', data, 6)[0]
offset_table_start = 0x0A
offsets = []
for i in range(count):
    offsets.append(struct.unpack_from('<I', data, offset_table_start + i*4)[0])

# res78
idx = 78
res78_start = offsets[idx]
res78_end = offsets[idx + 1] if idx + 1 < count else len(data)
res78 = data[res78_start:res78_end]

print(f"res78: {len(res78)} bytes")
print(f"res78前32字节: {res78[:32].hex()}")

# 解析res78头部
sample_offset = struct.unpack_from('<I', res78, 8)[0]  # 16
sample_size = struct.unpack_from('<I', res78, 12)[0] - sample_offset  # 6343

print(f"样本偏移: {sample_offset}")
print(f"样本大小: {sample_size}")

sample_data = res78[sample_offset:sample_offset + sample_size]
print(f"提取样本: {len(sample_data)} bytes")

# 基于IDA分析的确切参数
SAMPLE_RATE = 11025  # 从sub_414E0: *(a1+0x3C) = 0x2B11 = 11025

out_dir = 'output/sfx_wav/res078_ida_exact'
os.makedirs(out_dir, exist_ok=True)

# 保存原始样本
with open(f'{out_dir}/sample0.bin', 'wb') as f:
    f.write(sample_data)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename}")

print("\n=== 基于IDA精确分析的解码 ===")

# Miles Sound System默认格式: 8-bit unsigned PCM
# 需要转换为signed PCM for WAV
pcm8_to_16 = bytes([b ^ 0x80 for b in sample_data])
save_wav(pcm8_to_16, SAMPLE_RATE, f'{out_dir}/8bit_11025hz.wav')

# 也生成其他采样率对比
for sr in [8000, 11025, 16000, 22050]:
    save_wav(pcm8_to_16, sr, f'{out_dir}/8bit_{sr}hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print(f"\nIDA精确参数:")
print(f"  采样率: {SAMPLE_RATE} Hz (0x{SAMPLE_RATE:X})")
print(f"  格式: 8-bit unsigned PCM")
print(f"  样本大小: {sample_size} bytes")
print(f"  声道: Mono")
print(f"\n重点试听: 8bit_11025hz.wav")
