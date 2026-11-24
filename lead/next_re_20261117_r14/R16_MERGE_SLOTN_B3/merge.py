# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B3 · merge executor.

Writes only: COVERAGE/coverage.tsv (13 rows col4), COVERAGE/PANEL.md (1 M88 insert),
and own product dir. All five §2.1 numbers are MEASURED from on-disk bytes.
"""
import hashlib, json, os, re, shutil, sys, collections, datetime, subprocess
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B3", "delta.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B3")
STRICT_SRC = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

C4   = "\u2463"
SB   = "④ 活表槽位见证"
S126 = "§12.6"
S124 = "§12.4"
M87_HEAD    = "> ✅ **M87 补记"
M77_ANCHOR  = "> 📌 **M77 并表实算说明**"
M88_HEAD    = "> ✅ **M88 补记"

def sha(b): return hashlib.sha256(b).hexdigest()
def pct(n, d): return "%.2f" % (100.0 * n / d) if d else "0.00"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

def statinfo(p):
    st=os.stat(p); b=open(p,"rb").read()
    iso=datetime.datetime.fromtimestamp(st.st_mtime,
        datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    return dict(path=p, mtime=st.st_mtime, mtime_local=iso,
                bytes=len(b), sha256=sha(b), lines_nl=b.count(b"\n"),
                CRLF=b.count(b"\r\n"), LF=b.count(b"\n")-b.count(b"\r\n"),
                CR=b.count(b"\r")-b.count(b"\r\n"),
                BOM=(b[:3]==b"\xef\xbb\xbf"), ends_nl=b.endswith(b"\n"))

def load_atlas():
    s=set()
    for i,line in enumerate(open(ATLAS, encoding="utf-8-sig")):
        if i==0: continue
        p=line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): s.add(ne(p[0]))
    return s

def cov_metrics(data, atlas):
    coldist=collections.Counter(len(ln.split("\t")) for ln in data)
    yz=ina=outa=na=nb=0
    s126_lines=s124_lines=s126_hits=s124_hits=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1
            if SB in c[3]: nb+=1
        if S126 in ln: s126_lines+=1
        if S124 in ln: s124_lines+=1
        s126_hits+=ln.count(S126); s124_hits+=ln.count(S124)
    return dict(data_rows=len(data), coldist={str(k):v for k,v in coldist.items()},
                yizheng=yz, atlas_in=ina, atlas_out=outa,
                N_A=na, N_B=nb,
                s126_lines=s126_lines, s124_lines=s124_lines,
                s126_hits=s126_hits, s124_hits=s124_hits)

def cov_split(text):
    parts=text.split("\n")
    return parts[0], [ln for ln in parts[1:] if ln!=""]

def build_m88_lines(N_pre, N_A_pre, N_A_post, N_B_pre, N_B_post, yz, pre_entries):
    netA=N_A_post-N_A_pre; netB=N_B_post-N_B_pre
    ent_str="/".join("`%s`" % e for e in pre_entries)
    return [
      "> ✅ **M88 补记：43 行 `slotN` 的 ④ 成文收官（批次 3 并入 13 行，累计 43 / 43）**",
      "> 本批 13 行取自 `PROBE_802\\slotN43.tsv` 数据行 31–43，`col_ok=match` / `install_ext=y` 13/13；",
      "> 异族审计（`R16_AUDIT_SLOTN_B3\\VERDICT.md`）判 **A/B/D/E/F 五项全 0 不合格，78/78 字节项独立复算为真，0 必改**；指针 13/13 已是 `§12.6`（无需规范化），全文 `§12.4` 命中 0 处；",
      "> ⚠️ 本批有 **2 处对扫描产物 site 的合法改选**：`005B3570`（`InfantryClass::slot123`）与 `005B35E0`（`InfantryClass::slot122`）的 `work_scan.site_of=0043B71F` 实际装的是 BuildingClass 表（`007E3EBC`），与行名类冲突；均改取 InfantryClass 表 `007EB058`，装表点分别为 `00517D9D` / `00521A11`。审计两行均判**成立**，并核实「同一张表有多处装表点（`007EB058` 共 3 处）属正常」。引用这两行时须知情。",
      ("> 数字（实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **%d / %s（%s%%）升至 %d / %s（%s%%）**，本批**净增 = %d − %d = %d 行**，**不是简单 +13**：13 行中有 **%d 行**（%s）改前第 4 列已在「合同闭合 ③b④」分类标签里含字符 `④`，改后计数不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **%d / %s（%s%%）升至 %d / %s（%s%%）**（净增 %d 行）。"
        % (N_A_pre, format(yz,","), pct(N_A_pre,yz), N_A_post, format(yz,","), pct(N_A_post,yz),
           N_A_post, N_A_pre, netA, N_pre, ent_str,
           N_B_pre, format(yz,","), pct(N_B_pre,yz), N_B_post, format(yz,","), pct(N_B_post,yz), netB)),
      "> **43 行收官**：三批合计 43 行（15 + 15 + 13），`slotN` 类已无剩余可补（D-47(A) 裁决下的上限已兑现）。",
      ("> ⚠️ **口径 A 的已知异质性**：口径 A 只要求含字符 `④`，A−B 由 %d → %d 行含 `④` 而非 `④ 活表槽位见证` 形态（含 `③b④` 分类/环标签、`④ N 个 E8 直调站点`、`④ 活 vt 构造安装点` 等）。⇒ **引用 ④ 成文率必须说明用的是 A 还是 B**，不得当作「四环齐全」的等价物。"
        % (N_A_pre-N_B_pre, N_A_post-N_B_post)),
      "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**；",
    ]

def main():
    os.makedirs(OUTD, exist_ok=True)
    cov_b=open(COV,"rb").read(); pan_b=open(PANEL,"rb").read(); delta_b=open(DELTA,"rb").read()
    cov_before=statinfo(COV); pan_before=statinfo(PANEL); delta_info=statinfo(DELTA)
    cov_text=cov_b.decode("utf-8"); pan_text=pan_b.decode("utf-8")
    delta_text=delta_b.decode("utf-8-sig")

    shutil.copyfile(COV, os.path.join(OUTD,"coverage.before.bak"))
    shutil.copyfile(PANEL, os.path.join(OUTD,"PANEL.before.bak"))

    atlas=load_atlas()
    hdr, data_before=cov_split(cov_text)
    m_before=cov_metrics(data_before, atlas)

    drows=[ln.split("\t") for ln in delta_text.split("\n") if ln!=""][1:]
    assert len(drows)==13, ("delta data rows",len(drows))
    newcol={}
    for d in drows:
        assert len(d)==8, ("delta ncols",len(d),d[0])
        newcol[ne(d[0])]=d[3]

    by_entry={}
    for idx,ln in enumerate(data_before):
        c=ln.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)
    targets=[]
    for d in drows:
        e=ne(d[0]); idxs=by_entry.get(e,[])
        assert len(idxs)==1, ("entry not unique",e,idxs)
        i=idxs[0]; c=data_before[i].split("\t")
        assert len(c)==8, ("cov ncols",e,len(c))
        before4=c[3]; after4=newcol[e]
        assert after4.startswith(before4) and len(after4)>len(before4), ("prefix/append FAIL",e)
        for j in (0,1,2,4,5,6,7):
            assert c[j]==d[j], ("other-col mismatch",e,j)
        assert c[4].strip()=="[已证]", ("grade not 已证",e)
        assert SB in after4 and C4 in after4, ("after missing witness",e)
        seg=after4[len(before4):]
        targets.append(dict(entry=e, name=d[2], line_index=i,
            col4_before=before4, col4_after=after4,
            before_has_circled4=(C4 in before4), before_has_witness=(SB in before4),
            append_seg=seg, append_s126_hits=seg.count(S126), append_s124_hits=seg.count(S124),
            added_bytes=len(after4.encode("utf-8"))-len(before4.encode("utf-8"))))

    append_s126=sum(t["append_s126_hits"] for t in targets)
    append_s124=sum(t["append_s124_hits"] for t in targets)
    assert append_s126==13 and append_s124==0, ("append pointer counts",append_s126,append_s124)
    assert all(S124 not in d[3] for d in drows), "delta 含 §12.4，需先规范化"

    N_pre=sum(1 for t in targets if t["before_has_circled4"])
    N_A_pre=m_before["N_A"]; N_B_pre=m_before["N_B"]
    assert all(not t["before_has_witness"] for t in targets), "改前 13 行已有 ④ 活表槽位见证"

    data_after=list(data_before)
    for t in targets:
        c=data_after[t["line_index"]].split("\t"); c[3]=t["col4_after"]
        data_after[t["line_index"]]="\t".join(c)
    cov_after_text=hdr+"\n"+"\n".join(data_after)
    cov_after_b=cov_after_text.encode("utf-8")
    assert cov_after_b.count(b"\n")==cov_b.count(b"\n"), "coverage LF count changed"
    assert cov_after_b[:3]!=b"\xef\xbb\xbf" and not cov_after_b.endswith(b"\n")

    m_after=cov_metrics(data_after, atlas)
    N_A_post=m_after["N_A"]; N_B_post=m_after["N_B"]
    assert N_A_post==N_A_pre+(len(targets)-N_pre), (N_A_pre,N_A_post,N_pre)
    assert N_B_post==N_B_pre+len(targets), (N_B_pre,N_B_post)

    yz=m_after["yizheng"]
    pre_entries=[t["entry"] for t in targets if t["before_has_circled4"]]
    M88_LINES=build_m88_lines(N_pre, N_A_pre, N_A_post, N_B_pre, N_B_post, yz, pre_entries)

    pan_lines=pan_text.split("\n")
    m87=[i for i,l in enumerate(pan_lines) if l.startswith(M87_HEAD)]
    m77=[i for i,l in enumerate(pan_lines) if l.startswith(M77_ANCHOR)]
    m88=[i for i,l in enumerate(pan_lines) if l.startswith(M88_HEAD)]
    assert len(m87)==1 and len(m77)==1 and len(m88)==0, ("anchors",m87,m77,m88)
    assert m77[0]>m87[0], "M77 锚点须在 M87 之后"
    m87_block=pan_lines[m87[0]:m77[0]]
    assert len(m87_block)==7 and all(l.startswith("> ") for l in m87_block), \
        ("M87 block",len(m87_block),[l[:30] for l in m87_block])
    ins_at=m77[0]
    pan_lines[ins_at:ins_at]=M88_LINES
    pan_after_text="\n".join(pan_lines)
    pan_after_b=pan_after_text.encode("utf-8")
    assert pan_after_b.count(b"\n")==pan_b.count(b"\n")+len(M88_LINES)

    for path,data in [(COV,cov_after_b),(PANEL,pan_after_b)]:
        tmp=path+".tmp_r16merge_b3"
        with open(tmp,"wb") as f: f.write(data)
        os.replace(tmp,path)

    cov_after=statinfo(COV); pan_after=statinfo(PANEL)

    before_state=dict(
        coverage=dict(cov_before, header=hdr, metrics=m_before,
            target_rows=[dict(entry=t["entry"], name=t["name"],
                              col4_before=t["col4_before"], col4_after=t["col4_after"],
                              before_has_circled4=t["before_has_circled4"],
                              before_has_witness=t["before_has_witness"],
                              append_seg=t["append_seg"],
                              append_s126_hits=t["append_s126_hits"],
                              append_s124_hits=t["append_s124_hits"],
                              added_bytes=t["added_bytes"]) for t in targets]),
        panel=dict(pan_before, insert_after="M87 block", insert_before_anchor=M77_ANCHOR,
                   inserted_lines=M88_LINES, m87_block_lines=len(m87_block)),
        delta=dict(delta_info, nrows=len(drows), needs_normalization=False,
                   append_s126_hits=append_s126, append_s124_hits=append_s124),
        measured=dict(N_pre=N_pre, N_A_pre=N_A_pre, N_B_pre=N_B_pre,
                      N_A_post=N_A_post, N_B_post=N_B_post,
                      yizheng=yz, pre_circled4_entries=pre_entries),
        atlas_entries=len(atlas),
        strict_prefix_ok=sum(1 for t in targets if t["col4_after"].startswith(t["col4_before"])),
        other_cols_ok=len(targets),
    )
    with open(os.path.join(OUTD,"before_state.json"),"w",encoding="utf-8") as f:
        json.dump(before_state,f,ensure_ascii=False,indent=1)

    slocal=os.path.join(OUTD,"strict_panel_local.py")
    ssrc=open(STRICT_SRC,encoding="utf-8").read()
    newout='OUT = os.path.join(ROOT, "R16_MERGE_SLOTN_B3", "strict_out")'
    ssrc2,n=re.subn(r'^OUT\s*=.*$',newout,ssrc,flags=re.M)
    assert n==1, ("strict OUT replace count",n)
    with open(slocal,"w",encoding="utf-8") as f: f.write(ssrc2)
    r=subprocess.run([sys.executable,slocal],capture_output=True,text=True,encoding="utf-8")
    mn=re.search(r"名义达标:\s*(\S+)",r.stdout)
    st=re.search(r"严格达标:\s*(\S+)",r.stdout)
    nominal=mn.group(1) if mn else None
    strict=st.group(1) if st else None

    after_state=dict(
        coverage=dict(cov_after, metrics=m_after,
                      s126_lines=m_after["s126_lines"], s126_hits=m_after["s126_hits"],
                      s124_lines=m_after["s124_lines"], s124_hits=m_after["s124_hits"]),
        panel=dict(pan_after, inserted_lines=M88_LINES, m87_block_lines=len(m87_block)),
        strict=dict(nominal=nominal, strict=strict, returncode=r.returncode,
                    stdout=r.stdout, stderr=r.stderr,
                    script="strict_panel_local.py (copy of RULING_R15_20261119/work/strict_panel.py; only OUT redirected to own dir)",
                    out_dir=os.path.join(OUTD,"strict_out")),
        measured=dict(N_pre=N_pre, N_A_pre=N_A_pre, N_A_post=N_A_post,
                      N_B_pre=N_B_pre, N_B_post=N_B_post),
    )
    with open(os.path.join(OUTD,"after_state.json"),"w",encoding="utf-8") as f:
        json.dump(after_state,f,ensure_ascii=False,indent=1)

    ba=[]
    ba.append("R16-MERGE-SLOTN-B3  BEFORE / AFTER")
    ba.append("="*70)
    for label,b,a in (("coverage.tsv",cov_before,cov_after),("PANEL.md",pan_before,pan_after)):
        ba.append("[%s]" % label)
        ba.append("  BEFORE  mtime=%s  bytes=%d  sha256=%s  lines_nl=%d  eol=%s" %
                  (b["mtime_local"],b["bytes"],b["sha256"],b["lines_nl"],
                   "CRLF=%d LF=%d CR=%d BOM=%s ends_nl=%s"%(b["CRLF"],b["LF"],b["CR"],b["BOM"],b["ends_nl"])))
        ba.append("  AFTER   mtime=%s  bytes=%d  sha256=%s  lines_nl=%d  eol=%s" %
                  (a["mtime_local"],a["bytes"],a["sha256"],a["lines_nl"],
                   "CRLF=%d LF=%d CR=%d BOM=%s ends_nl=%s"%(a["CRLF"],a["LF"],a["CR"],a["BOM"],a["ends_nl"])))
        ba.append("")
    ba.append("[13 行第 4 列 before -> after]")
    for t in targets:
        ba.append("  %s %s" % (t["entry"],t["name"]))
        ba.append("    BEFORE: %s" % t["col4_before"])
        ba.append("    AFTER : %s" % t["col4_after"])
        ba.append("    append(%d B): %s" % (t["added_bytes"],t["append_seg"]))
    ba.append("")
    ba.append("[PANEL M88 插入块（%d 行，插于 M87 块后、M77 锚点前）]" % len(M88_LINES))
    for l in M88_LINES: ba.append("  "+l)
    with open(os.path.join(OUTD,"BEFORE_AFTER.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(ba)+"\n")

    print("MERGE DONE")
    print("coverage bytes %d -> %d sha %s -> %s" %
          (cov_before["bytes"],cov_after["bytes"],cov_before["sha256"][:8],cov_after["sha256"][:8]))
    print("panel    bytes %d -> %d sha %s -> %s" %
          (pan_before["bytes"],pan_after["bytes"],pan_before["sha256"][:8],pan_after["sha256"][:8]))
    print("target_rows=%d strict_prefix=%d other_cols_ok=%d" %
          (len(targets),before_state["strict_prefix_ok"],before_state["other_cols_ok"]))
    print("append §12.6=%d §12.4=%d (no normalization)" % (append_s126,append_s124))
    print("N_pre=%d N_A %d->%d (net +%d) N_B %d->%d (net +%d)" %
          (N_pre,N_A_pre,N_A_post,N_A_post-N_A_pre,N_B_pre,N_B_post,N_B_post-N_B_pre))
    print("pre_circled4_entries=%s" % ",".join(pre_entries))
    print("whole-table s126_lines=%d s126_hits=%d s124_hits=%d" %
          (m_after["s126_lines"],m_after["s126_hits"],m_after["s124_hits"]))
    print("nominal=%s strict=%s strict_rc=%d" % (nominal,strict,r.returncode))
    if r.returncode!=0: print("STRICT STDERR:",r.stderr)

if __name__=="__main__":
    main()
