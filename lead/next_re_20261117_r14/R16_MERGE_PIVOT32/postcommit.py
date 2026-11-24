# -*- coding: utf-8 -*-
"""R16-MERGE-PIVOT32 写盘后自证：pin + before_col4 还原性 + 全部 11 项复核（只读目标文件）。"""
import os, sys, json, hashlib, collections, math, re
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
OUT  = os.path.join(ROOT, "R16_MERGE_PIVOT32")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e
def parse(data):
    lines=data.splitlines(keepends=True)
    rows=[]
    for raw in lines[1:]:
        had=raw.endswith(b"\n"); body=raw[:-1] if had else raw
        if body.endswith(b"\r"): body=body[:-1]
        rows.append({"raw":raw,"body":body,"had":had,"cols":body.decode("utf-8").split("\t")})
    return lines[0], rows
def metrics(rows, atlas):
    m=collections.Counter(); cc=collections.Counter()
    perS=collections.defaultdict(collections.Counter)
    for r in rows:
        c=r["cols"]; cc[len(c)]+=1
        if len(c)<8: continue
        e=ne(c[0]); sub=c[1].strip(); name=c[2].strip(); sem=c[3]; grade=c[4].strip()
        if grade=="[已证]":
            m["proved_total"]+=1
            if "④" in sem: m["cal_A"]+=1
            if "④ 活表槽位见证" in sem: m["cal_B"]+=1
            if e in atlas:
                m["proved_atlas"]+=1
                if "[未证]" not in sem: m["proved_strict"]+=1
            else: m["proved_out"]+=1
        if "§12.6" in sem: m["s126_rows"]+=1; m["s126_hits"]+=sem.count("§12.6")
        m["clsid_none"]+=sem.count("CLSID None")
        if e in atlas:
            d=perS[sub]; d["atlas_n"]+=1
            if name and not name.startswith("sub_"):
                d["named_L"]+=1
                if not RE_CSUB.search(name):
                    d["named_S14"]+=1
                    if not RE_SLOT.search(name): d["named_strict"]+=1
            if grade=="[已证]":
                d["proved_n"]+=1
                if "[未证]" not in sem: d["proved_strict"]+=1
    m["data_rows"]=len(rows); m["colcount"]=dict(cc)
    nom,st=set(),set()
    for sub,d in perS.items():
        a=d["atlas_n"]; tn=math.ceil(0.9*a); tp=math.ceil(0.5*a)
        if d["named_S14"]>=tn and d["proved_n"]>=tp: nom.add(sub)
        if d["named_S14"]>=tn and d["proved_strict"]>=tp: st.add(sub)
    m["nominal"]=sorted(nom); m["strict"]=sorted(st)
    return m

def load_atlas():
    s=set()
    for i,l in enumerate(open(ATLAS,encoding="utf-8-sig")):
        if i==0: continue
        p=l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): s.add(ne(p[0]))
    return s

def main():
    L=[]
    def log(s): L.append(s); print(s)
    rep=json.load(open(os.path.join(OUT,"PIN_AND_RESTORE.json"),encoding="utf-8"))
    before_cov_sha=rep["before_cov_sha"]; before_pan_sha=rep["before_pan_sha"]
    after_cov_sha=rep["after_cov_sha"]; after_pan_sha=rep["after_pan_sha"]
    cov_on=open(COV,"rb").read(); pan_on=open(PANEL,"rb").read()
    log("[P0] 盘上 after sha: cov=%s pan=%s" % (sha(cov_on),sha(pan_on)))
    assert sha(cov_on)==after_cov_sha and sha(pan_on)==after_pan_sha, "盘上 sha 与 staged 不符"

    # pin + before_col4 还原性（核心）
    pin=open(os.path.join(OUT,"_PIN_coverage.tsv"),"rb").read()
    before_col4=json.load(open(os.path.join(OUT,"_before_col4.json"),encoding="utf-8"))
    changes=rep["changes"]
    assert len(changes)==32 and len(before_col4)==32
    sent_t=rep["sentinel_template"]
    restore=pin
    for k,c in enumerate(changes):
        key=str(c["idx"])
        assert before_col4[key]["entry"]==c["entry"], "before_col4 entry 不匹配（off-by-one?）"
        s=(sent_t%k).encode("utf-8")
        assert restore.count(s)==1, ("sentinel 不唯一", k)
        restore=restore.replace(s, before_col4[key]["col4"].encode("utf-8"), 1)
    log("[P1] PIN + before_col4 重建 sha = %s" % sha(restore))
    assert sha(restore)==before_cov_sha, ("还原 sha != 改前", sha(restore), before_cov_sha)
    # 与字节备份逐字节相等
    bak=open(os.path.join(OUT,"_before_exact_coverage.tsv"),"rb").read()
    assert restore==bak, "还原字节 != 改前备份（逐字节）"
    log("[P1a] 还原字节 == 改前精确备份（逐字节相等）OK")

    # pin + after_col4（从盘上 after 提取）重建 after
    _,after_rows=parse(cov_on)
    restore_after=pin
    for k,c in enumerate(changes):
        s=(sent_t%k).encode("utf-8")
        new_col4=after_rows[c["idx"]]["cols"][3]
        assert new_col4==c["new_col4"], ("盘上 new_col4 与 ledger 不符", c["entry"])
        restore_after=restore_after.replace(s,new_col4.encode("utf-8"),1)
    assert sha(restore_after)==after_cov_sha, "PIN+after_col4 重建 sha != 盘上 after"
    log("[P2] PIN + after_col4 重建 sha == 盘上 after sha OK（off-by-one 已排除）")

    # PANEL 还原性
    m96=rep["M96_text"].encode("utf-8")
    assert pan_on.count(m96)==1, "M96 块出现次数 !=1"
    pan_restored=pan_on.replace(m96,b"",1)
    assert sha(pan_restored)==before_pan_sha, ("PANEL 删块 sha != 改前", sha(pan_restored), before_pan_sha)
    bakp=open(os.path.join(OUT,"_before_exact_PANEL.md"),"rb").read()
    assert pan_restored==bakp, "PANEL 删块 != 改前备份"
    log("[P3] PANEL 删 M96 块后 sha == 改前 sha，且逐字节等于改前备份 OK")

    # 改后指标（盘上）
    atlas=load_atlas()
    ma=metrics(after_rows,atlas)
    log("[P4] 盘上改后指标：行数=%d 列分布=%s [已证]=%d atlas内=%d 外=%d 口径A=%d 口径B=%d §12.6行=%d 字面=%d CLSIDNone=%d 名义=%s 严格=%s" % (
        ma["data_rows"],ma["colcount"],ma["proved_total"],ma["proved_atlas"],ma["proved_out"],
        ma["cal_A"],ma["cal_B"],ma["s126_rows"],ma["s126_hits"],ma["clsid_none"],
        ",".join(ma["nominal"]),",".join(ma["strict"])))
    assert ma["data_rows"]==18498 and ma["colcount"]=={8:18498}
    assert ma["proved_total"]==1654 and ma["proved_atlas"]==1648 and ma["proved_out"]==6
    assert ma["cal_A"]==375 and ma["cal_B"]==210
    assert ma["s126_rows"]==151 and ma["clsid_none"]==0
    assert ma["nominal"]==["S15","S16","S17"] and ma["strict"]==["S17"]
    log("[P4a] ④ 不变量/⑥口径/⑦归零/⑧§12.6/⑩达标 全部通过")

    # 只有 32 行第4列变（盘上 after vs 备份 before）
    _,before_rows=parse(bak)
    diff=[]
    for i,(br,ar) in enumerate(zip(before_rows,after_rows)):
        if br["cols"]==ar["cols"]: continue
        diff.append(i)
        assert all(br["cols"][k]==ar["cols"][k] for k in (0,1,2,4,5,6,7)), ("非第4列改动",i)
    assert len(diff)==32 and set(diff)==set(c["idx"] for c in changes), ("改动行集合不符",diff)
    log("[P5] ⑤ 仅 32 行第4列变（行索引集合精确匹配 ledger），其它 7 列逐字节相同 OK")

    # 行尾
    assert cov_on.count(b"\r")==0 and pan_on.count(b"\r")==0
    log("[P6] ⑪ 行尾全 LF 无 CR OK")

    open(os.path.join(OUT,"POSTCOMMIT_VERIFY.txt"),"w",encoding="utf-8").write("\n".join(L)+"\n")
    print("\n=== POST-COMMIT ALL PASSED ===")

if __name__=="__main__":
    main()
