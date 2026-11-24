import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

for va in [0x81B1D8, 0x889F64, 0x887734]:
    try:
        print(hex(va), "=", repr(R.cstr(va, 80)))
    except Exception as e:
        print(hex(va), "ERR", e)

print("--- IAT relevant ---")
for k, v in sorted(R.IAT.items()):
    if any(s in v for s in ["stricmp", "malloc", "free", "FindFirst", "FindNext"]):
        print(hex(k), v)

print("--- function 0x526960 (section count?) ---")
R.dump(0x526960, 0x80)
print("--- function 0x526cc0 (get key by index?) ---")
R.dump(0x526CC0, 0x90)
print("--- function 0x528a10 ---")
R.dump(0x528A10, 0xA0)
print("--- 0x7c8d20 ---")
R.dump(0x7C8D20, 0x40)
print("--- 0x7ca489 ---")
R.dump(0x7CA489, 0x40)
print("--- 0x410800 ---")
R.dump(0x410800, 0x60)
