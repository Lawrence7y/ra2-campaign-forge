#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Channel discovery: F (full aligned grid), G (data pointer tables), H (structured metadata).
Writes channel candidates to EVIDENCE/channel_*.tsv with raw features; no verdict yet.
"""
import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
import pefile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from res2_common import *
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
os.makedirs(EVID, exist_ok=True)

pe = PE(); sw = Sweep(pe); at = Atlas()
cov = load_set(COVERAGE)
gate = load_set(GATE, 0, True, lambda p: p[8]=="FUNC")
resid = load_set(RESID, 0, True, lambda p: p[2]=="FUNC")
known = cov | gate | resid

# qualified pool (aligned grid + TERM pred + non-JCC)
pool=[]
for va in range((pe.tlo+15)//16*16, pe.thi, 16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
poolset=set(pool)
print("pool=%d"%len(pool))

def four_criteria(T):
    """task four criteria: align16, first!=E8/E9/EB, pred TERM, prologue|leaf.
    pred via precomputed endmap (instruction whose end==T); same as pool definition.
    """
    a16=(T%16==0)
    b=pe.try_read(T,3)
    fb=(b[0] not in E8E9EB) if b else False
    pm=sw.endmap.get(T)   # O(1), no resync
    predterm=pm in TERM
    fl=form_c4a(pe.try_read(T,8)) or leafpat(b)
    return a16,fb,predterm,fl, (a16 and fb and predterm and fl)

# -------- CHANNEL F: all 16-aligned addresses in .text --------
F_all = list(range((pe.tlo+15)//16*16, pe.thi, 16))
F_four=[]
F_det=[]
for T in F_all:
    a16,fb,pt,fl,ok=four_criteria(T)
    if ok:
        F_four.append(T)
        F_det.append((T,fb,pt,fl,at.in_atlas(T),T in cov))
print("CHANNEL F: full aligned grid = %d; pass 4-criteria = %d (in_atlas=%d in_cov=%d new=%d)"%(
    len(F_all),len(F_four),sum(1 for d in F_det if d[4]),sum(1 for d in F_det if d[5]),
    sum(1 for d in F_det if not d[5])))
with open(os.path.join(EVID,"channel_F_grid.tsv"),"w",encoding="utf-8") as f:
    f.write("addr\tfirst_ok\tpred_term\tform\tin_atlas\tin_coverage\n")
    for T,fb,pt,fl,ia,ic in F_det:
        f.write("%08X\t%d\t%d\t%d\t%d\t%d\n"%(T,fb,pt,fl,ia,ic))

# -------- CHANNEL G: data-section dwords pointing into .text --------
def scan_data_ptrs(sname):
    s=pe.secs[sname]
    buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4
    words=struct.unpack_from("<%dI"%n,buf,0)
    ptrs=[]
    for i,w in enumerate(words):
        if pe.tlo<=w<pe.thi:
            ptrs.append((s["va"]+4*i,w))
    return ptrs

G_ptrs={}
for sn in (".rdata",".data"):
    for loc,w in scan_data_ptrs(sn):
        G_ptrs.setdefault(w,[]).append((sn,loc))
_rd=sum(1 for k,v in G_ptrs.items() if any(x[0]=='.rdata' for x in v))
_dt=sum(1 for k,v in G_ptrs.items() if any(x[0]=='.data' for x in v))
print("CHANNEL G: data dwords -> text distinct targets = %d (.rdata-targets=%d .data-targets=%d)"%(
    len(G_ptrs),_rd,_dt))

# dense pointer runs (dispatch/jump tables): consecutive dwords all in text, >=3
def dense_runs(sname,minrun=3):
    s=pe.secs[sname]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; words=struct.unpack_from("<%dI"%n,buf,0)
    runs=[]; i=0
    while i<n:
        if pe.tlo<=words[i]<pe.thi:
            j=i
            while j<n and pe.tlo<=words[j]<pe.thi: j+=1
            if j-i>=minrun: runs.append((s["va"]+4*i,j-i,words[i:j]))
            i=j
        else: i+=1
    return runs
G_runs={}
for sn in (".rdata",".data"):
    for va,n,ws in dense_runs(sn):
        G_runs[(sn,va)]=(n,ws)
print("CHANNEL G: dense pointer runs (>=3) = %d covering %d slots"%(
    len(G_runs),sum(n for n,_ in G_runs.values())))

# G candidates: pointer targets that are in pool (aligned grid qualified) and new
G_cand={}
for w,refs in G_ptrs.items():
    if w in poolset:
        G_cand[w]=refs
print("  G targets in pool = %d ; new (not cov) = %d"%(
    len(G_cand),sum(1 for w in G_cand if w not in cov)))
with open(os.path.join(EVID,"channel_G_ptrs.tsv"),"w",encoding="utf-8") as f:
    f.write("addr\tnsources\tfirst_source\tsources\n")
    for w in sorted(G_ptrs):
        refs=G_ptrs[w]
        f.write("%08X\t%d\t%s\t%s\n"%(w,len(refs),"%s:%08X"%refs[0],
                ";".join("%s:%08X"%r for r in refs[:8])))

# -------- CHANNEL H: structured metadata --------
H=collections.defaultdict(list)
# H1 import thunks: IAT entries from import dir + FF25 jmp stubs
try:
    pe.pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    for desc in pe.pe.DIRECTORY_ENTRY_IMPORT:
        dll=desc.dll.decode(errors="replace")
        for imp in desc.imports:
            if imp.address: H['import_iat'].append((imp.address,dll,imp.name.decode(errors="replace") if imp.name else str(imp.ordinal)))
except Exception as e:
    print("import parse err",e)
# scan text for FF 25 abs (jmp [abs]) and FF 15 abs (call [abs]) -> IAT refs
buf=pe.data[pe.secs[".text"]["raw"]:pe.secs[".text"]["raw"]+pe.secs[".text"]["rawsize"]]
i=0
while True:
    i=buf.find(b"\xff\x25",i)
    if i<0: break
    va=pe.tlo+i
    if i+6<=len(buf):
        tgt=struct.unpack_from("<I",buf,i+2)[0]
        H['jmp_abs'].append((va,tgt))
    i+=1
# H2 inline SEH: push handler (68 imm32) shortly before push fs:[0] (64 FF 35 00 00 00 00) / mov fs:[0],esp (64 89 25..)
pat_pushfs=b"\x64\xff\x35\x00\x00\x00\x00"
pat_movfs=b"\x64\x89\x25\x00\x00\x00\x00"
for pat,nm in ((pat_pushfs,"seh_pushfs"),(pat_movfs,"seh_movfs")):
    i=0
    while True:
        i=buf.find(pat,i)
        if i<0: break
        va=pe.tlo+i
        # look back up to 12 bytes for push imm32 68 xxxxxxxx pointing to text
        for back in range(1,13):
            if i-back-5<0: break
            if buf[i-back-5]==0x68:
                h=struct.unpack_from("<I",buf,i-back-4)[0]
                if pe.tlo<=h<pe.thi:
                    H[nm].append((va,h,i-back-5))
        i+=1
# H3 detour section function pointers / jmp targets
if ".detour" in pe.secs:
    s=pe.secs[".detour"]; db=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    # dwords into text
    n=len(db)//4; ws=struct.unpack_from("<%dI"%n,db,0)
    for k,w in enumerate(ws):
        if pe.tlo<=w<pe.thi: H['detour_ptr'].append((s["va"]+4*k,w))
    # E9 rel32 at detour starts
    for k in range(0,len(db)-4):
        if db[k]==0xE9:
            va=s["va"]+k; rel=struct.unpack_from("<i",db,k+1)[0]; tgt=va+5+rel
            if pe.tlo<=tgt<pe.thi: H['detour_jmp'].append((va,tgt))
print("CHANNEL H counts:")
for k in sorted(H): print("   %-14s %d"%(k,len(H[k])))
with open(os.path.join(EVID,"channel_H_meta.tsv"),"w",encoding="utf-8") as f:
    f.write("kind\tva\tvalue\textra\n")
    for k in sorted(H):
        for rec in H[k]:
            f.write("%s\t%08X\t%08X\t%s\n"%(k,rec[0],rec[1],str(rec[2]) if len(rec)>2 else ""))

# union of new candidates from G and H that are in pool
H_targets=set()
for k in H:
    for rec in H[k]:
        v=rec[1]
        if pe.tlo<=v<pe.thi: H_targets.add(v)
print("H targets in pool new=%d"%len((H_targets&poolset)-cov))
