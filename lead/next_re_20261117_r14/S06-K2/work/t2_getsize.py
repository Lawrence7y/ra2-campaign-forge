"""
S06-K2 T2: CellClass GetSize double-check (two independent channels).
Channel A: v[12] of the RTTI-derived primary vtable = B8 imm32 C3 -> size.
Channel B: constructor allocation points (push imm32 / mov [esp],imm / sub esp,imm forms).
Baseline: full .text B8 imm32 C3 candidate count + how many are NOT at a real vtable slot 12
(§969: ~837 candidates, 543 in non-slot-12) -> proves the discriminator is not specific by itself.
Outputs EVIDENCE/t2_getsize.txt
"""
from pehelp import *
import struct, collections

OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\t2_getsize.txt"
_l=[]
def p(s=''):
    print(s); _l.append(str(s))

CELL_VT=0x7e4eec
CELL_VTS=[0x7e4ec0,0x7e4ec8,0x7e4ed0,0x7e4eec]

def getsize_imm(f):
    b=read(f,6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3:
        return struct.unpack('<I',b[1:5])[0]
    return None

p("="*72)
p("S06-K2 T2 CellClass GetSize double-check")
p("="*72)

# ---- Channel A: v[12] ----
p("\n[Channel A] v[12] of RVTI primary vtable")
for vt in CELL_VTS:
    f12=u32(vt+12*4)
    g=getsize_imm(f12)
    b=read(f12,6)
    p(f"  vt {vt:#x} v[12]={f12:#x} bytes={b.hex() if b else '-'} -> GetSize={g} ({hex(g) if g else '-'})")
p(f"  PRIMARY vtable 0x7e4eec v[12]=0x{u32(CELL_VT+12*4):x} -> size 0x{getsize_imm(u32(CELL_VT+12*4)):x}")

# ---- Baseline: full .text B8 imm32 C3 candidates ----
p("\n[Baseline] full .text B8 <imm32> C3 candidates (§969 discrimination test)")
tlo,thi=text_bounds()
cands=[]
for va in range(tlo,thi-6):
    b=read(va,6)
    if len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        cands.append((va,struct.unpack('<I',b[1:5])[0]))
p(f"  B8 imm32 C3 candidates in .text = {len(cands)}")
# whole-image (all raw sections) byte-pattern count, report scope honestly
raw_all=pe.__data__
whole=[]
for i in range(len(raw_all)-6):
    if raw_all[i]==0xB8 and raw_all[i+5]==0xC3:
        whole.append((i,struct.unpack('<I',raw_all[i+1:i+5])[0]))
p(f"  B8 imm32 C3 raw byte pattern, whole file image = {len(whole)} (§969 '全镜像~837'; scope differs: raw bytes vs VA-decoded)")

# build set of all vtable slot-12 addresses: find COLs (u32(COL+0xC)=valid TD), then vtables whose [-1]=COL
rdata=next(s for s in SECTIONS if s[4]=='.rdata')
data=pe.get_data(rdata[2], rdata[3])
def is_td(td):
    if not td: return False
    sec=section_of(td)
    if not sec or sec[4] not in ('.rdata','.data'): return False
    nm=read(td+8,4) or b''
    return nm[:2] in (b'.?',) or nm.startswith(b'.?A')
cols=set()
for i in range(0,len(data)-3,4):
    v=struct.unpack_from('<I',data,i)[0]
    col=rdata[0]+i-0xC
    if col>=rdata[0] and is_td(v):
        cols.add(col)
slot12_addrs=set(); all_vt_slot={}
for col in cols:
    # find addresses A with dword[A]==col -> vtable at A+4
    for i in range(0,len(data)-3,4):
        if struct.unpack_from('<I',data,i)[0]==col:
            vstart=rdata[0]+i+4
            slots={}
            for k in range(60):
                f=u32(vstart+k*4)
                if not f: break
                s=section_of(f)
                if s and s[4]=='.text': slots[k]=f
                else: break
            if 12 in slots:
                slot12_addrs.add(slots[12]); all_vt_slot[vstart]=slots
p(f"  valid COLs found = {len(cols)}; vtables with slot12 in .text = {len(all_vt_slot)}; distinct slot12 funcs = {len(slot12_addrs)}")
in12=[c for c in cands if c[0] in slot12_addrs]
not12=[c for c in cands if c[0] not in slot12_addrs]
p(f"  B8/C3 candidates that ARE at some vtable slot 12 = {len(in12)}")
p(f"  B8/C3 candidates NOT at any vtable slot 12 = {len(not12)} (§969 expects ~543)")
p(f"  -> overlaying 'value is at a real vtable slot 12' prunes {len(not12)}/{len(cands)} false candidates")

# the specific 0x148 candidates at slot 12
p(f"\n  B8 48 01 00 00 C3 (size 0x148) candidates at any vtable slot 12:")
for va,val in in12:
    if val==0x148:
        # which vtables?
        owners=[hex(vt) for vt,slots in all_vt_slot.items() if slots.get(12)==va]
        p(f"    {va:#x} owners(vt12)={owners[:8]}{'...' if len(owners)>8 else ''}")
p(f"  total size-0x148 B8/C3 candidates anywhere in .text = {sum(1 for v,x in cands if x==0x148)}")

# ---- Channel B: allocation sites ----
p("\n[Channel B] constructor allocation points for size 0x148")
# search multiple encodings
SITE=0x148
patterns={
 'push imm32 (68 imm)': lambda va: (read(va,5) or b'')[:1]==b'\x68' and struct.unpack('<I',(read(va,5) or b'\0'*5)[1:5])[0]==SITE,
 'mov [esp],imm (C7 04 24 imm)': None,
 'push via 6A/FF handled elsewhere': None,
}
hits=collections.defaultdict(list)
# 68 imm32
for va in range(tlo,thi-5):
    b=read(va,5)
    if len(b)==5 and b[0]==0x68 and struct.unpack('<I',b[1:5])[0]==SITE:
        hits['push68'].append(va)
# C7 04 24 imm32
for va in range(tlo,thi-8):
    b=read(va,8)
    if len(b)==8 and b[:3]==b'\xc7\x04\x24' and struct.unpack('<I',b[3:7])[0]==SITE:
        hits['mov_esp'].append(va)
# sub esp, imm (81 EC imm32) with 0x148 - unlikely as allocation but check
for va in range(tlo,thi-6):
    b=read(va,6)
    if len(b)==6 and b[:2]==b'\x81\xec' and struct.unpack('<I',b[2:6])[0]==SITE:
        hits['sub_esp'].append(va)
for k in ('push68','mov_esp','sub_esp'):
    p(f"  {k}: {len(hits[k])} sites -> {[hex(x) for x in hits[k][:20]]}")

# Show context around the known 0x148 push sites to confirm they feed operator new + ctor
p("\n  context around push 0x148 sites (first 6):")
for va in hits['push68'][:6]:
    insns=disasm(va-6,40)
    ctx=' | '.join(f"{i.address:#x}:{i.mnemonic} {i.op_str}" for i in insns if i.id!=0)
    p(f"    @ {va:#x}: {ctx}")

# ---- 0x4c9150 shared stub trap ----
p("\n[0x4c9150 trap check]")
for vt in [0x7ed404,0x7e4eec]:
    f12=u32(vt+12*4)
    p(f"  vtable {vt:#x} v[12] = {f12:#x} (B8/C3? {getsize_imm(f12)}) -> {'NOT a GetSize' if getsize_imm(f12) is None else 'GetSize'}")
p(f"  0x4c9150 bytes = {(read(0x4c9150,8) or b'').hex()} (shared abstract stub, not a real GetSize)")

with open(OUT,'w') as f: f.write('\n'.join(_l)+'\n')
p(f"\n[saved] {OUT}")
