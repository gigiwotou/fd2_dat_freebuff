import struct
import os

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game', 'FDOTHER.DAT')
filepath = os.path.normpath(filepath)

print(f"分析文件: {filepath}")
print(f"文件存在: {os.path.exists(filepath)}")

if os.path.exists(filepath):
    file_size = os.path.getsize(filepath)
    print(f"文件大小: {file_size}")
