import struct

def rol16(value, shift):
    return ((value << shift) | (value >> (16 - shift))) & 0xFFFF

def encrypt(data):
    encrypted = bytearray(data)
    n165 = 165
    for i in range(len(data)):
        n165 = (n165 + 0x9014) & 0xFFFF
        n165 = rol16(n165, 3)
        encrypted[i] = data[i] ^ (n165 & 0xFF)
    return bytes(encrypted)

# Create a test save with reasonable values
save_data = bytearray(22987)

# Set some reasonable values
# Scene index (n17) at offset 12485 = 33 (a valid map index)
save_data[12485] = 33
# Character count (n6_0) at offset 12484 = 4 (a reasonable party size)
save_data[12484] = 4
# Some map data at the beginning (first 2211 bytes)
for i in range(2211):
    save_data[i] = i % 256
# Temp map data (next 2560 bytes)
for i in range(2560):
    save_data[2211 + i] = (i * 7) % 256
# Some character data
for i in range(4 * 80):  # 4 characters * 80 bytes each
    save_data[4771 + i] = (i * 13) % 256

# Calculate checksum
checksum = sum(save_data[:22983]) & 0xFFFFFFFF
# Store checksum in little-endian
save_data[22983:22987] = struct.pack('<I', checksum)

print(f"Test save created with:")
print(f"  Scene index (raw): {save_data[12485]}")
print(f"  Character count (raw): {save_data[12484]}")
print(f"  Checksum: 0x{checksum:08X}")

# Encrypt
encrypted = encrypt(save_data)

# Write to file
with open('bin/FD2_TEST.SAV', 'wb') as f:
    f.write(encrypted)

print(f"Encrypted test save written to bin/FD2_TEST.SAV")

# Verify by decrypting
def decrypt(data):
    decrypted = bytearray(data)
    n165 = 165
    for i in range(len(data)):
        n165 = (n165 + 0x9014) & 0xFFFF
        n165 = rol16(n165, 3)
        decrypted[i] = data[i] ^ (n165 & 0xFF)
    return bytes(decrypted)

decrypted = decrypt(encrypted)
print(f"Decrypted verification:")
print(f"  Scene index: {decrypted[12485]}")
print(f"  Character count: {decrypted[12484]}")
print(f"  Checksum match: {sum(decrypted[:22983]) & 0xFFFFFFFF == struct.unpack('<I', decrypted[22983:22987])[0]}")
