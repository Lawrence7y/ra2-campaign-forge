"""S18-F1: EventType name table @0x82091C + validate all 46 jump targets are instruction boundaries."""
import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import u32, read, disasm_insns

def cstr(va, n=80):
    b=read(va,n)
    if not b: return None
    return b.split(b'\x00')[0].decode('latin1')

print("===== EventType name table @0x82091C (Kind -> name) =====")
names={}
for k in range(0x31):
    p=u32(0x82091C+4*k)
    s=cstr(p) if p else None
    if s:
        names[k]=s
        print(f"  Kind {k:#04x} ({k:2d}): @{p:#x} {s}")

print("\n===== jump table 0x4C8114: 46 targets, boundary check =====")
for i in range(0x2E):
    t=u32(0x4C8114+4*i)
    ins=disasm_insns(t,1)
    ok = bool(ins) and ins[0].address==t
    first = f"{ins[0].mnemonic} {ins[0].op_str}" if ins else "<none>"
    nm=names.get(i+1,'?')
    print(f"  idx {i:#04x} Kind {i+1:#04x} {nm:24s} -> 0x{t:08X} boundary={ok} first='{first}'")
