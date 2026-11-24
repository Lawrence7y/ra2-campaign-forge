# linear-sweep of .text with capstone disasm_lite, chunked 64KB, resync on invalid
import struct, json, re, array, time
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
d=open(P,'rb').read()
e_lfanew=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e_lfanew+6)[0]
optsz=struct.unpack_from('<H',d,e_lfanew+20)[0]
IB=struct.unpack_from('<I',d,e_lfanew+24+28)[0]
sec=e_lfanew+24+optsz
S={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8)
    S[nm]=dict(va=va,vs=vs,raw=ra,rawsize=rs)
tv,tr,tsz=S['.text']['va'],S['.text']['raw'],S['.text']['vs']
text=d[tr:tr+tsz]
base=IB+tv
t0=time.time()
md=Cs(CS_ARCH_X86,CS_MODE_32)
starts=array.array('I'); flags=array.array('B')
# flags: 1=ret 2=uncond jmp 4=call 8=int3 16=invalid-resync-marker(not used)
pushes={}   # addr -> imm (push imm32/imm8)
calls={}    # addr -> op_str
resync=0; nsync_bytes=0
CH=0x10000
off=0
while off < len(text):
    end=min(off+CH,len(text))
    chunk=text[off:end]
    got=0; last=off
    for (a,sz,m,o) in md.disasm_lite(chunk, base+off):
        f=0
        if m=='ret': f|=1
        elif m=='jmp': f|=2
        elif m=='call': f|=4
        elif m=='int3': f|=8
        starts.append(a); flags.append(f)
        if m=='push' and o.startswith('0x'):
            pushes[a]=int(o,16)
        if m=='call':
            calls[a]=o
        got+=1; last=(a-base)+sz
    if got==0:
        off+=1; resync+=1
    else:
        off=last if last>off else off+1
        if last<end and got>0:
            pass
print('insns',len(starts),'resync',resync,'time',round(time.time()-t0,1))
starts.tofile('/home/t628/projects/ra2-campaign-forge/_r120/x120_text_starts.bin')
flags.tofile('/home/t628/projects/ra2-campaign-forge/_r120/x120_text_flags.bin')
json.dump(dict(base=base,count=len(starts),resync=resync,
               pushes={hex(k):v for k,v in pushes.items()},
               calls={hex(k):v for k,v in calls.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r120/x120exec_sweep.json','w'))
print('pushes',len(pushes),'calls',len(calls))
