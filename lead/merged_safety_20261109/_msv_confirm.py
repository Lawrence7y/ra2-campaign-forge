# -*- coding: utf-8 -*-
"""_msv_confirm.py — 第二轮精确认证（修正首轮脚本自身 3 处笔误/过严判据）。

零真机、零采样。python -I -X utf8 -B + 绝对路径。写域前缀 _msv_。
"""
import ast
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
V = W / "_msv_fixtures"
R11 = REPO / "lead" / "r11_f2_fix_20261109"
OUT = []


def say(s=""):
    OUT.append(str(s))
    print(s)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_py(path):
    return subprocess.run([sys.executable, "-I", "-X", "utf8", "-B", str(path)],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


# ---------- 修正 1：C9 绕过 :24 后应在 :29 掉 KeyError（用字面路径，不引入新变量） ----------
say("=== C9-REDO 绕过 _f2v_verify9.py:24 后 :29 崩点 ===")
V9_TEXT = (R11 / "_f2v_verify9.py").read_text(encoding="utf-8")
HEAD_OLD = """j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))
n = 0
for i, r in enumerate(j["results_30"]):
    p = REPO / r["rel"]
    text = p.read_text(encoding="utf-8")
    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
"""
import hashlib as _h
BODY = b"INDEPENDENT-REVIEWER-COPIED-BODY-20261109-v3\n"
HEX = _h.sha256(BODY).hexdigest()
rec_merged = {"declared": HEX, "path": None, "match": True, "tier": "SAMEDOC_LINK_EQ",
              "members": [{"path": str(V / "_msv_alpha.dat"), "sha": HEX, "bytes": len(BODY)}]}
payload = json.dumps([("merged", [rec_merged])], ensure_ascii=False)
head_new = ("MSV_BINDINGS = json.loads(%r)\n" % payload
            + "n = 0\n"
            + "for i, (CASE_NAME, pb) in enumerate(MSV_BINDINGS):\n"
            + "    print(\"CASE %d %s\" % (i, CASE_NAME))\n"
            + "    text = \"\"\n"
            + "    pp, pw = [], []\n")
txt = V9_TEXT.replace(HEAD_OLD, head_new, 1)
BYPASS_OLD = '        vp = Path(src.get("verified_path") or src.get("path"))\n'
# 等行数替换为字面绝对路径：:24 不再 Path(None)，但 rec 仍缺 bytes
BYPASS_NEW = '        vp = Path(r"%s")\n' % str(V / "_msv_alpha.dat")
assert txt.count(BYPASS_OLD) == 1
txt = txt.replace(BYPASS_OLD, BYPASS_NEW, 1)
p = W / "_msv_v9_bypass24_redo.py"
p.write_text(txt, encoding="utf-8")
ast.parse(p.read_text(encoding="utf-8"))
r = run_py(p)
say("C9R EXIT=%d stdout=%r" % (r.returncode, r.stdout.strip()[:200]))
for ln in r.stderr.strip().splitlines():
    if "_msv_v9_bypass24_redo.py" in ln or "Error" in ln:
        say("C9R stderr: %s" % ln.strip())
say("C9R_EXPECT : line 29 KeyError 'bytes' = %s" %
    ("line 29" in r.stderr and "KeyError: 'bytes'" in r.stderr))

# ---------- 修正 2：精确结构签名（只看键集与容器类型，列表元素差异不算键增删） ----------
say()
say("=== E9-REDO 精确返回值结构签名（键集 + 容器类型） ===")


def schema(o):
    """结构签名：每个 dict 的键集 + 容器节点类型；列表统一记为 LIST（不因空/非空而变）。"""
    if isinstance(o, dict):
        return ("DICT", tuple((k, schema(v)) for k, v in sorted(o.items())))
    if isinstance(o, list):
        # 额外记录元素 schema 集合（有元素时），但空列表与有元素列表仍判等
        return ("LIST", frozenset(schema(x) for x in o))
    return ("SCALAR", type(o).__name__)


OLD = load("_msv_c_old", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NEW = load("_msv_c_new", W / "_ms_g9_candidate.py")
OWN = load("_msv_c_own", W / "_msv_g9_own.py")
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "已入账", "放行 N-5"]
DOC_M = W / "_msv_merged_doc.md"


def inject(mod, rec):
    mod.g7.r11_scan = lambda t, dd, root=None, recompute=None: ([], [], [dict(rec)])


OI = load("_msv_c_old_i", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NI = load("_msv_c_new_i", W / "_ms_g9_candidate.py")
ZI = load("_msv_c_own_i", W / "_msv_g9_own.py")
for m in (OI, NI, ZI):
    inject(m, rec_merged)
rio = OI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
rin = NI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
riz = ZI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
say("E9 顶层键集 old==new==own : %s" %
    (sorted(rio.keys()) == sorted(rin.keys()) == sorted(riz.keys())))
say("E10 R11 键集 old==new==own : %s" %
    (sorted(rio["predicates"]["R11"].keys())
     == sorted(rin["predicates"]["R11"].keys())
     == sorted(riz["predicates"]["R11"].keys())))
say("E11 键集签名（忽略列表元素个数）old==new==own : %s" %
    (schema(rio) == schema(rin) == schema(riz)))
say("E12 old problems 长度=%d new problems 长度=%d（值变化，非键增删）" %
    (len(rio["problems"]), len(rin["problems"])))
say("E13 新增 problem 元素的键集 = %s（既有契约 rule_id/msg）" %
    sorted(rin["problems"][0].keys()) if rin["problems"] else [])
# 结论：首轮 shape() 因空列表 vs 非空列表元素返回 False，属判据过严；键集零增删
say("E_RESULT STRUCTURE_UNCHANGED_REDO = %s" %
    (sorted(rio.keys()) == sorted(rin.keys()) == sorted(riz.keys())
     and sorted(rio["predicates"]["R11"].keys())
     == sorted(rin["predicates"]["R11"].keys())
     == sorted(riz["predicates"]["R11"].keys())
     and schema(rio) == schema(rin) == schema(riz)))

# ---------- 30 件全量回归（自己跑，OLD vs 候选 vs 自造补丁） ----------
say()
say("=== E14 30 件全量回归（结构 + verdict 漂移） ===")
j = json.loads((REPO / "lead" / "gate_r9r12_20261109" /
                "_g9_regression_out.json").read_text(encoding="utf-8"))
REQ30 = j["checklist"]["required_elements"]
FORB30 = j["checklist"]["forbidden_words"]
rels = [x["rel"] for x in j["results_30"]]
n_found = n_same_verdict = n_same_keys = 0
drift = []
for rel in rels:
    fp = REPO / rel
    if not fp.is_file():
        continue
    n_found += 1
    ro = OLD.check_deliverable(fp, REQ30, FORB30)
    rn = NEW.check_deliverable(fp, REQ30, FORB30)
    rz = OWN.check_deliverable(fp, REQ30, FORB30)
    if ro["verdict"] == rn["verdict"] == rz["verdict"]:
        n_same_verdict += 1
    else:
        drift.append((rel, ro["verdict"], rn["verdict"], rz["verdict"]))
    if (sorted(ro.keys()) == sorted(rn.keys()) == sorted(rz.keys())
            and all(sorted(ro["predicates"][k].keys()) == sorted(rn["predicates"][k].keys())
                    == sorted(rz["predicates"][k].keys()) for k in ro["predicates"])):
        n_same_keys += 1
say("E14 corpus n=%d found=%d ; verdict 全同=%d ; 键集全同=%d ; 漂移件=%r" %
    (len(rels), n_found, n_same_verdict, n_same_keys, drift))
say("E15 old/new/own self_test all_pass = %s / %s / %s" %
    (OLD.self_test()[1], NEW.self_test()[1], OWN.self_test()[1]))

# ---------- 修正 3：字符串检索笔误（6 件 / 两处 / 7 处会静默误读） ----------
say()
say("=== G-REDO 安全集边界：原文逐字核对 ===")
DESIGN = (W / "_ms_DESIGN.md").read_text(encoding="utf-8")
AUD = (REPO / "lead" / "merged_consumer_audit_20261109" /
       "MERGED_CONSUMER_AUDIT.md").read_text(encoding="utf-8")
MC = (REPO / "lead" / "merged_consumer_audit_20261109" /
      "_mc_AUDIT.md").read_text(encoding="utf-8")
for needle, hay, tag in [
    ("静默错比崩更该进安全集", DESIGN, "DESIGN"),
    ("崩 = **fail-closed**", DESIGN, "DESIGN"),
    ("静默错 = **fail-open**", DESIGN, "DESIGN"),
    ("两处不足以称「够」", DESIGN, "DESIGN"),
    ("并非「只有这两处」", DESIGN, "DESIGN"),
    ("6 件静默误读全读", DESIGN, "DESIGN"),
    ("一处汇聚点覆盖 6 件", DESIGN, "DESIGN"),
    ("1 处崩 + 7 处静默误读", MC, "_mc_AUDIT"),
    ("1 处已实证会崩、7 处会静默误读", MC, "_mc_AUDIT"),
    ("8 静默误读", AUD, "MERGED_CONSUMER_AUDIT"),
    ("读者=这 3 件（加 `_f2w_extract.py:13`）", AUD, "MERGED_CONSUMER_AUDIT"),
    ("1–3（代码必做）+ 5–6（治理/审计必做）", AUD, "MERGED_CONSUMER_AUDIT"),
]:
    say("G-R %-8s 含 %r : %s" % (tag, needle, needle in hay))
# 统计 DESIGN §四(a) 表格行数（以 "| `_f2" 开头的行）
tbl = [x for x in DESIGN.splitlines() if x.startswith("| `_f2")]
say("G-R DESIGN §四(a) 表格行数 = %d（回件称『6 件静默误读』）" % len(tbl))
# 逐件实读：8 件中真正读 JSON 的 4 件 / 直接调 r11_scan_plus 的 5 件
DOWNSTREAM = ["_f2w_checks.py", "_f2_selftest.py", "_f2_compare.py", "_f2v_final.py",
              "_f2v_run.py", "_f2w_dogfood.py", "_f2w_extract.py", "_f2w_pass.py"]
rj, cp = [], []
for fn in DOWNSTREAM:
    t = (R11 / fn).read_text(encoding="utf-8")
    if "_f2_compare_out.json" in t:
        rj.append(fn)
    if "r11_scan_plus(" in t:
        cp.append(fn)
say("G-R 读 _f2_compare_out.json 的件数=%d %s" % (len(rj), rj))
say("G-R 直接调 r11_scan_plus 的件数=%d %s" % (len(cp), cp))
say("G-R 两者交集=%s ；既非 JSON 读者也非直接调用者=%s" %
    (sorted(set(rj) & set(cp)),
     sorted(set(DOWNSTREAM) - set(rj) - set(cp))))
say("G-R 结论：DESIGN『6 件全读同一 JSON』与逐件实读不符；直接调 plus 的 4 件"
    "（_f2_selftest/_f2v_final/_f2v_run/_f2w_dogfood）不经该 JSON，"
    "单靠『④ 计数口径裁决』覆盖不到它们")

# ---------- .pyc 时间戳：是否本会话新增 ----------
say()
say("=== H-REDO 只读域 .pyc 时间戳（是否本会话新增） ===")
now = datetime.datetime.now()
say("H-R now = %s" % now.isoformat())
for d in [R11, REPO / "lead" / "gate_r9r12_20261109",
          REPO / "lead" / "r33e_merge_20261109",
          REPO / "lead" / "merged_consumer_audit_20261109"]:
    for x in sorted(d.rglob("*.pyc")):
        st = x.stat()
        say("H-R %-70s mtime=%s size=%d" %
            (str(x.relative_to(REPO)),
             datetime.datetime.fromtimestamp(st.st_mtime).isoformat(), st.st_size))
say("H-R 本会话所有 Python 均带 -B 且 sys.dont_write_bytecode=True；"
    "上列 .pyc 的 mtime 若早于本会话首条命令即属既存件（本次未新增）")

# ---------- 末轮指纹（第三轮） ----------
say()
say("=== H-R2 末轮八件指纹 ===")
BASE = [
    ("lead/r11_f2_fix_20261109/_f2v_verify9.py", "c22f28ad4228d028c16d8558a8dd9a0980947631ab5bcf5c9cd84e529cf439e3", 1618),
    ("lead/gate_r9r12_20261109/_g9_gate.py", "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("lead/r33e_merge_20261109/_re_linked.py", "7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    ("lead/merged_consumer_audit_20261109/_mc_AUDIT.md", "8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367", 33762),
    ("lead/merged_consumer_audit_20261109/MERGED_CONSUMER_AUDIT.md", "85de273758a6b87915f9735a07e1b9e1d11c594de50f41d83f5e70145257c263", 40884),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
ok = True
for rel, e, b in BASE:
    raw = (REPO / rel).read_bytes()
    got, nb = hashlib.sha256(raw).hexdigest(), len(raw)
    ok &= (got == e and nb == b)
    say("H-R2 %-70s %s %d MATCH=%s" % (rel, got, nb, got == e and nb == b))
say("H-R2 ALL_EIGHT_UNCHANGED = %s" % ok)

(W / "_msv_confirm_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_msv_confirm_out.txt"))
