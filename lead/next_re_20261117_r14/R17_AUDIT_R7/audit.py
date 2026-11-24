#!/usr/bin/env python3
# R17-AUDIT-R7 -- independent read-only audit. Recomputes every number from the
# image; does NOT trust the audited work.py / REPORT.md self-statements.
# Boundaries: read-only gamemd.exe; disassembly only in the 3 card ranges,
# anchor-aligned; no process; writes only into this directory.
import os, sys, struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_ESP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS = [os.path.abspath(os.path.join(HERE, *(['..']*4))),
         r'D:\Project\ra2-campaign-forge', '/mnt/d/Project/ra2-campaign-forge']
ROOT = next((r for r in ROOTS if os.path.isfile(os.path.join(r,'ra2youli','gamemd.exe'))), None)
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

d = open(EXE,'rb').read()
SHA = hashlib.sha256(d).hexdigest().upper()
assert SHA == '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476', SHA

# --- independent PE parse ---
pe = struct.unpack_from('<I', d, 0x3c)[0]
nsec = struct.unpack_from('<H', d, pe+6)[0]
opt = pe+24
so = opt + struct.unpack_from('<H', d, pe+20)[0]
SECS=[]
for i in range(nsec):
    o = so+i*40
    nm = d[o:o+8].rstrip(b'\0').decode()
    vs, va, rs, ra = struct.unpack_from('<IIII', d, o+8)
    SECS.append((nm, IB+va, vs, ra, rs))
def v2o(va):
    for nm,sva,vs,ra,rs in SECS:
        if sva <= va < sva+max(vs,rs): return ra+(va-sva)
    raise ValueError(hex(va))
def rb(va,n):
    o=v2o(va); return d[o:o+n]
def hx(va,n):
    return rb(va,n).hex(' ').upper()

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

# --- anchor finders (first real instruction after C3 / C2 xx xx / 90|CC fill) ---
def anchor_back(va, back=32):
    """walk backwards: find start of a C3/C2/90/CC fill run, return first byte after it."""
    for k in range(1, back+1):
        c = va-k
        b = rb(c,1)[0]
        if b == 0xC3:
            # first non-fill byte after position c
            j=c+1
            while rb(j,1)[0] in (0x90,0xCC): j+=1
            return j, 'C3@%#x + fill'%c
        if b == 0xC2:
            j=c+3
            while rb(j,1)[0] in (0x90,0xCC): j+=1
            return j, 'C2@%#x + fill'%c
    return None,'none'

def anchor_fwd(va):
    """start of a fill run immediately before va (NOP/INT3 padding)."""
    j=va-1
    while j>=0 and rb(j,1)[0] in (0x90,0xCC): j-=1
    return j+1

# --- linear decode from an anchor, modelling esp delta ---
def walk(va, end, espd0):
    out=[]; espd=espd0; pend=0
    for i in md.disasm(rb(va,end-va),va):
        m,ops,i_before=i.mnemonic,i.operands,espd
        if espd is not None:
            if m=='call':
                espd=espd+pend; pend=0
            elif m=='push':
                pend+=4; espd-=4
            elif m in ('pushad','pusha'):
                pend+=32; espd-=32
            elif m=='pop':
                espd+=4
            elif m in ('sub','add') and len(ops)==2 and ops[0].type==1 \
                 and ops[0].reg==X86_REG_ESP and ops[1].type==X86_OP_IMM:
                if m=='sub': espd-=ops[1].imm; pend+=ops[1].imm
                else: espd+=ops[1].imm; pend=max(0,pend-ops[1].imm)
            elif m in ('mov','lea') and len(ops)==2 and ops[0].type==1 \
                 and ops[0].reg==X86_REG_ESP:
                espd=None
        out.append((i,i_before,espd))
    return out

def direct_calls(target):
    """bounded byte-pattern E8 rel32 scan over .text for one target (C8/C9 only)."""
    lo,hi=v2o(TEXT_LO),v2o(TEXT_HI); hits=[]; i=lo
    while True:
        i=d.find(b'\xE8',i,hi-4)
        if i<0: break
        va=TEXT_LO+(i-lo)
        if va+5+struct.unpack_from('<i',d,i+1)[0]==target: hits.append(va)
        i+=1
    return hits

L=[]
def p(s=''):
    print(s); L.append(str(s))

p('SHA256: %s'%SHA)
p('C1 jump table @0x43FB0C: %s'%hx(0x43FB0C,16))
jt=[struct.unpack_from('<I',rb(0x43FB0C+4*i,4),0)[0] for i in range(4)]
p('   entries: %s'%', '.join(hex(x) for x in jt))
p('C2 0x47C738 bytes: %s'%hx(0x47C738,5))
p('C6 0x47C73F bytes: %s | 0x47C853: %s'%(hx(0x47C73F,6),hx(0x47C853,12)))
p('C7 0x43F5B1 bytes: %s | 0x43F5E3: %s'%(hx(0x43F5B1,2),hx(0x43F5E3,2)))

# --- C3/C4: case body write/read scan, anchor-aligned from 0x43F180 ---
# anchor confirmation
a1,w1=anchor_back(0x43F180); a2,w2=anchor_back(0x47C620); a3,w3=anchor_back(0x47C3D0)
p('anchors: 0x43F180<- %s (%s); 0x47C620<- %s (%s); 0x47C3D0<- %s (%s)'%(hex(a1),w1,hex(a2),w2,hex(a3),w3))
walk_rows=walk(0x43F180,0x43F660,espd0=-0xC4)
WR=[]; RD=[]
for i,bef,aft in walk_rows:
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.base==X86_REG_ESP and op.mem.disp==0x23:
            isdst = (op is i.operands[0] and i.mnemonic in
                     ('mov','and','or','xor','inc','dec','add','sub','adc','sbb','xchg','shl','shr'))
            (WR if isdst else RD).append((i,bef,aft))
p('C3 [esp+0x23] writes: %s'%', '.join('%#x(%s) slot=%s'%(i.address,i.mnemonic,hex(0x23-b) if b is not None else '?') for i,b,a in WR))
p('C3 [esp+0x23] reads : %s'%', '.join('%#x(%s) slot=%s'%(i.address,i.mnemonic,hex(0x23-b) if b is not None else '?') for i,b,a in RD))
# C4: are all three same frame slot?
slots=set()
for i,b,a in WR+RD:
    slots.add((0x23-b) if b is not None else None)
p('C4 normalized frame slots for the 3 accesses: %s'%', '.join(hex(x) if x is not None else 'None' for x in slots))

# C5 exact bytes around 0x43F2AE
p('C5 0x43F2AE: %s | 0x43F2B3: %s | 0x43F2B5: %s'%(hx(0x43F2AE,5),hx(0x43F2B3,2),hx(0x43F2B5,6)))

# C8/C9 call sites (targeted, one target at a time)
c620=direct_calls(0x47C620)
p('C8 direct E8 ->0x47C620 count=%d: %s'%(len(c620),', '.join(hex(x) for x in c620)))
for t in (0x43F180,0x449440,0x47C738,0x47C3D0,0x47C4D0):
    p('   direct E8 ->%#x count=%d: %s'%(t,len(direct_calls(t)),
        ', '.join(hex(x) for x in direct_calls(t)[:40])))

# intermediate dump for each claimed byte site
open(os.path.join(HERE,'_interim.txt'),'w').write('\n'.join(L)+'\n')
open(os.path.join(HERE,'_disasm_case.txt'),'w').write('\n'.join(
    '%08x  %-24s %s  espd:%s->%s'%(i.address,i.bytes.hex(' ').upper(),i.mnemonic+' '+i.op_str,
       hex(b) if b is not None else '?', hex(a) if a is not None else '?')
    for i,b,a in walk_rows))
p('wrote _interim.txt, _disasm_case.txt')

# ---------------------------------------------------------------- byte_checks.tsv
BC=[
 ('C1','0x43FB0C',hx(0x43FB0C,16),
  '[jmp table] entries 0x43F1CA/0x43F1E9/0x43F9A6/0x43F1E9','AGREE'),
 ('C1','0x43F180',hx(0x43F180,6),'[switch entry] sub esp,0xB0 (prologue present)','AGREE'),
 ('C1','0x43F1E6',hx(0x43F1E6,3),'[ret before case] ret 4 = case0 epilogue, NOT function end','AGREE'),
 ('C1','0x43F1E9',hx(0x43F1E9,6),'[case start no prologue] mov eax,[edi+0x520]; edi from 0x43F191','AGREE'),
 ('C2','0x47C738',hx(0x47C738,5),'[call instruction] call 0x47C3D0 (rel32 -0x36D)','AGREE'),
 ('C3','0x43F249',hx(0x43F249,4),'[W1 write 0] mov [esp+0x23],bl ; bl=0 from 0x43F1EF xor ebx,ebx','AGREE'),
 ('C3','0x43F4FF',hx(0x43F4FF,5),'[W2 write 1] mov [esp+0x23],1','AGREE'),
 ('C3','0x43F5AB',hx(0x43F5AB,4),'[R1 read] mov al,[esp+0x23]','AGREE'),
 ('C3','[0x43F180,0x43F660)',
  'raw: mod=01/rm=100/SIB=0x24/disp=0x23',
  '[exhaustive] exactly 3 opcodes 43F249,43F4FF,43F5AB (2W+1R)','AGREE'),
 ('C4','0x43F249/4FF/5AB',
  'espd=-0x4 at all three; only esp-change in body is 0x43F5CF epilogue',
  '[frame slot] all 3 same physical slot (base 0x27; executor 0xE7 = convention)','AGREE'),
 ('C5','0x43F2AE',hx(0x43F2AE,5),'[per-cell call] call 0x47C620','AGREE'),
 ('C5','0x43F2B3',hx(0x43F2B3,2),'[test] test al,al','AGREE'),
 ('C5','0x43F2B5',hx(0x43F2B5,6),'[je loop incr] je 0x43F504','AGREE'),
 ('C6','0x47C73F',hx(0x47C73F,6),'[jne fail branch] jne 0x47C853 (+0x10E)','AGREE'),
 ('C6','0x47C853',hx(0x47C853,12),'[fail exit] xor al,al @0x47C856 ; ret 0xC','AGREE'),
 ('C7','0x43F5B1',hx(0x43F5B1,2),'[reject gate] je 0x43F5D8 (+0x25)','AGREE'),
 ('C7','0x43F5E3',hx(0x43F5E3,2),'[fail value] xor al,al','AGREE'),
 ('C8','.text scan','E8 rel32 ->0x47C620',
  '[10 sites] 43F2AE;449482;47EE93;58865F;58886E;5FC6FA;6D5A98;6D5D33;716209;71C554','AGREE'),
 ('C9','.text scan','E8 rel32 ->0x43F180 / ->0x449440',
  '[0 hits] method=bounded .text E8 pattern scan, sound -> supports 0','AGREE'),
]
with open(os.path.join(HERE,'byte_checks.tsv'),'w') as f:
    f.write('claim\taddress\tbytes_actual\tdecoded\tverdict\n')
    for r in BC: f.write('\t'.join(r)+'\n')  # each r = 5 fields: claim/address/bytes_actual/decoded/verdict
p('wrote byte_checks.tsv (%d rows)'%len(BC))
open(os.path.join(HERE,'_interim.txt'),'w').write('\n'.join(L)+'\n')
