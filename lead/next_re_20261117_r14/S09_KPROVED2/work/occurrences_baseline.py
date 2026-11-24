import struct, csv, random, os
import pefile

BASE=r"D:\Project\ra2-campaign-forge"
EXE=os.path.join(BASE,r"ra2youli\gamemd.exe")
CLS=os.path.join(BASE,r"lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv")
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\x00').decode('latin-1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.get_data()))
def seg(va):
    for nm,sva,vs,d in secs:
        if sva<=va<sva+vs: return nm,d,va-sva
    return None,None,None
def u32(va):
    nm,d,o=seg(va)
    if d is None or o+4>len(d): return None
    return struct.unpack_from('<I',d,o)[0]
def cstr(va,ml=200):
    nm,d,o=seg(va)
    if d is None: return None
    e=d.find(b'\x00',o,min(o+ml,len(d)))
    if e<0:return None
    try:return d[o:e].decode('ascii')
    except:return d[o:e].decode('latin-1')
def valid_col(col):
    nm,_,_=seg(col)
    if nm not in ('.rdata','.data'): return None
    td=u32(col+0xC)
    if td is None: return None
    nm2,_,_=seg(td)
    if nm2 not in ('.rdata','.data'): return None
    name=cstr(td+8)
    if not name or not(name.startswith('.?AV') or name.startswith('.?AU')):return None
    return td,name

ents=['006A5840','006D0680','0063FB20','005BE6D0','004E2690','00654320','0069DEB0','00557730']
allbytes=open(EXE,'rb').read()
print("=== ALL 4-byte VA occurrences (dual-channel L1 cross-check) ===")
occ_results={}
for es in ents:
    e=int(es,16); pat=struct.pack('<I',e)
    occ=[]; start=0
    while True:
        i=allbytes.find(pat,start)
        if i<0:break
        occ.append(IB+i); start=i+1
    # classify each occurrence: is it a slot of some RTTI vtable with a valid COL?
    classified=[]
    for O in occ:
        found=[]
        for s in range(0,400):
            V=O-4*s
            col=u32(V-4)
            if col is None:continue
            r=valid_col(col)
            if r:
                td,name=r
                # confirm vtable start by checking slot s value == e (trivially true) and .text
                found.append((V,s,col,td,name))
        classified.append((O,found))
    occ_results[es]=(occ,classified)
    print("ENTRY=%s raw_occurrences=%d" % (es,len(occ)))
    for O,found in classified:
        nm,_,_=seg(O)
        if found:
            for V,s,col,td,name in found:
                print("   O=%08X sec=%s -> vt=%08X slot=%d col=%08X td=%08X name=%s"%(O,nm,V,s,col,td,name))
        else:
            print("   O=%08X sec=%s -> NO RTTI vtable (ctor/atexit/other data)"%(O,nm))

# ===== baseline =====
rows=list(csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'))
s09=[r for r in rows if r['subsystem']=='S09']
strict=set(r['entry'] for r in s09 if r['has2_rtti']=='1' and r['has4_strict']=='1')
loose=set(r['entry'] for r in s09 if r['has2_rtti']=='1' and r['has4_loose']=='1')
pop=[r['entry'] for r in s09]
print("\n=== BASELINE (seed 20261119, 2000 iters, sample 8 within S09) ===")
print("S09 population=%d A_strict=%d A_loose=%d strict_rate=%.6f loose_rate=%.6f"%(len(pop),len(strict),len(loose),len(strict)/len(pop),len(loose)/len(pop)))
rng=random.Random(20261119)
N=2000; S=8
tot_k_s=0; tot_k_l=0
for _ in range(N):
    sample=rng.sample(pop,S)
    tot_k_s+=sum(1 for e in sample if e in strict)
    tot_k_l+=sum(1 for e in sample if e in loose)
K_s=tot_k_s/N; mean_s=K_s/S
K_l=tot_k_l/N; mean_l=K_l/S
print("STRICT: total_hits=%d K(avg per trial)=%.6f mean(per row)=%.6f check K==8*mean: %.6f vs %.6f"%(tot_k_s,K_s,mean_s,K_s,S*mean_s))
print("LOOSE : total_hits=%d K(avg per trial)=%.6f mean(per row)=%.6f check K==8*mean: %.6f vs %.6f"%(tot_k_l,K_l,mean_l,K_l,S*mean_l))
print("Analytic expected K strict=%.6f loose=%.6f"%(S*len(strict)/len(pop),S*len(loose)/len(pop)))
