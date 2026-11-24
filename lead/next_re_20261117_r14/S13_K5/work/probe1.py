from re_core import *
import re
print("STRINGS")
for va in [0x817474,0x817694]:
    print(hex(va), repr(cstr(va)))
print("\nPRECEDENT CALLERS")
for va in find_bytes(bytes.fromhex('e84fa90600'), '.text'): print(hex(va))
for va in find_bytes(bytes.fromhex('e861a90600'), '.text'): print(hex(va))
for va in find_bytes(bytes.fromhex('e8a1eaffff'), '.text'): print(hex(va))
print("\nNEW CTOR 75CEC0 call sites")
for pat in ['e83dd93400','e8a1eaffff']:
    print(pat, [hex(x) for x in find_bytes(bytes.fromhex(pat), '.text')])
print("\nBULLET CTOR CALL SITES")
for pat in ['e823f7ffff','e8d1c93500','e8adc83500']:
    print(pat, [hex(x) for x in find_bytes(bytes.fromhex(pat), '.text')])
print("\nTARGET ROWS")
for x in target_rows():
    if int(x['entry'],16) in {0x40F510,0x46C440,0x4393F0,0x46C890,0x62AF70,0x7730F0,0x46B5C0}:
        print(x)
print("\nCOV ROWS")
c=cov_rows()
for va in [0x40F510,0x46C440,0x4393F0,0x46C890,0x62AF70,0x7730F0,0x46B5C0]: print(hex(va), c.get(va))
print("\nCTOR HEAD 75CEC0")
print("\n".join(fmt(i) for i in dis(0x75CEC0,180)))
print("\nCTOR HEAD 46BBC0")
print("\n".join(fmt(i) for i in dis(0x46BBC0,180)))
