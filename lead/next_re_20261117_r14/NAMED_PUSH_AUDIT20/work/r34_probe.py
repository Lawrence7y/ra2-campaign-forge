import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()
for E in (0x00719E30, 0x0075C7F0):
    print(f"=== bytes @{E:08X} ===")
    print(b.hexat(E, 0x60))
    print(f"=== disasm @{E:08X} ===")
    for i in b.dis(E, 40):
        print(f(i))
    print()

print("=== 0055AA49..0055AA60 (S_OK return of base QI) ===")
for i in b.dis(0x55AA49, 8):
    print(f(i))

print("\n=== IID constants used by each row (repe cmpsd source) ===")
for E in (0x0069EE30, 0x00719E30, 0x0075C7F0):
    seq = b.dis(E, 40)
    for k, i in enumerate(seq):
        if i.mnemonic == "mov" and i.op_str.startswith("edi, 0x") and k + 2 < len(seq) and seq[k + 2].mnemonic == "repe cmpsd":
            print(f"  {E:08X}: IID const at {i.op_str.split(', ')[1]}  ({f(i)})")
