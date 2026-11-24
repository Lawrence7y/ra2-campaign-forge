"""
S11-K1 final verification:
(A) broad RTTI TD name scan for any 'Loco' name (ensure 12 is complete)
(B) extract CLSID->factory ctor mapping from registration fn 0x6BB9A0 by parsing the
    repeated pattern: [new+ctor] ... push CLSID ... call RegisterClassObject(0x6C6400)
(C) two-channel class count:
    CH1 = RTTI TD name scan (data metadata)
    CH2 = count CLSID registrations in code (E8/xref) + base class (no CLSID)
"""
import re, struct
from pehelp import (IMAGE_BASE, rd, u32, sections, in_section, is_code, disasm, fmt)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K1\EVIDENCE\verify_final.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

# ---------- (A) broad RTTI scan ----------
P('===== (A) broad RTTI TD names containing "Loco" =====')
SEC=[]
for nm,vaoff,vsize,rsize,praw in sections():
    SEC.append((nm, IMAGE_BASE+vaoff, IMAGE_BASE+vaoff+max(vsize,rsize)))
pat=re.compile(rb'\.\?A[UV][A-Za-z0-9_]*Loco[A-Za-z0-9_]*@@\x00')
found={}
for nm,lo,hi in SEC:
    blob=rd(lo,hi-lo)
    for m in pat.finditer(blob):
        name=m.group(0)[:-1].decode('latin1')
        td=lo+m.start()-8
        try:
            v=u32(td); spare=u32(td+4)
        except Exception:
            continue
        if in_section(v,'.rdata') and spare==0:
            found[td]=name
P('valid TDs with Loco in name: %d' % len(found))
for td,name in sorted(found.items()):
    P('  TD %08X %s' % (td,name))
loco_tds = {td:n for td,n in found.items() if 'LocomotionClass' in n}
P('of which LocomotionClass family: %d' % len(loco_tds))

# ---------- (B) CLSID registration -> factory mapping ----------
P('')
P('===== (B) CLSID -> class factory ctor (from registration fn 0x6BB9A0) =====')
CLSID_NAME = {
 0x7E9A30:'Drive', 0x7E9A40:'Hover', 0x7E9A50:'Tunnel', 0x7E9A60:'Walk',
 0x7E9A70:'DropPod', 0x7E9A80:'Fly', 0x7E9A90:'Teleport', 0x7E9AA0:'Mech',
 0x7E9AB0:'Ship', 0x7E9AC0:'Jumpjet', 0x7E9AD0:'Rocket',
}
ins = disasm(0x6BD100, 0x400)
# parse: find 'push <CLSID>' then within next ~8 insns find 'call 0x6C6400';
# factory ctor is the 'call imm' just before the preceding 'push 1/push 1/push eax' block.
reg_map=[]
for idx,it in enumerate(ins):
    if it.mnemonic=='push' and it.op_str.startswith('0x'):
        try: val=int(it.op_str,16)
        except: continue
        if val in CLSID_NAME:
            # look backward for nearest 'call' that is a factory ctor (0x6C3Fxx..0x6C52xx)
            ctor=None
            for j in range(idx-1,max(-1,idx-12),-1):
                if ins[j].mnemonic=='call' and ins[j].op_str.startswith('0x6c'):
                    c=int(ins[j].op_str,16)
                    if 0x6C3F00<=c<=0x6C5300:
                        ctor=c; break
            reg_map.append((val,CLSID_NAME[val],ctor,it.address))
for clsid,nm,ctor,site in reg_map:
    P('CLSID %08X  %-9s  factory_ctor=%s  push_site=%08X' %
      (clsid,nm,('%08X'%ctor) if ctor else '?',site))
P('registration entries found: %d / 11' % len(reg_map))
P('distinct factory ctors: %d' % len(set(c for _,_,c,_ in reg_map if c)))

# ---------- (C) two-channel class count ----------
P('')
P('===== (C) two-channel class count =====')
P('CH1 (RTTI TD names) = %d (incl base LocomotionClass)' % len(loco_tds))
P('CH2 (code: %d CLSID registrations + 1 base w/o CLSID) = %d' % (len(reg_map), len(reg_map)+1))
P('concrete classes (with CLSID) = %d' % len(reg_map))

with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(L)+'\n')
print('WROTE',OUT)
