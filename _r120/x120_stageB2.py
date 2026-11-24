import struct,json,bisect,re
import array as _ar
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]; sec=e+24+optsz
S={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); S[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=S['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']
starts=_ar.array('I'); starts.frombytes(open(OUT+'x120_starts.bin','rb').read())
kinds=_ar.array('B'); kinds.frombytes(open(OUT+'x120_kinds.bin','rb').read())
A=json.load(open(OUT+'x120_stageA.json'))
pushset={a:v for a,v in A['pushes']}; calllist=[(a,k,o) for a,k,o in A['calls']]
callset={a:o for a,k,o in calllist}
N=len(starts)
# --- C1: first insn after >=1 byte 0xCC padding run
def padcand(minrun):
    out=[]
    for i,a in enumerate(starts):
        o=a-base
        if o==0: continue
        n=0; p=o-1
        while p>=0 and text[p]==0xCC: n+=1; p-=1
        if n>=minrun and text[o]!=0xCC: out.append(a)
    return out
C1a=padcand(1); C1b=padcand(2); C1c=padcand(3)
print('C1 candidates >=1:%d >=2:%d >=3:%d'%(len(C1a),len(C1b),len(C1c)))
# --- C2: instruction start after ret / uncond jmp
C2=[]
for i in range(1,N):
    if kinds[i-1] in (1,2): C2.append(starts[i])
C2=sorted(set(C2)); print('C2 count',len(C2))
# --- C3: call targets (rel32 direct) + after-terminator
C3=set()
for a,k,o in calllist:
    if k==3:
        try: t=int(o,16)
        except: continue
        if base<=t<base+len(text) and t in set(starts): C3.add(t)
C3=sorted(C3); print('C3 count',len(C3))
json.dump(dict(C1_ge1=len(C1a),C1_ge2=len(C1b),C1_ge3=len(C1c),C2=len(C2),C3=len(C3)),
          open(OUT+'x120_boundary_counts.json','w'),indent=1)
_ar.array('I',C1a).tofile(open(OUT+'x120_b_C1.bin','wb'))
_ar.array('I',C2).tofile(open(OUT+'x120_b_C2.bin','wb'))
_ar.array('I',C3).tofile(open(OUT+'x120_b_C3.bin','wb'))
