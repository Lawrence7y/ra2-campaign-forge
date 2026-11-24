# -*- coding: utf-8 -*-
r"""_fd_probe3.py — E2 补充探针：(乙3) 最大非灾难删除臂 / 各臂 fp 命中串再生证据 /
C11@乙2 命中细节 / 引号类歧义在本语料的影响面 / jiac 对 A02,C20 的回归。只写本任务写域。"""
import sys, json, hashlib, re, ast, types
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SB = WD / "_fd_sandbox"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
OUT = {}

def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

def load_src(name, path):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), m.__dict__)
    return m

def lit_assigns(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Name):
                    try: out[tgt.id] = ast.literal_eval(n.value)
                    except Exception: pass
    return out

A = lit_assigns(DGA / "_dga_adversarial.py")
CASES = A["CASES"]
BY = {c[0]: c for c in CASES}
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

def detect_with(DG, G7, text):
    G7.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
    toks = [t for t in TOKS if t in text] or ["已生效"]
    p, h = DG.dg_scan(text, toks)
    return ("CATCH" if p else "PASS"), (h[0]["hit"] if h else "")

DG0 = load_src("dg0", SB / "_dg_core_base.py")
G70 = load_src("g70", SB / "_g7_predicates_base.py")

# ---------- (A) 各臂 fp 命中串（再生证据） ----------
print("=== (A) 各臂下 7 条 fp 的 DG_pure 命中串（构式再生证据） ===")
ARMS = [("base", SB / "_dg_core_base.py"), ("jia", WD / "_fd_dg_core_jia.py"),
        ("yi_NEG1删不敢并不并非", WD / "_fd_dg_core_yi.py"),
        ("yi2_NEG2删否认不承认", WD / "_fd_dg_core_yi2.py")]
regen = {}
for name, path in ARMS:
    DG = load_src("d_" + name, path)
    row = {}
    for pid in ["P06", "P07", "P08", "P09", "P10", "P11", "P12"]:
        v, hit = detect_with(DG, G70, BY[pid][2])
        row[pid] = [v, hit]
    regen[name] = row
    print(name, json.dumps(row, ensure_ascii=False))
OUT["fp_hit_string_per_arm"] = regen

print("\n=== (A2) 表内再生路径独立验证（在 yi 核上） ===")
DGY = load_src("d_yi", WD / "_fd_dg_core_yi.py")
paths = {
    "不敢不承认 经 不+敢+不承认": "不敢不承认",
    "不否认 经 不+ε+否认": "不否认",
    "P08 全 pre (yi)": "旧稿并不否认尽管本件不宣告",
}
path_proof = {}
for k, s in paths.items():
    m = DGY.DG_DROPIN_RE.search(s)
    path_proof[k] = {"search_target": s, "match": m.group(0) if m else "", "matched": bool(m)}
    print("%s => match=%r" % (k, m.group(0) if m else ""))
OUT["regen_path_proof"] = path_proof

# ---------- (B) 乙3：最大非灾难删除臂 ----------
print("\n=== (B) 乙3 = NEG1-{不敢,并不,并非} + NEG2-{否认,不承认,不宣告} + MID-{敢} ===")
base_txt = (SB / "_dg_core_base.py").read_text(encoding="utf-8")
def apply(txt, old, new, tag):
    assert txt.count(old) == 1, tag
    return txt.replace(old, new)
t = base_txt
t = apply(t, '    "并非", "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",',
          '    "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",', "乙3 删并非")
t = apply(t, '    "不能", "不可", "不得", "没有", "不敢", "不会", "不可能", "不该", "不应",',
          '    "不能", "不可", "不得", "没有", "不会", "不可能", "不该", "不应",', "乙3 删不敢")
t = apply(t, '    "没法", "无法", "不见得", "不一定", "不否认", "并不",',
          '    "没法", "无法", "不见得", "不一定", "不否认",', "乙3 删并不")
t = apply(t, '    "否认", "不承认", "不认为", "不宣告", "不出现",',
          '    "不认为", "不出现",', "乙3 删否认/不承认/不宣告")
t = apply(t, '    "会", "敢", "必", "免", "始", "尝", "曾", "有",',
          '    "会", "必", "免", "始", "尝", "曾", "有",', "乙3 删MID敢")
p3 = WD / "_fd_dg_core_yi3.py"
p3.write_text(t, encoding="utf-8", newline="")
h, n = sha(p3)
print("被核对象 SHA256 = %s，字节数 = %d  (_fd_dg_core_yi3.py)" % (h, n))
DG3 = load_src("d_yi3", p3)
print("n_NEG1=%d n_MID=%d n_NEG2=%d" % (len(set(DG3.NEG1)), len(set(DG3.MID)), len(set(DG3.NEG2))))
OUT["yi3_core_sha256"] = h
OUT["yi3_core_bytes"] = n
rows3 = {}
fp3, fn3 = [], []
for c in CASES:
    v, hit = detect_with(DG3, G70, c[2])
    rows3[c[0]] = [c[3], v, hit]
    if c[3] == "PASS" and v == "CATCH": fp3.append(c[0])
    if c[3] == "CATCH" and v == "PASS": fn3.append(c[0])
print("yi3 strict fp=%d %s ; fn=%d %s" % (len(fp3), fp3, len(fn3), fn3))
OUT["yi3_strict"] = {"fp_ids": fp3, "fn_ids": fn3, "verdicts": rows3}
for pid in ["P06", "P07", "P08", "P11", "C11", "C17", "C18", "C19"]:
    print("  yi3 %s expect=%s => %s hit=%r" % (pid, rows3[pid][0], rows3[pid][1], rows3[pid][2]))

# 灾难臂：NEG2 再删单字「不」（仅内存，不落盘）
t_cata = t.replace('    "不", "没", "没有", "毫无", "无", "未", "非", "莫", "别", "勿", "不是",',
                   '    "没", "没有", "毫无", "无", "未", "非", "莫", "别", "勿", "不是",')
assert t_cata != t
mcata = types.ModuleType("cata")
exec(compile(t_cata, "cata", "exec"), mcata.__dict__)
v, hit = detect_with(mcata, G70, BY["P06"][2])
v13, h13 = detect_with(mcata, G70, BY["C13"][2])
v15, h15 = detect_with(mcata, G70, BY["C15"][2])
OUT["yi4_catastrophic"] = {"P06": [v, hit], "C13": [v13, h13], "C15": [v15, h15],
                           "R12_TEN_anchor_all_generated": all(bool(mcata.DG_DROPIN_RE.search(c)) for c in mcata.R12_TEN)}
print("灾难臂(NEG2 再删单字不): P06=%s(%r) C13=%s(%r) C15=%s(%r) R12_TEN锚=%s" % (
    v, hit, v13, h13, v15, h15, OUT["yi4_catastrophic"]["R12_TEN_anchor_all_generated"]))

# ---------- (C) C11@乙2 命中细节 ----------
print("\n=== (C) C11 在乙2 下的命中细节 ===")
DG2 = load_src("d_yi2", WD / "_fd_dg_core_yi2.py")
c11 = BY["C11"][2]
m = re.search(re.escape("已生效"), c11)
r = DG2.dg_double_neg(c11[:m.start()], c11[m.end():])
OUT["C11_at_yi2"] = {"pre": c11[:m.start()], "hit_text": r["hit_text"], "reason": r["reason"], "hit": r["hit"]}
print(json.dumps(OUT["C11_at_yi2"], ensure_ascii=False))
m2 = DG2.DG_DROPIN_RE.search("非不承认本件")
OUT["C11_yi2_direct_search"] = {"target": "非不承认本件", "match": m2.group(0) if m2 else ""}
print("直接 search('非不承认本件') =>", repr(m2.group(0) if m2 else ""))

# ---------- (D) 引号类歧义在本语料的影响面 ----------
print("\n=== (D) 41 条中出现的引号字符扫描 ===")
QUOTE_CHARS = {'"': 'ASCII双引号', '《': '书名号', '“': '弯双引号', '「': '直角引号',
               '『': '双直角', '`': '反引号', "'": 'ASCII单引号', '（': '全角圆括号',
               '【': '方头括号', '〈': '角括号', '｢': '半角直角'}
found = {}
for c in CASES:
    for ch, nm in QUOTE_CHARS.items():
        if ch in c[2]:
            found.setdefault(nm, []).append(c[0])
OUT["quote_chars_in_41"] = found
print(json.dumps(found, ensure_ascii=False))

# ---------- (E) jiac 对 A02/C20 的回归细节 ----------
print("\n=== (E) jiac 整窗 veto 对 A02/C20 的回归 ===")
DGJ = load_src("d_jiac", WD / "_fd_dg_core_jiac.py")
for aid in ["A02", "C20"]:
    c = BY[aid]
    toks = [t for t in TOKS if t in c[2]] or ["已生效"]
    tok = toks[0]
    m = re.search(re.escape(tok), c[2])
    r = DGJ.dg_double_neg(c[2][:m.start()], c[2][m.end():])
    OUT["jiac_" + aid] = {"text": c[2], "hit": r["hit"], "hit_text": r["hit_text"],
                          "scope": r["scope"], "reason": r["reason"]}
    print(aid, json.dumps(OUT["jiac_" + aid], ensure_ascii=False))

print("\n=== (F) 原件复核 ===")
for rel in ["lead/dneg_generative_20261109/_dg_core.py", "lead/gate_fp7_20261108/_g7_predicates.py",
            "lead/dg_adversarial_20261109/_dga_adversarial.py"]:
    hh, nn = sha(ROOT / rel)
    print("被核对象 SHA256 = %s，字节数 = %d  (%s)" % (hh, nn, rel))
(WD / "_fd_probe3_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("written: _fd_probe3_out.json")
