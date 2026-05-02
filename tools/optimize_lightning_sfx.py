#!/usr/bin/env python3
"""
基于用户反馈优化闪电音效
用户确认：8bit_4000hz.wav节奏正确，更像闪电
优化方向：微调采样率、音量、低频增强
"""
import struct
import os
import wave
import math

# 加载样本数据
with open('output/sfx_wav/res078_correct/sample0.bin', 'rb') as f:
    sample_data = f.read()

print(f"样本大小: {len(sample_data)} bytes")

out_dir = 'output/sfx_wav/res078_optimized'
os.makedirs(out_dir, exist_ok=True)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename} ({len(pcm_data)} bytes, {sample_rate}Hz)")

def pcm8_to_pcm16(pcm8):
    """8-bit unsigned 转 16-bit signed"""
    # 确保长度是偶数
    if len(pcm8) % 2 != 0:
        pcm8 = pcm8[:-1]
    return bytes([b ^ 0x80 for b in pcm8])

def apply_volume(pcm_data, volume=1.0):
    """调整音量"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    adjusted = [max(-32768, min(32767, int(s * volume))) for s in samples]
    return b''.join(struct.pack('<h', s) for s in adjusted)

def apply_lowpass_filter(pcm_data, cutoff_ratio=0.5):
    """低通滤波器 - 减少高频噪音，增强低频"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    filtered = list(samples)
    
    # 移动平均滤波
    window = 2
    for i in range(window, len(samples) - window):
        filtered[i] = int(sum(samples[i-window:i+window+1]) / (2*window + 1))
    
    return b''.join(struct.pack('<h', s) for s in filtered)

def apply_bass_boost(pcm_data, boost_factor=1.5):
    """低频增强 - 使声音更像打雷"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    enhanced = list(samples)
    
    # 简单的低频增强：使用长窗口的移动平均来提取低频成分
    window = 5
    low_freq = []
    for i in range(len(samples)):
        start = max(0, i - window)
        end = min(len(samples), i + window + 1)
        low_freq.append(int(sum(samples[start:end]) / (end - start)))
    
    # 将低频成分叠加到原信号
    for i in range(len(samples)):
        enhanced[i] = max(-32768, min(32767, samples[i] + int(low_freq[i] * (boost_factor - 1))))
    
    return b''.join(struct.pack('<h', s) for s in enhanced)

def apply_envelope(pcm_data, attack_ms=10, release_ms=300, sample_rate=4000):
    """应用包络线 - 快速起音，缓慢释音，像闪电"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    attack_samples = int(attack_ms * sample_rate / 1000)
    release_samples = int(release_ms * sample_rate / 1000)
    
    enveloped = list(samples)
    for i in range(len(samples)):
        if i < attack_samples:
            envelope = i / attack_samples if attack_samples > 0 else 1.0
        elif i > len(samples) - release_samples:
            envelope = (len(samples) - i) / release_samples if release_samples > 0 else 1.0
        else:
            envelope = 1.0
        enveloped[i] = int(samples[i] * envelope)
    
    return b''.join(struct.pack('<h', s) for s in enveloped)

def apply_distortion(pcm_data, drive=2.0):
    """失真效果 - 增加雷电的粗糙感"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    distorted = []
    
    for s in samples:
        # 软削波
        val = s / 32767.0 * drive
        if val > 1.0:
            val = 1.0
        elif val < -1.0:
            val = -1.0
        distorted.append(int(val * 32767))
    
    return b''.join(struct.pack('<h', s) for s in distorted)

print("\n=== 优化测试 ===")

# 基础8-bit转16-bit
base_pcm = pcm8_to_pcm16(sample_data)

# 1. 不同采样率的8-bit PCM（围绕4000Hz）
print("\n--- 不同采样率 ---")
for sr in [3000, 3500, 4000, 4500, 5000, 5512, 6000, 8000]:
    pcm = pcm8_to_pcm16(sample_data)
    save_wav(pcm, sr, f'{out_dir}/8bit_{sr}hz.wav')

# 2. 音量调整
print("\n--- 音量调整 (4000Hz) ---")
for vol in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
    pcm = apply_volume(base_pcm, vol)
    save_wav(pcm, 4000, f'{out_dir}/8bit_vol{vol:.2f}_4000hz.wav')

# 3. 低通滤波
print("\n--- 低通滤波 (4000Hz) ---")
for cutoff in [0.3, 0.5, 0.7]:
    pcm = apply_lowpass_filter(base_pcm, cutoff)
    save_wav(pcm, 4000, f'{out_dir}/8bit_lowpass{cutoff:.1f}_4000hz.wav')

# 4. 低频增强
print("\n--- 低频增强 (4000Hz) ---")
for boost in [1.2, 1.5, 2.0, 2.5]:
    pcm = apply_bass_boost(base_pcm, boost)
    save_wav(pcm, 4000, f'{out_dir}/8bit_bass{boost:.1f}_4000hz.wav')

# 5. 包络效果
print("\n--- 包络效果 (4000Hz) ---")
for attack in [5, 10, 20]:
    for release in [200, 300, 500]:
        pcm = apply_envelope(base_pcm, attack, release, 4000)
        save_wav(pcm, 4000, f'{out_dir}/8bit_env_a{attack}_r{release}_4000hz.wav')

# 6. 组合效果：低通 + 低频增强
print("\n--- 组合效果：低通+低频增强 ---")
pcm = apply_lowpass_filter(base_pcm, 0.5)
pcm = apply_bass_boost(pcm, 1.5)
save_wav(pcm, 4000, f'{out_dir}/8bit_combined1_4000hz.wav')

# 7. 组合效果：低频增强 + 包络
print("\n--- 组合效果：低频增强+包络 ---")
pcm = apply_bass_boost(base_pcm, 1.5)
pcm = apply_envelope(pcm, 10, 300, 4000)
save_wav(pcm, 4000, f'{out_dir}/8bit_combined2_4000hz.wav')

# 8. 组合效果：低通 + 低频增强 + 包络
print("\n--- 组合效果：完整链 ---")
pcm = apply_lowpass_filter(base_pcm, 0.5)
pcm = apply_bass_boost(pcm, 1.5)
pcm = apply_envelope(pcm, 10, 300, 4000)
save_wav(pcm, 4000, f'{out_dir}/8bit_full_chain_4000hz.wav')

# 9. 添加失真效果
print("\n--- 失真效果 ---")
for drive in [1.5, 2.0, 3.0]:
    pcm = apply_distortion(base_pcm, drive)
    save_wav(pcm, 4000, f'{out_dir}/8bit_distortion{drive:.1f}_4000hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print("\n推荐试听:")
print("  1. 8bit_4000hz.wav (原始确认版本)")
print("  2. 8bit_5000hz.wav (稍高采样率)")
print("  3. 8bit_vol1.50_4000hz.wav (增加音量)")
print("  4. 8bit_bass1.5_4000hz.wav (低频增强)")
print("  5. 8bit_full_chain_4000hz.wav (完整处理链)")
print("  6. 8bit_combined2_4000hz.wav (低频增强+包络)")
