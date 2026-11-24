"""
S10-K2 T4: increment - find the other side of 3 single-side MissionClass fields
(+0xB8 6W/0R, +0xCC 2W/0R, +0x6C 0W/1R). Scan MissionClass's OWN methods in
0x5B2D00..0x5B3B40. Track this-register (ecx/esi/edi/ebx), distinguish byte/dword,
exclude call/jmp [reg+disp] virtual slot calls (report excluded count explicitly).
capstone skipdata=True. No cross-class offset reuse.
"""
import os, json, csv
from pehelp import IMAGE_BASE, rd, u32, sections, section_of, is_code, disasm
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX, X86_REG_ESI, X86_REG_EDI, X86_REG_EBX, X86_REG_EAX, X86_REG_EDX, X86_REG_EBP, X86_REG_ESP

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID=os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    s=str(s); L.append(s)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode('ascii'))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# function boundaries from atlas for interval containment (boundary source only)
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
funcs=[]
with open(ATL) as f:
    for r in csv.DictReader(f,delimiter='\t'):
        e=int(r['entry'],16); sz=int(r['size'])
        if 0x5B2D00<=e<0x5B3C00: funcs.append((e,e+sz))
funcs.sort()
P('===== functions in 0x5B2D00..0x5B3C00 (atlas boundary source) =====')
for a,b in funcs: P('  %08X..%08X (%d B)'%(a,b,b-a))

# fields of interest with expected widths
FIELDS={0xB8:'byte',0xCC:'dword',0x6C:'dword'}
# this-register tracking: a reg is 'this' if set by mov reg,ecx early, or mov reg,edi where edi=this
# We'll do a simple linear dataflow within each function: seed this-regs from 'mov X,ecx' (function entry)
def scan_func(lo,hi):
    ins=list(md.disasm(rd(lo,hi-lo),lo))
    # determine this regs: any 'mov r, ecx' -> r is this-alias
    thisregs=set()
    for x in ins:
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==X86_OP_REG and x.operands[1].type==X86_OP_REG:
            if x.operands[1].reg==X86_REG_ECX: thisregs.add(x.operands[0].reg)
    # seed ecx itself as this at entry
    accesses=[]; vcalls=0
    for x in ins:
        # virtual calls: call/jmp [reg+disp] -> exclude, count
        if x.mnemonic in ('call','jmp') and x.operands and x.operands[0].type==X86_OP_MEM:
            vcalls+=1
            continue
        if not x.operands: continue
        for oi,op in enumerate(x.operands):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.disp not in FIELDS: continue
            # base reg must be a this-alias (object pointer), NOT esp/ebp stack
            breg = m.base
            if breg in (X86_REG_ESP,X86_REG_EBP): continue  # stack, skip
            if breg not in thisregs: continue
            # determine read/write: op0 (dest) of mov/add/inc/etc is write; op1 is read
            # for cmp/test -> read; for mov -> op0 write, op1 read
            width=FIELDS[m.disp]
            # size check via capstone operands size
            osz=x.operands[oi].size
            is_write=False
            if x.mnemonic in ('mov','add','sub','inc','dec','and','or','xor','movzx','movsx') and oi==0: is_write=True
            if x.mnemonic in ('mov','cmp','test','add','sub','and','or') and oi>=1: is_write=False
            accesses.append(dict(addr=x.address,bytes=x.bytes.hex(),mn=x.mnemonic,opstr=x.op_str,
                                 disp=m.disp,width=width,osz=osz,readwrite='W' if is_write else 'R',
                                 base=md.reg_name(breg),opidx=oi))
    return accesses,vcalls,thisregs

P('\n===== T4 FIELD ACCESS SCAN (3 single-side fields) =====')
allacc={0xB8:[],0xCC:[],0x6C:[]}
total_vcalls=0
for lo,hi in funcs:
    acc,vc,tr=scan_func(lo,hi)
    total_vcalls+=vc
    if acc:
        P('\n fn %08X..%08X thisregs={%s} vcalls_excluded=%d' % (lo,hi,','.join(md.reg_name(r) for r in tr),vc))
        for a in acc:
            P('   %08X %-16s %-6s %-40s disp=0x%X %s osz=%d %s base=%s' %
              (a['addr'],a['bytes'],a['mn'],a['opstr'],a['disp'],a['width'],a['osz'],a['readwrite'],a['base']))
            allacc[a['disp']].append(a)
P('\nvirtual-slot calls excluded (call/jmp [reg+disp]) across scanned functions: %d' % total_vcalls)

P('\n===== T4 OTHER-SIDE FINDINGS =====')
for disp in [0xB8,0xCC,0x6C]:
    rs=[a for a in allacc[disp] if a['readwrite']=='R']
    ws=[a for a in allacc[disp] if a['readwrite']=='W']
    P(' +0x%X (%s): reads=%d writes=%d  %s' % (disp,FIELDS[disp],len(rs),len(ws),
        'OTHER-SIDE FOUND: read point(s)' if (disp in (0xB8,0xCC) and rs) or (disp==0x6C and ws) else 'no other side in this-region scan'))

with open(os.path.join(EVID,'t4_fields.json'),'w') as f:
    json.dump({'accesses':{('%X'%d):v for d,v in allacc.items()},'vcalls_excluded':total_vcalls,
               'funcs':[['%08X'%a,'%08X'%b] for a,b in funcs]},f,indent=2)
with open(os.path.join(EVID,'t4_fields.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t4_fields.txt/.json')
