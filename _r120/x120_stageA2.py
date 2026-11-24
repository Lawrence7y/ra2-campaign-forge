# One-pass chunked sweep (64KB chunks, disasm_lite, no detail) -> compact binary/JSON facts.
import struct, json, time, array, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
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
md=Cs(CS_ARCH_X86,CS_MODE_32)
starts=array.array('I'); kinds=array.array('B'); sizes=array.array('B')
pushes=array.array('I'); pushv=array.array('I')
jumps=array.array('I'); jumpt=array.array('I')
calls=array.array('I'); callk=array.array('B'); callt=array.array('I')
IATS={0x7e15f8:'OleLoadFromStream',0x7e15f4:'OleSaveToStream',0x7e15e4:'StgOpenStorage',
      0x7e15c8:'StgCreateDocfile',0x7e15fc:'CoCreateInstance',0x7e1600:'OleRun',
      0x7e15f0:'CLSIDFromString',0x7e15e0:'StringFromGUID2'}
iatref=array.array('I'); iatslot=array.array('I')
t0=time.time(); off=0; resync=0; CH=0x10000
while off < len(text):
    end=min(off+CH,len(text)); chunk=text[off:end]; got=0; last=off
    for (a,sz,m,o) in md.disasm_lite(chunk, base+off):
        k=0; tg=None
        if m=='ret': k=1
        elif m=='jmp':
            k=2
            if o.startswith('0x'): tg=int(o,16)
        elif m=='call':
            if text[a-base]==0xE8: k=3; tg=int(o,16) if o.startswith('0x') else None
            else: k=4
        elif m=='int3': k=5
        elif m and m[0]=='j' or m in ('loop','loope','loopne'):
            k=6
            if o.startswith('0x'): tg=int(o,16)
        starts.append(a); kinds.append(k); sizes.append(sz)
        if m=='push' and re.fullmatch(r'0x[0-9a-f]+',o):
            pushes.append(a); pushv.append(int(o,16))
        if k in (2,6) and tg is not None:
            jumps.append(a); jumpt.append(tg)
        if m=='call':
            calls.append(a); callk.append(k); callt.append(tg if tg is not None else 0)
        if '0x' in o:
            for slot in IATS:
                if '0x%x'%slot in o:
                    iatref.append(a); iatslot.append(slot); break
        got+=1; last=(a-base)+sz
    if got==0: off+=1; resync+=1
    else: off=last if last>off else off+1
for nm,arr in [('a2_starts',starts),('a2_kinds',kinds),('a2_sizes',sizes),('a2_pushes',pushes),('a2_pushv',pushv),
               ('a2_jumps',jumps),('a2_jumpt',jumpt),('a2_calls',calls),('a2_callk',callk),
               ('a2_callt',callt),('a2_iatref',iatref),('a2_iatslot',iatslot)]:
    arr.tofile(open(OUT+nm+'.bin','wb'))
json.dump(dict(base=base,text_len=len(text),n_insn=len(starts),resync=resync,
               n_push_imm=len(pushes),n_jumps=len(jumps),n_calls=len(calls),
               n_iatref=len(iatref),iat_map={hex(k):v for k,v in IATS.items()},
               elapsed=round(time.time()-t0,1)),open(OUT+'x120exec_sweep_meta.json','w'),indent=1)
print('insn',len(starts),'push',len(pushes),'jmp',len(jumps),'call',len(calls),'iatref',len(iatref),
      'resync',resync,'%.1fs'%(time.time()-t0))
