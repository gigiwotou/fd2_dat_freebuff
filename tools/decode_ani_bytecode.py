#!/usr/bin/env python3
"""
基于IDA精确分析的音频字节码解释器

IDA分析：
- sub_36FF4(count, data): 解释器主循环
  for (i=0; i<count; i++) {
      byte = *data++;
      call funcs_37012[byte](data);  // byte*4是函数指针偏移
  }

- funcs_37012表（10个函数，每个4字节）:
  [0] sub_36E3D: 用数据字节填充buf（768字节）
  [1] sub_36E57: 复制0x300字节到buf
  [2] sub_36E65: 复杂解码 - 读取数据填充buf（768字节）
  [3] sub_36EA7: 从数据解码到buf
  [4] sub_36EE0: 用count值填充buf

- buf是768字节的音频缓冲区
- 每块解码后通过sub_36FF4处理，然后sub_25A96播放
"""
import struct
import os
import wave

# 读取所有块
blocks = []
for f in sorted(os.listdir('output/sfx_wav/ani_decode')):
    if f.endswith('.bin'):
        with open(f'output/sfx_wav/ani_decode/{f}', 'rb') as fh:
            blocks.append(fh.read())

print(f"加载了 {len(blocks)} 个块")

# IDA字节码解释器
class AudioDecoder:
    def __init__(self):
        self.buf = bytearray(768)  # 768字节音频缓冲区
        self.count = 0  # 全局count变量
    
    def func_0(self, data_ptr):
        """sub_36E3D: 用数据字节填充buf"""
        byte = data_ptr[0]
        value = (byte << 16) | byte  # 重复16位模式
        # memset32(buf, value, 0xC0)  0xC0 = 192个DWORD = 768字节
        for i in range(192):
            self.buf[i*4:(i+1)*4] = struct.pack('<I', value & 0xFFFFFFFF)
        return 1  # 消耗1字节
    
    def func_1(self, data_ptr):
        """sub_36E57: 复制数据到buf"""
        # qmemcpy(buf, data, 0x300) 0x300 = 768字节
        copy_size = min(0x300, len(data_ptr))
        self.buf[:copy_size] = data_ptr[:copy_size]
        return copy_size  # 消耗copy_size字节
    
    def func_2(self, data_ptr):
        """sub_36E65: 复杂解码填充buf"""
        pos = 0
        buf_pos = 0
        n768 = 0
        
        while n768 != 768:
            if pos >= len(data_ptr):
                break
            v4 = data_ptr[pos]
            pos += 1
            
            if (v4 & 0xC0) == 0xC0:
                # 压缩模式
                v2 = v4 & 0x3F
                n768 += v2
                
                if pos >= len(data_ptr):
                    break
                value = data_ptr[pos]
                pos += 1
                value_word = (value << 8) | value
                
                # 填充word
                for i in range(v2 >> 1):
                    if buf_pos + 2 <= 768:
                        self.buf[buf_pos] = value_word & 0xFF
                        self.buf[buf_pos + 1] = (value_word >> 8) & 0xFF
                        buf_pos += 2
                
                # 处理剩余的字节
                if v2 & 1:
                    if buf_pos < 768:
                        self.buf[buf_pos] = value & 0xFF
                        buf_pos += 1
            else:
                # 直接模式
                if buf_pos < 768:
                    self.buf[buf_pos] = v4
                    buf_pos += 1
                    n768 += 1
        
        return pos  # 返回消耗的字节数
    
    def func_3(self, data_ptr):
        """sub_36EA7: 从数据解码"""
        pos = 0
        byte1 = data_ptr[0]
        pos += 1
        v3 = byte1
        
        for _ in range(v3):
            if pos >= len(data_ptr):
                break
            
            byte2 = data_ptr[pos]
            pos += 1
            
            # dst = buf + 3 * byte2
            dst = 3 * byte2
            
            if pos >= len(data_ptr):
                break
            byte3 = data_ptr[pos]
            pos += 1
            
            # count = 2 * byte3 + byte3 >> 1 = byte3 * 2.5
            count = (2 * byte3 + byte3) >> 1
            
            # 复制count字节
            copy_size = min(count, len(data_ptr) - pos, 768 - dst)
            self.buf[dst:dst+copy_size] = data_ptr[pos:pos+copy_size]
            pos += copy_size
        
        return pos  # 返回消耗的字节数
    
    def func_4(self, data_ptr):
        """sub_36EE0: 用count填充buf"""
        byte = data_ptr[0]
        value = (byte << 16) | byte
        
        count_val = self.count
        # memset32(buf, value, count_val >> 2)
        for i in range(count_val >> 2):
            self.buf[i*4:(i+1)*4] = struct.pack('<I', value & 0xFFFFFFFF)
        
        # memset(buf + 4*(count>>2), value, count & 3)
        remainder = count_val & 3
        start = 4 * (count_val >> 2)
        for i in range(remainder):
            if start + i < 768:
                self.buf[start + i] = value & 0xFF
        
        return 1  # 消耗1字节
    
    def decode_block(self, block_data, count):
        """解码一个块"""
        self.buf = bytearray(768)
        
        pos = 0
        for i in range(count):
            if pos >= len(block_data):
                break
            
            opcode = block_data[pos]
            pos += 1
            
            # 调用对应的函数
            consumed = 0
            if opcode == 0:
                consumed = self.func_0(block_data[pos:])
            elif opcode == 1:
                consumed = self.func_1(block_data[pos:])
            elif opcode == 2:
                consumed = self.func_2(block_data[pos:])
            elif opcode == 3:
                consumed = self.func_3(block_data[pos:])
            elif opcode == 4:
                consumed = self.func_4(block_data[pos:])
            else:
                # 未知opcode，跳过
                print(f"  未知opcode: {opcode}")
                consumed = 0
            
            pos += consumed
        
        return bytes(self.buf)

# 解码所有块
decoder = AudioDecoder()
all_audio = bytearray()

out_dir = 'output/sfx_wav/ani_decoded'
os.makedirs(out_dir, exist_ok=True)

for i, block in enumerate(blocks):
    if len(block) < 4:
        continue
    
    # 解析块头
    size = struct.unpack_from('<H', block, 0)[0]
    count = struct.unpack_from('<H', block, 2)[0]
    block_data = block[8:]  # 跳过8字节头
    
    print(f"\n块 {i}: size={size}, count={count}, 数据={len(block_data)}字节")
    
    if count == 0 or len(block_data) == 0:
        continue
    
    # 解码
    decoder.count = size  # 设置全局count
    audio = decoder.decode_block(block_data, count)
    
    # 保存解码后的音频
    with open(f'{out_dir}/block{i}.bin', 'wb') as f:
        f.write(audio)
    
    all_audio.extend(audio)
    
    # 保存WAV用于试听（仅前几个块）
    if i < 5:
        with wave.open(f'{out_dir}/block{i}.wav', 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)  # 8-bit
            wf.setframerate(11025)
            wf.writeframes(audio)

# 保存完整音频
with wave.open(f'{out_dir}/all_audio.wav', 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(1)
    wf.setframerate(11025)
    wf.writeframes(bytes(all_audio))

print(f"\n解码完成！")
print(f"总音频大小: {len(all_audio)} 字节")
print(f"文件保存到: {out_dir}/")
