# -*- coding: utf-8 -*-
"""_nn_norm.py — 归一化原型（只读）+ 两段式失效量化 + 边界反例验证。
只写 stdout；不修改任何既有件；零真机/零采样代码。
归一化只用于「召回」，角色判定一律回到原文行上做。
"""
import os, sys, re, unicodedata
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:/Project/ra2-campaign-forge/lead"
MAXDEPTH = 2
EXT = ".md"

# ---------- 归一化（L1：仅引号类归一，1:1 保长，带位置映射） ----------
OPEN_Q  = "\x01"   # 私有哨兵：所有左引号
CLOSE_Q = "\x02"   # 私有哨兵：所有右引号
SYM_Q   = "\x03"   # 私有哨兵：成对反引号 / 直双引号

QUOTE_OPEN  = "「『“‘"
QUOTE_CLOSE = "」』”’"
SYMMETRIC   = "`\"'"

def normalize_line(s):
    """返回 (norm, idx_map, orig_delims)。
    norm 与 s 等长（1:1），idx_map[j] = 原文下标 j；orig_delims[j] = 原引号字符（非引号为 None）。
    只替换引号类字符，其它码位一律原样保留 —— 故位置恒等映射，绝不漂移。
    """
    out, idx, dels = [], [], []
    for j, c in enumerate(s):
        if c in QUOTE_OPEN:
            out.append(OPEN_Q); dels.append(c)
        elif c in QUOTE_CLOSE:
            out.append(CLOSE_Q); dels.append(c)
        elif c in SYMMETRIC:
            out.append(SYM_Q); dels.append(c)
        else:
            out.append(c); dels.append(None)
        idx.append(j)
    return "".join(out), idx, dels

def norm_needle(nd):
    n, _, _ = normalize_line(nd)
    return n

def find_norm(line, nd):
    """在归一化后的行里找归一化 needle；把命中位置映射回原文偏移。
    返回 [(orig_start, orig_end, matched_original_text, norm_offset)]
    """
    n, idx, _ = normalize_line(line)
    q = norm_needle(nd)
    res = []
    pos = 0
    while True:
        k = n.find(q, pos)
        if k < 0:
            break
        a, b = idx[k], idx[k + len(q) - 1] + 1
        res.append((a, b, line[a:b], k))
        pos = k + 1
    return res

# ---------- 语料 ----------
def iter_files():
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        depth = 0 if rel == "." else rel.count("/") + 1
        if depth > MAXDEPTH:
            dn[:] = []
            continue
        for f in sorted(fn):
            if f.lower().endswith(EXT):
                p = os.path.join(dp, f)
                if os.path.isfile(p):
                    rel = os.path.relpath(p, ROOT).replace("\\", "/")
                    if rel.startswith("needle_norm_20261109/"):
                        continue   # 排除本任务写域，冻结到编排方 631 件口径
                    yield p, rel

VARIANTS = [
    ("angle_corner", "只能判「不可复现」"),
    ("curly_corner", "只能判『不可复现』"),
    ("curly_double", "只能判“不可复现”"),
    ("no_quote",     "只能判不可复现"),
    ("half_paren",   "只能判(不可复现)"),
    ("no_punct",     "只能判 不可复现"),
]
CANON = "只能判「不可复现」"

def main():
    files = {}
    for p, rel in iter_files():
        b = open(p, "rb").read()
        if b"\x00" in b:
            continue
        files[rel] = b.decode("utf-8", "replace").splitlines()
    print("### 归一化原型 / 漏检量化 / 边界反例")
    print("corpus: lead/ depth<=2 *.md ; scanned files = %d" % len(files))
    print("")

    print("=== 1. 归一化键：6 变体各归到哪个键（覆盖类判定） ===")
    for name, nd in VARIANTS:
        print("  %-14s %-22s -> key=%r  covered_by_L1=%s" %
              (name, repr(nd), norm_needle(CANON) if False else norm_needle(nd),
               norm_needle(nd) == norm_needle(CANON)))
    print("  canonical key = %r" % norm_needle(CANON))
    print("  => L1(仅引号归一) 覆盖 3/6 变体；另 3 类属于「去引号 / 换括注 / 插空白」，")
    print("     不是引号变体，不得由 L1 强行归一（见第 5 节反例）。")
    print("")

    # 原始 6 变体集合（逐行精确子串）
    raw = defaultdict(set)
    for rel, ls in files.items():
        for i, L in enumerate(ls, 1):
            for name, nd in VARIANTS:
                if nd in L:
                    raw[name].add((rel, i))
    union = set().union(*raw.values())
    base = raw["angle_corner"]
    # L1 归一化后的召回：用 canonical 的归一化键去搜
    l1 = set()
    for rel, ls in files.items():
        for i, L in enumerate(ls, 1):
            if find_norm(L, CANON):
                l1.add((rel, i))
    print("=== 2. 归一化前后召回（同一语料、同一单位 (file,line)） ===")
    print("  raw angle_corner        : files=%2d lines=%2d" % (len({r for r,_ in base}), len(base)))
    print("  L1 normalized canonical : files=%2d lines=%2d" % (len({r for r,_ in l1}), len(l1)))
    print("  raw union(all 6)        : files=%2d lines=%2d" % (len({r for r,_ in union}), len(union)))
    print("  L1 gain over baseline   : +%d lines (+%.2f%% vs union), +%d NEW files" %
          (len(l1-base), 100.0*len(l1-base)/len(union),
           len({r for r,_ in l1} - {r for r,_ in base})))
    print("  L1 == raw(angle+curly+curlydouble) union ? %s" %
          (l1 == (raw["angle_corner"] | raw["curly_corner"] | raw["curly_double"])))
    print("  L1 仍未覆盖 (union - L1)  : lines=%d files=%d" %
          (len(union-l1), len({r for r,_ in union-l1})))
    print("  -- 残余明细（应由「非引号变体」规则单独处理，不得靠过度归一） --")
    for r,i in sorted(union-l1):
        who = [n for n,_ in VARIANTS if (r,i) in raw[n]]
        print("     %s:%d <- %s | %s" % (r,i,",".join(who), files[r][i-1].strip()[:150]))
    print("")

    print("=== 3. 位置映射可回溯验证（逐命中核对原文片段） ===")
    ok = True
    checked = 0
    for rel, ls in files.items():
        for i, L in enumerate(ls, 1):
            for (a,b,txt,k) in find_norm(L, CANON):
                checked += 1
                if L[a:b] != txt or txt not in L:
                    ok = False
                    print("  !! MAPPING FAIL %s:%d a=%d b=%d" % (rel,i,a,b))
    print("  mapped hits checked = %d ; all(orig_slice == reported_text) = %s" % (checked, ok))
    # 抽 3 条展示
    shown = 0
    for rel, i in sorted(l1):
        L = files[rel][i-1]
        for (a,b,t,_) in find_norm(L, CANON):
            if shown < 3:
                print("  sample %s:%d orig[%d:%d] = %r" % (rel,i,a,b,t))
                shown += 1
    print("")

    print("=== 4. 两段式失效量化（needle 先过滤 -> 角色后判） ===")
    # 4a: 单 needle 下，哪些文件被 file-level prefilter 直接跳过
    killed_files, killed_lines = [], []
    for rel, ls in files.items():
        txt = "\n".join(ls)
        if CANON not in txt:              # _rs_carrier_scan.py:229 的 file-level gate
            if any((rel,i) in union for i in range(1,len(ls)+1)):
                killed_files.append(rel)
                killed_lines += [(rel,i) for i in range(1,len(ls)+1) if (rel,i) in union]
    print("  file-level prefilter (line 229) 会整件跳过的「含变体但无直角引号」文件 = %d" % len(killed_files))
    for r in killed_files:
        print("     %s (union lines=%s)" % (r, sorted(i for rr,i in union if rr==r)))
    print("  这些件里的漏检行数 = %d" % len(killed_lines))
    # 4b: 通过 file gate 的件里，被 line-level gate 跳过的行
    #  _ve_DRAFT_S609.md 有 :69/:70 直角引号 -> file gate PASS；:22 被 line gate 杀
    line_only = []
    for rel, i in union - base:
        txt = "\n".join(files[rel])
        if CANON in txt:
            line_only.append((rel,i))
    print("  通过 file gate 但被 line-level gate (classify_line line 165) 跳过的行 = %d" % len(line_only))
    print("  其中 :22 是否在内 = %s" % (("s604_verdict_entry_20261109/_ve_DRAFT_S609.md",22) in line_only))
    print("  => 双闸：任一闸漏即 <not-scanned>，角色判定 (R5) 根本没有机会执行。")
    print("")

    print("=== 5. 过度归一化的构造反例（>=3）；每条都用本文件的 normalize_line 实跑 ===")
    def over_normalize_delete_quotes(s):
        """反例用：把引号与标点全删、空白全删的「过度」归一（不采用）。"""
        s = re.sub(r"[「」『』“”‘’\"'`（）()、，,；;。\s]", "", s)
        return s
    def nfkc(s):
        return unicodedata.normalize("NFKC", s)
    cex = [
      ("CE1 去引号合并：裸断言 vs 引述否定",
       "**只能判「不可复现」、不能定位当年错误步骤**",
       "其边界句「只能判不可复现、不能定位当年错误步骤」自本节起不再成立"),
      ("CE2 删标点+删引号：并列两结论 vs 整句被引用",
       "只能判「不可复现」、不能定位当年错误步骤",
       "只能判「不可复现、不能定位当年错误步骤」"),
      ("CE3 同义扩展：数值复现 vs 载体恢复",
       "只能判「不可复现」",
       "只能判「不可复原」"),
      ("CE4 空白删除：表格两列 vs 散文断言",
       "| 只能判 | 不可复现 |",
       "只能判不可复现"),
    ]
    for title, A, B in cex:
        ka, kb = over_normalize_delete_quotes(A), over_normalize_delete_quotes(B)
        la, lb = norm_needle(A), norm_needle(B)
        print("  %s" % title)
        print("     A = %r" % A)
        print("     B = %r" % B)
        print("     过度归一 key(A)=%r key(B)=%r MERGED=%s" % (ka,kb,ka==kb))
        print("     L1  key(A)=%r" % la)
        print("     L1  key(B)=%r ; L1_MERGED=%s" % (lb, la==lb))
    print("  -- NFKC 单独反例（全半角字面量，项目按码位比对，见 GATE_LITERAL_MATCH_POSTMORTEM.md:70） --")
    x, y = "规则 APPROVE_SCOPE 已生效", "规则 ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ 已生效"
    print("     A=%r" % x); print("     B=%r" % y)
    print("     NFKC(A)=%r NFKC(B)=%r MERGED=%s" % (nfkc(x),nfkc(y),nfkc(x)==nfkc(y)))
    print("     L1(A)=%r L1(B)=%r MERGED=%s" % (norm_needle(x),norm_needle(y),norm_needle(x)==norm_needle(y)))
    print("")

    print("=== 6. 真实语料里的「不可复原」（CE3 不是构造孤例） ===")
    for rel, ls in files.items():
        for i, L in enumerate(ls,1):
            if "不可复原" in L:
                print("     %s:%d %s" % (rel,i,L.strip()[:180]))
    print("")

    print("=== 7. 宽泛捞候选的量（噪声评估） ===")
    b1 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if "不可复现" in L}
    b2 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if "只能判" in L}
    b3 = b1 & b2
    print("  broad(不可复现)      lines=%3d files=%2d" % (len(b1), len({r for r,_ in b1})))
    print("  broad(只能判)        lines=%3d files=%2d" % (len(b2), len({r for r,_ in b2})))
    print("  broad(两者同现)      lines=%3d files=%2d" % (len(b3), len({r for r,_ in b3})))
    print("  L1 归一召回          lines=%3d files=%2d" % (len(l1), len({r for r,_ in l1})))
    print("  broad(不可复现) - L1 lines=%3d files=%2d  <-- 需角色判定/主题判定收窄的候选" %
          (len(b1-l1), len({r for r,_ in b1-l1})))
    print("  broad(只能判)   - L1 lines=%3d files=%2d" % (len(b2-l1), len({r for r,_ in b2-l1})))
    print("  broad(两者同现) - L1 lines=%3d files=%2d" % (len(b3-l1), len({r for r,_ in b3-l1})))
    # 主题外占比：b1-l1 中含"只能判"的 = 与句子高度相关但仍未命中 L1 的
    print("  (b1-L1) 中同时含「只能判」的 = %d 行（多为无引号/换标点的真变体或引述）" % len((b1-l1)&b2))
    print("")

    print("=== 8. 归一化自检注入样本（合成 fixture，全部在内存，不写文件） ===")
    fixtures = [
      ("POS-angle",     "**只能判「不可复现」、不能定位当年错误步骤**", True),
      ("POS-curly",     "其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）自本节起不再成立", True),
      ("POS-curlyDbl",  "只能判“不可复现”", True),
      ("POS-nested",    "其边界句「只能判『不可复现』、不能定位当年错误步骤」自本节起不再成立", True),
      ("NEG-noquote",   "只能判不可复现、不能定位错误源头", False),
      ("NEG-halfparen", "只能判(不可复现)", False),
      ("NEG-nopunct",   "只能判 不可复现", False),
      ("NEG-word",      "只能判「不可复原」", False),
      ("NEG-other",     "两列不可复现，时长列与倍率复现", False),
      ("NEG-table",     "| 只能判 | 不可复现 |", False),
    ]
    allok = True
    for name, L, expect in fixtures:
        got = bool(find_norm(L, CANON))
        good = (got == expect)
        allok &= good
        for (a,b,t,k) in find_norm(L, CANON):
            assert L[a:b] == t
        print("  %-4s %-14s expect=%-5s got=%-5s %s" %
              ("PASS" if good else "FAIL", name, expect, got, repr(L[:60])))
    print("  FIXTURE_SELF_TEST = %s" % ("PASS" if allok else "FAIL"))
    # ---- 退出码聚合（纯追加；原件各行一字未动）----
    # 只聚合「本脚本对自身的检查」：§3 位置映射 ok + §8 合成 fixture allok。
    # 对被测语料的领域词量化/报告（§1/2/4/5/6/7）一律不参与判定。
    # 驱动变量 ok 是 main() 的局部变量（§3 判定），故用 nonlocal 而非
    # 模板里的 global：既不新增全局名字(C3)，也不遮蔽库本体(C2)。
    def check(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)          # 合取聚合：全部通过才真
        print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))
    check("§3 位置映射 orig_slice == reported_text", ok)
    check("§8 合成 fixture self-test", allok)
    main._gate_ok = ok   # 挂到既有函数对象：不新增任何全局名字(C3)

if __name__ == "__main__":
    main()
    print("核验结论: " + ("ALL PASS" if main._gate_ok else "FAIL"))
    raise SystemExit(0 if main._gate_ok else 1)
