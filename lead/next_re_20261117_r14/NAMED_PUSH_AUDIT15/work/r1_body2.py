import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

print("=== rest of 007B10C0 from 0x7B123F ===")
dump(0x7B123F, 0x120)

print()
print("=== function end search: scan forward for ret that closes 007B10C0 ===")
i = 0
for ins in disasm(0x7B10C0, 0x400):
    if ins.mnemonic in ('ret', 'jmp') and ins.op_str == '':
        print(f"   candidate end: {fmt_insn(ins)}")
