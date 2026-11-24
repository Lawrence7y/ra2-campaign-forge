import os, struct, json
import pefile
from capstone import *
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT = r'D:\Project\ra2-campaign-forge\_ghidra\S08-KPROVED2\EVIDENCE'
SYM = r'D:\Project\ra2-campaign-forge\re_atlas\evidence\rtti\symbols.json'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'

pe = pefile.PE(EXE)
base = pe.OPTIONAL_HEADER.ImageBase
text = next(s for s in pe.sections if s.Name.rstrip(b'\x00').decode()=='.text')
TEXT_VA = base + text.VirtualAddress
TEXT_SIZE = text.Misc_VirtualSize
TEXT_RAW = text.PointerToRawData
buf = open(EXE,'rb').read()

def off(va):
    rva = va - base
    for s in pe.sections:
        va0 = base + s.VirtualAddress
        size = max(s.Misc_VirtualSize, s.SizeOfRawData)
        if va0 <= va < va0 + size:
            delta = va - va0
            if delta < s.SizeOfRawData:
                return s.PointerToRawData + delta
    return None

def read(va,n):
    o=off(va)
    if o is None: return b''
    return buf[o:o+n]

def u32(va):
    b=read(va,4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None

def cstr(va,limit=128):
    o=off(va)
    if o is None: return ''
    b=buf[o:o+limit]
    z=b.find(b'\x00')
    if z>=0: b=b[:z]
    return b.decode('latin1','replace')

def w8(va): return f'{va:08X}'

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# coverage names
names={}
for line in open(COV,encoding='utf-8').read().splitlines()[1:]:
    f=line.split('\t')
    if len(f)>=5 and f[1]=='S08': names[f[0]]=f[2]

sym=json.load(open(SYM,encoding='utf-8'))
addrs=['0040D250','0045A070','0045A0A0','0045A0C0','0045A640','0045A680','0045A730','0045AB00','0045AB50','0045AC00','0045AC30','0045AC70','0045AC90','004D24A0','004D2510','004D27B0','004D27D0','004D2810','004D2910']
addrs_i=[int(a,16) for a in addrs]
rows=[]
for a in addrs_i:
    hits=[]
    for cname,c in sym['classes'].items():
        for i,v in enumerate(c.get('vfuncs',[])):
            if int(v,16)==a:
                hits.append((cname,i,c))
    if not hits:
        rows.append(dict(entry=w8(a),name=names.get(w8(a),''),rtti='NONE')); continue
    cname,slot,c=hits[0]
    vt=int(c['vtable_va'],16); col=int(c['col_va'],16); td=int(c['type_descriptor_va'],16)
    chain = (u32(vt-4)==col and u32(col+0xC)==td)
    slotval = u32(vt+4*slot)
    tname=cstr(td+8)
    rows.append(dict(entry=w8(a),name=names.get(w8(a),''),cls=cname,slot=slot,vt=w8(vt),col=w8(col),td=w8(td),chain_ok=bool(chain and slotval==a),rtti_name=tname,slot_val=w8(slotval) if slotval is not None else '',all_hits=len(hits)))
with open(os.path.join(OUT,'S08_RTTI.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tname\tcls\tslot\tvt\tcol\ttd\tchain_ok\trtti_name\tslot_val\tall_hits\n')
    for r in rows:
        f.write('\t'.join(str(r.get(k,'')) for k in ['entry','name','cls','slot','vt','col','td','chain_ok','rtti_name','slot_val','all_hits'])+'\n')

# disassemble each candidate up to max bytes; print all non-int3 until function end heuristic
for r in rows:
    a=int(r['entry'],16)
    code=read(a,0x600)
    ins=list(md.disasm(code,a,0x600))
    out=[]
    seen_ret=False
    for k,i in enumerate(ins):
        if i.mnemonic=='int3' and seen_ret and k>3:
            # stop after padding begins
            break
        out.append(f'{i.address:08X}  {i.bytes.hex():<20}  {i.mnemonic:<8} {i.op_str}')
        if i.mnemonic.startswith('ret'):
            seen_ret=True
    with open(os.path.join(OUT,f'DISASM_{r["entry"]}.txt'),'w',encoding='utf-8') as f:
        f.write('# '+r['entry']+' '+r.get('name','')+'\n')
        f.write('\n'.join(out)+'\n')

# full .text linear instruction scan for direct calls, vtable immediate writes, and context
code=read(TEXT_VA,TEXT_SIZE)
insns=list(md.disasm(code,TEXT_VA,TEXT_SIZE))
starts={i.address:i for i in insns}
targets=set(addrs_i)
call_sites={a:[] for a in addrs_i}
vt_set={int(r['vt'],16) for r in rows if r.get('vt')}
vt_writes={v:[] for v in vt_set}
for i in insns:
    if i.mnemonic=='call' and i.op_str.startswith('0x'):
        try: t=int(i.op_str,16)
        except: t=None
        if t in targets:
            call_sites[t].append(i)
    for op in i.operands:
        if op.type==X86_OP_IMM and op.imm in vt_set and i.mnemonic.startswith('mov') and i.operands[0].type==X86_OP_MEM:
            vt_writes[op.imm].append(i)
with open(os.path.join(OUT,'DIRECT_CALLS.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tsite\tsite_in_text\tinsn\n')
    for a in addrs_i:
        if not call_sites[a]: f.write(w8(a)+'\t\t\t\n')
        for i in call_sites[a]: f.write(f'{w8(a)}\t{i.address:08X}\t1\t{i.mnemonic} {i.op_str}\n')
with open(os.path.join(OUT,'VTABLE_IMM_WRITES.tsv'),'w',encoding='utf-8') as f:
    f.write('vt\tsite\tinsn\n')
    for v in sorted(vt_set):
        for i in vt_writes[v]: f.write(f'{v:08X}\t{i.address:08X}\t{i.mnemonic} {i.op_str}\n')

# contexts around vtable immediate writes
with open(os.path.join(OUT,'VTABLE_IMM_WRITE_CONTEXT.txt'),'w',encoding='utf-8') as f:
    for v in sorted(vt_set):
        f.write(f'\n===== VT {v:08X} =====\n')
        for i in vt_writes[v]:
            f.write(f'--- site {i.address:08X}: {i.mnemonic} {i.op_str}\n')
            idx=next((k for k,x in enumerate(insns) if x.address==i.address),None)
            if idx is None: continue
            for j in range(max(0,idx-20),min(len(insns),idx+20)):
                x=insns[j]
                mark='>>' if j==idx else '  '
                f.write(f'{mark} {x.address:08X}  {x.bytes.hex():<16}  {x.mnemonic:<8} {x.op_str}\n')

# selfcheck
print('base',hex(base),'text',hex(TEXT_VA),hex(TEXT_VA+TEXT_SIZE),'insns',len(insns))
print('rtti_ok',sum(1 for r in rows if r.get('chain_ok')),'of',len(rows))
print('call_rows',sum(1 for a in addrs_i if call_sites[a]))
for a in addrs_i:
    if call_sites[a]: print('CALL',w8(a),[hex(i.address) for i in call_sites[a]])
print('vt_write_total',sum(len(v) for v in vt_writes.values()))
for v,n in vt_writes.items(): print('VTWRITE',f'{v:08X}',len(n),[f'{i.address:08X}' for i in n[:20]])
