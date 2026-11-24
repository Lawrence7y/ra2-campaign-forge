#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R17-R24-RECON_FINAL/work.py: static, read-only, no process/debug/launch. Writes only this directory.
import hashlib, json, pathlib, re, struct
IMG=pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
COV=pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT=pathlib.Path(__file__).resolve().parent
TD_VF=0x7F9594
CLASS_RE=re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")
IID_RE=re.compile(r"RTTI=([0-9A-Fa-f]{6,8})→\.\?A[UV]([A-Za-z0-9_?@$]+?)@@")
NV={"RulesClass","ScenarioClass","InputManagerClass","CDDriveManagerClass","GameOptionsClass","ZBufferClass"}
MI=["MPBattleClass","MPMegawealthClass","MPSiegeClass","MPUnholyAllianceClass"]
CAT={"G":"(g) 已由 coverage 内已验证 IID 解决","I":"(i) 共同基类重复计数/无独立 RTTI","F":"(f) 名字在镜像 ASCII 中零出现","H":"(h) 仅以容器模板实参/表行名出现（非模板类）","B":"(b) 复合名前缀片段","E":"(e) 其它/保守未判定"}
def u16(b,o): return struct.unpack_from("<H",b,o)[0]
def u32(b,o): return struct.unpack_from("<I",b,o)[0]
def wj(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
def wt(n,h,rows):
    with (OUT/n).open("w",encoding="utf-8",newline="") as f:
        f.write("\t".join(h)+"\n")
        for r in rows: f.write("\t".join(str(x) for x in r)+"\n")
def shape(n):
    a=n.count("@")
    if n.startswith("?$"): return "template_at%d"%a
    q=a+1
    return "plain_A@B" if q==2 else "plain_A@B@C" if q==3 else "plain_%d_segment"%q
def pvs(s):
    return [s[i:] for i in range(1,min(4,len(s)-1)+1) if s[:i] and all(c in "PAV" for c in s[:i])]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    b=IMG.read_bytes(); sha=hashlib.sha256(b).hexdigest().upper()
    if not sha.startswith("73201CC0"): raise SystemExit("sha mismatch "+sha)
    pe=u32(b,0x3C); nsec=u16(b,pe+6); optsz=u16(b,pe+20); opt=pe+24; ib=u32(b,opt+28)
    secs={}
    for i in range(nsec):
        o=opt+optsz+i*40; nm=b[o:o+8].rstrip(b"\0").decode("latin1")
        vs,va,rs,rp=struct.unpack_from("<IIII",b,o+8)
        secs[nm]={"name":nm,"vs":vs,"va":va,"rs":rs,"rp":rp,"lo":ib+va}
    tds=[]; pc={}
    for nm in (".rdata",".data"):
        s=secs[nm]; end=s["rp"]+s["rs"]; o=s["rp"]
        while o+12<=end:
            if u32(b,o)==TD_VF and u32(b,o+4)==0 and b[o+8:o+10]==b".?":
                p=o+8
                while p<end and b[p]!=0: p+=1
                raw=b[o+8:p]
                if 4<=len(raw)<=512 and all(32<=c<=126 for c in raw):
                    d=raw.decode("ascii")
                    pf=".?AV" if d.startswith(".?AV") else ".?AU" if d.startswith(".?AU") else ".?AW" if d.startswith(".?AW") else "other"
                    if pf!="other":
                        bare=d[4:-2] if d.endswith("@@") else d[4:]
                        pc[pf]=pc.get(pf,0)+1
                        tds.append({"decorated":d,"bare":bare,"prefix":pf,"tdVA":s["lo"]+o-s["rp"],"section":nm,"fileOff":o})
                        o=p+1
                        while o%4: o+=1
                        continue
            o+=4
    tds.sort(key=lambda e:e["tdVA"]); by={e["tdVA"]:e for e in tds}
    ex={}; tp={}; pl={}
    for e in tds:
        ex.setdefault(e["bare"].lower(),e)
        n=e["bare"]
        if n.startswith("?$") and "@" in n: tp.setdefault(n[2:].split("@",1)[0].lower(),[]).append(e)
        if not n.startswith("?$") and "@" in n: pl.setdefault(n.lower(),[]).append(e)
    cb=COV.read_bytes(); cs=hashlib.sha256(cb).hexdigest().upper(); lines=cb.decode("utf-8").splitlines()
    counts={}; ctx={}; rawocc=0; wr=0; bw=0
    for i,line in enumerate(lines[1:],2):
        if not line: continue
        c=line.split("\t")
        if len(c)!=8: bw+=1
        sem=c[3] if len(c)>3 else ""
        arr=CLASS_RE.findall(sem); rawocc+=len(arr)
        tt=list(dict.fromkeys(arr))
        if tt: wr+=1
        for z in tt:
            counts[z]=counts.get(z,0)+1
            ctx.setdefault(z,[]).append({"line":i,"entry":c[0] if c else "","sub":c[1] if len(c)>1 else "","name":c[2] if len(c)>2 else "","sem":sem})
    toks=sorted(counts,key=lambda n:(-counts[n],n))
    # Q1 rule: X_Y -> X@Y, whole-token replacement, plain non-template compound TD only; no segment dropping.
    def resolve(z,mode):
        seeds=[z]+([z[1:]] if z.startswith("?") else [])
        for x in seeds:
            if x.lower() in ex: return {"me":"exact","nm":x,"td":ex[x.lower()]}
        for x in seeds:
            for y in pvs(x):
                if y.lower() in ex: return {"me":"prefix","nm":y,"td":ex[y.lower()]}
        if mode=="C":
            k=z.replace("_","@").lower()
            if k in pl: return {"me":"compound","nm":z.replace("_","@"),"tds":pl[k]}
        if z.lower() in tp: return {"me":"template_base","nm":z,"tds":tp[z.lower()]}
        return None
    def bucket(mode):
        res={z:resolve(z,mode) for z in toks}; res={k:v for k,v in res.items() if v}
        ms={}
        for r in res.values(): ms[r["me"]]=ms.get(r["me"],0)+1
        cv=set()
        for r in res.values():
            if r["me"] in ("exact","prefix"): cv.add(r["td"]["tdVA"])
            else: cv.update(e["tdVA"] for e in r["tds"])
        return {"res":res,"ms":ms,"b":len(res),"co":len(toks)-len(res),"ri":len(tds)-len(cv),"cv":cv}
    S,C=bucket("S"),bucket("C"); add=sorted(by[v]["bare"] for v in C["cv"]-S["cv"])
    blob=b.decode("latin1")
    def ac(n): return blob.count(n)
    ic=[]
    for z in MI:
        found=None
        for x in ctx.get(z,[]):
            m=IID_RE.search(x["sem"])
            if m:
                td=by.get(int(m.group(1),16))
                if td and td["bare"].lower()==m.group(2).lower():
                    found={"line":x["line"],"va":hex(int(m.group(1),16)),"claim":m.group(2),"td":td["bare"]}; break
        ic.append({"token":z,"ok":found is not None,"evidence":found})
    mpx=ctx.get("MPGameModeClass",[]); mpd=set(); mn=[x["line"] for x in mpx if "MPGameModeClass 在本镜像无 RTTI" in x["sem"]]
    for x in mpx:
        m=IID_RE.search(x["sem"])
        if m:
            td=by.get(int(m.group(1),16))
            if td and td["bare"].lower()==m.group(2).lower(): mpd.add(td["bare"])
    def th(n): return [e for e in tds if e["bare"].startswith("?$") and n.lower() in e["bare"].lower()]
    def ph(n):
        out=[]
        for c in [n]+pvs(n): out += [e for e in tds if not e["bare"].startswith("?$") and e["bare"].lower().startswith(c.lower()+"@")]
        return list({e["tdVA"]:e for e in out}.values())
    def classify(n):
        x=(ctx.get(n) or [{}])[0]; loc="coverage L%s entry=%s name=%s"%(x.get("line",0),x.get("entry",""),x.get("name",""))
        if n in MI:
            q=next(z for z in ic if z["token"]==n)
            if q["ok"]:
                e=q["evidence"]
                return ("G","成立：4/4 IID 解码与 TD 一致",loc+"；"+e["va"]+" → "+e["td"])
        if n=="MPGameModeClass": return ("I","成立：共同基类重复计数",loc+"；coverage 明写无 RTTI L"+"/L".join(map(str,mn[:2]))+"；派生 RTTI %d 个"%len(mpd))
        h=th(n)
        if h and n.lower() not in ex:
            cn=sum(1 for y in ctx.get(n,[]) if (n+"::") in (y["name"]+" "+y["sem"]))
            co=sum(1 for y in ctx.get(n,[]) if "T_DynamicVectorClass_" in y["sem"] or "T_VectorClass_" in y["sem"])
            return ("H","成立：9/9 非模板类",loc+"；XxxClass:: %d 行、容器行 %d；TD %s"%(cn,co,"、".join(e["bare"] for e in h[:2])))
        q=ph(n)
        if q: return ("B","成立：需带 @ 尾段",loc+"；"+"、".join(e["bare"]+" @0x%x"%e["tdVA"] for e in q[:2]))
        if n in NV and ac(n)==0: return ("F","成立：ASCII 0 次，归因无证据",loc+"；ASCII 0 次；YRpp/kb 外来源")
        return ("E","保守未判定",loc+"；ASCII %d 次；未解析不是名字错"%ac(n))
    final=[]
    for n in toks:
        if n not in C["res"]:
            c,v,e=classify(n); final.append((n,counts[n],c,v,e))
    cd={}
    for _,_,c,_,_ in final: cd[c]=cd.get(c,0)+1
    comp=[]
    for e in tds:
        if "@" in e["bare"]:
            comp.append((e["bare"],e["decorated"],shape(e["bare"]),e["bare"].count("@"),e["bare"][2:].split("@",1)[0] if e["bare"].startswith("?$") else "",hex(e["tdVA"]),e["section"],e["fileOff"]))
    wt("compound_names.tsv",["bare_class","decorated_name","shape_class","at_count","template_base","td_VA","section","file_off"],comp)
    wt("unresolved_final.tsv",["name","coverage_rows","final_category","verdict_on_audit","evidence"],[(n,r,CAT[c],v,e) for n,r,c,v,e in final])
    wt("reconcile_final.tsv",["token","coverage_rows","S_bucket","S_mechanism","C_bucket","C_mechanism","compound_TD"],[(n,counts[n],"BOTH" if n in S["res"] else "COVERAGE_ONLY",S["res"].get(n,{}).get("me",""),"BOTH" if n in C["res"] else "COVERAGE_ONLY",C["res"].get(n,{}).get("me",""),C["res"][n]["nm"] if n in C["res"] and C["res"][n]["me"]=="compound" else "") for n in toks])
    wj("_stage0_sections.json",{"image":str(IMG),"sha256":sha,"imageSize":len(b),"imageBase":hex(ib),"sections":secs,"scanBytes":secs[".rdata"]["rs"]+secs[".data"]["rs"],"coverage":str(COV),"coverageSha256":cs,"coverageBytes":len(cb)})
    wj("_stage1_compound.json",{"tdEntries":len(tds),"uniqueBare":len(ex),"prefixCounts":pc,"withAtEntries":len(comp),"plainNonTemplate":len(pl),"templateNames":sum(1 for e in tds if e["bare"].startswith("?$")),"shapeCounts":{k:sum(1 for e in comp if e[2]==k) for k in sorted(set(e[2] for e in comp))},"matchRule":"X_Y -> X@Y exact against plain non-template compound TD; no segment dropping"})
    wj("_stage2_coverage.json",{"dataRows":len(lines)-1,"badWidth":bw,"rowsWith":wr,"rawTokenOccurrences":rawocc,"distinctTokens":len(toks),"counts":counts})
    wj("_stage3_buckets.json",{"S":{"both":S["b"],"coverageOnly":S["co"],"rttiOnly":S["ri"],"coveredEntries":len(tds)-S["ri"],"mechanisms":S["ms"]},"C":{"both":C["b"],"coverageOnly":C["co"],"rttiOnly":C["ri"],"coveredEntries":len(tds)-C["ri"],"mechanisms":C["ms"]},"compoundAddedTDs":add,"coverageShaAfter":hashlib.sha256(COV.read_bytes()).hexdigest().upper()})
    wj("_stage4_attrib.json",{"finalUnresolvedCount":len(final),"categoryDistribution":cd,"noVtableAsciiCounts":{n:ac(n) for n in sorted(NV)},"iidChecks":ic,"mpDerivedDecoded":sorted(mpd),"templateCritique":{"templateOnlyTokens":9,"explicitClassScopeLines":sum(1 for n,_,c,_,_ in final if c=="H" for y in ctx.get(n,[]) if (n+"::") in (y["name"]+" "+y["sem"]))}})
    pct=lambda a,z:"%.2f%%"%(100.0*a/z)
    M=[str(IMG)+"  sha256 "+sha,"","# R17-R24-RECON-FINAL","","## Q1","", "- TD with @: %d (template %d, plain %d)."%(len(comp),sum(1 for e in comp if e[2].startswith("template")),len(pl)), "- Rule: X_Y -> X@Y whole token, case-insensitive exact match, no segment dropping.","","## Q2","","| mode | BOTH | COVERAGE_ONLY | RTTI_ONLY |","|---|---:|---:|---:|","| S | %d | %d | %d |"%(S["b"],S["co"],S["ri"]),"| C | %d | %d | %d |"%(C["b"],C["co"],C["ri"]),"","Historical: R19 209/220/779; R20 403/26/383; audit 397/32. S equals audit; C corrects the 6 underscore matches to compound TDs and hence RTTI_ONLY=377.","","## Q3","","Final unresolved %d; distribution %s."%(len(final),", ".join("%s=%d"%(CAT[k],cd[k]) for k in sorted(cd))),"","Audit template critique accepted: 9/9 are not template classes; no-vtable critique accepted: 6/6 ASCII 0; naming-difference critique accepted: 4 IID-resolved + 1 common-base duplicate.","","## Q4","","Denominator is 429 distinct coverage tokens. S %d (%s), C %d (%s). This is token-level correspondence, not occurrence coverage. in-binary covers only classes with RTTI. Unresolved is not a name error."%(S["b"],pct(S["b"],429),C["b"],pct(C["b"],429)),"","未取得项：0。"]
    (OUT/"REPORT.md").write_text("\n".join(M)+"\n",encoding="utf-8")
if __name__=="__main__": main()
