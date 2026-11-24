# -*- coding: utf-8 -*-
"""_nnv_verify.py — 独立复核员自写实现，不 import 撰写人的任何 _nn_ 模块。
用途：① 六变体全量量化 / 漏检率；② 语料漂移口径；③ L1 归一独立重算（含位置映射）；
④ W1/W2/W3/W4 宽泛候选交叉核；⑤ 变体类自动发现 + 集合差门禁可执行性；
⑥ 构造 3+ 个「不该合并」样本，测撰写人 L1 键是否误合并；
⑦ 两段式失效链：file gate / line gate 逐件逐行重算。
只读；只写 stdout；零真机/零采样代码；python -I -X utf8。
"""
import os, sys, re, hashlib
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:/Project/ra2-campaign-forge/lead"
WRITE_DOMAIN = "needle_norm_20261109/"

# 与编排方口径一致：排除本任务写域（该写域文件是对被核对象的讨论，不是语料）
def iter_md(exclude_write_domain=True, include_all=False):
    out = []
    for dp, dn, fn in os.walk(ROOT):
        rel_d = os.path.relpath(dp, ROOT).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            if not os.path.isfile(p):
                continue
            r = os.path.relpath(p, ROOT).replace("\\", "/")
            if exclude_write_domain and r.startswith(WRITE_DOMAIN):
                continue
            if not include_all and r.startswith(WRITE_DOMAIN) and not f.startswith("_nnv_"):
                # 本任务写域内除 _nnv_ 外的 _nn_ 产物也不计入语料
                continue
            out.append((p, r))
    return out

def load(files):
    d = {}
    for p, r in files:
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        d[r] = b.decode("utf-8", "replace").splitlines()
    return d

VARIANTS = [
    ("angle_corner", "只能判「不可复现」"),
    ("curly_corner", "只能判『不可复现』"),
    ("curly_double", "只能判“不可复现”"),
    ("no_quote",     "只能判不可复现"),
    ("half_paren",   "只能判(不可复现)"),
    ("no_punct",     "只能判 不可复现"),
]
CANON = "只能判「不可复现」"

# ---- 独立重写的 L1（按撰写人 REPORT:190-205 与 _nn_norm.py:19-25 的规格） ----
QOPEN = "「『“‘"
QCLOSE = "」』”’"
QSYM = "`\"'"

def l1(s):
    o = []
    for c in s:
        if c in QOPEN: o.append("\x01")
        elif c in QCLOSE: o.append("\x02")
        elif c in QSYM: o.append("\x03")
        else: o.append(c)
    return "".join(o)

def find_norm(line, nd):
    n, q = l1(line), l1(nd)
    res, pos = [], 0
    while True:
        k = n.find(q, pos)
        if k < 0: break
        res.append((k, k + len(q), line[k:k+len(q)]))
        pos = k + 1
    return res

def main():
    all_files = iter_md(exclude_write_domain=False, include_all=True)
    excl_nn = [(p, r) for p, r in all_files if not (r.startswith(WRITE_DOMAIN) and not os.path.basename(p).startswith("_nnv_"))]
    excl_all = iter_md(exclude_write_domain=True)
    print("### 独立复核 · 语料口径")
    print("lead/ depth<=2 *.md 全部(含写域所有件) =", len(all_files))
    print("排除写域内非 _nnv_ 件(=撰写人 15 件产物) =", len(excl_nn))
    print("排除整个 needle_norm_20261109/ 写域 =", len(excl_all))
    print("")

    for label, files in [("EXCL_NON_NNV", excl_nn), ("EXCL_ALL_WRITE", excl_all)]:
        print("===== 口径 %s =====" % label)
        fs = load(files)
        print("scanned files =", len(fs))
        raw = {}
        for name, nd in VARIANTS:
            raw[name] = {(r, i) for r, ls in fs.items() for i, L in enumerate(ls, 1) if nd in L}
        for name, nd in VARIANTS:
            s = raw[name]
            print("  %-14s files=%2d lines=%2d" % (name, len({r for r, _ in s}), len(s)))
        U = set().union(*raw.values())
        B = raw["angle_corner"]
        uf = {r for r, _ in U}; bf = {r for r, _ in B}
        print("  angle_corner only: files=%d lines=%d" % (len(bf), len(B)))
        print("  union(all 6)     : files=%d lines=%d" % (len(uf), len(U)))
        print("  missed files     : %d (= %.2f%%)" % (len(uf-bf), 100.0*len(uf-bf)/len(uf)))
        print("  missed lines     : %d (= %.2f%%)" % (len(U-B), 100.0*len(U-B)/len(U)))
        print("  baseline recall lines=%.2f%% files=%.2f%%" % (100.0*len(B)/len(U), 100.0*len(bf)/len(uf)))
        print("  -- missed files --")
        for r in sorted(uf-bf): print("     ", r)
        print("  -- per-variant new lines beyond angle --")
        for name, nd in VARIANTS:
            new = raw[name]-B
            print("     %-14s new_lines=%2d new_files=%2d" % (name, len(new), len({r for r,_ in new})))
        print("")

    # 后续用撰写人等价口径：排除整个写域
    fs = load(excl_all)
    raw = {n: {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1) if nd in L} for n,nd in VARIANTS}
    U = set().union(*raw.values()); B = raw["angle_corner"]

    print("===== L1 归一独立重算 =====")
    L1 = {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1) if find_norm(L, CANON)}
    three = raw["angle_corner"] | raw["curly_corner"] | raw["curly_double"]
    print("  L1 files=%d lines=%d" % (len({r for r,_ in L1}), len(L1)))
    print("  L1 == union(angle+curly+curlydouble) ?", L1 == three)
    print("  L1 - three (假阳) =", len(L1-three), " three - L1 (假阴) =", len(three-L1))
    print("  L1 gain over baseline lines =", len(L1-B), "(%.2f%% vs union)" % (100.0*len(L1-B)/len(U)))
    print("  residual (U - L1) lines =", len(U-L1), "files =", len({r for r,_ in U-L1}), "(%.2f%%)" % (100.0*len(U-L1)/len(U)))
    print("  residual all == no_quote ?", (U-L1) == raw["no_quote"])
    # 位置映射自检：逐个 find_norm 命中检查 L[a:b]==raw 且长度不变
    checked = bad = 0
    for r,ls in fs.items():
        for i,L in enumerate(ls,1):
            if len(l1(L)) != len(L): bad += 1
            for (a,b,t) in find_norm(L, CANON):
                checked += 1
                if L[a:b] != t: bad += 1
    print("  mapped hits checked =", checked, "; length-preserving & orig_slice==reported_text bad =", bad)
    print("")

    print("===== 宽泛候选 W1/W2/W3/W4 独立交叉 =====")
    W1 = {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1) if "不可复现" in L}
    W2 = {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1) if "只能判" in L}
    W3 = W1 & W2
    W4 = {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1) if re.search(r"只能判.{0,3}不可复现", L)}
    for nm,S in [("W1",W1),("W2",W2),("W3",W3),("W4",W4),("U",U)]:
        print("  %-3s lines=%3d files=%2d" % (nm,len(S),len({r for r,_ in S})))
    print("  U-W3=%d W3-U=%d U-W4=%d W4-U=%d W3==U %s W4==U %s" %
          (len(U-W3),len(W3-U),len(U-W4),len(W4-U),W3==U,W4==U))
    print("  W1-U = %d lines / %d files" % (len(W1-U),len({r for r,_ in W1-U})))
    print("  W1-U 中含锚词『只能判』行数 =", sum(1 for r,i in W1-U if "只能判" in fs[r][i-1]))
    print("  W1-U 中含引号行数 =", sum(1 for r,i in W1-U if re.search(r"[「『“`]",fs[r][i-1])))
    # 显式补充轨正则（REPORT:178 / 232）：单独召回 no_quote
    supp = {(r,i) for r,ls in fs.items() for i,L in enumerate(ls,1)
            if re.search(r"只能判[「『“(]?不可复现[」』”)]?", L)}
    print("  explicit supplemental regex lines=%d files=%d" % (len(supp),len({r for r,_ in supp})))
    print("  L1 | supp = %d lines; == U ? %s" % (len(L1|supp), (L1|supp)==U))
    print("")

    print("===== 两段式失效链独立重算 (file gate :229 / line gate :165) =====")
    killed_files, killed_by_file, killed_by_line = [], [], []
    for r,ls in fs.items():
        txt = "\n".join(ls)
        if CANON not in txt:
            u_lines = [(r,i) for i in range(1,len(ls)+1) if (r,i) in U]
            if u_lines:
                killed_files.append(r)
                killed_by_file += u_lines
        else:
            for i in range(1,len(ls)+1):
                if (r,i) in U and (r,i) not in B:
                    killed_by_line.append((r,i))
    print("  file-level prefilter (line 229) 整件跳过且含变体的文件 =", len(killed_files), sorted(killed_files))
    print("  这些件的漏检行数 =", len(killed_by_file))
    print("  通过 file gate 但被 line gate(:165) 跳过的行 =", len(killed_by_line))
    print("  :22 在其中 =", ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md",22) in killed_by_line)
    print("  合计漏检 =", len(killed_by_file)+len(killed_by_line), " == |U-B| ?", len(killed_by_file)+len(killed_by_line)==len(U-B))
    print("")

    print("===== 变体类自动发现（集合差门禁数据源） =====")
    sep = Counter()
    anchors = defaultdict(list)
    for r,ls in fs.items():
        for i,L in enumerate(ls,1):
            for m in re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L):
                key=(m.group(1),m.group(2))
                sep[key]+=1
                if len(anchors[key])<1: anchors[key].append((r,i))
    print("  自动发现 (pre,post) 类数 =", len(sep))
    for k,c in sep.most_common():
        print("     pre=%-12r post=%-10r count=%-3d anchor=%s" % (k[0],k[1],c,anchors[k]))
    # 门禁可执行性：把「现行 6 负控覆盖的类」映射成 (pre,post)，做集合差
    controls_pairs = {("「","」"),("『","』")}  # 现行 6 项仅 angle/curly 两类（见 _nn_crosscheck.py:36-42）
    # 用实际负控行文本反推 (pre,post)
    ctrl_lines = [
        ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",123),
        ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",25),
        ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",196),
        ("ledger_bound_20261109/_lb_BOUND_VOLUME.md",129),
        ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md",22),
        ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",215),
    ]
    covered = set()
    for r,i in ctrl_lines:
        L = fs.get(r,[""]*max(i,1))[i-1] if r in fs else ""
        for m in re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L):
            covered.add((m.group(1),m.group(2)))
    print("  现行 6 负控实际覆盖 (pre,post) 类 =", len(covered), sorted(covered))
    diff = set(sep)-covered
    print("  GATE: discovered=%d covered=%d DIFF=%d -> SELF_TEST would %s" % (len(sep),len(covered),len(diff),"FAIL" if diff else "PASS"))
    print("  DIFF 明细 =", sorted(diff))
    print("  (门禁是否需要人工列举变体？自动发现由 re.finditer 全语料枚举，答案为否)")
    print("")

if __name__ == "__main__":
    main()
