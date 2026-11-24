"""Final targeted evidence: INI keys for +0xB8, ore callers semantics, overlay load chain."""
from lib import *
import bisect, struct
asrt=sorted(atlas.items()); keys=[k for k,v in asrt]
def func_of(a):
    i=bisect.bisect_right(keys,a)-1
    if i>=0:
        e,sz=asrt[i]
        if e<=a<e+sz: return (e,sz)
    return None
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
cov={}
with open(COV,encoding='utf-8') as f:
    next(f)
    for ln in f:
        q=ln.rstrip('\n').split('\t')
        if len(q)>=5: cov[q[0].upper()]=(q[1],q[2],q[3],q[4])

def cstr(va,n=80):
    b=read(va,n)
    if not b: return None
    z=b.find(b'\0'); return b[:z if z>=0 else len(b)].decode('latin1','replace')

print("=== INI key strings around +0xB8 value load ===")
for va in [0x8448EC,0x81938C,0x8448E0,0x819380]:
    print(f"  {va:#x}: {cstr(va)!r}")

print("\n=== callers of 0x485020 (7 functions) semantics from coverage ===")
for f in [0x424000,0x4DE000,0x4DE200,0x568070,0x685000,0x6D7A00,0x70F950]:
    c=cov.get(f"{f:08X}")
    print(f"  {f:#x} size={atlas.get(f)} name={c[1] if c else '?'} grade={c[3] if c else '?'}")
    print(f"       sem={(c[2] if c else '')[:70]}")

print("\n=== 0x721B00 (TiberiumClass::LoadRules?) full disasm ===")
for ins in disasm(0x721B00,0x2A0):
    if ins.id==0: continue
    print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

print("\n=== overlay (cell+0x44) load: xref to 0x47bc21 write context in ctor ===")
# cell+0x44 overlay type: find where set from INI / map load (writes outside ctor)
for ins in disasm(0x56E000,0x400):
    if ins.id==0: continue
    if '0x44]' in ins.op_str and ins.mnemonic in ('mov','cmp'):
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
