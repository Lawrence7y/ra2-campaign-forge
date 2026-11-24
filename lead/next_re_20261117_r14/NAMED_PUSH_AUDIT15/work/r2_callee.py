import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

print("=== callee 004A33A0 full ===")
ins = list(disasm(0x004A33A0, 0x260))
for i in ins:
    print(fmt_insn(i))
