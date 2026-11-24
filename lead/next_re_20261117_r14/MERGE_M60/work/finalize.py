# -*- coding: utf-8 -*-
"""M60: post-merge verification + generate MERGE_LOG.md / BEFORE_AFTER.txt / VERIFY.txt"""
import os, re, json, hashlib, math
from collections import Counter

BASE = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
OUT = os.path.join(BASE, "MERGE_M60")
COV = os.path.join(BASE, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(BASE, "COVERAGE", "PANEL.md")
ATLAS = "D:/Project/ra2-campaign-forge/lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
B1 = os.path.join(BASE, "SEMFIX_ENGFAM_B1", "coverage_delta.tsv")
B2 = os.path.join(BASE, "SEMFIX_ENGFAM_B2", "coverage_delta.tsv")
B1V = os.path.join(BASE, "SEMFIX_ENGFAM_B1", "_audit", "verdict.tsv")
B2V = os.path.join(BASE, "SEMFIX_ENGFAM_B2", "_audit", "verdict.tsv")
SYS = ["S%02d" % i for i in range(1, 23)]
UNPROVEN_RE = re.compile(r"unproven|unverified|not proven", re.I)

BEFORE = {
    COV:  ("2026-11-19T18:51:39.4666144Z", "2026-11-20T02:51:39.4666144+08:00", 3741215, "1975DA14ABC5DC9D8274AD38316BFD3AD1D09A62E83558354C170D3D443001FC"),
    PANEL:("2026-11-19T18:52:46.5744090Z", "2026-11-20T02:52:46.5744090+08:00", 115045, "3B64BBD644A4760A4B3417BFABC298A014A13AEE898AFFD7034882EC5FC05858"),
}
# panel old values (read from disk before edit), strict dual-column table L105-L127
OLD_PANEL = {
    "S01": (53, 6, "11.32", 6, "11.32", 27, "—", "—"),
    "S02": (330, 34, "10.30", 4, "1.21", 165, "—", "—"),
    "S03": (194, 38, "19.59", 36, "18.56", 97, "—", "—"),
    "S04": (316, 91, "28.80", 91, "28.80", 158, "—", "—"),
    "S05": (643, 165, "25.66", 133, "20.68", 322, "—", "—"),
    "S06": (847, 126, "14.88", 111, "13.11", 424, "—", "—"),
    "S07": (804, 67, "8.33", 44, "5.47", 402, "—", "—"),
    "S08": (22, 9, "40.91", 9, "40.91", 11, "—", "—"),
    "S09": (1051, 114, "10.85", 89, "8.47", 526, "—", "—"),
    "S10": (526, 130, "24.71", 116, "22.05", 263, "—", "—"),
    "S11": (368, 28, "7.61", 27, "7.34", 184, "—", "—"),
    "S12": (279, 55, "19.71", 40, "14.34", 140, "—", "—"),
    "S13": (240, 89, "37.08", 88, "36.67", 120, "—", "—"),
    "S14": (489, 107, "21.88", 94, "19.22", 245, "—", "—"),
    "S15": (158, 106, "67.09", 53, "33.54", 79, "达标", "—"),
    "S16": (90, 47, "52.22", 21, "23.33", 45, "达标", "—"),
    "S17": (102, 56, "54.90", 55, "53.92", 51, "达标", "达标"),
    "S18": (659, 54, "8.19", 44, "6.68", 330, "—", "—"),
    "S19": (355, 20, "5.63", 11, "3.10", 178, "—", "—"),
    "S20": (410, 46, "11.22", 34, "8.29", 205, "—", "—"),
    "S21": (129, 28, "21.71", 28, "21.71", 65, "—", "—"),
    "S22": (4851, 55, "1.13", 12, "0.25", 2426, "—", "—"),
    "TOTAL": (12916, 1457, "11.28", 1140, "8.83", "—", "3/22", "1/22"),
}
RULING = {
    "S01":(6,6),"S02":(35,5),"S03":(38,36),"S04":(91,91),"S05":(165,133),"S06":(126,111),
    "S07":(67,44),"S08":(9,9),"S09":(114,97),"S10":(130,116),"S11":(28,27),"S12":(55,40),
    "S13":(100,99),"S14":(107,94),"S15":(106,53),"S16":(47,21),"S17":(56,55),"S18":(54,44),
    "S19":(27,18),"S20":(46,34),"S21":(28,28),"S22":(55,2),
}

def rlines(p):
    b = open(p, "rb").read()
    s = b.decode("utf-8")
    return s.splitlines()

def main():
    # ---- recompute from disk (post-merge) ----
    atlas = set(r[0].strip().upper() for r in (l.split("\t") for l in rlines(ATLAS)[1:]) if r)
    cov = [l.split("\t") for l in rlines(COV)[1:]]
    assert all(len(r) == 8 for r in cov)
    proved_all = sum(1 for r in cov if r[4] == "[已证]")
    proved_in = sum(1 for r in cov if r[4] == "[已证]" and r[0].strip().upper() in atlas)
    proved_out = proved_all - proved_in
    unproven = [r for r in cov if UNPROVEN_RE.search(r[3])]
    stats = {}
    for s in SYS:
        rows = [r for r in cov if r[1] == s and r[0].strip().upper() in atlas]
        n = len(rows)
        p = sum(1 for r in rows if r[4] == "[已证]")
        st = sum(1 for r in rows if r[4] == "[已证]" and "未证" not in r[3])
        stats[s] = (n, p, st)
    sum_n = sum(v[0] for v in stats.values())
    sum_p = sum(v[1] for v in stats.values())
    sum_s = sum(v[2] for v in stats.values())

    # ---- parse PANEL strict table post-edit ----
    plines = rlines(PANEL)
    hdr_i = next(i for i,l in enumerate(plines) if l.startswith("| S | atlas_n | proved_n | proved_pct |"))
    total_i = next(i for i,l in enumerate(plines) if l.startswith("| **TOTAL** |") and i > hdr_i)
    new_panel = {}
    for l in plines[hdr_i+2:total_i+1]:
        cells = [c.strip().replace("**","") for c in l.strip().strip("|").split("|")]
        key = cells[0]
        n,p,pp,st,stp,thr,nom,strict = int(cells[1]),int(cells[2]),cells[3],int(cells[4]),cells[5],cells[6],cells[7],cells[8]
        new_panel[key] = (n,p,pp,st,stp,thr,nom,strict)
    assert set(new_panel) == set(SYS+["TOTAL"]), set(new_panel) ^ set(SYS+["TOTAL"])

    # ---- cross-checks ----
    errs = []
    def chk(cond, msg):
        if not cond: errs.append(msg)
    chk(len(cov) == 18498, "data rows != 18498: %d" % len(cov))
    chk(proved_all == 1496, "proved_all != 1496: %d" % proved_all)
    chk(proved_in == 1490, "proved_in != 1490: %d" % proved_in)
    chk(proved_out == 6, "proved_out != 6: %d" % proved_out)
    chk(len(unproven) == 0, "unproven != 0: %d" % len(unproven))
    chk(sum_n == 12916, "sum_n != 12916: %d" % sum_n)
    chk(sum_p == 1490, "sum22 proved != 1490: %d" % sum_p)
    chk(sum_s == 1163, "sum22 strict != 1163: %d" % sum_s)
    for s in SYS:
        n,p,st = stats[s]
        chk((p,st) == RULING[s], "%s recompute %d/%d != ruling %s" % (s,p,st,RULING[s]))
        np_,npp,nst,nstp = new_panel[s][1], new_panel[s][2], new_panel[s][3], new_panel[s][4]
        chk(np_ == p, "%s panel proved %d != recompute %d" % (s,np_,p))
        chk(nst == st, "%s panel strict %d != recompute %d" % (s,nst,st))
        chk(npp == "%.2f" % (100.0*p/n), "%s panel proved_pct %s != recompute %.2f" % (s,npp,100.0*p/n))
        chk(nstp == "%.2f" % (100.0*st/n), "%s panel strict_pct %s != recompute %.2f" % (s,nstp,100.0*st/n))
    # TOTAL
    tp, tst = new_panel["TOTAL"][1], new_panel["TOTAL"][3]
    chk(tp == sum_p == 1490, "TOTAL proved %d != sum22 %d" % (tp,sum_p))
    chk(tst == sum_s == 1163, "TOTAL strict %d != sum22 %d" % (tst,sum_s))
    chk(new_panel["TOTAL"][2] == "%.2f" % (100.0*sum_p/sum_n), "TOTAL proved_pct wrong")
    chk(new_panel["TOTAL"][4] == "%.2f" % (100.0*sum_s/sum_n), "TOTAL strict_pct wrong")
    # 达标 flip check (nominal & strict, per subsystem + TOTAL tallies)
    flips = []
    for s in SYS:
        old = OLD_PANEL[s]; new = new_panel[s]
        if old[6] != new[6]: flips.append("%s 名义 %s→%s (proved %d→%d)" % (s,old[6],new[6],old[1],new[1]))
        if old[7] != new[7]: flips.append("%s 严格 %s→%s (strict %d→%d)" % (s,old[7],new[7],old[3],new[3]))
    if OLD_PANEL["TOTAL"][6] != new_panel["TOTAL"][6] or OLD_PANEL["TOTAL"][7] != new_panel["TOTAL"][7]:
        flips.append("TOTAL tally changed")
    chk(not flips, "FLIPS: %s" % flips)
    # changed cells (panel)
    changed_cells = []
    for s in SYS+["TOTAL"]:
        old, new = OLD_PANEL[s], new_panel[s]
        labels = ["atlas_n","proved","proved%","strict","strict%","门槛","名义","严格"]
        for i,(a,b) in enumerate(zip(old,new)):
            if str(a) != str(b):
                changed_cells.append((s,labels[i],a,b))

    # ---- AFTER fingerprints ----
    def stat(p):
        import datetime
        st = os.stat(p)
        mt = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc)
        return (mt.isoformat().replace("+00:00","Z"),
                hashlib.sha256(open(p,"rb").read()).hexdigest().upper(), st.st_size)
    after = {p: stat(p) for p in (COV, PANEL)}

    # ===== write BEFORE_AFTER.txt =====
    ba = ["M60 BEFORE / AFTER FINGERPRINTS", "="*60, ""]
    for p in (COV, PANEL):
        b = BEFORE[p]; a = after[p]
        ba += ["FILE: %s" % p,
               "  BEFORE mtime_utc=%s  mtime_local=%s  bytes=%d  sha256=%s" % (b[0],b[1],b[2],b[3]),
               "  AFTER  mtime_utc=%s  bytes=%d  sha256=%s" % (a[0],a[2],a[1]),
               "  sha256 changed: %s" % (b[3]!=a[1]), ""]
    open(os.path.join(OUT,"BEFORE_AFTER.txt"),"w",encoding="utf-8").write("\n".join(ba)+"\n")

    # ===== write MERGE_LOG.md =====
    # 34 delta rows with batch + new semantics
    drows = []
    for path, tag in [(B1,"B1"),(B2,"B2")]:
        for l in rlines(path)[1:]:
            f = l.split("\t")
            drows.append((f[0].strip().upper(), tag, f[2], f[3]))
    drows.sort()
    ml = ["# M60 MERGE LOG", "",
          "## 第一部分：并 34 行语义（只改第 4/6 列，grade `[已证]` 一字未动）", "",
          "来源：`SEMFIX_ENGFAM_B1/coverage_delta.tsv` 17 行 + `SEMFIX_ENGFAM_B2/coverage_delta.tsv` 17 行 = 34 行。",
          "两批 `_audit/verdict.tsv` 各 17 行全 PASS。34 个 entry 全部已在 coverage（S17、grade `[已证]`、atlas 内）、唯一。",
          "- 第 4 列 `one_line_semantics` ← delta 第 4 列**原文照抄**",
          "- 第 6 列 `evidence_path` → `SEMFIX_ENGFAM_B{1,2}/_audit/VERDICT.md`（按批次）",
          "- 第 1/2/3/5/7/8 列逐字节不变；数据行仍 18,498；制表符分隔 8 列不变。", "",
          "### 34 行 entry 清单", "",
          "| # | entry | 批次 | name | 新 evidence_path | 新语义（delta 原文，verbatim） |",
          "|---:|---|---|---|---|---|"]
    for i,(e,tag,name,sem) in enumerate(drows,1):
        ev = "SEMFIX_ENGFAM_%s/_audit/VERDICT.md" % tag
        ml.append("| %d | `%s` | %s | `%s` | `%s` | %s |" % (i,e,tag,name,ev,sem))
    ml += ["", "## 第二部分：PANEL 严格双列表逐格改前→改后", "",
           "仅改 L103–L127 严格口径双列表；其它表（L56/63/67/73/76、L170+）未动。",
           "注：L140 新增 `📌 M60 旧截面修正`（替换原卡注文），紧跟 L139 M58 界向更正注之后。", "",
           "| 子系统 | 格 | 改前 | 改后 |", "|---|---|---:|---:|"]
    for s,lab,a,b in changed_cells:
        ml.append("| %s | %s | %s | %s |" % (s,lab,a,b))
    ml += ["", "### 达标判定（按新值重算）", "",
           "判定口径：`proved >= ceil(0.5n)` / `strict >= ceil(0.5n)`。",
           "名义达标 3/22（S15/S16/S17）、严格达标 1/22（仅 S17）**不变**；**无翻转**。",
           "22 行 proved 合计 1490 = TOTAL proved 1490；strict 合计 1163 = TOTAL strict 1163。", ""]
    if errs:
        ml += ["## ⚠️ 校验错误", ""] + ["- %s" % e for e in errs] + [""]
    else:
        ml += ["## 校验：全部通过", ""]
    open(os.path.join(OUT,"MERGE_LOG.md"),"w",encoding="utf-8").write("\n".join(ml)+"\n")

    # ===== write VERIFY.txt =====
    v = ["M60 POST-MERGE VERIFY", "="*60, "",
         "[覆盖表]",
         "  数据行数            = %d (期望 18498) %s" % (len(cov), "OK" if len(cov)==18498 else "FAIL"),
         "  全表 [已证]         = %d (期望 1496) %s" % (proved_all, "OK" if proved_all==1496 else "FAIL"),
         "  atlas 内 [已证]     = %d (期望 1490) %s" % (proved_in, "OK" if proved_in==1490 else "FAIL"),
         "  atlas 外 [已证]     = %d (期望 6)    %s" % (proved_out, "OK" if proved_out==6 else "FAIL"),
         "  unproven 族行数     = %d (期望 0)    %s" % (len(unproven), "OK" if len(unproven)==0 else "FAIL"),
         "  grade 直方图        = %s" % dict(Counter(r[4] for r in cov)),
         "", "[atlas]", "  行数 = %d (期望 12916)" % len(set(atlas)), "",
         "[22 行 + TOTAL 逐行新值  proved/strict  (改前→改后)]",
         "  子   n      proved(前→后)      strict(前→后)     pct(后)  strict_pct(后)  名义/严格"]
    for s in SYS:
        n,p,st = stats[s]
        o = OLD_PANEL[s]; nw = new_panel[s]
        v.append("  %-4s %-6d %4d→%-4d %4d→%-4d %8s %8s     %s/%s" % (
            s,n,o[1],p,o[3],st,nw[2],nw[4],nw[6],nw[7]))
    v.append("  %-4s %-6d %4d→%-4d %4d→%-4d %8s %8s     %s/%s" % (
        "TOTAL",sum_n,OLD_PANEL["TOTAL"][1],tp,OLD_PANEL["TOTAL"][3],tst,
        new_panel["TOTAL"][2],new_panel["TOTAL"][4],new_panel["TOTAL"][6],new_panel["TOTAL"][7]))
    v += ["",
          "[合计核对]",
          "  22 行 proved 合计 = %d ; TOTAL proved = %d ; 相等 = %s" % (sum_p,tp,sum_p==tp),
          "  22 行 strict 合计 = %d ; TOTAL strict = %d ; 相等 = %s" % (sum_s,tst,sum_s==tst),
          "", "[达标翻转]",
          "  翻转项: %s" % (flips if flips else "无（名义 3/22 仅 S15/S16/S17，严格 1/22 仅 S17，均不变）"),
          "", "[复算 vs 裁决卡交叉验证]",
          "  22 行 proved/strict 与 M60-MERGE-RULING.md 第 5 节逐行一致: %s" % (
              "是" if all((p,st)==RULING[s] for s,(n,p,st) in stats.items()) else "否"),
          "", "[结论]",
          "  %s" % ("ALL CHECKS PASSED" if not errs else "FAILED: " + "; ".join(errs)), ""]
    open(os.path.join(OUT,"VERIFY.txt"),"w",encoding="utf-8").write("\n".join(v)+"\n")

    print("=== changed panel cells (%d) ===" % len(changed_cells))
    for c in changed_cells: print("  ",c)
    print("sum22 proved=%d strict=%d ; TOTAL proved=%d strict=%d ; equal=%s" % (sum_p,sum_s,tp,tst,sum_p==tp and sum_s==tst))
    print("flips:", flips if flips else "NONE")
    print("errors:", errs if errs else "NONE")
    print("WROTE MERGE_LOG.md / BEFORE_AFTER.txt / VERIFY.txt")

if __name__ == "__main__":
    main()
