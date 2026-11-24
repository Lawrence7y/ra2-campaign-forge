import sys,struct,json,re,collections,time,array
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000
md=Cs(CS_ARCH_X86,CS_MODE_32)

R=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}
VT_SET=set(VT)

RE_DISPATCH=re.compile(r'^jmp\s+dword ptr \[(e[a-z]{2})\s*\*\s*4\s*\+\s*(0x[0-9a-f]+)\]$')
RE_SW0=re.compile(r'^jmp\s+dword ptr \[(0x[0-9a-f]+)\s*\+\s*(e[a-z]{2})\s*\*\s*4\]$')
RE_MOVIMM=re.compile(r'^mov\s+dword ptr \[(e[a-z]{2})(?:\s*\+\s*(0x[0-9a-f]+))?\],\s*(0x[0-9a-f]+)$')

calls=[]; dispatch=[]; ctorev=[]; prologue=[]
CHUNK=0x10000
t0=time.time()
va=TL
insn_total=0
while va<TH:
    end=min(va+CHUNK,TH); blob=rd(va,end-va); pos=0; n=len(blob)
    while pos<n:
        got=None
        for ins in md.disasm_lite(blob[pos:pos+16],va+pos):
            got=ins; break
        if got is None: pos+=1; continue
        a,sz,mn,op=got
        if sz==0: pos+=1; continue
        insn_total+=1
        if mn=='call' or mn=='jmp':
            try:
                if op and op[0]!='e' and not op.startswith('0x') and not op.startswith('dword'):
                    pass
            except Exception: pass
            if op.startswith('0x'):
                t=int(op,16)
                if TL<=t<TH: calls.append((a,mn,t))
        if mn=='jmp' and 'dword ptr [' in op:
            m=RE_DISPATCH.match(op) or RE_SW0.match(op)
            if m:
                g=m.groups()
                base=int(g[1] if RE_DISPATCH.match(op) else g[0],16)
                dispatch.append((a,base,op))
        if mn=='mov' and 'dword ptr [' in op:
            m=RE_MOVIMM.match(op)
            if m:
                imm=int(m.group(3),16)
                if imm in VT_SET:
                    ctorev.append((a,m.group(1),int(m.group(2),16) if m.group(2) else 0,imm,op))
        if mn=='push' and op=='ebp':
            o=foff(a+1)
            if o and _img[o:o+2]==b'\x8b\xec': prologue.append(a)
        pos+=sz
    va=end
print('insns',insn_total,'%.1fs'%(time.time()-t0))
print('calls/jmps rel',len(calls),'dispatch',len(dispatch),'ctor',len(ctorev),'prologue',len(prologue))
print('distinct dispatch bases',len({b for _,b,_ in dispatch}))
print('distinct ctor vt',len({x[3] for x in ctorev}))
json.dump(dict(calls=calls,dispatch=dispatch,ctor=ctorev,prologue=sorted(set(prologue))),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_xrefs.json','w'))
for d in dispatch[:5]: print(hex(d[0]),d[2])
for c in ctorev[:5]: print(hex(c[0]),c[4])
