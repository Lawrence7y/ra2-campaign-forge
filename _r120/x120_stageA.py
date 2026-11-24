import struct, json, time, array
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]
sec=e+24+optsz; S={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); S[nm]=(va,vs,ra,rs)
tv,tvs,tra,trs=S['.text']; text=d[tra:tra+tvs]; base=IB+tv
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
starts=array.array('I'); kinds=array.array('B')
pushes=[]; calls=[]
t0=time.time(); off=0; resync=0
CH=0x10000
while off<len(text):
    end=min(off+CH,len(text)); chunk=text[off:end]; got=0; last=off
    for (a,sz,m,o) in md.disasm_lite(chunk, base+off):
        k=0
        if m=='ret': k=1
        elif m=='jmp': k=2
        elif m=='call':
            k=3 if text[(a-base):(a-base)+1]==b'\xe8' else 4
            calls.append((a,k,o))
        elif m=='int3': k=5
        elif m[0]=='j' or m=='loop' or m=='loope' or m=='loopne': k=6
        starts.append(a); kinds.append(k)
        if m=='push' and o.startswith('0x') and o.endswith(('','')) and o[2:].strip('0123456789abcdef')=='':
            pushes.append((a,int(o,16)))
        got+=1; last=(a-base)+sz
    if got==0: off+=1; resync+=1
    else: off=last if last>off else off+1
starts.tofile(open(OUT+'x120_starts.bin','wb')); kinds.tofile(open(OUT+'x120_kinds.bin','wb'))
json.dump(dict(base=base,n=len(starts),resync=resync,pushes=pushes,calls=calls),open(OUT+'x120_stageA.json','w'))
print('insns',len(starts),'resync',resync,'push_imm',len(pushes),'calls',len(calls),'%.1fs'%(time.time()-t0))
