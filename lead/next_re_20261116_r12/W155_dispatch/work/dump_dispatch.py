#!/usr/bin/env python3
# W155: full dump + structured parse of the dispatch ladder at 0x55B8F0.
# Also byte-channel caller search (direct E8 rel32 and FF /2 indirect tables).
import os, csv, re, bisect, collections, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r'D:\Project\ra2-campaign-forge'
CARD = os.path.join(ROOT, r'lead\next_re_20261116_r12\W155_dispatch')
EVID = os.path.join(CARD, 'EVIDENCE')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ARRAYS = os.path.join(ROOT, r'lead\next_re_20261112_r10\W132_arrays\instance_arrays.tsv')
EDGES = os.path.join(ROOT, r'lead\next_re_20261112_r10\W131_subsystems\calledges.raw.log')

pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
TEXT_VA=IB+sec.VirtualAddress; RAW=open(EXE,'rb').read()
def off(va): return pe.get_offset_from_rva(va-IB)
def rd(va,n): return RAW[off(va):off(va)+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True

# array maps
by_count={}; by_items={}
with open(ARRAYS,encoding='utf-8',errors='replace') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        try:
            c=int(row['count'],16); it=int(row['items'],16)
            by_count[c]=(row['element'],int(row['base'],16),it)
            by_items[it]=(row['element'],int(row['base'],16),c)
        except Exception: pass

START=0x55B8F0
# disassemble until ret (c2 08 00 / c3)
ins=[]
for x in md.disasm(rd(START,0x300),START):
    ins.append(x)
    if x.mnemonic=='ret': break
END=ins[-1].address+ins[-1].size
with open(os.path.join(EVID,'dispatch_full_disasm.txt'),'w',encoding='utf-8') as out:
    out.write('function entry 0x%08X (atlas hole) end 0x%08X length=%d bytes n_insn=%d\n' % (START,END,END-START,len(ins)))
    for x in ins:
        out.write('0x%08X  %-20s %-8s %s\n' % (x.address,x.bytes.hex(),x.mnemonic,x.op_str))

# parse blocks: start at 'mov eax,[count]'; end before next such / ret
starts=[i for i,x in enumerate(ins) if x.mnemonic=='mov' and re.fullmatch(r'eax, dword ptr \[0x([0-9a-f]+)\]',x.op_str)]
call5c=[i for i,x in enumerate(ins) if x.mnemonic=='call' and re.search(r'\[edx \+ 0x5c\]',x.op_str)]
rows=[]
for j,si in enumerate(starts):
    ei=starts[j+1] if j+1<len(starts) else len(ins)
    m=re.fullmatch(r'eax, dword ptr \[0x([0-9a-f]+)\]',ins[si].op_str)
    cnt=int(m.group(1),16)
    # find items load within block
    itemva=None; gateva=None; callva=None; nback=None
    for k in range(si,ei):
        o=ins[k].op_str
        mi=re.fullmatch(r'ecx, dword ptr \[0x([0-9a-f]+)\]',o)
        if mi and itemva is None: itemva=int(mi.group(1),16)
        if '[ecx + 0x98]' in o and gateva is None: gateva=ins[k].address
        if ins[k].mnemonic=='call' and callva is None: callva=ins[k].address
        if ins[k].mnemonic=='jns' and nback is None: nback=ins[k].address
    arr=by_count.get(cnt)
    rows.append(dict(start=ins[si].address,end=ins[ei-1].address,cnt=cnt,items=itemva,
                     elem=arr[0] if arr else 'UNKNOWN',base=arr[1] if arr else -1,
                     gate=gateva,call=callva,nback=nback,
                     block_len=(ins[ei-1].address+ins[ei-1].size)-ins[si].address,
                     snapshot=('mov eax,[Count]' in ' '.join(x.mnemonic+' '+x.op_str for x in ins[si:si+1]))))

with open(os.path.join(EVID,'dispatch_blocks.tsv'),'w',encoding='utf-8') as out:
    out.write('block\tstart\tend\tlen\tcount_addr\titems_addr\tarray_element\tbase\tgate_+0x98\tcall5c_va\tbackedge_jns\tupper_bound_source\n')
    for i,r in enumerate(rows,1):
        out.write('%d\t0x%08X\t0x%08X\t%d\t0x%08X\t0x%08X\t%s\t0x%08X\t0x%08X\t0x%08X\t0x%08X\t%s\n' % (
            i,r['start'],r['end'],r['block_len'],r['cnt'],r['items'],r['elem'],r['base'],r['gate'],r['call'],r['nback'],
            'snapshot: mov eax,[Count] once per block'))

# ---- byte-channel CALLER search: E8 rel32 targets to any address in [START,END) ----
# rebuild instruction map from atlas for boundary filtering
funcs=[]
with open(os.path.join(CARD,'work','maps.pkl'),'rb') as f:
    import pickle; M=pickle.load(f)
func_insns=M['func_insns']
insn_start=set(a for lst in func_insns.values() for a,*_ in lst)
callers_to=collections.defaultdict(list)
for e,lst in func_insns.items():
    for va,sz,mnem,op,h in lst:
        if mnem=='call' and op.startswith('0x'):
            t=int(op,16)
            if START<=t<END:
                callers_to[t].append((va,e))
with open(os.path.join(EVID,'callers_bytescan.txt'),'w',encoding='utf-8') as out:
    out.write('Direct E8 rel32 calls into [0x55B8F0,0x%08X) found in atlas-mapped instructions:\n'%END)
    for t,v in sorted(callers_to.items()):
        out.write('target 0x%08X: %s\n' % (t,', '.join('0x%08X(from func 0x%08X)'%x for x in v)))
    out.write('\nAll direct E8 rel32 calls to 0x55B8F0 exactly: %s\n' % (callers_to.get(START,[])))

# ---- Ghidra call-edge log channel ----
with open(os.path.join(EVID,'callers_ghidra_log.txt'),'w',encoding='utf-8') as out:
    hits=[]
    with open(EDGES,encoding='utf-8',errors='replace') as f:
        for ln in f:
            if 'CallEdges.java> ' not in ln: continue
            q=ln.split('CallEdges.java> ',1)[1].strip().split()
            if len(q)<3: continue
            try: c,a,s=(int(x,16) for x in q[:3])
            except Exception: continue
            if (START<=a<END) or (START<=c<END) or (START<=s<END):
                hits.append((c,a,s))
    out.write('calledge rows touching [0x%08X,0x%08X): %d\n' % (START,END,len(hits)))
    for c,a,s in hits: out.write('0x%08X -> 0x%08X @0x%08X\n'%(c,a,s))

print('blocks=%d call5c=%d end=0x%X' % (len(rows),len(call5c),END))
