import struct,json,array as _ar
P='ra2bench/gamemd.exe'; d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]; IB=0x400000
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text); TL=len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open('_r120/'+n+'.bin','rb').read()); return a
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
CALLT=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3)
ENTRIESET={t for t in CALLT if base<=t<tend and sz_at[t-base]>0}
def preds(a):
    out=[]
    for k in range(1,16):
        p=a-k; po=p-base
        if po<0 or po>=TL: continue
        s=sz_at[po]
        if s==0: continue
        kk=kd_at[po]; t=tg_at[po]
        if p+s==a and kk not in (1,2,5,7): out.append(p)
        if (kk in (2,6) or kk==3) and t==a: out.append(p)
    return out
for site in (0x4af7df,0x4db560,0x7f7c80+0):
    if site==0x7f7c80: continue
    print('=== site',hex(site),'sz_at',sz_at[site-base],'kd',kd_at[site-base])
    seen={site}; work=[site]; found=set()
    while work:
        x=work.pop()
        for p in preds(x):
            if p in seen: continue
            if p in ENTRIESET: found.add(p); continue
            seen.add(p); work.append(p)
    print('  reach back',len(seen),'entries',[hex(x) for x in sorted(found)])
    print('  min/max',hex(min(seen)),hex(max(seen)))
    # any entry in [min,max]?
    print('  entries in range',[hex(x) for x in sorted(ENTRIESET) if min(seen)<=x<=max(seen)])
    # print insns around site entry guess 0x4af780
    for a in (0x4af780,0x4af7df):
        print('   insn at',hex(a),'sz',sz_at[a-base],'kind',kd_at[a-base])
