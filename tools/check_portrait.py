import struct

# First character data: [0x07, 0x00, 0x05, 0x00, 0x30, 0x00]
# X=7, Y=5, portrait=?

data = bytes([0x07, 0x00, 0x05, 0x00, 0x30, 0x00])

print("Character 0 hex dump:")
for i in range(6):
    print(f"  byte[{i}] = 0x{data[i]:02x} = {data[i]}")

print()
print("Portrait ID interpretations:")
print(f"  byte[3] = {data[3]} (0x{data[3]:02x})")
print(f"  byte[4] = {data[4]} (0x{data[4]:02x})")
print()

# From enemy info, portrait should be 48 (0x30) for first enemy
print("Expected: First enemy portrait = 48 (from enemy info)")
print(f"  byte[4] = 0x30 = 48  <-- CORRECT!")
print(f"  byte[3] = 0x00 = 0   <-- WRONG")
