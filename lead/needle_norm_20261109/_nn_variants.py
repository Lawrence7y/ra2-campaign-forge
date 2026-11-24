# -*- coding: utf-8 -*-
"""_nn_variants.py — 六变体全量独立核对（只读，stdout 打印）。
口径：lead/ 下 depth<=2 的全部 .md，逐行逐 needle 精确子串匹配；
记录 (file, line) 命中集合，输出按变体的文件数/行数、并集/差集、
同一文件多变体共现、同一行多变体共现、以及归一化覆盖评估。
只读；不写任何文件；零真机/零采样代码；hashlib 仅用于输出指纹自检。
"""
import os, sys, hashlib, json
from collections import defaultdict, Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:/Project/ra2-campaign-forge/lead"
MAXDEPTH = 2
EXT = ".md"

VARIANTS = [
    ("angle_corner", "只能判「不可复现」"),
    ("curly_corner", "只能判『不可复现』"),
    ("curly_double", "只能判“不可复现”"),
    ("no_quote",     "只能判不可复现"),
    ("half_paren",   "只能判(不可复现)"),
    ("no_punct",     "只能判 不可复现"),
]
# 编排方给定 6 变体清单（含 detail 的文件/行），用于逐条核对
ORCH = {
 "angle_corner": {"files":18, "detail":[("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",[123,215]),("lead/ledger_appendix_20261108/_lad_tpl.md",[151]),("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",[25]),("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",[196]),("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",[129]),("lead/minhard_check_20261109/MINHARD_SET_CHECK.md",[34,75,94,164,214]),("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md",[49,66,125,196,197,206]),("lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",[17,251,293])]},
 "curly_corner": {"files":16, "detail":[("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",[179,270,288]),("lead/ledger_bound_20261109/_lb2_TEMPLATE.md",[152,202]),("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",[112,201]),("lead/minhard_check_20261109/MINHARD_SET_CHECK.md",[79]),("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md",[52]),("lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",[17,295,358]),("lead/refsync_scope_20261109/_rs_CARRIER_MAP.md",[60,188,275]),("lead/s604_attribution_20261108/S604_ATTRIBUTION.md",[138])]},
 "curly_double": {"files":0, "detail":[]},
 "no_quote": {"files":7, "detail":[("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",[226]),("lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md",[137,143]),("lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",[46,50]),("lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md",[148]),("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",[56]),("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",[54]),("lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",[153])]},
 "half_paren": {"files":0, "detail":[]},
 "no_punct": {"files":0, "detail":[]},
}

def iter_files(root, maxdepth):
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace("\\", "/")
        depth = 0 if rel == "." else rel.count("/") + 1
        if depth > maxdepth:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(EXT):
                continue
            p = os.path.join(dp, f)
            if os.path.isfile(p):
                r = os.path.relpath(p, root).replace("\\", "/")
                if r.startswith("needle_norm_20261109/"):
                    continue   # 排除本任务写域，冻结到编排方 631 件口径
                yield p, r, depth

def main():
    files = list(iter_files(ROOT, MAXDEPTH))
    print("### 六变体全量独立核对 (lead/ depth<=2 all %s)" % EXT)
    print("scanned files = %d" % len(files))
    print("")
    hits = {}          # name -> set (rel, lineno)
    hits_by_file = {}  # name -> {rel: [lines]}
    lines_cache = {}
    for p, rel, depth in files:
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        txt = b.decode("utf-8", "replace")
        lines_cache[rel] = txt.splitlines()
        for name, nd in VARIANTS:
            hits.setdefault(name, set())
            for i, L in enumerate(lines_cache[rel], 1):
                if nd in L:
                    hits[name].add((rel, i))
    for name, _ in VARIANTS:
        d = defaultdict(list)
        for rel, i in sorted(hits[name]):
            d[rel].append(i)
        hits_by_file[name] = dict(d)

    print("=== A. 各变体命中文件数 / 行数 ===")
    for name, nd in VARIANTS:
        fs = hits_by_file[name]
        print("  %-14s needle=%-22s files=%3d lines=%3d" %
              (name, repr(nd), len(fs), len(hits[name])))

    print("")
    print("=== B. 逐变体明细（每个文件每一行）与编排方 detail 逐条核对 ===")
    all_ok = True
    for name, nd in VARIANTS:
        fs = hits_by_file[name]
        print("  -- %s (%s) --" % (name, repr(nd)))
        for rel in sorted(fs):
            print("     %s lines=%s" % (rel, fs[rel]))
        o = ORCH[name]
        # 编排方给的是 detail 片段（angle/curly 只列了 8 个文件，但 files=18/16）
        # 先核 files 总数，再核 detail 中每个 (file,line) 是否都在本会话命中集合内
        cnt_ok = (len(fs) == o["files"])
        det_ok = True
        for rel, lns in o["detail"]:
            # 编排方 rel 带 lead/ 前缀，本会话 rel 相对 lead/ 根
            short = rel[len("lead/"):] if rel.startswith("lead/") else rel
            for ln in lns:
                if (short, ln) not in hits[name]:
                    det_ok = False
                    print("     !! MISMATCH detail %s:%d NOT in my hits" % (rel, ln))
        good = cnt_ok and det_ok
        all_ok &= good
        print("     orch files=%d my files=%d => %s ; detail %d/%d anchors %s ; VERDICT=%s" %
              (o["files"], len(fs), "MATCH" if cnt_ok else "DIFF",
               sum(len(x[1]) for x in o["detail"]),
               sum(len(x[1]) for x in o["detail"]),
               "all present" if det_ok else "MISSING",
               "MATCH" if good else "DIFF"))
    print("  ORCH_VERIFY_ALL = %s" % ("MATCH" if all_ok else "DIFF"))

    print("")
    print("=== C. 并集 / 差集（漏检量化） ===")
    u = set().union(*[hits[n] for n, _ in VARIANTS])
    uf = {rel for rel, _ in u}
    base = hits["angle_corner"]
    bf = {rel for rel, _ in base}
    print("  angle_corner only: files=%d lines=%d" % (len(bf), len(base)))
    print("  union(all 6)     : files=%d lines=%d" % (len(uf), len(u)))
    print("  missed files     : %d (= %.2f%% of union)" % (len(uf - bf), 100.0*len(uf-bf)/len(uf)))
    print("  missed lines     : %d (= %.2f%% of union)" % (len(u - base), 100.0*len(u-base)/len(u)))
    print("  -- missed files list --")
    for rel in sorted(uf - bf):
        print("     %s lines=%s" % (rel, sorted(i for r,i in u if r==rel)))
    print("  -- missed lines list (file:line -> which variant) --")
    for rel, i in sorted(u - base):
        who = [n for n, _ in VARIANTS if (rel,i) in hits[n]]
        print("     %s:%d <- %s" % (rel, i, ",".join(who)))
    print("  -- per-variant NEW hits beyond angle_corner --")
    for name, _ in VARIANTS:
        new = hits[name] - base
        print("     %-14s new_lines=%2d new_files=%2d" % (name, len(new), len({r for r,_ in new})))

    print("")
    print("=== D. 共现 / 去重 ===")
    # 同一文件被多个变体命中
    f2v = defaultdict(set)
    for rel, i in u:
        for n, _ in VARIANTS:
            if (rel,i) in hits[n]:
                f2v[rel].add(n)
    multi_f = {r:v for r,v in f2v.items() if len(v)>1}
    print("  files hit by >1 variant = %d" % len(multi_f))
    for r in sorted(multi_f):
        print("     %s <- %s" % (r, sorted(multi_f[r])))
    # 同一 (file,line) 被多个变体命中（真正重复计数）
    # 注意：一个行内可能同时含两个变体字面串，或同一变体多次出现
    l2v = defaultdict(set)
    for rel, i in u:
        for n, _ in VARIANTS:
            if (rel,i) in hits[n]:
                l2v[(rel,i)].add(n)
    multi_l = {k:v for k,v in l2v.items() if len(v)>1}
    print("  (file,line) hit by >1 variant = %d" % len(multi_l))
    for (r,i),v in sorted(multi_l.items()):
        print("     %s:%d <- %s" % (r,i,sorted(v)))
        L = lines_cache[r][i-1]
        for n, nd in VARIANTS:
            if n in v:
                print("        %-14s offsets=%s" % (n, [j for j in range(len(L)) if L.startswith(nd,j)]))
    # 行内多次出现的字面串（同一变体内重复）
    print("  -- lines with >1 occurrence of SAME variant --")
    for name, nd in VARIANTS:
        for rel, i in sorted(hits[name]):
            L = lines_cache[rel][i-1]
            c = L.count(nd)
            if c > 1:
                print("     %s:%d %s x%d" % (rel,i,name,c))
    print("")
    print("=== E. 引号内/外语义 & 词面变体（反例素材探查，只读） ===")
    # 找含 "不可复现" 但不属于 6 变体的行（用于评估宽泛捞候选噪声）
    import re
    broad = re.compile(r"不可复现")
    only_broad = []
    for rel, ls in lines_cache.items():
        for i, L in enumerate(ls, 1):
            if broad.search(L):
                if not any((rel,i) in hits[n] for n,_ in VARIANTS):
                    only_broad.append((rel,i,L))
    print("  lines containing 不可复现 but NOT ANY of 6 variants = %d ; distinct files=%d" %
          (len(only_broad), len({r for r,_,_ in only_broad})))
    print("  -- first 40 (for noise assessment) --")
    for r,i,L in only_broad[:40]:
        print("     %s:%d %s" % (r,i,L.strip()[:180]))
    # 宽泛候选：只含 不可复现 或 只能判 的行总量
    b1 = [(r,i) for r,ls in lines_cache.items() for i,L in enumerate(ls,1) if "不可复现" in L]
    b2 = [(r,i) for r,ls in lines_cache.items() for i,L in enumerate(ls,1) if "只能判" in L]
    print("  broad('不可复现') lines=%d files=%d" % (len(b1), len({r for r,_ in b1})))
    print("  broad('只能判')   lines=%d files=%d" % (len(b2), len({r for r,_ in b2})))
    print("  broad('不可复现') minus union(all6) lines=%d files=%d" %
          (len(set(b1)-u), len({r for r,_ in set(b1)-u})))
    print("")
    print("=== F. 词面混淆反例词频（不可复原 / 不可重复 / 不可再现 等） ===")
    for w in ["不可复原","不可重复","不可再现","不可复现","不能定位当年错误步骤","只能判"]:
        c = sum(L.count(w) for ls in lines_cache.values() for L in ls)
        f = sum(1 for ls in lines_cache.values() for L in ls if w in L)
        print("  %-14s total_lines=%4d total_occurrences=%4d" % (w, f, c))

if __name__ == "__main__":
    main()
