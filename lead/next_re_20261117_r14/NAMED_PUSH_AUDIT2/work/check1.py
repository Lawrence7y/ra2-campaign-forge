import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C, fnd
import capstone
X86 = capstone.x86

print("### 1) TeamClass 0x6E9140 dispatch head")
print(C.show_range(0x6E9430, 0x6E9470, "bounds+jumptable"))

print("\n### 2) jumptable detail")
for ins in C.disasm(0x6E9430, 40, nbytes=0x40):
    if ins.mnemonic in ("cmp", "ja", "jmp") and ("eax" in ins.op_str or "[" in ins.op_str):
        print("   " + C.fmt(ins))
tbl = C.u32(0x6E9F74)
print("   table base 0x6E9F74 first entry:", "%08X" % (tbl or 0))
