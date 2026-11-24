# RD disassembly v2: save addr/size/kind/target + fallthrough-continuation bitmap.
import struct, json, array, time
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]; entry=IB+struct.unpack_from('<I',d,e+24+16)[0]
sec=e+24+optsz; S={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); S[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=S['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
N=len(text)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
covered=bytearray(N); entered=bytearray(N)
A=array.array('I'); Z=array.array('B'); K=array.array('B'); T=array.array('I'); F=array.array('B')
work=[entry]; entered[entry-base]=1
call_targets=set()
t0=time.time()
while work:
    a=work.pop()
    while base<=a<tend:
        o=a-base
        if covered[o]: break
        ins=None
        for i in md.disasm(text[o:o+16],a): ins=i; break
        if ins is None: break
        m=ins.mnemonic; k=0; tgt=0; flownext=1
        if m=='ret': k=1; flownext=0
        elif m=='jmp':
            k=2; flownext=0
            if ins.op_str.startswith('0x'): tgt=int(ins.op_str,16)
        elif m=='call':
            if text[o]==0xE8:
                k=3; tgt=int(ins.op_str,16); call_targets.add(tgt)
                if base<=tgt<tend and not entered[tgt-base]: entered[tgt-base]=1; work.append(tgt)
            else: k=4
        elif m=='int3': k=5; flownext=0
        elif m and (m[0]=='j' or m in ('loop','loope','loopne')):
            k=6
            if ins.op_str.startswith('0x'):
                tgt=int(ins.op_str,16)
                if base<=tgt<tend and not entered[tgt-base]: entered[tgt-base]=1; work.append(tgt)
        elif m.startswith('.'): k=7; flownext=0   # skipdata byte
        if k==2 and tgt:
            if base<=tgt<tend and not entered[tgt-base]: entered[tgt-base]=1; work.append(tgt)
        A.append(a); Z.append(ins.size); K.append(k); T.append(tgt); F.append(flownext)
        covered[o]=1
        if not flownext: break
        na=a+ins.size
        if na-base<N and covered[na-base]: break
        a=na
print('insn',len(A),'call_targets',len(call_targets),'%.1fs'%(time.time()-t0))
A.tofile(open(OUT+'rd2_addr.bin','wb')); Z.tofile(open(OUT+'rd2_size.bin','wb'))
K.tofile(open(OUT+'rd2_kind.bin','wb')); T.tofile(open(OUT+'rd2_tgt.bin','wb'))
F.tofile(open(OUT+'rd2_flow.bin','wb'))
json.dump(dict(entry=hex(entry),n_insn=len(A),n_call_targets=len(call_targets),
   bytes_covered=sum(covered),elapsed=round(time.time()-t0,1)),
   open(OUT+'rd2_meta.json','w'),indent=1)
