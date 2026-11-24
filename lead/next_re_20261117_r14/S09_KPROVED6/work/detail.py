"""Detailed per-entry disassembly dump with correct CFG loopback + jump-table detection."""
import sys, json
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r'D:\Project\ra2-campaign-forge')
raw = (ROOT/'ra2youli'/'gamemd.exe').read_bytes()
pe = pefile.PE(data=raw, fast_load=True); ib = pe.OPTIONAL_HEADER.ImageBase
secs = [dict(name=s.Name.rstrip(b'\0').decode('latin1'), va=ib+s.VirtualAddress,
             vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData) for s in pe.sections]
by = {s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va'] <= va < s['va']+s['rs']:
            o = s['ptr']+va-s['va']
            if o+4 <= len(raw): return o
    return None
def u32(va):
    o = va2off(va); return int.from_bytes(raw[o:o+4],'little') if o is not None else None
text = by['.text']; tva=text['va']; tlen=text['vs']; code = raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva<=v<tva+tlen
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}
sz=bytearray(tlen+16); kind=bytearray(tlen+16); tgt={}; insmap={}
RET=1;JMP=2;JCC=3;CALL=4
for ins in md.disasm(code,tva):
    o=ins.address-tva
    if o>=len(sz): break
    sz[o]=ins.size; insmap[o]=ins; mn=ins.mnemonic
    if mn=='ret' or mn.startswith('ret'): kind[o]=RET
    elif mn=='jmp':
        kind[o]=JMP
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn in JCCS:
        kind[o]=JCC
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn=='call': kind[o]=CALL

def extent(entry, cap=8000):
    seen=set(); stack=[entry]; addrs=[]; lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); addrs.append(a); n+=1
            if n>cap: stack=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t)
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s; continue
            a=a+s
    return lo,hi,sorted(addrs)

for k in sys.argv[1:]:
    entry=int(k,16); lo,hi,addrs=extent(entry)
    print('='*90)
    print('ENTRY %s  CFG=[%08X,%08X) size=%d ins=%d'%(k,lo,hi,hi-lo,len(addrs)))
    # find jump tables: indirect jmp [reg*4+disp] patterns / cmp reg,imm followed by jmp [..]
    backedges=[]
    for a in addrs:
        o=a-tva
        if o in tgt:
            t=tgt[o]
            if lo<=t<=a and kind[o] in (JMP,JCC):
                backedges.append((a-entry, t-entry))
    if backedges: print('BACKEDGES (rel):', ['+%04X->+%04X'%x for x in backedges])
    for a in addrs:
        o=a-tva; ins=insmap.get(o)
        if ins is None: continue
        rel=a-entry
        mark=''
        if o in tgt and lo<=tgt[o]<=a and kind[o] in (JMP,JCC): mark=' <<BACK'
        print('  +%04X  %08X  %-8s %s%s'%(rel,a,ins.mnemonic,ins.op_str,mark))
