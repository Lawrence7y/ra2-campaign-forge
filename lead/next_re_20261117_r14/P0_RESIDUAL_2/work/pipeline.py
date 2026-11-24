#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FINAL PIPELINE — P0-RESIDUAL-2.
Builds ENUM.tsv, coverage_delta.tsv, and all control evidence. Read-only on gamemd.exe.
Deterministic seed 20261117. Writes only inside P0_RESIDUAL_2\\.
"""
import sys, os, struct, collections, random, re, csv, bisect, json, hashlib, datetime
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
from res2_common import *
OUT=os.path.dirname(HERE)
EVID=os.path.join(OUT,"EVIDENCE"); os.makedirs(EVID,exist_ok=True)
random.seed(20261117)

pe=PE(); sw=Sweep(pe); at=Atlas()
# ---- coverage baseline: re-read fresh at comparison time; record metadata (Lead 裁定) ----
_cov_st=os.stat(COVERAGE)
COV_META=dict(path=COVERAGE, mtime=datetime.datetime.fromtimestamp(_cov_st.st_mtime).isoformat(),
              size_bytes=_cov_st.st_size, rows_data=0, sha256=hashlib.sha256(open(COVERAGE,'rb').read()).hexdigest().upper())
cov=load_set(COVERAGE)
COV_META['rows_data']=len(cov)
TOUCHED={0x5B3740,0x6C41D0}   # concurrent M2 additions Lead confirmed present
COV_META['concurrent_M2_present']={("%08X"%a):(a in cov) for a in sorted(TOUCHED)}
gate=load_set(GATE,0,True,lambda p:p[8]=="FUNC")
resid=load_set(RESID,0,True,lambda p:p[2]=="FUNC")
positives=gate|resid
print("SHA",sha256_file()==SHA256,"| .text",hex(pe.tlo),hex(pe.thi),"| cov",len(cov),"gate",len(gate),"resid",len(resid))
print("COV_META",COV_META)

# ---------- helpers ----------
def first_insn(a):
    d=pe.try_read(a,16)
    ii=next(md32(True).disasm(d,a),None)
    return (ii.mnemonic+' '+ii.op_str) if ii else '.byte'

def prologue_leaf(a):
    """task criterion 4 (operational form filter c4a|leaf) + literal leaf-shape."""
    b=pe.try_read(a,8); b3=pe.try_read(a,3)
    form = form_c4a(b) or leafpat(b3)              # audit operational form filter
    c4a  = form_c4a(b)
    leaf = leafpat(b3)
    return form,c4a,leaf

def leaf_shape(a):
    """literal task leaf shape: body>=2B and terminates ret/jmp within 0x400."""
    d=pe.try_read(a,0x400)
    if not d or len(d)<2: return False
    for ins in md32(True).disasm(d,a):
        if ins.id:
            if ins.mnemonic in ("ret","retn","retf","jmp"):
                return (ins.address+ins.size-a)>=2
    return False

def tail_of(a,maxb=0x200):
    """disassemble a to first terminator; return (end_kind,length)."""
    d=pe.try_read(a,maxb)
    if not d: return ('none',0)
    for ins in md32(True).disasm(d,a):
        if ins.id and ins.mnemonic in ("ret","retn","retf","jmp"):
            return (ins.mnemonic, ins.address+ins.size-a)
    return ('none',0)

# intervals for "inside known function body"
intervals=[(e,e+sz) for e,sz in at.rows if sz>0]
def pl(ev):
    m=re.search(r'body_len=(\d+)',ev) or re.search(r'body=(\d+)\(',ev)
    return int(m.group(1)) if m else None
for path,col in ((GATE,11),(RESID,4)):
    with open(path,encoding="utf-8",errors="replace") as f:
        r=csv.reader(f,delimiter="\t"); next(r)
        for p in r:
            if len(p)>col:
                ln=pl(p[col])
                if ln and ln>0: intervals.append((int(p[0],16),int(p[0],16)+ln))
intervals.sort(); mg=[]
for a,b in intervals:
    if mg and a<=mg[-1][1]: mg[-1][1]=max(mg[-1][1],b)
    else: mg.append([a,b])
ISTART=[x[0] for x in mg]
def inbody(a):
    i=bisect.bisect_right(ISTART,a)-1
    return i>=0 and mg[i][0]<a<mg[i][1]

# reference maps (Channel G/H)
ptr=collections.Counter(); ptrsrc={}
for sn in (".rdata",".data",".detour"):
    if sn not in pe.secs: continue
    s=pe.secs[sn]; buf=pe.data[s["raw"]:s["raw"]+s["rawsize"]]
    n=len(buf)//4; ws=struct.unpack_from("<%dI"%n,buf,0)
    for i,w in enumerate(ws):
        if pe.tlo<=w<pe.thi:
            ptr[w]+=1; ptrsrc.setdefault(w,[]).append("%s+%X"%(sn,4*i))
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, sweep_calls
bn=Bin(); calls,jmps,st=sweep_calls(bn)
callcnt=collections.Counter({t:len(v) for t,v in calls.items()})
jmpcnt=collections.Counter({t:len(v) for t,v in jmps.items()})

# ---------- qualified pool / ENUM universe ----------
pool=[]
grid=list(range((pe.tlo+15)//16*16,pe.thi,16))
for va in grid:
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins=sw.insn_at(pe,va)
    if ins is None or ins.mnemonic in JCC or ins.id==0: continue
    pool.append(va)
poolset=set(pool)
enum_universe=sorted(poolset-cov)
print("grid=%d pool=%d ENUM universe(pool\\cov)=%d"%(len(grid),len(pool),len(enum_universe)))

# ---------- Channel candidate sets (for recall) ----------
def chF(a):  # strict four-criteria
    b3=pe.try_read(a,3)
    return (a%16==0) and b3 and b3[0] not in E8E9EB and (sw.endmap.get(a) in TERM) and prologue_leaf(a)[0]
def chF_broad(a):
    b=pe.try_read(a,8); b3=pe.try_read(a,3)
    if not b3 or b3[0] in E8E9EB or (sw.endmap.get(a) not in TERM) or a%16: return False
    lb=leafpat(b3) or (len(b)>=4 and b[0]==0x8B and (b[1]&0xF0)==0x50 and b[2]==0x24)
    return form_c4a(b) or lb
def chG(a): return ptr.get(a,0)>0 or callcnt.get(a,0)>0 or jmpcnt.get(a,0)>0
def chH(a): return callcnt.get(a,0)>0 or jmpcnt.get(a,0)>0  # metadata/ref (subset present in this PE)

# ---------- T3.2 POSITIVE RECALL ----------
recall_rows=[]
for name,S in (("gate476",gate),("resid1096",resid),("combined",positives)):
    nF=sum(1 for a in S if chF(a)); nFb=sum(1 for a in S if chF_broad(a))
    nG=sum(1 for a in S if chG(a)); nU=sum(1 for a in S if chF(a) or chG(a))
    nUb=sum(1 for a in S if chF_broad(a) or chG(a))
    recall_rows.append((name,len(S),nF,nFb,nG,nU,nUb))
    print("RECALL %-9s n=%d F=%d(%.1f%%) Fb=%d(%.1f%%) G=%d(%.1f%%) F|G=%d(%.1f%%) Fb|G=%d(%.1f%%)"%(
        name,len(S),nF,100*nF/len(S),nFb,100*nFb/len(S),nG,100*nG/len(S),
        nU,100*nU/len(S),nUb,100*nUb/len(S)))

# ---------- T3.1 BASELINE ----------
base16=random.sample(grid,min(5000,len(grid)))
interior=[va for e,sz in at.rows for va in range((e+16+15)//16*16,e+sz,16) if va<pe.thi]
baseint=random.sample(interior,min(5000,len(interior)))
c3pos=[pe.tlo+i for i in range(0,pe.thi-pe.tlo) if pe.byte(pe.tlo+i)==0xC3]
basec3=random.sample(c3pos,min(5000,len(c3pos)))
def baserate(S):
    c=collections.Counter()
    for a in S:
        c['F']+=chF(a); c['Fb']+=chF_broad(a); c['form']+=prologue_leaf(a)[0]
        c['predterm']+= (sw.endmap.get(a) in TERM)
        c['leafshape']+=leaf_shape(a)
        c['a16']+= (a%16==0)
    return c,len(S)
base_rows=[]
for nm,S in (("random16B",base16),("atlas_interior",baseint),("randomC3",basec3)):
    c,n=baserate(S)
    base_rows.append((nm,n,c))
    print("BASE %-14s n=%d a16=%d(%.1f%%) predterm=%d(%.1f%%) form=%d(%.1f%%) F=%d(%.1f%%) Fb=%d(%.1f%%) leafshape=%d(%.1f%%)"%(
        nm,n,c['a16'],100*c['a16']/n,c['predterm'],100*c['predterm']/n,c['form'],100*c['form']/n,
        c['F'],100*c['F']/n,c['Fb'],100*c['Fb']/n,c['leafshape'],100*c['leafshape']/n))

# ---------- T3.3 NEGATIVE ----------
neg=[0x4824D4]
with open(os.path.join(R14,"P0_GATE","EVIDENCE","B_RAIL_C5_EXCLUDED.tsv"),encoding="utf-8") as f:
    rdr=csv.reader(f,delimiter="\t"); next(rdr)
    for p in rdr:
        if p and p[0]: neg.append(int(p[0],16))
neg_rows=[]
for a in neg:
    neg_rows.append((a,a%16==0,pe.byte(a),(sw.endmap.get(a) or '?'),chF(a),chF_broad(a),prologue_leaf(a)[0],first_insn(a)))
    print("NEG %08X a16=%s first=%s pred=%s F=%s Fb=%s form=%s [%s]"%(
        (a,a%16==0,hex(pe.byte(a)) if pe.byte(a) is not None else '?',sw.endmap.get(a),chF(a),chF_broad(a),prologue_leaf(a)[0],first_insn(a))))
nfp=sum(1 for r in neg_rows if r[4] or r[5])
print("NEG false positives (F or Fb) = %d/%d"%(nfp,len(neg_rows)))

# ---------- T2 ADJUDICATION ----------
def classify(a):
    form,c4a,leaf=prologue_leaf(a)
    a16=(a%16==0); fb=(pe.byte(a) not in E8E9EB); pt=(sw.endmap.get(a) in TERM)
    ib=inbody(a)
    if chF(a) and not ib:
        verdict="FUNC"; grade="[静态推断]"
        why="4crit_pass(c4a|leaf);not_in_known_body"
    elif ib:
        verdict="NOT_FUNC"; grade="[静态推断]"
        why="inside_known_function_body(mid-function-label)"
    else:
        verdict="UNDECIDABLE"; grade="[未证]"
        reason=[]
        if not form: reason.append("fails_form_filter(c4a|leaf)")
        if not fb: reason.append("first_byte_E8_E9_EB")
        if not pt: reason.append("predecessor_not_TERM")
        if not a16: reason.append("not_align16")
        if not reason: reason.append("structural_signals_non_discriminative_in_pool")
        why=";".join(reason)
    return verdict,grade,why,a16,fb,pt,form,c4a,leaf,ib

enum_rows=[]; vcount=collections.Counter()
for a in enum_universe:
    verdict,grade,why,a16,fb,pt,form,c4a,leaf,ib=classify(a)
    vcount[verdict]+=1
    pred=sw.endmap.get(a) or '?'
    fbyte=pe.byte(a)
    channels=[]
    if chF(a): channels.append('F')
    if ptr.get(a,0)>0: channels.append('G')
    if callcnt.get(a,0)>0 or jmpcnt.get(a,0)>0: channels.append('H')
    if not channels: channels=['F-grid']
    fpu = pe.byte(a) in (0xDD,0xDB)
    if fpu: channels.append('FPU-leaf')
    ev="align=%d;first=%s;pred=%s;form(c4a|leaf)=%d(c4a=%d,leaf=%d);inbody=%d;ptr=%d;call=%d;jmp=%d;fpu=%d;tail=%s;%s"%(
        a16, hex(fbyte) if fbyte is not None else '?', pred, form,c4a,leaf, ib,
        ptr.get(a,0),callcnt.get(a,0),jmpcnt.get(a,0), 1 if fpu else 0, tail_of(a)[0],why)
    if fpu:
        ev += ";NOTE=real_FPU_leaf_body_ends_ret_but_fails_form_filter_form_filter_recall_gap"
    enum_rows.append((a,'|'.join(channels),verdict,a16,
                      hex(fbyte) if fbyte is not None else '?',pred,
                      form or leaf_shape(a),first_insn(a),why,ev))
print("VERDICT counts:",dict(vcount))

# write ENUM.tsv
with open(os.path.join(OUT,"ENUM.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["address","channel","verdict","align16","first_byte","predecessor",
                "prologue_or_leaf","first_insn","undecidable_reason","evidence"])
    for a,ch,v,a16,fb,pred,pl,fi,why,ev in enum_rows:
        w.writerow(["%08X"%a,ch,v,"Y" if a16 else "N",fb,pred,"Y" if pl else "N",fi,why if v=="UNDECIDABLE" else "",ev])

# write coverage_delta.tsv (FUNC & not in coverage)
subs={}
with open(os.path.join(OUT,"coverage_delta.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["entry(hex8)","subsystem(Sxx)","name","one_line_semantics","grade","evidence_path"])
    funcs=[r for r in enum_rows if r[2]=="FUNC"]
    for a,ch,v,a16,fb,pred,pl,fi,why,ev in funcs:
        w.writerow(["%08X"%a,"S22","sub_%08X"%a,"[未证] %s"%fi,"[未证]",
                    "EVIDENCE/ENUM.tsv#%08X"%a])

# write control evidence TSVs
with open(os.path.join(EVID,"recall.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["sample","n","chF_pass","chF_recall_pct","chFbroad_pass","chFbroad_recall_pct",
                "chG_pass","chG_recall_pct","union_F_G","union_F_G_pct","union_Fbroad_G","union_Fbroad_G_pct"])
    for name,n,nF,nFb,nG,nU,nUb in recall_rows:
        w.writerow([name,n,nF,round(100*nF/n,2),nFb,round(100*nFb/n,2),nG,round(100*nG/n,2),
                    nU,round(100*nU/n,2),nUb,round(100*nUb/n,2)])
with open(os.path.join(EVID,"baseline.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["baseline","n","align16","align16_pct","pred_TERM","pred_pct","form","form_pct",
                "chF","chF_pct","chFbroad","chFbroad_pct","leaf_shape","leafshape_pct"])
    for nm,n,c in base_rows:
        w.writerow([nm,n,c['a16'],round(100*c['a16']/n,2),c['predterm'],round(100*c['predterm']/n,2),
                    c['form'],round(100*c['form']/n,2),c['F'],round(100*c['F']/n,2),
                    c['Fb'],round(100*c['Fb']/n,2),c['leafshape'],round(100*c['leafshape']/n,2)])
with open(os.path.join(EVID,"negative.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["address","align16","first_byte","predecessor","chF","chFbroad","form","first_insn"])
    for r in neg_rows: w.writerow(["%08X"%r[0],"Y" if r[1] else "N",hex(r[2]) if r[2] is not None else '?',r[3],int(r[4]),int(r[5]),int(r[6]),r[7]])

# ---- oracle & cross-checks ----
oracle=0x7775C0
oracle_row=dict(address="%08X"%oracle, in_cov=oracle in cov, chF=chF(oracle),
                dataptr=ptr.get(oracle,0), first=hex(pe.byte(oracle)), pred=sw.endmap.get(oracle))
# cross-check: the 2 concurrent M2 additions must NOT appear as new candidates
crosscheck={("%08X"%a): dict(in_cov=a in cov, in_enum_universe=(a in poolset),
                             reported_as_new=(a in [r[0] for r in enum_rows]))
            for a in sorted(TOUCHED)}
print("ORACLE 0x7775C0:",oracle_row)
print("CROSSCHECK 2 M2 additions:",crosscheck)
# write oracle/crosscheck evidence
with open(os.path.join(EVID,"oracle_and_crosscheck.tsv"),"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["kind","address","detail"])
    w.writerow(["oracle_7775C0","007775C0",str(oracle_row)])
    for a,d in crosscheck.items(): w.writerow(["concurrent_M2_crosscheck",a,str(d)])

stats=dict(grid=len(grid),pool=len(pool),enum_universe=len(enum_universe),
           vcount=dict(vcount),nfp=nfp,nneg=len(neg_rows),
           recall=[[n,NN,a,b,c,d,e] for (n,NN,a,b,c,d,e) in recall_rows],
           baseline=[[nm,n,dict(c)] for nm,n,c in base_rows],
           text=[hex(pe.tlo),hex(pe.thi)], cov=len(cov),gate=len(gate),resid=len(resid),
           cov_meta=COV_META, oracle=oracle_row, crosscheck=crosscheck)
json.dump(stats,open(os.path.join(EVID,"stats.json"),"w"),indent=1,default=str)
# final re-read of coverage to confirm stability (Lead 裁定 point 3)
final_rows=len(load_set(COVERAGE)); final_st=os.stat(COVERAGE)
STABLE=(final_rows==COV_META['rows_data'] and final_st.st_size==COV_META['size_bytes'] and abs(final_st.st_mtime-_cov_st.st_mtime)<1e-6)
print("FINAL coverage stability check: rows=%d size=%d STABLE=%s"%(final_rows,final_st.st_size,STABLE))
stats['final_cov_stable']=STABLE
json.dump(stats,open(os.path.join(EVID,"stats.json"),"w"),indent=1,default=str)
print("\nWROTE ENUM.tsv (%d), coverage_delta.tsv (%d FUNC), EVIDENCE/*"%(len(enum_rows),len(funcs)))
