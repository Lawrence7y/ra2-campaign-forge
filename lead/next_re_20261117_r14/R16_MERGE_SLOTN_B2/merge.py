# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B2 · 执行并表（coverage.tsv / PANEL.md 唯一写者）。

写域：COVERAGE/coverage.tsv（仅 15 行第 4 列）、COVERAGE/PANEL.md（仅插入 1 条 M87 披露，
      既有内容零删除零改字）、产物目录 R16_MERGE_SLOTN_B2/。其余一律只读。
不改变 grade / 判定 / named / proved / strict；不做逆向。
"""
import hashlib, json, os, re, shutil, sys, collections, datetime, subprocess
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B2", "delta.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B2")
STRICT_SRC = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

C4   = "\u2463"            # ④
SB   = "④ 活表槽位见证"    # 口径 B 子串
OLD  = "R14_COMMON §12.4"
NEW  = "R14_COMMON §12.6"
M86_HEAD = "> ✅ **M86 补记"
M77_ANCHOR = "> 📌 **M77 并表实算说明**"

# M87 披露：所有数字来自开卡实测（measure.py），不引用任何预测值。
M87_LINES = [
    "> ✅ **M87 补记：43 行 `slotN` 的 ④ 成文 —— 批次 2 并入 15 行（累计 30 / 43）**",
    "> 本批 15 行取自 `PROBE_802\\slotN43.tsv` 数据行 16–30，`col_ok=match` / `install_ext=y` 15/15；",
    "> 异族审计（`R16_AUDIT_SLOTN_B2\\VERDICT.md`）判 **§A/§B/§E/§F 全 0 不合格，90/90 字节项独立复算为真**，§C 行 30 表改选四问全中、判成立；唯一必改项是**披露指针编号过时**（`§12.4` → `§12.6`，因 COMMON 重号），已按 Lead「并表环节统一规范化」口径处理，**替换 15 处**，改后 `coverage.tsv` 内 `§12.6` 命中 30 行、`§12.4` 命中 0 行；",
    "> ⚠️ 本批有 **1 处对扫描产物 site 的合法改选**：`005B2FD0`（`InfantryClass::slot124`）的 `work_scan.site_of=0043B71F` 实际装的是 **BuildingClass** 表（`007E3EBC`），与行名类冲突；改取 InfantryClass 表 `007EB058` 及其自己的装表点 `00517D9D`。审计四问全中、判**成立**。引用该行时须知情：其 `装表点` 不等于 `work_scan.json:A_agg.site_of`。",
    "> 数字（实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **328 / 1,654（19.83%）升至 337 / 1,654（20.37%）**，本批**净增 = 337 − 328 = 9 行**，**不是简单 +15**：15 行中有 **6 行**改前第 4 列已在「合同闭合 ③b④」分类标签里含字符 `④`，改后计数不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **106 / 1,654（6.41%）升至 121 / 1,654（7.32%）**（净增 15 行）。",
    "> ⚠️ **口径 A 的已知异质性**：口径 A 只要求含字符 `④`，A−B 仍有 222 → 216 行含 `④` 而非 `④ 活表槽位见证` 形态（含 `③b④` 分类/环标签、`④ N 个 E8 直调站点`、`④ 活 vt 构造安装点` 等）。⇒ **引用 ④ 成文率必须说明用的是 A 还是 B**，不得当作「四环齐全」的等价物。",
    "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**；",
]

def sha(b): return hashlib.sha256(b).hexdigest()

def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e

def statinfo(p):
    st=os.stat(p); b=open(p,"rb").read()
    iso=datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    return dict(path=p, mtime=st.st_mtime, mtime_local=iso, bytes=len(b), sha256=sha(b),
                nlines_lf=b.count(b"\n"), crlf=b.count(b"\r\n"),
                bom=(b[:3]==b"\xef\xbb\xbf"), ends_nl=b.endswith(b"\n"))

def load_atlas():
    s=set()
    for i,line in enumerate(open(ATLAS,encoding="utf-8-sig")):
        if i==0: continue
        p=line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): s.add(ne(p[0]))
    return s

def cov_metrics(text, atlas):
    data=text.splitlines()[1:]
    coldist=collections.Counter(len(ln.split("\t")) for ln in data)
    yz=ina=outa=na=nb=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1
            if SB in c[3]: nb+=1
    return dict(data_rows=len(data), coldist=dict((str(k),v) for k,v in coldist.items()),
                yizheng=yz, atlas_in=ina, atlas_out=outa, N_A=na, N_B=nb)

def main():
    os.makedirs(OUTD, exist_ok=True)
    cov_b=open(COV,"rb").read(); pan_b=open(PANEL,"rb").read(); delta_b=open(DELTA,"rb").read()
    cov_before=statinfo(COV); pan_before=statinfo(PANEL); delta_info=statinfo(DELTA)
    cov_text=cov_b.decode("utf-8"); pan_text=pan_b.decode("utf-8")
    atlas=load_atlas()
    metrics_before=cov_metrics(cov_text, atlas)

    # 备份（供可复跑 verify.py 做还原性检查）
    shutil.copyfile(COV, os.path.join(OUTD,"coverage.before.bak"))
    shutil.copyfile(PANEL, os.path.join(OUTD,"PANEL.before.bak"))

    # ---- delta: 15 行 + 指针规范化留痕 ----
    drows=[ln.split("\t") for ln in delta_b.decode("utf-8-sig").splitlines()[1:]]
    assert len(drows)==15, len(drows)
    repl_count=0; newcol={}
    for d in drows:
        assert len(d)==8
        c=d[3]; repl_count+=c.count(OLD)
        newcol[ne(d[0])]=c.replace(OLD,NEW)
    assert repl_count==15, ("replacement count",repl_count)

    # ---- 定位 15 行 + 严格前缀 / 其余列逐字节校验 ----
    cov_lines=cov_text.splitlines(keepends=True)
    by_entry={}
    for idx,ln in enumerate(cov_lines):
        core=ln[:-1] if ln.endswith("\n") else ln
        c=core.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)
    target=[]
    for d in drows:
        e=ne(d[0]); idxs=by_entry.get(e,[])
        assert len(idxs)==1, (e,idxs)
        i=idxs[0]; core=cov_lines[i][:-1] if cov_lines[i].endswith("\n") else cov_lines[i]
        c=core.split("\t")
        assert len(c)==8, (e,len(c))
        before4=c[3]; after4=newcol[e]
        assert after4.startswith(before4), ("strict-prefix FAIL",e)
        for j in [0,1,2,4,5,6,7]:
            assert c[j]==d[j], ("other-col mismatch",e,j)
        assert SB in after4 and C4 in after4, ("after missing ④ witness",e)
        target.append(dict(entry=e, line_index=i, before4=before4, after4=after4,
                           before_has_circled4=(C4 in before4),
                           before_has_witness=(SB in before4),
                           added_bytes=len(after4.encode("utf-8"))-len(before4.encode("utf-8"))))

    # 实测 N_pre / N_A_pre / N_B_pre（改前）
    N_pre=sum(1 for t in target if t["before_has_circled4"])
    assert all(not t["before_has_witness"] for t in target), "改前 15 行已有 ④ 活表槽位见证？与审计 §10.3 不符"
    N_A_pre=metrics_before["N_A"]; N_B_pre=metrics_before["N_B"]
    assert N_pre==6 and N_A_pre==328 and N_B_pre==106, (N_pre,N_A_pre,N_B_pre)

    # ---- 落地 coverage.tsv：只改 15 行第 4 列 ----
    for t in target:
        i=t["line_index"]; ln=cov_lines[i]
        nl="\n" if ln.endswith("\n") else ""
        core=ln[:-1] if nl else ln
        c=core.split("\t"); c[3]=t["after4"]
        cov_lines[i]="\t".join(c)+nl
    cov_after_text="".join(cov_lines); cov_after_b=cov_after_text.encode("utf-8")
    assert cov_after_b.count(b"\n")==cov_b.count(b"\n"), "coverage LF count changed"
    assert cov_after_b[:3]!=b"\xef\xbb\xbf" and not cov_after_b.endswith(b"\n")

    metrics_after=cov_metrics(cov_after_text, atlas)
    N_A_post=metrics_after["N_A"]; N_B_post=metrics_after["N_B"]
    assert N_A_post==337 and N_B_post==121, (N_A_post,N_B_post)
    s126_lines=sum(1 for ln in cov_after_text.splitlines() if NEW in ln)
    s124_hits=cov_after_text.count(OLD)
    assert s126_lines==30 and s124_hits==0, (s126_lines,s124_hits)

    # ---- PANEL.md：只在 M86 块之后插入 M87，既有内容零改字 ----
    pan_lines=pan_text.splitlines(keepends=True)
    m86=[i for i,ln in enumerate(pan_lines) if ln.startswith(M86_HEAD)]
    m77=[i for i,ln in enumerate(pan_lines) if ln.startswith(M77_ANCHOR)]
    assert len(m86)==1 and len(m77)==1, ("anchors",m86,m77)
    assert m77[0]>m86[0], "M77 必须在 M86 之后"
    # M86 块（L214-223，共 10 行）里每行都应是引用行；M77 紧随其后
    m86_block=pan_lines[m86[0]:m77[0]]
    assert len(m86_block)==10 and all(ln.startswith("> ") for ln in m86_block), ("M86 block",len(m86_block))
    ins_lines=[s+"\n" for s in M87_LINES]
    pan_lines[m77[0]:m77[0]]=ins_lines
    pan_after_text="".join(pan_lines); pan_after_b=pan_after_text.encode("utf-8")
    assert pan_after_b.count(b"\n")==pan_b.count(b"\n")+len(M87_LINES)

    # ---- 原子写入 ----
    for path,data in [(COV,cov_after_b),(PANEL,pan_after_b)]:
        tmp=path+".tmp_r16merge_b2"
        with open(tmp,"wb") as f: f.write(data)
        os.replace(tmp,path)

    cov_after=statinfo(COV); pan_after=statinfo(PANEL)

    # ---- before_state.json ----
    before_state=dict(
        coverage=dict(cov_before, metrics=metrics_before,
                      target_rows=[dict(entry=t["entry"], col4_before=t["before4"],
                                        col4_after=t["after4"],
                                        before_has_circled4=t["before_has_circled4"],
                                        before_has_witness=t["before_has_witness"],
                                        added_bytes=t["added_bytes"]) for t in target]),
        panel=dict(pan_before, insert_after="M86 block", insert_before_anchor=M77_ANCHOR,
                   inserted_lines=M87_LINES),
        delta=dict(delta_info, nrows=15, replacement_pattern=OLD, replacement_new=NEW,
                   replacement_count=repl_count),
        measured=dict(N_pre=N_pre, N_A_pre=N_A_pre, N_B_pre=N_B_pre,
                      N_A_post=N_A_post, N_B_post=N_B_post,
                      s126_lines_after=s126_lines, s124_hits_after=s124_hits),
    )
    with open(os.path.join(OUTD,"before_state.json"),"w",encoding="utf-8") as f:
        json.dump(before_state,f,ensure_ascii=False,indent=1)

    # ---- strict_panel 复算（OUT 改到自己的目录），达标须未翻转 ----
    slocal=os.path.join(OUTD,"strict_panel_local.py")
    ssrc=open(STRICT_SRC,encoding="utf-8").read()
    newout='OUT = os.path.join(ROOT, "R16_MERGE_SLOTN_B2", "strict_out")'
    ssrc2,n=re.subn(r'^OUT\s*=.*$',newout,ssrc,flags=re.M)
    assert n==1, ("strict OUT replace count",n)
    with open(slocal,"w",encoding="utf-8") as f: f.write(ssrc2)
    r=subprocess.run([sys.executable,slocal],capture_output=True,text=True,encoding="utf-8")
    mn=re.search(r"名义达标:\s*(\S+)",r.stdout)
    st=re.search(r"严格达标:\s*(\S+)",r.stdout)
    nominal=mn.group(1) if mn else None
    strict=st.group(1) if st else None

    # ---- after_state.json ----
    after_state=dict(
        coverage=dict(cov_after, metrics=metrics_after,
                      s126_lines=s126_lines, s124_hits=s124_hits),
        panel=dict(pan_after, inserted_lines=M87_LINES),
        strict=dict(nominal=nominal, strict=strict, returncode=r.returncode,
                    stdout=r.stdout, stderr=r.stderr,
                    script="strict_panel_local.py (copy; only OUT redirected to own dir)",
                    out_dir=os.path.join(OUTD,"strict_out")),
    )
    with open(os.path.join(OUTD,"after_state.json"),"w",encoding="utf-8") as f:
        json.dump(after_state,f,ensure_ascii=False,indent=1)

    print("MERGE DONE")
    print("coverage bytes %d -> %d sha %s -> %s" % (cov_before["bytes"],cov_after["bytes"],cov_before["sha256"][:8],cov_after["sha256"][:8]))
    print("panel    bytes %d -> %d sha %s -> %s" % (pan_before["bytes"],pan_after["bytes"],pan_before["sha256"][:8],pan_after["sha256"][:8]))
    print("replacements=%d target_rows=%d N_pre=%d" % (repl_count,len(target),N_pre))
    print("N_A %d->%d  N_B %d->%d" % (N_A_pre,N_A_post,N_B_pre,N_B_post))
    print("s126_lines_after=%d s124_hits_after=%d" % (s126_lines,s124_hits))
    print("nominal=%s strict=%s strict_rc=%d" % (nominal,strict,r.returncode))
    if r.returncode!=0: print("STRICT STDERR:",r.stderr)

if __name__=="__main__":
    main()
