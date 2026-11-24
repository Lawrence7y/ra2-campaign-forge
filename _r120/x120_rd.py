# Recursive-descent disassembly (code-reachability ground truth), self-written PE parse.
import struct, json, array, time, sys
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
md=Cs(CS_ARCH_X86,CS_MODE_32)
md.skipdata=True
N=len(text)
covered=bytearray(N)      # 1 if address is a decoded instruction start
seen_block=bytearray(N)
insn_addr=array.array('I'); insn_kind=array.array('B'); insn_tgt=array.array('I')
# kind: 1 ret,2 jmp(uncond),3 call direct,4 call indirect,5 int3,6 jcc,0 other
work=[]; call_targets=set(); noncall_targets=set()
def push(a):
    if base<=a<tend and not seen_block[a-base]:
        work.append(a)
push(entry)
# seed with direct-call targets found by a first linear sweep is circular; instead traverse and add discovered
t0=time.time()
while work:
    a=work.pop()
    while True:
        if not (base<=a<tend): break
        o=a-base
        if covered[o]: break
        if seen_block[o]: break
        seen_block[o]=1
        chunk=text[o:o+16]
        got=None
        for ins in md.disasm(chunk,a):
            got=ins; break
        if got is None:
            break
        k=0; tgt=0; flow_next=True
        m=got.mnemonic
        if m=='ret': k=1; flow_next=False
        elif m=='jmp':
            k=2; flow_next=False
            if got.op_str.startswith('0x'):
                tgt=int(got.op_str,16)
        elif m=='call':
            if text[o]==0xE8:
                k=3; tgt=int(got.op_str,16); call_targets.add(tgt); push(tgt)
            else:
                k=4
        elif m=='int3': k=5; flow_next=False
        elif m[0]=='j' or m in ('loop','loope','loopne'):
            k=6; tgt=int(got.op_str,16) if got.op_str.startswith('0x') else 0
        if k==6 and tgt:
            noncall_targets.add(tgt); push(tgt)
        if k==2 and tgt:
            if base<=tgt<tend: noncall_targets.add(tgt)
            push(tgt)
        insn_addr.append(a); insn_kind.append(k); insn_tgt.append(tgt)
        covered[o]=1
        nxt=a+got.size
        if not flow_next: 
            break
        if nxt-base<N and covered[nxt-base]: 
            noncall_targets.add(nxt); break
        a=nxt
print('decoded insns',len(insn_addr),'blocks',len(seen_block),'call targets',len(call_targets),
      'elapsed %.1fs'%(time.time()-t0))
insn_addr.tofile(open(OUT+'rd_addr.bin','wb')); insn_kind.tofile(open(OUT+'rd_kind.bin','wb'))
insn_tgt.tofile(open(OUT+'rd_tgt.bin','wb'))
json.dump(dict(entry=hex(entry),base=hex(base),n_insn=len(insn_addr),
   n_call_targets=len(call_targets),n_noncall_targets=len(noncall_targets),
   bytes_covered=sum(covered)),open(OUT+'rd_meta.json','w'),indent=1)
open(OUT+'rd_covered.bin','wb').write(bytes(covered))
