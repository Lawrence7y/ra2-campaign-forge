# -*- coding: utf-8 -*-
r"""_ai_verify.py — 对抗集独立性分析员：独立复核 + 四级分级 + 构式共享量化 + 不变式重跑。

纪律：零真机 / 零采样代码；只做 re + ast + 静态文本 + hashlib。
      ★ 不 import 保护件（用 compile/exec 内存加载，sys.dont_write_bytecode=True，绝不写 __pycache__）。
      ★ 不修改任何保护件；输出只落 lead/advset_indep_20261109/。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/advset_indep_20261109/_ai_verify.py
"""
import sys, json, hashlib, re, ast, types, itertools
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "advset_indep_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
DGA_PY = DGA / "_dga_adversarial.py"
DGA_MD = DGA / "DG_ADVERSARIAL.md"
DGA_JSON = DGA / "_dga_adversarial_out.json"


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def load_src(name, path):
    """内存执行源码字节：不经过 importlib 文件加载 ⇒ 不产生 .pyc，保护树零写。"""
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
    return {n.value for n in ast.walk(t)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def lev(a, b):
    """字符级 Levenshtein（纯 Python，静态文本）。"""
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


# =====================================================================
print("=== (0) 九件绑定指纹：本会话 hashlib 独立重算 ===")
EXPECT = {
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
fp_ok = True
for rel, (h, n) in EXPECT.items():
    gh, gn = sha(ROOT / rel)
    ok = (gh == h and gn == n)
    fp_ok &= ok
    print("  %s %s sha=%s bytes=%d" % ("MATCH" if ok else "MISMATCH", rel, gh, gn))
print("  ALL_MATCH =", fp_ok)
assert fp_ok

# =====================================================================
print("\n=== (1) 内存加载三份谓词源码（compile/exec，不写盘）+ 保护树快照 ===")
PROTECTED_DIRS = [DGA, DG_DIR, ROOT / "lead" / "h5_governance_20261109",
                  ROOT / "lead" / "gate_fp7_20261108", ROOT / "lead" / "gate_n13_20261109"]


def snapshot():
    out = {}
    for d in PROTECTED_DIRS:
        for p in sorted(d.rglob("*")):
            if p.is_file():
                b = p.read_bytes()
                out[str(p)] = [hashlib.sha256(b).hexdigest(), len(b), p.stat().st_mtime_ns]
    return out


SNAP0 = snapshot()
DG = load_src("_ai_dg", DG_DIR / "_dg_core.py")
H5 = load_src("_ai_h5", H5P)
G7 = load_src("_ai_g7", G7P)
DROP = load_src("_ai_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert DROP.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE
print("  保护树快照文件数 =", len(SNAP0), " DG_STATS =", DG.DG_STATS)

TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
DETECTORS = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]


def detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {k: "PASS" for k in DETECTORS}
    hits = {}
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    hits["DG_pure"] = h[0]["hit"] if h else ""
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    raw = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            mm = DG.DG_DROPIN_RE.search(text[:m.start()])
            if mm:
                raw.append(mm.group(0))
    hits["DG_dropin"] = raw[0] if raw else ""
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hits["H5_lit"] = ml.group(0) if ml else ""
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"
    hits["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12_lit"] = m12.group(0) if m12 else ""
    hits["R12"] = hits["R12_lit"]
    return r, hits


# =====================================================================
print("\n=== (2) 第一步(a) 41 条 + 零精确重合：AST 静态抽取，不执行 _dga_adversarial.py ===")
A = lit_assigns(DGA_PY)
CASES, FORCED = A["CASES"], A["FORCED"]
TRAIN_FILES = {
    "_dg_step34.py": DG_DIR / "_dg_step34.py",
    "_dgv_probe.py": DG_DIR / "_dgv_probe.py",
    "_dgv_neg2.py": DG_DIR / "_dgv_neg2.py",
    "_dg_step1.py": DG_DIR / "_dg_step1.py",
}
TRAIN_ALL, per_file = set(), {}
for tag, p in TRAIN_FILES.items():
    s = all_strings(p)
    per_file[tag] = len(s)
    TRAIN_ALL |= s
my_texts = {c[2] for c in CASES}
overlap = sorted(my_texts & TRAIN_ALL)
print("  自造样本数 =", len(CASES), "; 训练集逐件抽取串数 =", list(per_file.items()),
      "; 并集串数 =", len(TRAIN_ALL))
print("  与全部训练集精确重合 =", len(overlap), overlap)
# 更强的字符串级检查：互为子串 / 归一化后相同
sub_relations = []
for s in my_texts:
    for t in TRAIN_ALL:
        if s != t and (s in t or t in s) and len(t) >= 8:
            sub_relations.append((s, t[:40]))
print("  互为子串（非精确相等）对 =", len(sub_relations), sub_relations[:5])
# 与编排方 _dga_adversarial_out.json 的 41 条逐条核对
dga_out = json.loads(DGA_JSON.read_text(encoding="utf-8"))
print("  _dga_adversarial_out.json novelty.n_cases =", dga_out["novelty"]["n_cases"],
      " exact_overlap =", dga_out["novelty"]["exact_overlap"],
      " note =", dga_out["novelty"]["note"])
json_ids = [x["id"] for x in dga_out["cases"]]
print("  out.json ids 与 AST CASES ids 全同 =", json_ids == [c[0] for c in CASES])

# =====================================================================
print("\n=== (3) 第一步(b) 六判定器 41 条逐条实跑 + strict/forced fp/fn ===")
rows = []
for cid, shape, text, exp, why, attack in CASES:
    r, hits = detect(text)
    rows.append({"id": cid, "shape": shape, "text": text, "expect": exp,
                 "forced": FORCED.get(cid, exp), "why": why, "attack": attack,
                 "verdicts": r, "hits": hits})
    print("  %-4s exp=%-5s shape=%-12s DG_p=%-5s DG_d=%-5s H5_l=%-5s H5_g=%-5s R12=%-5s R12_l=%-5s "
          "hits(p/d/Hl/Hg/Rl)=%s|%s|%s|%s|%s | %s" %
          (cid, exp, shape, r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["H5_gov"],
           r["R12"], r["R12_lit"], hits["DG_pure"], hits["DG_dropin"],
           hits["H5_lit"], hits["H5_gov"], hits["R12_lit"], text[:26]))


def score(key, forced=False):
    fp, fn, amb, fpi, fni = 0, 0, 0, [], []
    for x in rows:
        exp = x["forced"] if forced else x["expect"]
        if exp == "AMBIG" and not forced:
            amb += 1
            continue
        got = x["verdicts"][key]
        if exp == "PASS" and got == "CATCH":
            fp += 1; fpi.append(x["id"])
        elif exp == "CATCH" and got == "PASS":
            fn += 1; fni.append(x["id"])
    return {"n": len(rows) - amb, "amb_excluded": amb, "fp": fp, "fn": fn,
            "fp_ids": fpi, "fn_ids": fni}


strict = {k: score(k) for k in DETECTORS}
forced = {k: score(k, True) for k in DETECTORS}
print("  --- strict（排除 5 条 AMBIG）---")
for k in DETECTORS:
    s = strict[k]
    print("  %-10s n=%-3d fp=%-2d %-42s fn=%-2d %s" %
          (k, s["n"], s["fp"], str(s["fp_ids"]), s["fn"], str(s["fn_ids"])))
print("  --- forced（41 条全计，AMBIG 按 FORCED 保守应判）---")
for k in DETECTORS:
    s = forced[k]
    print("  %-10s n=%-3d fp=%-2d %-42s fn=%-2d %s" %
          (k, s["n"], s["fp"], str(s["fp_ids"]), s["fn"], str(s["fn_ids"])))
# 与编排方申报表核对
EXPECT_STRICT = {"DG_pure": (7, 11), "DG_dropin": (8, 10), "H5_lit": (9, 14),
                 "H5_gov": (7, 14), "R12": (2, 17), "R12_lit": (2, 17)}
EXPECT_FORCED = {"DG_pure": (10, 12), "DG_dropin": (11, 11), "H5_lit": (11, 15),
                 "H5_gov": (9, 15), "R12": (3, 18), "R12_lit": (3, 18)}
print("  strict 六判定器 fp/fn 与编排方申报全同 =",
      all((strict[k]["fp"], strict[k]["fn"]) == EXPECT_STRICT[k] for k in DETECTORS))
print("  forced 六判定器 fp/fn 与编排方申报全同 =",
      all((forced[k]["fp"], forced[k]["fn"]) == EXPECT_FORCED[k] for k in DETECTORS))

# 与任务书【41 条对抗样本的形态分布】逐条 hits 核对
ORCH = {
"P01": ["","","","",""], "P02": ["","","","",""], "P03": ["","","","",""],
"P04": ["","","","",""], "P05": ["","","","",""],
"P06": ["不敢不承认","不敢不承认","不敢不","不敢不",""],
"P07": ["不敢不承认","不敢不承认","不敢不","不敢不",""],
"P08": ["并不否认","并不否认","并不否认","并不否认",""],
"P09": ["并不否认","并不否认","并不否认","并不否认",""],
"P10": ["并不否认","并不否认","并不否认","并不否认",""],
"P11": ["并非不宣告","并非不宣告","并非不","并非不","并非不"],
"P12": ["并不否认","并不否认","并不否认","并不否认",""],
"P13": ["","","","",""], "P14": ["","","","",""], "P15": ["","","","",""],
"P16": ["","","莫不","",""], "P17": ["","并非不宣告","并非不","","并非不"],
"C01": ["","","","",""], "C02": ["","","","",""], "C03": ["","","","",""],
"C04": ["","","","",""], "C05": ["","","","",""],
"C06": ["非登记五份原件不可","非登记五份原件不可","","",""],
"C07": ["","","","",""],
"C08": ["","非登记一或二不可","","",""],
"C09": ["","","","",""],
"C10": ["","","非本件不宣告","非本件不宣告",""],
"C11": ["","","非不承认","非不承认",""],
"C12": ["","","","",""],
"C13": ["何尝不认为","何尝不认为","","",""],
"C14": ["不见得不认为","不见得不认为","","",""],
"C15": ["岂敢不承认","岂敢不承认","","",""],
"C16": ["不由得不承认","不由得不承认","","",""],
"C17": ["并非不宣告","并非不宣告","并非不","并非不","并非不"],
"C18": ["亦非不宣告","亦非不宣告","亦非不","亦非不",""],
"C19": ["并非不宣告","并非不宣告","并非不","并非不","并非不"],
"C20": ["不是不承认","不是不承认","莫不","莫不","不是不"],
"A01": ["不否认","不否认","","",""],
"A02": ["并不否认","并不否认","并不否认","并不否认",""],
"A03": ["不无","不无","不无","不无","不无"],
"A04": ["","","","",""],
}
mismatch = []
for x in rows:
    got = [x["hits"][k] for k in ("DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12_lit")]
    if got != ORCH[x["id"]]:
        mismatch.append((x["id"], got, ORCH[x["id"]]))
print("  41 条 hits 与编排方形态分布逐条全同 =", not mismatch, " 不一致 =", mismatch)
from collections import Counter
shape_hist = dict(Counter(x["shape"] for x in rows))
print("  shape_hist =", json.dumps(shape_hist, ensure_ascii=False))

# =====================================================================
print("\n=== (4) 训练集句子（带 id）+ 近重复量化 ===")
labeled = {}
for tag, p in TRAIN_FILES.items():
    asg = lit_assigns(p)
    for name, val in asg.items():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, (tuple, list)) and len(item) >= 2 and isinstance(item[0], str) \
                        and re.fullmatch(r"[A-Z]{1,3}\d{1,2}", item[0]) and isinstance(item[1], str):
                    labeled.setdefault(item[0] + "@" + tag, item[1])
# 补 19 式句子 / H5_EXTRA / H5_SPLIT / CTRL_CATCH / SKELETON / GAPS探针 / PARITY / A
for name, idx in (("GAPS", 1), ("NEG20", 1), ("A", 1), ("PARITY", 0)):
    for item in lit_assigns(TRAIN_FILES["_dg_step34.py"]).get(name, []):
        if isinstance(item, (tuple, list)) and len(item) > idx and isinstance(item[idx], str):
            labeled.setdefault("S:" + str(item[idx])[:12], item[idx])
for name in ("H5_EXTRA", "H5_SPLIT"):
    for s in lit_assigns(TRAIN_FILES["_dg_step34.py"]).get(name, []):
        labeled.setdefault("H:" + s[:12], s)
for name in ("GAPS", "NEG"):
    for item in lit_assigns(TRAIN_FILES["_dgv_probe.py"]).get(name, []):
        s = item[1] if isinstance(item, (tuple, list)) else item
        if isinstance(s, str):
            labeled.setdefault("V:" + s[:12], s)
for name in ("CASES",):
    for item in lit_assigns(TRAIN_FILES["_dgv_neg2.py"]).get(name, []):
        if isinstance(item, (tuple, list)) and len(item) > 1:
            labeled.setdefault("W:" + item[1][:12], item[1])
for s in lit_assigns(TRAIN_FILES["_dgv_neg2.py"]).get("SKELETON", []):
    labeled.setdefault("K:" + s[:12], s)
for name in ("GAPS",):
    for item in lit_assigns(TRAIN_FILES["_dg_step1.py"]).get(name, []):
        if isinstance(item, (tuple, list)) and len(item) > 1:
            labeled.setdefault("G:" + item[1][:12], item[1])
for s in lit_assigns(TRAIN_FILES["_dg_step1.py"]).get("CTRL_CATCH", []):
    labeled.setdefault("C:" + s[:12], s)
# 只保留长度 >= 8 的中文句子用于近重复比较
SENTS = {k: v for k, v in labeled.items() if len(v) >= 8 and re.search(r"[\u4e00-\u9fff]", v)}
SENTS_LIST = sorted(set(SENTS.values()))
print("  带 id 训练句子数 =", len(SENTS), " 去重后 =", len(SENTS_LIST))
near = {}
for x in rows:
    best = (10 ** 9, None, None)
    for s in SENTS_LIST:
        if abs(len(s) - len(x["text"])) > 22:
            continue
        d = lev(x["text"], s)
        if d < best[0]:
            ids = [k for k, v in SENTS.items() if v == s]
            best = (d, s, ids[:3])
    near[x["id"]] = {"dist": best[0], "sample": best[1], "train_ids": best[2],
                     "ratio": round(best[0] / max(len(x["text"]), len(best[1] or "")), 3)}
for x in rows:
    n = near[x["id"]]
    print("  %-4s min_edit=%-3d ratio=%-6s train=%-46s ids=%s" %
          (x["id"], n["dist"], n["ratio"], (n["sample"] or "")[:44], n["train_ids"]))
for k in (2, 3, 5, 8, 12):
    print("  min_edit <= %2d 的样本数 = %d" % (k, sum(1 for v in near.values() if v["dist"] <= k)))
print("  min_edit <= 3 的样本 ids =", [x["id"] for x in rows if near[x["id"]]["dist"] <= 3])

# =====================================================================
print("\n=== (5) 第三步 构式共享量化：DN 构式目录 / DG 七表 / hit 分解 ===")
GAPS19 = [g[0] for g in lit_assigns(TRAIN_FILES["_dg_step34.py"])["GAPS"]]
H5_EXTRA = lit_assigns(TRAIN_FILES["_dg_step34.py"])["H5_EXTRA"]
H5_SPLIT = lit_assigns(TRAIN_FILES["_dg_step34.py"])["H5_SPLIT"]
R12_TEN = list(DG.R12_TEN)
# H5_DN_EXTRA 纯字面支（sre_parse 口径：19 纯字面 + 1 通配支）
h5_lit_branches = [b for b in H5.H5_DN_EXTRA.split("|") if "[^" not in b]
h5_ten_branches = H5.H5_R12_TEN.split("|")
DN_FORMS = sorted(set(GAPS19 + R12_TEN + H5_EXTRA + H5_SPLIT + h5_lit_branches + h5_ten_branches))
print("  GAPS19=%d R12_TEN=%d H5_EXTRA=%d H5_SPLIT=%d H5_DN_EXTRA纯字面=%d H5_R12_TEN=%d DN_FORMS去重=%d" %
      (len(GAPS19), len(R12_TEN), len(H5_EXTRA), len(H5_SPLIT), len(h5_lit_branches),
       len(h5_ten_branches), len(DN_FORMS)))
print("  DN_FORMS =", json.dumps(DN_FORMS, ensure_ascii=False))
TABLES = {"NEG1": tuple(DG.NEG1), "MID": tuple(DG.MID), "NEG2": tuple(DG.NEG2),
          "GAP": tuple(DG.GAP), "SCOPE_VERB": tuple(DG.SCOPE_VERB),
          "SPLIT_TAIL": tuple(DG.SPLIT_TAIL), "PSEUDO_DN": tuple(DG.PSEUDO_DN)}
print("  DG 七表条目数 =", {k: len(set(v)) for k, v in TABLES.items()})
# _SECOND 14 词 / DG_BREAK_RE 10 词 / DG_COORD_RE / 4 类引号
SECOND = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔",
          "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
COORD = ["或", "以及", "同时", "并且", "一是", "二是", "其一", "其二", "/", "／", "、"]
QUOTES4 = ["「」", "『』", "“”", "``"]
FAMILY = sorted(set([w for v in TABLES.values() for w in v if len(w) >= 2] +
                    SECOND + BREAK10 + COORD + QUOTES4))

T12_CACHE = {}
def t12_decomp(h):
    if h in T12_CACHE:
        return T12_CACHE[h]
    out = []
    for n1 in set(DG.NEG1):
        for mid in set(DG.MID):
            for n2 in set(DG.NEG2):
                if n1 + mid + n2 == h:
                    out.append((n1, mid, n2))
    T12_CACHE[h] = out
    return out


def hit_in_tables(h):
    if not h:
        return {"literal": [], "t12": [], "t3": False, "decomposable": False}
    literal = [name for name, v in TABLES.items() if h in v]
    t12 = t12_decomp(h)
    m = DG.DG_DROPIN_RE.search(h)
    t3 = bool(m and m.group("t3"))
    return {"literal": literal, "t12": t12[:3], "t3": t3,
            "decomposable": bool(t12) or t3}


print("\n  --- 逐条：hit 是否在 DG 表内 / 是否可由 DG 表拼出 / 是否用了训练集构式 ---")
share_rows = []
for x in rows:
    s, hid = x["text"], x["id"]
    dn_in = sorted({k for k in DN_FORMS if k in s}, key=lambda z: -len(z))
    dn_shared = [k for k in dn_in if any(k in t for t in SENTS_LIST)]
    fam_in = sorted({w for w in FAMILY if w in s}, key=lambda z: -len(z))
    fam_shared = [w for w in fam_in if any(w in t for t in SENTS_LIST)]
    hp, hd = x["hits"]["DG_pure"], x["hits"]["DG_dropin"]
    dec_p, dec_d = hit_in_tables(hp), hit_in_tables(hd)
    share_rows.append({"id": hid, "dn_in": dn_in, "dn_shared": dn_shared,
                       "fam_in": fam_in[:8], "fam_shared": fam_shared[:8],
                       "hit_DG_pure": hp, "hit_DG_dropin": hd,
                       "pure_literal": dec_p["literal"], "pure_t12": dec_p["t12"],
                       "pure_t3": dec_p["t3"], "pure_decomposable": dec_p["decomposable"],
                       "dropin_decomposable": dec_d["decomposable"]})
    print("  %-4s dn_in=%-22s dn_shared=%-20s fam_shared=%-14s hit_p=%-14s 表内字面=%-10s T12分解=%s" %
          (hid, ",".join(dn_in[:3]), ",".join(dn_shared[:3]), ",".join(fam_shared[:3]),
           hp, ",".join(dec_p["literal"]) or "-", dec_p["t12"][:1] or "-"))
n_dn_in = sum(1 for r in share_rows if r["dn_in"])
n_dn_shared = sum(1 for r in share_rows if r["dn_shared"])
n_fam_shared = sum(1 for r in share_rows if r["fam_shared"])
n_hit = sum(1 for r in share_rows if r["hit_DG_pure"] or r["hit_DG_dropin"])
n_dec = sum(1 for r in share_rows if r["pure_decomposable"] or r["dropin_decomposable"])
print("  含目录内 DN 构式的样本数 =", n_dn_in, "/41")
print("  且该构式出现在训练句子里的样本数 (D1) =", n_dn_shared, "/41")
print("  含表内构式且命中串可由 DG 表拼出的样本数 (D3) =", n_dec, "/41 ；任意 DG hit 非空 =", n_hit, "/41")
print("  ★ 用了训练集出现过的构式（D1 ∪ D3）= ",
      len({r["id"] for r in share_rows if r["dn_shared"] or r["pure_decomposable"] or r["dropin_decomposable"]}), "/41")
print("  共享族词(MID/PSEUDO/boundary/_SECOND/引号)的样本数 =", n_fam_shared, "/41")
print("  DG_pure 非空 hit 全部可由 DG 表 T12/T3 拼出 =",
      all(r["pure_decomposable"] for r in share_rows if r["hit_DG_pure"]))
print("\n  --- 第三步(c) fp 7 条（P06-P12）hit 明细 ---")
for x in rows:
    if x["id"] in ("P06", "P07", "P08", "P09", "P10", "P11", "P12"):
        r = next(z for z in share_rows if z["id"] == x["id"])
        print("  %-4s DG_pure_hit=%-14s 表内字面=%-8s T12分解=%-24s T3=%-5s dn_in=%s" %
              (x["id"], r["hit_DG_pure"], ",".join(r["pure_literal"]) or "-",
               str(r["pure_t12"][:1]), r["pure_t3"], r["dn_in"][:3]))

# =====================================================================
print("\n=== (6) 第二步 四级独立性判据逐条定级 ===")
# L0: s ∉ TRAIN_ALL（精确）
# L1: 且 不共享同一 DN 构式（dn_shared 为空 且 hit 非空表内构式为空）
# L2: 且 不共享同一 MID/PSEUDO/boundary 词（fam_shared 为空）
# L3: 且 不是同一套表拼出来的（既非表内构式、又非训练集近重复 min_edit<=5、又不依赖表内族词）
grade_rows = []
for x in rows:
    r = next(z for z in share_rows if z["id"] == x["id"])
    L0 = x["text"] not in TRAIN_ALL
    shared_dn = bool(r["dn_shared"]) or bool(r["pure_decomposable"]) or bool(r["dropin_decomposable"])
    shared_family = bool(r["fam_shared"]) or bool(r["dn_in"])
    same_tables = (near[x["id"]]["dist"] <= 5) or bool(r["dn_in"]) or bool(r["fam_shared"])
    if not L0:
        g = "belowL0"
    elif shared_dn:
        g = "L0"
    elif shared_family:
        g = "L1"
    elif same_tables:
        g = "L2"
    else:
        g = "L3"
    grade_rows.append({"id": x["id"], "shape": x["shape"], "grade": g,
                       "L0": L0, "shared_dn": shared_dn, "shared_family": shared_family,
                       "same_tables": same_tables, "min_edit": near[x["id"]]["dist"],
                       "min_edit_train": near[x["id"]]["train_ids"],
                       "attack": x["attack"]})
    print("  %-4s shape=%-14s grade=%-4s shared_dn=%-5s shared_family=%-5s same_tables=%-5s min_edit=%-3s attack=%s" %
          (x["id"], x["shape"], g, shared_dn, shared_family, same_tables,
           near[x["id"]]["dist"], x["attack"] or "-"))
print("  ★ 分级分布 =", json.dumps(dict(Counter(r["grade"] for r in grade_rows)), ensure_ascii=False))
print("  达 L2 及以上的样本数 =", sum(1 for r in grade_rows if r["grade"] in ("L2", "L3")),
      " 达 L3 =", sum(1 for r in grade_rows if r["grade"] == "L3"))
print("  attack 字段非空（自述攻某条不变式）的样本数 =", sum(1 for r in grade_rows if r["attack"]))
print("  why 字段含 _dg_core.py: 引用的样本数 =",
      sum(1 for x in rows if "_dg_core.py:" in x["why"]))

# =====================================================================
print("\n=== (7) 第四步 六条绕过构造独立重跑（自建语料，非照抄） ===")
# ① 未登记边界/让步词
MY_BREAK = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究",
            "总而言之", "归根结底", "话说回来", "退一步说", "哪怕", "说白了"]
b_rows = []
for w in MY_BREAK:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = detect(t)
    b_rows.append({"w": w, "in_DG_BREAK_RE": bool(DG.DG_BREAK_RE.search(w)),
                   "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"]})
print("  ① 未登记词 n=%d ; BREAK=False 且 DG_pure=CATCH 的条数 = %d ; 明细 = %s" %
      (len(b_rows), sum(1 for z in b_rows if not z["in_DG_BREAK_RE"] and z["DG_pure"] == "CATCH"),
       [(z["w"], z["DG_pure"], z["DG_dropin"]) for z in b_rows]))
reg_rows = []
for w in BREAK10:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _ = detect(t)
    reg_rows.append((w, r["DG_pure"], r["DG_dropin"]))
print("  ①b 已登记 10 词：DG_pure=PASS %d/10 ; DG_dropin=CATCH %d/10 ; 明细=%s" %
      (sum(1 for z in reg_rows if z[1] == "PASS"),
       sum(1 for z in reg_rows if z[2] == "CATCH"), reg_rows))
# ② 未登记引号
MY_QUOTES = [('"', '"'), ("《", "》"), ("(", ")"), ("'", "'"), ("【", "】"), ("〈", "〉"), ("｢", "｣")]
q_rows = []
for op, cl in MY_QUOTES:
    t = op + "并非不宣告已生效" + cl + "只是引文，本件不采信该说法"
    r, _ = detect(t)
    q_rows.append({"q": op + cl, "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"]})
print("  ② 未登记引号 n=%d ; DG_pure=CATCH（应 PASS）的条数 = %d ; 明细 = %s" %
      (len(q_rows), sum(1 for z in q_rows if z["DG_pure"] == "CATCH"), q_rows))
t = "「 并非不宣告已生效 」只是引文，本件不采信该说法"
r, _ = detect(t)
print("  ②b 已登记「」内置空格：expect=PASS DG_pure=%s DG_dropin=%s R12=%s" %
      (r["DG_pure"], r["DG_dropin"], r["R12"]))
# ③ MID / COMP
MY_MID = ["容", "许", "想", "愿", "甘", "料", "要", "需", "欲", "准"]
m_rows = []
for w in MY_MID:
    t = "不" + w + "不宣告本件已生效"
    r, _ = detect(t)
    m_rows.append({"mid": w, "in_MID": w in set(DG.MID), "DG_pure": r["DG_pure"]})
print("  ③ 未登记 MID n=%d ; 在表内=False 且 DG_pure=PASS（真 DN 漏判）的条数 = %d ; 明细 = %s" %
      (len(m_rows), sum(1 for z in m_rows if not z["in_MID"] and z["DG_pure"] == "PASS"), m_rows))
c_rows = []
for n in range(0, 8):
    t = "非登记" + "原" * n + "不可才算本件已生效"
    r, _ = detect(t)
    c_rows.append((n, r["DG_pure"], r["DG_dropin"]))
print("  ③b COMP 0..7 字数扫描 = %s ; ≤4 全 CATCH=%s ; ≥5 全 PASS=%s" %
      (c_rows, all(z[1] == "CATCH" for z in c_rows if z[0] <= 4),
       all(z[1] == "PASS" for z in c_rows if z[0] >= 5)))
# ④ 第二主语 veto 结构性不可达
parts = (list(DG.NEG1) + list(DG.MID) + list(DG.NEG2) + list(DG.GAP) +
         list(DG.SCOPE_VERB) + list(DG.SPLIT_TAIL))
in_parts = {s: [p for p in parts if s in p] for s in SECOND}
print("  ④ _SECOND 14 词出现在任一 DG 表条目内 =",
      {k: v for k, v in in_parts.items() if v} or "{}（全空）")
t12_hits = {n1 + mid + n2 for n1 in set(DG.NEG1) for mid in set(DG.MID) for n2 in set(DG.NEG2)}
print("  ④ T12 笛卡尔积 hit_text 数 =", len(t12_hits),
      "; 其中含 _SECOND 任一项 =", sum(1 for h in t12_hits if any(s in h for s in SECOND)))
print("  ④ comp 负向前瞻排除 _SECOND（_dg_core.py:118）= 静态可见；"
      "'非登记本件不可才算本件已生效' DG_pure =", detect("非登记本件不可才算本件已生效")[0]["DG_pure"])
fired2, fired5, fired_ids = 0, 0, []
for x in rows:
    for tok in TOKS:
        for m in re.finditer(re.escape(tok), x["text"]):
            d = DG.dg_double_neg(x["text"][:m.start()])
            if "第二主语" in d["reason"]:
                fired2 += 1; fired_ids.append((x["id"], "第二主语"))
            if "并列标记" in d["reason"]:
                fired5 += 1; fired_ids.append((x["id"], "并列标记"))
print("  ④ 41 条上『第二主语』veto 实际触发次数 =", fired2,
      "；『并列标记』veto 触发次数 =", fired5, "；触发明细 =", fired_ids)
ss = ["并非本件不宣告已生效", "并不否认甲方不宣告已生效", "非登记本件不可才算本件已生效"]
for t in ss:
    r, _ = detect(t)
    print("  ④ 双向反例 %-22s DG_pure=%-5s H5_lit=%s" % (t[:20], r["DG_pure"], r["H5_lit"]))
# ⑤ 并列 veto 只查 hit_text
coord_cases = ["本件不承认或并不否认已生效", "本件不承认、并不否认均不成立已生效",
               "非登记一或二不可才算本件已生效", "非登记甲、乙不可才算本件已生效",
               "非登记原件不可才算本件已生效"]
print("  ⑤ 自建并列构造：")
for t in coord_cases:
    r, h = detect(t)
    print("    %-30s DG_pure=%-5s DG_dropin=%-5s raw_hit=%s" %
          (t[:28], r["DG_pure"], r["DG_dropin"], h["DG_dropin"]))
# ⑥ PSEUDO_DN 词首负向前瞻位置局部性
my_pseudo = ["无非不是不承认本件已生效", "莫非并不是不承认本件已生效",
             "没不承认本件已生效", "非不承认本件已生效", "没没不承认本件已生效",
             "莫不是不承认本件已生效"]
print("  ⑥ 自建 PSEUDO 位置变体：")
for t in my_pseudo:
    r, h = detect(t)
    print("    %-30s DG_pure=%-5s raw_hit=%s" % (t[:28], r["DG_pure"], h["DG_dropin"]))
pseudo_rows = []
for p in DG.PSEUDO_DN:
    t = p + "不承认本件已生效"
    raw = bool(DG.DG_DROPIN_RE.search(t[:t.find("已生效")]))
    pure = bool(DG.dg_scan(t, ["已生效"])[0])
    pseudo_rows.append((p, raw, pure))
print("  ⑥ 12 项逐项 raw_regex=%s ; True(命中从 veto 词之后另起)=%d/12" %
      (pseudo_rows, sum(1 for z in pseudo_rows if z[1])))
# ⑦ 奇偶四象限（自建，复现）
quad = [("G1", "不查不验本件已生效", "PASS"), ("G2", "未漏核，并非不宣告本件已生效", "CATCH"),
        ("G3", "非登记五份原始件不可才算本件已生效", "CATCH"),
        ("G4", "前稿不敢不承认其实本件不宣告已生效", "PASS")]
print("  ⑦ 奇偶四象限：")
for cid, t, exp in quad:
    r, _ = detect(t)
    negc = 0
    for m in re.finditer("已生效", t):
        st = max(0, m.start() - G7.NEG_WINDOW)
        bd = max(t.rfind(ch, 0, m.start()) for ch in G7.CLAUSE_BREAK)
        if bd > st: st = bd
        negc = max(negc, len(G7.NEG_RE.findall(t[st:m.start()])))
    parity = "CATCH" if negc % 2 == 0 and negc > 0 else "PASS"
    print("    %s neg_count=%d expect=%-5s parity=%-5s DG_pure=%s" % (cid, negc, exp, parity, r["DG_pure"]))
# 交付形态 guard 不执行（co_names）
guards = ["_mask_quotes", "_scope", "dg_double_neg", "DG_SECOND_SUBJ_RE", "DG_COORD_RE"]
for fname in ("r10_context", "r12_scan"):
    names = set(getattr(DROP, fname).__code__.co_names)
    print("  交付形态 %-12s co_names 含 guard = %s" %
          (fname, {g: (g in names) for g in guards}))

# =====================================================================
print("\n=== (8) 保护树零写核验（会话内前/后快照） ===")
SNAP1 = snapshot()
print("  保护树文件数 前=%d 后=%d ; 全量 sha256+bytes+mtime_ns 一致 = %s" %
      (len(SNAP0), len(SNAP1), SNAP0 == SNAP1))
print("  新增文件 =", sorted(set(SNAP1) - set(SNAP0)), " 消失文件 =", sorted(set(SNAP0) - set(SNAP1)))
print("  九件指纹二次重算 ALL_MATCH =",
      all(sha(ROOT / r) == (h, n) for r, (h, n) in EXPECT.items()))

OUT = {
    "fingerprints": {r: {"sha": h, "bytes": n, "verified": True} for r, (h, n) in EXPECT.items()},
    "protected_unchanged": SNAP0 == SNAP1,
    "novelty": {"n_cases": len(CASES), "train_strings_per_file": per_file,
                "train_union": len(TRAIN_ALL), "exact_overlap": overlap,
                "substring_pairs": sub_relations},
    "rows": rows, "strict": strict, "forced": forced,
    "orch_hits_match": not mismatch, "shape_hist": shape_hist,
    "train_sentences_n": len(SENTS_LIST), "near": near,
    "dn_forms": DN_FORMS, "tables": {k: sorted(set(v)) for k, v in TABLES.items()},
    "share_rows": share_rows, "grade_rows": grade_rows,
    "grade_distribution": dict(Counter(r["grade"] for r in grade_rows)),
    "invariant_reruns": {"1_break": b_rows, "1b_registered": reg_rows, "2_quotes": q_rows,
                         "3_mid": m_rows, "3b_comp": c_rows,
                         "4_second_in_parts": {k: v for k, v in in_parts.items() if v},
                         "4_t12_hits_n": len(t12_hits), "4_second_veto_fired": fired2,
                         "4_coord_veto_fired": fired5, "4_fired_ids": fired_ids,
                         "5_coord": coord_cases, "6_pseudo": pseudo_rows,
                         "7_quad": quad},
}
(WD / "_ai_verify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _ai_verify_out.json")
