#!/usr/bin/env python3
"""
精确优化闪电音效 - 消除风声感，增强闪电特征

风声特征分析：
- 风声：中高频连续，缺乏明显起音，低频不足
- 闪电：尖锐起音，低频轰鸣，高频碎裂，快速衰减

优化策略：
1. 增强低频（减少风声感）
2. 添加尖锐起音
3. 增加瞬态响应
4. 应用快速衰减
"""
import struct
import os
import wave

# 加载样本数据
with open('output/sfx_wav/res078_correct/sample0.bin', 'rb') as f:
    sample_data = f.read()

# 确保长度是偶数
if len(sample_data) % 2 != 0:
    sample_data = sample_data[:-1]

print(f"样本大小: {len(sample_data)} bytes")

out_dir = 'output/sfx_wav/res078_lightning_v3'
os.makedirs(out_dir, exist_ok=True)

def save_wav(pcm_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    print(f"  保存: {filename}")

def pcm8_to_pcm16(pcm8):
    """8-bit unsigned 转 16-bit signed"""
    return bytes([b ^ 0x80 for b in pcm8])

def apply_heavy_lowpass(pcm_data, strength=3):
    """强低通滤波 - 消除高频风声"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for _ in range(strength):
        prev = result[:]
        for i in range(1, len(samples)-1):
            result[i] = int(prev[i-1] * 0.25 + prev[i] * 0.5 + prev[i+1] * 0.25)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_transient_enhance(pcm_data, threshold=5000, boost=2.0):
    """增强瞬态 - 让起音更尖锐"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    for i in range(1, len(samples)-1):
        diff = abs(samples[i] - samples[i-1])
        if diff > threshold:
            result[i] = int(samples[i] * boost)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_sub_bass(pcm_data, mix=0.5):
    """添加次低频 - 增加震撼感"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 提取极低频成分
    window = 20
    for i in range(len(samples)):
        start = max(0, i - window)
        end = min(len(samples), i + window + 1)
        sub_bass = int(sum(samples[start:end]) / (end - start))
        result[i] = int(samples[i] * (1 - mix) + sub_bass * mix)
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_impulse(pcm_data, impulse_strength=0.3, impulse_duration=10):
    """在开头添加冲击脉冲 - 模拟闪电瞬间"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    result = list(samples)
    
    # 在前几个样本添加高振幅脉冲
    for i in range(min(impulse_duration, len(samples))):
        impulse = int(30000 * impulse_strength * (1 - i/impulse_duration))
        result[i] = int(samples[i] + impulse * (1 if i % 2 == 0 else -1))
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

def apply_quick_decay(pcm_data, decay_time_ms=200, sample_rate=4000):
    """快速衰减 - 闪电是瞬态声音"""
    samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
    decay_samples = int(decay_time_ms * sample_rate / 1000)
    
    result = []
    for i, s in enumerate(samples):
        if i < decay_samples:
            envelope = 1.0 - (i / decay_samples) * 0.8
        else:
            envelope = 0.2
        result.append(int(s * envelope))
    
    return b''.join(struct.pack('<h', max(-32768, min(32767, s))) for s in result)

print("\n=== 精确优化闪电音效 ===")

base_pcm = pcm8_to_pcm16(sample_data)

# 1. 强低通滤波
print("\n--- 强低通滤波 ---")
for strength in [1, 2, 3, 5]:
    pcm = apply_heavy_lowpass(base_pcm, strength)
    save_wav(pcm, 4000, f'{out_dir}/lowpass{strength}_4000hz.wav')

# 2. 瞬态增强
print("\n--- 瞬态增强 ---")
for threshold in [3000, 5000, 8000]:
    for boost in [1.5, 2.0, 3.0]:
        pcm = apply_transient_enhance(base_pcm, threshold, boost)
        save_wav(pcm, 4000, f'{out_dir}/transient_t{threshold}_b{boost:.1f}_4000hz.wav')

# 3. 次低频增强
print("\n--- 次低频增强 ---")
for mix in [0.2, 0.3, 0.5, 0.7]:
    pcm = apply_sub_bass(base_pcm, mix)
    save_wav(pcm, 4000, f'{out_dir}/subbass{mix:.1f}_4000hz.wav')

# 4. 冲击脉冲
print("\n--- 冲击脉冲 ---")
for strength in [0.2, 0.3, 0.5]:
    pcm = apply_impulse(base_pcm, strength)
    save_wav(pcm, 4000, f'{out_dir}/impulse{strength:.1f}_4000hz.wav')

# 5. 快速衰减
print("\n--- 快速衰减 ---")
for decay in [100, 200, 300, 500]:
    pcm = apply_quick_decay(base_pcm, decay, 4000)
    save_wav(pcm, 4000, f'{out_dir}/decay{decay}ms_4000hz.wav')

# 6. 组合效果 - 重点优化
print("\n--- 组合效果 ---")

# 组合1: 低通 + 次低频 (消除风声，增加低频)
pcm = apply_heavy_lowpass(base_pcm, 2)
pcm = apply_sub_bass(pcm, 0.5)
save_wav(pcm, 4000, f'{out_dir}/combo1_lowpass_subbass_4000hz.wav')

# 组合2: 冲击 + 低通 + 次低频
pcm = apply_impulse(base_pcm, 0.3)
pcm = apply_heavy_lowpass(pcm, 2)
pcm = apply_sub_bass(pcm, 0.5)
save_wav(pcm, 4000, f'{out_dir}/combo2_impulse_lowpass_subbass_4000hz.wav')

# 组合3: 冲击 + 低通 + 次低频 + 快速衰减
pcm = apply_impulse(base_pcm, 0.3)
pcm = apply_heavy_lowpass(pcm, 2)
pcm = apply_sub_bass(pcm, 0.5)
pcm = apply_quick_decay(pcm, 300, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo3_full_lightning_4000hz.wav')

# 组合4: 瞬态 + 低通 + 次低频
pcm = apply_transient_enhance(base_pcm, 5000, 2.0)
pcm = apply_heavy_lowpass(pcm, 2)
pcm = apply_sub_bass(pcm, 0.5)
save_wav(pcm, 4000, f'{out_dir}/combo4_transient_lowpass_subbass_4000hz.wav')

# 组合5: 完整闪电链 - 所有效果
pcm = apply_impulse(base_pcm, 0.3)
pcm = apply_transient_enhance(pcm, 5000, 2.0)
pcm = apply_heavy_lowpass(pcm, 2)
pcm = apply_sub_bass(pcm, 0.5)
pcm = apply_quick_decay(pcm, 300, 4000)
save_wav(pcm, 4000, f'{out_dir}/combo5_complete_lightning_4000hz.wav')

# 7. 不同采样率的完整处理
print("\n--- 不同采样率 ---")
for sr in [4000, 5000, 6000, 8000]:
    pcm = apply_impulse(base_pcm, 0.3)
    pcm = apply_heavy_lowpass(pcm, 2)
    pcm = apply_sub_bass(pcm, 0.5)
    pcm = apply_quick_decay(pcm, 300, sr)
    save_wav(pcm, sr, f'{out_dir}/full_{sr}hz.wav')

print(f"\n完成! 文件保存到 {out_dir}/")
print("\n重点试听:")
print("  1. base_4000hz.wav (原始基础)")
print("  2. combo1_lowpass_subbass_4000hz.wav (低通+低频)")
print("  3. combo3_full_lightning_4000hz.wav (完整闪电效果)")
print("  4. combo5_complete_lightning_4000hz.wav (完整处理链)")
print("  5. full_4000hz.wav vs full_8000hz.wav (采样率对比)")
