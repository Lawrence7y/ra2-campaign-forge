import sys, os, struct, json
from collections import Counter
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "P0_INITTERM")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE,"rb").read()
secs = {}
for s in pe.sections:
    name = s.Name.decode(errors="replace").rstrip("\x00")
    secs[name] = (IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
def rd(va,n):
    rva=va-IB
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            off=s.PointerToRawData+(rva-s.VirtualAddress); return data[off:off+n]
    return b""
RDATA_S,RDATA_E=secs[".rdata"][0],secs[".rdata"][0]+secs[".rdata"][1]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
rows=[]
with open(os.path.join(CARD,"INITTERM_TABLE.tsv"),encoding="utf-8") as f:
    hdr=f.readline().rstrip("\n").split("\t")
    for line in f: rows.append(dict(zip(hdr,line.rstrip("\n").split("\t"))))
tgt_list=[int(r["target"],16) for r in rows]
bucket={}; feat={}; body_len={}
for k,r in enumerate(rows):
    va=tgt_list[k]
    nxt=tgt_list[k+1] if k+1<len(tgt_list) else va+0x400
    span=min(nxt-va, 4096)
    buf=rd(va,span)
    ins=list(md.disasm(buf,va))
    vptrs=[]; calls=[]
    for i in range(len(buf)-5):
        b=buf[i]
        if b==0xC7 and (buf[i+1]&0xC7)==0x05:
            imm=struct.unpack_from("<I",buf,i+2)[0]
            if RDATA_S<=imm<RDATA_E: vptrs.append(imm)
        if b==0xE8:
            rel=struct.unpack_from("<i",buf,i+1)[0]
            calls.append((va+i+5+rel)&0xFFFFFFFF)
    mnems=[x.mnemonic for x in ins if not x.mnemonic.startswith(".")]
    x87=[m for m in mnems if (m.startswith("f") and m not in ("fnstsw","fnclex","fninit","fldcw","fnstcw","fnop","fwait"))]
    has_store=any(x.mnemonic=="mov" and ("[" in x.op_str) and not ("[esp" in x.op_str or "[ebp" in x.op_str) for x in ins)
    if vptrs: bk="A_VPTR_WRITE"
    elif calls: bk="B_CALL_THUNK"
    elif x87: bk="C_FP_INIT"
    elif has_store: bk="D_PLAIN_STORE"
    else: bk="E_OTHER"
    bucket[va]=bk; body_len[va]=span
    feat[va]=";".join(["vptr:%08X"%v for v in vptrs[:2]]+["call:%08X"%c for c in calls[:2]]+x87[:2])
cnt=Counter(bucket.values())
cov_cnt=Counter(bucket[int(r["target"],16)] for r in rows if r["in_coverage"]=="Y")
print("BUCKETS:",dict(cnt))
print("IN_COVERAGE_BY_BUCKET:",dict(cov_cnt))
with open(os.path.join(CARD,"EVIDENCE","t3_buckets_refined.tsv"),"w",encoding="utf-8",newline="") as f:
    f.write("index\ttarget\tbucket\tin_coverage\tfeatures\n")
    for r in rows:
        va=int(r["target"],16)
        f.write("\t".join([r["index"],r["target"],bucket[va],r["in_coverage"],feat[va]])+"\n")
lines=[]
for bk in sorted(cnt):
    reps=[r for r in rows if bucket[int(r["target"],16)]==bk][:3]
    lines.append("=== BUCKET %s count=%d in_coverage=%d ==="%(bk,cnt[bk],cov_cnt[bk]))
    for r in reps:
        va=int(r["target"],16)
        lines.append("  target=%s index=%s span=%d feat=%s"%(r["target"],r["index"],body_len[va],feat[va]))
        n=0
        for x in md.disasm(rd(va,min(body_len[va],80)),va):
            lines.append("    %08X  %-20s %s %s"%(x.address,x.bytes.hex(),x.mnemonic,x.op_str))
            n+=1
            if n>=18: break
        lines.append("")
open(os.path.join(CARD,"EVIDENCE","t3_bucket_disasm.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
json.dump({"bucket_counts":dict(cnt),"in_cov_by_bucket":dict(cov_cnt)},
          open(os.path.join(CARD,"EVIDENCE","t3_stats.json"),"w",encoding="utf-8"),indent=2)
print("DONE")
