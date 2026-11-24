import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT14\work")
from auditlib import *

def sec(t): print("\n" + "="*72); print(t); print("="*72)

# --- callee 0x55A9B0 (common QI base, used by 3 entries) ---
sec("CALEE 0x55A9B0 (base QueryInterface) - look for E_POINTER/E_NOINTERFACE/S_OK returns")
disasm_range = disasm(0x55A9B0, 0xC0)
for i in disasm_range:
    print(fmt_insn(i))

# --- callee 0x55AA60 (stream-read helper, used by 004B62C0) ---
sec("CALEE 0x55AA60 - look for E_POINTER (80004003), jl passthrough, ret 0xc")
for i in disasm(0x55AA60, 0x70):
    print(fmt_insn(i))

# --- 004B62C0 taken branch 0x4B637C and tail ---
sec("004B62C0 taken branch @0x4B637C")
for i in disasm(0x4B637C, 0x30):
    print(fmt_insn(i))
sec("004B62C0 fallthrough @0x4B635E..0x4B637C (verify call [0x7E15F4])")
for i in disasm(0x4B635E, 0x20):
    print(fmt_insn(i))
print("u32(0x7E15F4) =", hex(u32(0x7E15F4)))
