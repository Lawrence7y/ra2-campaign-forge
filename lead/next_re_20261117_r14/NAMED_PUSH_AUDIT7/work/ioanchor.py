"""AUDIT7: ground-truth which vtable slot is Read vs Write, via ReadFile/WriteFile imports."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast

pe = pefile.PE(EXE, fast_load=False)
want = ('ReadFile', 'WriteFile', 'ReadFileEx', 'WriteFileEx', 'fread', 'fwrite', 'memcpy', 'memmove')
iat = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode()
    for imp in entry.imports:
        nm = imp.name.decode() if imp.name else None
        if nm in want:
            iat[imp.address] = f"{dll}!{nm}"

print("IAT slots found:")
for a, n in sorted(iat.items()):
    print(f"  {a:08X} {n}")

recs = fast.db()['recs']
callers = {}
# indirect call through an absolute IAT slot: call dword ptr [imm] -> MEM operand, no base/index
for a, (mn, opstr, bh, imms) in recs.items():
    if mn == 'call' and 'dword ptr [' in opstr and ']' in opstr and '+' not in opstr.split('[')[1].split(']')[0]:
        inner = opstr.split('[')[1].split(']')[0]
        try:
            tgt = int(inner, 16)
        except ValueError:
            continue
        if tgt in iat:
            callers.setdefault(iat[tgt], []).append((a, fast.func_start(a)))

for name, lst in callers.items():
    print(f"\n{name}: {len(lst)} call sites")
    for a, f in lst[:14]:
        print(f"   site {a:08X} in fn {f:08X}")
