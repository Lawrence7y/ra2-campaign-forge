#!/usr/bin/env python3
# W155: targeted byte proof around 0x55B8F0 / 0x55B960, plus candidate dispatch ranking.
import os, csv, re, bisect, collections, pickle
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r'D:\Project\ra2-campaign-forge'
CARD = os.path.join(ROOT, r'lead\next_re_20261116_r12\W155_dispatch')
EVID = os.path.join(CARD, 'EVIDENCE')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
ARRAYS = os.path.join(ROOT, r'lead\next_re_20261112_r10\W132_arrays\instance_arrays.tsv')
EDGES = os.path.join(ROOT, r'lead\next_re_20261112_r10\W131_subsystems\calledges.raw.log')

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text')
TEXT_VA = IB + sec.VirtualAddress
RAW = open(EXE, 'rb').read()

def rva(va): return va - IB
def off(va): return pe.get_offset_from_rva(rva(va))
def rd(va, n): return RAW[off(va):off(va)+n]

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

# ---------- PART 1: raw-byte + extended linear disasm proof ----------
with open(os.path.join(EVID, 'targeted_bytes.txt'), 'w', encoding='utf-8') as out:
    out.write('=== raw bytes (direct file offset via pefile get_offset_from_rva) ===\n')
    for va in [0x55B8C3,0x55B8DD,0x55B8DE,0x55B8E1,0x55B8ED,0x55B8F0,0x55B8F5,0x55B912,0x55B960,0x4666E0]:
        b = rd(va, 24)
        out.write('0x%08X fileoff=0x%06X : %s\n' % (va, off(va), b.hex(' ')))
    out.write('\n=== literal byte searches in [0x55B000,0x55C000) ===\n')
    blob = rd(0x55B000, 0x1000)
    for name, pat in [('68 00 00 01 00', bytes.fromhex('6800000100')),
                      ('a1 b8 e9 a8 00', bytes.fromhex('a1b8e9a800')),
                      ('c2 08 00', bytes.fromhex('c20800')),
                      ('FF 5x 5C (raw)', None)]:
        if pat:
            hits=[]; st=0
            while True:
                i=blob.find(pat, st)
                if i<0: break
                hits.append(0x55B000+i); st=i+1
            out.write('%s : %d hits %s\n' % (name, len(hits), ' '.join('0x%X'%h for h in hits[:20])))
        else:
            hits=[]
            for i in range(len(blob)-2):
                if blob[i]==0xFF and 0x50<=blob[i+1]<=0x57 and blob[i+2]==0x5C:
                    hits.append(0x55B000+i)
            out.write('%s : %d hits %s\n' % (name, len(hits), ' '.join('0x%X'%h for h in hits)))
    out.write('\n=== extended linear disasm FROM known atlas entry 0x55B880, through padding ===\n')
    baseset = rd(0x55B880, 0x180)
    for ins in md.disasm(baseset, 0x55B880):
        mark = ''
        if ins.address in (0x55B8C3,0x55B8ED,0x55B8F0,0x55B912,0x55B960): mark=' <<< TARGET'
        out.write('0x%08X  %-20s %-28s ; %s%s\n' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
    out.write('\n=== linear disasm starting AT 0x55B8F0 (candidate new function) ===\n')
    for ins in md.disasm(rd(0x55B8F0, 0x120), 0x55B8F0):
        mark = ' <<< TARGET' if ins.address in (0x55B912,0x55B960) else ''
        out.write('0x%08X  %-20s %-28s ; %s%s\n' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))

# ---------- PART 2: atlas + instruction map + candidate ranking ----------
funcs=[]
with open(ATLAS, encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        try: funcs.append((int(row['entry'],16), int(row['size'],10), row))
        except Exception: pass
funcs.sort(); entries=[e for e,s,r in funcs]
func_at={e:(e,s,r) for e,s,r in funcs}
def containing(va):
    i=bisect.bisect_right(entries,va)-1
    if i<0: return None
    e,s,r=funcs[i]
    return (e,s,r) if va < e+max(s,1) else None

count_addrs={}
with open(ARRAYS, encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        try: count_addrs[int(row['count'],16)] = (row['element'], int(row['base'],16), int(row['items'],16))
        except Exception: pass

callers=collections.defaultdict(set); callees=collections.defaultdict(set); sites=collections.defaultdict(list)
with open(EDGES, encoding='utf-8', errors='replace') as f:
    for ln in f:
        if 'CallEdges.java> ' not in ln: continue
        q=ln.split('CallEdges.java> ',1)[1].strip().split()
        if len(q)<3: continue
        try: c,a,s=(int(x,16) for x in q[:3])
        except Exception: continue
        callers[a].add(c); callees[c].add(a); sites[(c,a)].append(s)

insn_at={}; func_insns=collections.defaultdict(list)
for e,s,r in funcs:
    if s<=0 or not (0 <= e-TEXT_VA < len(RAW)): continue
    code=RAW[off(e):off(e)+s]
    for ins in md.disasm(code, e):
        if ins.address in insn_at: continue
        h=ins.bytes.hex(); insn_at[ins.address]=(ins.size,ins.mnemonic,ins.op_str,h,e)
        func_insns[e].append((ins.address,ins.size,ins.mnemonic,ins.op_str,h))

# call5c sites from previous scan
with open(os.path.join(EVID,'bytescan_sites.tsv'), encoding='utf-8') as f:
    rdr=csv.DictReader(f,delimiter='\t')
    sites5c=[]
    for row in rdr:
        if row['boundary']=='1':
            sites5c.append((int(row['va'],16), int(row['func_entry'],16) if row['func_entry']!='-' else -1))

def globals_in_fn(e):
    g=set()
    for va,sz,mnem,op,h in func_insns.get(e,[]):
        for x in re.findall(r'0x([0-9a-f]{6,8})', op):
            v=int(x,16)
            if 0x800000 <= v < 0xB80000: g.add(v)
    return g

def back_edges(e):
    be=[]
    for va,sz,mnem,op,h in func_insns.get(e,[]):
        if mnem.startswith('j') or mnem=='loop':
            m=re.fullmatch(r'(0x[0-9a-f]+)', op.strip())
            if m:
                t=int(m.group(1),16)
                if t<=va: be.append((va,t))
    return be

rows=[]
for fe in sorted(set(fe for va,fe in sites5c)):
    fl=[va for va,f in sites5c if f==fe]
    g=globals_in_fn(fe); be=back_edges(fe)
    cg=sorted(a for a in g if a in count_addrs)
    rows.append(dict(entry=fe,size=func_at[fe][1],n=len(func_insns.get(fe,[])),
                     c5=len(fl),sites=fl,counts=cg,be=len(be),
                     callers=sorted(callers.get(fe,[]))))

with open(os.path.join(EVID,'candidate_rank.tsv'),'w',encoding='utf-8') as out:
    out.write('func\tsize\tn_instr\tcall5c_n\tcall5c_sites\tarray_counts_in_fn\tbackedges\tn_callers\tcallers\n')
    for r in rows:
        out.write('0x%08X\t%d\t%d\t%d\t%s\t%s\t%d\t%d\t%s\n' % (
            r['entry'],r['size'],r['n'],r['c5'],
            ','.join('0x%X'%x for x in r['sites']),
            ','.join('0x%X(%s)'%(x,count_addrs[x][0]) for x in r['counts']),
            r['be'],len(r['callers']), ','.join('0x%X'%x for x in r['callers'][:12])))

with open(os.path.join(EVID,'candidate_rank.txt'),'w',encoding='utf-8') as out:
    out.write('Functions with boundary-confirmed call [reg+0x5C], sorted by (has array Count ref, has backedges, #sites)\n')
    for r in sorted(rows,key=lambda r:(-bool(r['counts']),-r['be'],-r['c5'])):
        out.write('0x%08X size=%d n=%d call5c=%d backedges=%d counts=%s callers=%d %s\n' % (
            r['entry'],r['size'],r['n'],r['c5'],r['be'],
            ','.join('0x%X'%x for x in r['counts']),len(r['callers']),
            ','.join('0x%X'%x for x in r['callers'][:8])))

# full disasm for selected functions
SEL=[0x55AFB0,0x55D360,0x4A3660,0x5FD6A0,0x6418B0,0x641B00,0x6B9D00,0x4666E0]
with open(os.path.join(EVID,'selected_full_disasm.txt'),'w',encoding='utf-8') as out:
    for e in SEL:
        out.write('\n===== 0x%08X size=%d n=%d =====\n' % (e,func_at[e][1] if e in func_at else -1,len(func_insns.get(e,[]))))
        for x in func_insns.get(e,[]):
            tag=''
            if x[4].startswith('ff5') or (x[4].startswith('ff9') and x[4].endswith('5c000000')) or x[4]=='ff54245c': tag=' <<< CALL5C'
            out.write('0x%08X  %-20s %-26s %s%s\n' % (x[0],x[4],x[2],x[3],tag))

with open(os.path.join(CARD,'work','maps.pkl'),'wb') as f:
    pickle.dump(dict(funcs=funcs,func_at=func_at,func_insns=dict(func_insns),insn_at=insn_at,
                     callers=dict(callers),callees=dict(callees),sites=dict(sites),count_addrs=count_addrs),f)
print('done; candidates=%d' % len(rows))
