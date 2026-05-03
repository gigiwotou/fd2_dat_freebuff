import struct

def rol16(value, shift):
    return ((value << shift) | (value >> (16 - shift))) & 0xFFFF

def xor_encrypt(data):
    result = bytearray(data)
    n165 = 165
    for i in range(len(data)):
        n165 = (n165 + 0x9014) & 0xFFFF
        n165 = rol16(n165, 3)
        result[i] = data[i] ^ (n165 & 0xFF)
    return bytes(result)

with open('bin/FD2.SAV', 'rb') as f:
    data = f.read()

# Test 1: If raw data is all 0xFF, encrypt and check
print("Test 1: If original is all 0xFF, encrypted would be:")
all_ff = bytes([0xFF] * 22987)
encrypted_ff = xor_encrypt(all_ff)
print(f"  First 20: {encrypted_ff[:20].hex()}")
print(f"  Matches actual? {encrypted_ff[:20] == data[:20]}")

# Test 2: If raw data is all 0x00, encrypt and check
print("\nTest 2: If original is all 0x00, encrypted would be:")
all_00 = bytes([0x00] * 22987)
encrypted_00 = xor_encrypt(all_00)
print(f"  First 20: {encrypted_00[:20].hex()}")
print(f"  Matches actual? {encrypted_00[:20] == data[:20]}")

# Test 3: What if we decrypt and then re-encrypt to get back original?
decrypted = xor_encrypt(data)
re_encrypted = xor_encrypt(decrypted)
print(f"\nTest 3: Decrypt then re-encrypt:")
print(f"  Decrypted first 20: {decrypted[:20].hex()}")
print(f"  Re-encrypted matches original? {re_encrypted == data}")
