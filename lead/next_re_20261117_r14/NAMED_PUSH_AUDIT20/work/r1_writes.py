import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()

print("=== region 006D1E20..006D1EC0 (writes #2 #3) ===")
print(show(b.dis(0x6D1E20, 0x30)))
print("\n=== func_back(006D1E58)=", hex(b.func_back(0x6D1E58) or 0), " func_back(006D1E80)=", hex(b.func_back(0x6D1E80) or 0))
print("\n=== region 006DC430..006DC4A0 (write #4) ===")
print(show(b.dis(0x6DC430, 0x28)))
print("\n=== func_back(006DC473)=", hex(b.func_back(0x6DC473) or 0))
print("=== callers of 006DC470-ish function ===")
fs = b.func_back(0x6DC473)
print("start:", hex(fs), " callers:", [hex(x) for x in b.callers_of(fs)] if fs else None)
print("push sites (atexit?):", [hex(x) for x in b.push_sites(fs)] if fs else None)

print("\n=== dtor signature check for 006DC430 func ===")
if fs:
    print(show(b.dis(fs, 40)))

print("\n=== 7C8E17 (operator new?) ===")
print(show(b.dis(0x7C8E17, 6)))
