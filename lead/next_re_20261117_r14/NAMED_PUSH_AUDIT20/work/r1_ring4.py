import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show

b = Bin()

for vt in (0x7F4348,):
    print(f"=== writers of vt {vt:08X} (all sections) ===")
    for w in b.writers_of_imm(vt):
        print(f"  imm@{w['imm_at']:08X} ins@{w.get('ins_va', 0):08X} {w['text']}  bytes={w['bytes']}")

print("\n=== ctor candidate 006D1C20 prologue ===")
print(show(b.dis(0x6D1C20, 22)))
print("\n=== is 006D1C20 reached by callers? ===")
cs = b.callers_of(0x6D1C20)
print([hex(x) for x in cs])
for c in cs[:8]:
    print(f"-- context around {c:08X}")
    print(show(b.dis(c - 0x18, 12), "    "))

print("\n=== other refs to 006D1C20 via push imm (atexit?) ===")
print([hex(x) for x in b.push_sites(0x6D1C20)])

print("\n=== func start of 006D1C20 region / previous terminator ===")
print("func_back(006D1D54) =", hex(b.func_back(0x6D1D54) or 0))
print(show(b.dis(0x6D1BD0, 22)))
