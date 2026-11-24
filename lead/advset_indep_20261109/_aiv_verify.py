# -*- coding: utf-8 -*-
r"""_aiv_verify.py — 对抗集独立性【独立复核员】自建实跑件。

纪律：零真机 / 零采样代码；只 re + ast + json + hashlib + 静态源码 compile/exec。
不 import 保护件（不产生 __pycache__）；不执行任何 _ai_* 脚本（避免覆写被核交付件）。
唯一写域 lead/advset_indep_20261109/，本件前缀 _aiv_。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/advset_indep_20261109/_aiv_verify.py
"""
import sys, json, hashlib, re, ast, types
from pathlib import Path
from collections import Counter

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "advset_indep_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
DGD = ROOT / "lead" / "dneg_generative_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
DGA_PY = DGA / "_dga_adversarial.py"

BASE = {
    "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md": ("e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb", 42689),
    "lead/dg_adversarial_20261109/_dga_adversarial_out.json": ("395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c", 55528),
    "lead/dg_adversarial_20261109/_dga_adversarial.py": ("e94e29be01d62abeeb58e76570306e5bcbd46a2d706647d7a0269c0d271cd27b", 29736),
    "lead/dneg_generative_20261109/_dg_core.py": ("7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322),
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md": ("94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4", 46334),
    "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def memload(name, path):
    """compile/exec 源码字节到新模块；不经过 importlib 文件加载 ⇒ 不写 .pyc。"""
    src = Path(path).read_text(encoding="utf-8")
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(src, str(path), "exec"), m.__dict__)
    return m


def lit_assigns(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Name):
                    try:
                        out[tgt.id] = ast.literal_eval(n.value)
                    except Exception:
                        pass
    return out


def all_strings(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    return {n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def lev(a, b):
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lcs_len(a, b):
    """最长公共子串长度（朴素 DP）。"""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


PROTECTED = [DGA, DGD, ROOT / "lead" / "h5_governance_20261109",
             ROOT / "lead" / "gate_fp7_20261108", ROOT / "lead" / "gate_n13_20261109",
             ROOT / "lead" / "PENDING_DECISIONS.md", ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"]


def snap():
    out = {}
    for d in PROTECTED:
        ps = [d] if d.is_file() else sorted(d.rglob("*"))
        for p in ps:
            if p.is_file():
                b = p.read_bytes()
                out[str(p)] = [hashlib.sha256(b).hexdigest(), len(b), p.stat().st_mtime_ns]
    return out


print("=== (0) 九件编排方基线指纹：本会话 hashlib 独立实算 ===")
fp_ok = True
for rel, (h, n) in BASE.items():
    g = sha(ROOT / rel)
    ok = g == (h, n)
    fp_ok &= ok
    print("  %s %s %d  %s" % ("MATCH" if ok else "DIFF", g[0], g[1], rel))
print("  ALL_9_MATCH =", fp_ok)

# 被核交付件 10 件：会话首指纹，会话末复算，证明我未改被核对象
DELIVERED = sorted(p for p in WD.iterdir() if p.is_file() and p.name.startswith(("_ai_", "_AI_")))
DEL0 = {p.name: sha(p) for p in DELIVERED}
print("  被核交付件数 =", len(DEL0), " 名单 =", sorted(DEL0))
MAIN = WD / "_AI_ADVSET_INDEPENDENCE.md"
print("  主被核对象 _AI_ADVSET_INDEPENDENCE.md =", sha(MAIN))

SNAP0 = snap()
print("  保护树/台账快照文件数 =", len(SNAP0))

# =====================================================================
print("\n=== (1) 自建六判定器（源码 compile/exec；判定与计分全部我自己写）===")
DG = memload("_aiv_dg", DGD / "_dg_core.py")
H5 = memload("_aiv_h5", H5P)
G7 = memload("_aiv_g7", G7P)
DROP = memload("_aiv_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert DROP.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE
print("  DG_STATS =", DG.DG_STATS)

TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
DET = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]


def my_detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    v, h = {}, {}
    problems, hitlist = DG.dg_scan(text, toks)
    v["DG_pure"] = "CATCH" if problems else "PASS"
    h["DG_pure"] = hitlist[0]["hit"] if hitlist else ""
    p2, _ = DROP.r12_scan(text, toks)
    v["DG_dropin"] = "CATCH" if p2 else "PASS"
    raw = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            mm = DG.DG_DROPIN_RE.search(text[:m.start()])
            if mm:
                raw.append(mm.group(0))
    h["DG_dropin"] = raw[0] if raw else ""
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    v["H5_lit"] = "CATCH" if ml else "PASS"
    h["H5_lit"] = ml.group(0) if ml else ""
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    v["H5_gov"] = "CATCH" if hg else "PASS"
    h["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks)
    v["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    v["R12_lit"] = "CATCH" if m12 else "PASS"
    h["R12_lit"] = m12.group(0) if m12 else ""
    return v, h


A = lit_assigns(DGA_PY)
CASES, FORCED = A["CASES"], A["FORCED"]
TRAIN_FILES = {"_dg_step34.py": DGD / "_dg_step34.py", "_dgv_probe.py": DGD / "_dgv_probe.py",
               "_dgv_neg2.py": DGD / "_dgv_neg2.py", "_dg_step1.py": DGD / "_dg_step1.py"}
TRAIN_ALL = set()
per_file = {}
for tag, p in TRAIN_FILES.items():
    s = all_strings(p)
    per_file[tag] = len(s)
    TRAIN_ALL |= s
exact_overlap = sorted({c[2] for c in CASES} & TRAIN_ALL)
print("  自造样本数 =", len(CASES), " 训练集逐件抽取串数 =", list(per_file.items()),
      " 并集 =", len(TRAIN_ALL), " 精确重合 =", len(exact_overlap), exact_overlap)

rows = []
for cid, shape, text, exp, why, attack in CASES:
    v, h = my_detect(text)
    rows.append({"id": cid, "shape": shape, "text": text, "expect": exp,
                 "forced": FORCED.get(cid, exp), "why": why, "attack": attack,
                 "verdicts": v, "hits": h})


def my_score(key, forced):
    fp, fn, amb, fpi, fni = 0, 0, 0, [], []
    for x in rows:
        exp = x["forced"] if forced else x["expect"]
        if (not forced) and x["expect"] == "AMBIG":
            amb += 1
            continue
        g = x["verdicts"][key]
        if exp == "PASS" and g == "CATCH":
            fp += 1; fpi.append(x["id"])
        elif exp == "CATCH" and g == "PASS":
            fn += 1; fni.append(x["id"])
    return {"n": len(rows) - amb, "fp": fp, "fn": fn, "fp_ids": fpi, "fn_ids": fni}


strict = {k: my_score(k, False) for k in DET}
forced = {k: my_score(k, True) for k in DET}
print("  --- 我自建 strict（排除 5 条 AMBIG，n=36）---")
for k in DET:
    s = strict[k]
    print("  %-10s n=%-3d fp=%-2d %-45s fn=%-2d %s" % (k, s["n"], s["fp"], str(s["fp_ids"]), s["fn"], str(s["fn_ids"])))
print("  --- 我自建 forced（41 条全计，AMBIG 按 FORCED）---")
for k in DET:
    s = forced[k]
    print("  %-10s n=%-3d fp=%-2d %-45s fn=%-2d %s" % (k, s["n"], s["fp"], str(s["fp_ids"]), s["fn"], str(s["fn_ids"])))
# 与【被核对象】申报（evidence C2 / _ai_verify_stdout.txt:66-78 / DG_ADVERSARIAL.md:146-166）对比
DECL_STRICT = {"DG_pure": (7, 11), "DG_dropin": (8, 10), "H5_lit": (9, 14),
               "H5_gov": (7, 14), "R12": (2, 17), "R12_lit": (2, 17)}
DECL_FORCED = {"DG_pure": (10, 12), "DG_dropin": (11, 11), "H5_lit": (11, 15),
               "H5_gov": (9, 15), "R12": (3, 18), "R12_lit": (3, 18)}
print("  ★ strict 六判定器 (fp,fn) 与申报全同 =",
      all((strict[k]["fp"], strict[k]["fn"]) == DECL_STRICT[k] for k in DET))
print("  ★ forced 六判定器 (fp,fn) 与申报全同 =",
      all((forced[k]["fp"], forced[k]["fn"]) == DECL_FORCED[k] for k in DET))
c06 = next(x for x in rows if x["id"] == "C06")
print("  ★ C06 DG_pure =", c06["verdicts"]["DG_pure"], " (判对 ⇒ 实际漏判 11 条)")
print("  ★ strict DG_pure fn 名单 =", strict["DG_pure"]["fn_ids"])

# 逐条 verdict 与【被核对象/编排方】形态分布 hits 对照（只核对 DG_pure hit）
ORCH_HIT = {
    "P06": "不敢不承认", "P07": "不敢不承认", "P08": "并不否认", "P09": "并不否认",
    "P10": "并不否认", "P11": "并非不宣告", "P12": "并不否认", "P16": "", "P17": "",
    "C06": "非登记五份原件不可", "C13": "何尝不认为", "C14": "不见得不认为",
    "C15": "岂敢不承认", "C16": "不由得不承认", "C17": "并非不宣告",
    "C18": "亦非不宣告", "C19": "并非不宣告", "C20": "不是不承认",
    "A01": "不否认", "A02": "并不否认", "A03": "不无",
}
mis = [(x["id"], x["hits"]["DG_pure"], v) for x in rows for k, v in ORCH_HIT.items() if x["id"] == k and x["hits"]["DG_pure"] != v]
print("  ★ 23 条非空/关键 DG_pure hit 与编排方申报全同 =", not mis, " 不一致 =", mis)

# =====================================================================
print("\n=== (2) 我自建四级判据：41 条逐条判（不是只给分布）===")
# 训练集句子：我自己的口径 = 四个训练源 AST 全部字符串常量中，长度>=8 且含中文者
TRAIN_SENTS = sorted({s for s in TRAIN_ALL if len(s) >= 8 and re.search(r"[\u4e00-\u9fff]", s)})
print("  我的训练句子集（自建口径，AST 全部字符串常量）去重数 =", len(TRAIN_SENTS))

NEG_CHARS = set("不无未非没莫勿甭别岂")
catalog = set()
for p in TRAIN_FILES.values():
    for name, val in lit_assigns(p).items():
        if isinstance(val, (list, tuple)):
            for item in val:
                cells = item if isinstance(item, (list, tuple)) else [item]
                for c in cells:
                    if isinstance(c, str) and len(c) >= 2 and any(ch in c for ch in NEG_CHARS):
                        catalog.add(c)
        elif isinstance(val, str) and len(val) >= 2 and any(ch in val for ch in NEG_CHARS):
            catalog.add(val)
catalog |= set(DG.R12_TEN) | set(DG.PSEUDO_DN)
for br in (H5.H5_DN_EXTRA.split("|") + H5.H5_R12_TEN.split("|")):
    if "[^" not in br and len(br) >= 2 and any(ch in br for ch in NEG_CHARS):
        catalog.add(br)
CAT = sorted(catalog, key=lambda z: (-len(z), z))
CAT_IN_TRAIN = [c for c in CAT if any(c in s for s in TRAIN_SENTS)]
print("  我自建 DN 构式目录 n =", len(CAT), " 其中在训练句子中出现过 n =", len(CAT_IN_TRAIN))

SECOND = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔", "台账",
          "母本", "本域", "本轮", "审阅回件", "复核回件"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
COORD = ["或", "以及", "同时", "并且", "一是", "二是", "其一", "其二", "/", "／", "、"]
FAMILY = sorted(set([w for w in DG.MID if w] + list(DG.PSEUDO_DN) + BREAK10 + COORD + SECOND +
                    [w for w in DG.NEG1 if len(w) >= 2] + [w for w in DG.NEG2 if len(w) >= 2] +
                    CAT + ["「」", "『』", "“”", "``"]), key=lambda z: -len(z))
print("  我自建构式族词表 FAMILY n =", len(FAMILY))

T12_ALL = {n1 + m + n2 for n1 in set(DG.NEG1) for m in set(DG.MID) for n2 in set(DG.NEG2)}


def decomposable(hit):
    if not hit:
        return False, [], False
    t12 = [(n1, m, n2) for n1 in set(DG.NEG1) for m in set(DG.MID) for n2 in set(DG.NEG2)
           if n1 + m + n2 == hit]
    mm = DG.DG_DROPIN_RE.search(hit)
    t3 = bool(mm and mm.group("t3"))
    return (bool(t12) or t3), t12[:1], t3


grade_rows = []
for x in rows:
    s = x["text"]
    d1 = [c for c in CAT_IN_TRAIN if c in s]
    d2 = [f for f in FAMILY if f in s]
    dp, t12p, t3p = decomposable(x["hits"]["DG_pure"])
    dd, _, _ = decomposable(x["hits"]["DG_dropin"])
    d3 = dp or dd
    best_lcs = max((lcs_len(s, t) for t in TRAIN_SENTS), default=0)
    best_edit = min((lev(s, t) for t in TRAIN_SENTS), default=10 ** 9)
    # 按【被核对象 §2.1】判据实现（我自己的修正版）：
    #   L0 = 零精确重合；L1 = L0 且 无训练构式 且 hit 非表内可拼；
    #   L2 = L1 且 无族词 且 LCS<4 且 min_edit>5；L3 = L2 且 构造者盲化
    if s in TRAIN_ALL:
        g = "belowL0"
    elif d1 or d3:
        g = "L0"
    elif d2:
        g = "L1"
    elif best_lcs >= 4 or best_edit <= 5:
        g = "L1"          # 近重复 ⇒ 不够 L2，按定义停在 L1
    else:
        g = "L2"          # 盲化另判；本集无一到此
    # L3 证据：CASES.attack / why / shape 是否点名受测不变式、常量、源码行号
    blind = (not x["attack"]) and ("_dg_core.py:" not in x["why"]) and \
            (not re.search(r"MID|COMP=|PSEUDO|第二主语|未登记|分离式|DG_BREAK_RE|DG_QUOTE_RE|DG_COORD_RE|_SECOND|闭合表|词首负向前瞻|≤4", x["shape"] + " " + x["why"]))
    g_final = "L3" if (g == "L2" and blind) else g
    grade_rows.append({"id": x["id"], "shape": x["shape"], "grade": g_final,
                       "d1": d1[:3], "d2": d2[:3], "d3": d3,
                       "hit": x["hits"]["DG_pure"], "lcs": best_lcs, "min_edit": best_edit,
                       "attack": x["attack"], "blind": blind})
    print("  %-4s grade=%-4s d1=%-14s d2=%-12s d3=%-5s hit=%-12s lcs=%-2d edit=%-3d attack=%-3s blind=%s" %
          (x["id"], g_final, ",".join(d1[:2]) or "-", ",".join(d2[:2]) or "-", d3,
           x["hits"]["DG_pure"] or "-", best_lcs, best_edit, x["attack"] or "-", blind))
print("  ★ 我的逐条分级分布 =", json.dumps(dict(Counter(r["grade"] for r in grade_rows)), ensure_ascii=False))
for lv in ("L0", "L1", "L2", "L3"):
    print("  %s ids = %s" % (lv, [r["id"] for r in grade_rows if r["grade"] == lv]))
print("  ★ 共享训练构式 d1 非空 = %d/41 ; 共享族词 d2 非空 = %d/41 ; hit 表内可拼 d3 = %d/41" %
      (sum(1 for r in grade_rows if r["d1"]), sum(1 for r in grade_rows if r["d2"]),
       sum(1 for r in grade_rows if r["d3"])))
print("  ★ d1∪d3 = %d/41 ; LCS>=4 = %d/41 ; LCS>=6 = %d/41 ; min_edit<=3 = %d/41 ; min_edit<=5 = %d/41" %
      (sum(1 for r in grade_rows if r["d1"] or r["d3"]),
       sum(1 for r in grade_rows if r["lcs"] >= 4), sum(1 for r in grade_rows if r["lcs"] >= 6),
       sum(1 for r in grade_rows if r["min_edit"] <= 3), sum(1 for r in grade_rows if r["min_edit"] <= 5)))
print("  ★ 严格口径 L0=24/L1=17 的复算（我的目录口径）：L0=%d L1=%d ；两口径均 L2=L3=0 = %s" %
      (sum(1 for r in grade_rows if r["grade"] == "L0"),
       sum(1 for r in grade_rows if r["grade"] == "L1"),
       all(r["grade"] in ("L0", "L1") for r in grade_rows)))

# ---- L3 生成机制反证：CASES 自述证据（AST 直读保护件）----
n_attack = sum(1 for x in rows if x["attack"])
n_why_core = sum(1 for x in rows if "_dg_core.py:" in x["why"])
n_why_tab = sum(1 for x in rows if re.search(r"MID|BREAK|_SECOND|QUOTE|COORD|PSEUDO|COMP|23 项|闭合表|词首负向前瞻|≤4", x["why"]))
n_shape_tab = [x["id"] + ":" + x["shape"] for x in rows
               if re.search(r"MID|COMP=|PSEUDO|第二主语|未登记|分离式", x["shape"])]
print("  ★ L3 反证：attack 非空 = %d/41 ; why 含源码行号 = %d/41 ; why 含表/常量名 = %d/41 ; shape 含表内常量名 = %d/41" %
      (n_attack, n_why_core, n_why_tab, len(n_shape_tab)))
print("    shape 明细 =", n_shape_tab)

# ---- 判据实现缺陷检测：照抄 _ai_grade.py:134-139 的分支，喂合成行 ----
def their_grade(r):
    if r["min_edit"] == 0: return "belowL0"
    if r["d1"] or r["d3_pure"] or r["d3_dropin"]: return "L0"
    if r["d2"]: return "L1"
    if r["lcs_train"].get("len", 0) >= 4 or r["min_edit"] <= 5: return "L2"
    return "L3"


synth = [
    {"min_edit": 2, "d1": [], "d2": [], "d3_pure": False, "d3_dropin": False,
     "lcs_train": {"len": 8}},
    {"min_edit": 9, "d1": [], "d2": [], "d3_pure": False, "d3_dropin": False,
     "lcs_train": {"len": 2}},
]
for i, r in enumerate(synth):
    print("  ★ 交付脚本 _ai_grade.py:134-139 分支复现 合成行%d → %s （定义要求：近重复应停在 L1；"
          "无族词且远距也须再查盲化才可 L3）" % (i + 1, their_grade(r)))

# =====================================================================
print("\n=== (3) DG 失败模式（第三步(d) 核心洞察）：fp7 逐条 hit 分解 ===")
fp7 = [x for x in rows if x["id"] in ("P06", "P07", "P08", "P09", "P10", "P11", "P12")]
fp_attr = []
for x in fp7:
    ok, t12, t3 = decomposable(x["hits"]["DG_pure"])
    gr = next(r for r in grade_rows if r["id"] == x["id"])
    fp_attr.append({"id": x["id"], "hit": x["hits"]["DG_pure"], "decomposable": ok,
                    "t12": t12, "t3": t3, "d1": gr["d1"], "min_edit": gr["min_edit"]})
    print("  %-4s hit=%-12s 表内可拼=%-5s T12分解=%-24s d1=%-14s min_edit=%d" %
          (x["id"], x["hits"]["DG_pure"], ok, str(t12), ",".join(gr["d1"][:2]), gr["min_edit"]))
print("  ★ 7/7 hit 全部可由 NEG1·MID·NEG2 (T12) 拼出 =",
      all(z["decomposable"] and z["t12"] for z in fp_attr))
print("  ★ 7/7 用训练句子里出现过的构式 d1 =", all(z["d1"] for z in fp_attr))
print("  ★ 7/7 min_edit<=6 =", all(z["min_edit"] <= 6 for z in fp_attr))
print("  归因归类：A=表内构式+本应切断而未切断的边界词/引号 = P06/P07/P08/P11/P12 (5) ; "
      "B=guard 作用域错误（第二主语/并列 veto 只查 hit_text）= P09/P10 (2)")

# =====================================================================
print("\n=== (4) 我自建绕过重跑（≥3 条，实跑 6 条；自建语料不照抄 _ai_*）===")
# ① 未登记边界/让步词（我自选 8 词）
MY_BREAK = ["究其根本", "说穿了", "细究起来", "退一步讲", "殊不知", "不宁唯是", "偏偏", "诚然"]
b = []
for w in MY_BREAK:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    v, _ = my_detect(t)
    b.append((w, bool(DG.DG_BREAK_RE.search(w)), v["DG_pure"], v["DG_dropin"]))
print("  ① 我自建 8 词：", b)
print("  ★ ① 未登记且 DG_pure=CATCH（应 PASS） = %d/%d" %
      (sum(1 for z in b if not z[1] and z[2] == "CATCH"), len(b)))
reg = []
for w in BREAK10:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    v, _ = my_detect(t)
    reg.append((w, v["DG_pure"], v["DG_dropin"]))
print("  ①b 已登记 10 词：pure=PASS %d/10 ; dropin=CATCH %d/10" %
      (sum(1 for z in reg if z[1] == "PASS"), sum(1 for z in reg if z[2] == "CATCH")))
# ② 未登记引号（我自选 5 类）
MY_Q = [("〔", "〕"), ("[", "]"), ("<<", ">>"), ("⟪", "⟫"), ("‹", "›")]
q = []
for op, cl in MY_Q:
    t = op + "并非不宣告已生效" + cl + "只是引文，本件不采信该说法"
    v, _ = my_detect(t)
    q.append((op + cl, v["DG_pure"], v["DG_dropin"]))
print("  ② 我自建 5 类未登记引号：", q)
print("  ★ ② DG_pure=CATCH（应 PASS） = %d/%d" % (sum(1 for z in q if z[1] == "CATCH"), len(q)))
# ③ MID / COMP（我自选 8 个 MID + 另一动词的 COMP 扫描）
MY_MID = ["容", "许", "想", "愿", "甘", "料", "需", "欲"]
m = []
for w in MY_MID:
    t = "不" + w + "不宣告本件已生效"
    v, _ = my_detect(t)
    m.append((w, w in set(DG.MID), v["DG_pure"]))
print("  ③ 我自建 8 MID：", m)
print("  ★ ③ 未登记且真 DN 漏判 = %d/%d" % (sum(1 for z in m if not z[1] and z[2] == "PASS"), len(m)))
comp = []
for n in range(0, 7):
    t = "非写成" + "甲" * n + "不可才算本件已生效"
    v, _ = my_detect(t)
    comp.append((n, v["DG_pure"], v["DG_dropin"]))
print("  ③b 我自建 COMP（动词=写成，字符=甲）0..6 =", comp)
print("  ★ ③b ≤4 全 CATCH =", all(z[1] == "CATCH" for z in comp if z[0] <= 4),
      " ; ≥5 全 PASS =", all(z[1] == "PASS" for z in comp if z[0] >= 5))
# ④ 第二主语 veto 结构性不可达：静态全枚举 + 41 条触发计数
t12_second = [h for h in T12_ALL if DG.DG_SECOND_SUBJ_RE.search(h)]
t12_coord = [h for h in T12_ALL if DG.DG_COORD_RE.search(h)]
parts = list(DG.NEG1) + list(DG.MID) + list(DG.NEG2) + list(DG.GAP) + list(DG.SCOPE_VERB) + list(DG.SPLIT_TAIL) + list(DG.PSEUDO_DN)
in_parts = [p for p in parts if DG.DG_SECOND_SUBJ_RE.search(p)]
fired2 = fired5 = 0
fire_ids = []
for x in rows:
    for tok in TOKS:
        for mm in re.finditer(re.escape(tok), x["text"]):
            d = DG.dg_double_neg(x["text"][:mm.start()])
            if "第二主语" in d["reason"]:
                fired2 += 1; fire_ids.append((x["id"], "第二主语"))
            if "并列标记" in d["reason"]:
                fired5 += 1; fire_ids.append((x["id"], "并列标记"))
print("  ④ T12 笛卡尔积 = %d 去重 = %d ; 含 _SECOND = %d ; 含并列标记 = %d" %
      (DG.DG_STATS["cartesian_T12"], len(T12_ALL), len(t12_second), len(t12_coord)))
print("  ④ 7 张表全部条目中含 _SECOND 的条目 =", in_parts)
t3_second = []
for s in SECOND:
    t = "非登记" + s + "不可才算本件已生效"
    v, _ = my_detect(t)
    t3_second.append((s, v["DG_pure"]))
print("  ④ T3 comp 塞入 14 个 _SECOND 词，DG_pure 全 PASS =",
      all(z[1] == "PASS" for z in t3_second), t3_second)
print("  ④ 41 条上 veto 触发：第二主语 = %d ; 并列标记 = %d ; 明细 = %s" % (fired2, fired5, fire_ids))
print("  ★ ④ 结构性不可达（保证从未生效） =",
      len(t12_second) == 0 and not in_parts and all(z[1] == "PASS" for z in t3_second) and fired2 == 0)
# ⑤ 并列 veto 只查 hit_text（我自建 4 例）
coord_cases = ["本件不承认抑或并不否认已生效", "本件不承认、并不否认均不成立已生效",
               "非写成甲或乙不可才算本件已生效", "非写成原件不可才算本件已生效"]
cc = []
for t in coord_cases:
    v, h = my_detect(t)
    cc.append((t, v["DG_pure"], v["DG_dropin"], h["DG_dropin"]))
print("  ⑤ 我自建并列构造：")
for z in cc:
    print("    %-28s pure=%-5s dropin=%-5s raw_hit=%s" % (z[0][:26], z[1], z[2], z[3]))
print("  ★ ⑤ 至少 1 条 fp（真 PASS 被 CATCH）+ 1 条 fn（真 CATCH 被 PASS）= ",
      any(z[1] == "CATCH" for z in cc[:2]) and any(z[1] == "PASS" for z in cc[2:3]))
# ⑥ PSEUDO_DN 词首局部 veto（我自建 4 例 + 12 项逐项）
pseudo_cases = ["无非不是不承认本件已生效", "莫非并不是不承认本件已生效",
                "莫不是不承认本件已生效", "非不承认本件已生效"]
pc = []
for t in pseudo_cases:
    v, h = my_detect(t)
    pc.append((t, v["DG_pure"], h["DG_dropin"]))
print("  ⑥ 我自建 PSEUDO 位置变体：", pc)
pr = []
for p in DG.PSEUDO_DN:
    t = p + "不承认本件已生效"
    raw = bool(DG.DG_DROPIN_RE.search(t[:t.find("已生效")]))
    pr.append((p, raw))
print("  ⑥ 12 项逐项 raw_regex True = %d/12 ; 明细 = %s" % (sum(1 for z in pr if z[1]), pr))
# 交付形态 co_names
guards = ["_mask_quotes", "_scope", "dg_double_neg", "DG_SECOND_SUBJ_RE", "DG_COORD_RE"]
for fn in ("r10_context", "r12_scan"):
    names = set(getattr(DROP, fn).__code__.co_names)
    print("  ★ 交付形态 %-12s co_names 含 guard = %s" % (fn, {g: (g in names) for g in guards}))

# =====================================================================
print("\n=== (5) 越界核验：保护树 / 台账 / 被核交付件 会话内零写 ===")
SNAP1 = snap()
DEL1 = {p.name: sha(p) for p in WD.iterdir() if p.is_file() and p.name.startswith(("_ai_", "_AI_"))}
print("  保护树文件数 前=%d 后=%d ; 全量 sha+bytes+mtime_ns 一致 = %s" %
      (len(SNAP0), len(SNAP1), SNAP0 == SNAP1))
print("  新增 =", sorted(set(SNAP1) - set(SNAP0)), " 消失 =", sorted(set(SNAP0) - set(SNAP1)))
print("  被核交付件 10 件前/后一致 =", DEL0 == DEL1, " 件数 =", len(DEL1))
print("  我新增文件 =", sorted(p.name for p in WD.iterdir()
                          if p.is_file() and p.name.startswith("_aiv_")))
print("  九件基线二次重算 ALL_9_MATCH =",
      all(sha(ROOT / r) == (h, n) for r, (h, n) in BASE.items()))
print("  主被核对象二次实算 =", sha(MAIN))

OUT = {"baseline_match": fp_ok, "delivered_unchanged": DEL0 == DEL1,
       "protected_unchanged": SNAP0 == SNAP1, "n_cases": len(CASES),
       "exact_overlap": exact_overlap, "strict": strict, "forced": forced,
       "claims_match": {"strict": all((strict[k]["fp"], strict[k]["fn"]) == DECL_STRICT[k] for k in DET),
                        "forced": all((forced[k]["fp"], forced[k]["fn"]) == DECL_FORCED[k] for k in DET)},
       "my_train_sentences_n": len(TRAIN_SENTS), "catalog_n": len(CAT), "family_n": len(FAMILY),
       "grade_rows": grade_rows, "grade_distribution": dict(Counter(r["grade"] for r in grade_rows)),
       "l3_evidence": {"attack_n": n_attack, "why_core_n": n_why_core, "why_table_n": n_why_tab,
                       "shape_table_n": len(n_shape_tab)},
       "fp7": fp_attr, "bypass": {"1": b, "2": q, "3_mid": m, "3_comp": comp,
                                  "4_t12": {"total": len(T12_ALL), "second": len(t12_second),
                                            "coord": len(t12_coord), "fired2": fired2, "fired5": fired5,
                                            "in_parts": in_parts, "t3_second": t3_second},
                                  "5": cc, "6": pc, "6_pseudo12": pr},
       "main_sha": sha(MAIN)[0], "main_bytes": sha(MAIN)[1]}
(WD / "_aiv_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _aiv_out.json")
