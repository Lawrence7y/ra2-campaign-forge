# Two-tier entry set: tier1 = PE entry + direct E8 call targets;
# tier2 = instruction starts that follow ret/uncond-jmp and are NOT forward-reachable from tier1
#         (i.e. code reachable only indirectly, e.g. through vtables) -> indirect function entries.
import struct, json, array as _ar, time
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]; ENTRY=IB+struct.unpack_from('<I',d,e+24+16)[0]
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text); TL=len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open(OUT+n+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
SL=[int(x) for x in starts]; NS=len(SL)
sz_at=bytearray(TL); kd_at=bytearray(TL); tg_at=_ar.array('I',[0])*TL
for i in range(NS):
    o=SL[i]-base; sz_at[o]=int(sizes[i]); kd_at[o]=int(kinds[i])
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in range(NS):
    if kd_at[SL[i]-base] in (2,6):
        o=SL[i]-base; ins=None
        for x in md.disasm(text[o:o+16],SL[i]): ins=x; break
        if ins and ins.op_str.startswith('0x'): tg_at[o]=int(ins.op_str,16)
CALLT=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3})
T1=sorted({t for t in CALLT if base<=t<tend and sz_at[t-base]>0}|{ENTRY})
T1SET=set(T1)
# global forward reachability from tier1
reach=bytearray(TL); work=list(T1); t0=time.time()
for a in T1: reach[a-base]=1
while work:
    a=work.pop()
    o=a-base
    kk=kd_at[o]
    nxt=[]
    if kk in (2,6,3) and tg_at[o]:
        nxt.append(tg_at[o])
    if kk not in (1,2,5,7):
        nxt.append(a+sz_at[o])
    for b in nxt:
        if base<=b<tend:
            ob=b-base
            if sz_at[ob]>0 and not reach[ob]:
                reach[ob]=1; work.append(b)
print('tier1',len(T1),'forward-reachable insns',sum(reach),'of',NS,'%.1fs'%(time.time()-t0))
B2=[int(starts[i]) for i in range(1,NS) if kinds[i-1] in (1,2)]
orph=[a for a in B2 if not reach[a-base]]
# also drop orphan candidates that are unreachable *and* fully surrounded by unreachable data-like code:
# keep only those we can justify (start of a reachable-only-indirectly region of >=4 insns)
ORPH=sorted(set(orph))
print('B2 candidates',len(B2),'unreachable from tier1',len(ORPH))
T2=ORPH
ENTRIES=sorted(set(T1)|set(T2))
json.dump(dict(tier1=len(T1),tier2=len(T2),total=len(ENTRIES),
   forward_reachable_insns=sum(reach),insns=NS,
   tier2_addrs=[hex(x) for x in T2]),
   open(OUT+'x120exec_entries.json','w'),indent=1)
open(OUT+'reach.bin','wb').write(bytes(reach))
_ar.array('I',ENTRIES).tofile(open(OUT+'entries.bin','wb'))
print('entries total',len(ENTRIES))
print('is 0x4af780 tier2?',0x4af780 in set(T2))
