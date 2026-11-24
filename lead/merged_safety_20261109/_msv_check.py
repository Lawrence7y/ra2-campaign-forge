# -*- coding: utf-8 -*-
"""_msv_check.py — 独立复核员自造核验脚本（不复用编排方任何输出/夹具/候选副本结论）。

零真机、零采样。python -I -X utf8 -B + 绝对路径。
只读受保护件；新写文件全部落在 lead/merged_safety_20261109/ 写域，前缀 _msv_。
不修改 _f2v_verify9.py / _g9_gate.py / 任何既有件。
"""
import ast
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
V.mkdir(exist_ok=True)
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


# ============================ ① 八件指纹（首轮） ============================
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


def fps():
    return {rel: (hashlib.sha256((REPO / rel).read_bytes()).hexdigest(),
                  (REPO / rel).stat().st_size) for rel, _, _ in BASE}


FP_FIRST = fps()
say("=== A. 八件指纹首轮（本会话 hashlib 实算） ===")
for rel, e, b in BASE:
    got, nb = FP_FIRST[rel]
    say("A %-70s %s %d MATCH=%s" % (rel, got, nb, got == e and nb == b))
say("A_RESULT ALL_EIGHT_MATCH=%s" % all(FP_FIRST[r] == (e, b) for r, e, b in BASE))

# ============================ ② 自造 merged / unique / multi rec ============================
say()
say("=== B. 自己造 merged rec（自己的夹具、自己的 hex、自己的文档） ===")
re = load("_msv_re", REPO / "lead" / "r33e_merge_20261109" / "_re_linked.py")
MA = V / "_msv_alpha.dat"
MB = V / "_msv_beta.dat"
MC = V / "_msv_uniq.dat"
BODY = b"INDEPENDENT-REVIEWER-COPIED-BODY-20261109-v3\n"
MA.write_bytes(BODY)
MB.write_bytes(BODY)
UNIQ = b"INDEPENDENT-REVIEWER-UNIQUE-ANCHOR-20261109\n"
MC.write_bytes(UNIQ)
HEX = hashlib.sha256(BODY).hexdigest()
UHEX = hashlib.sha256(UNIQ).hexdigest()
NB = len(BODY)

DOC_M = W / "_msv_merged_doc.md"
DOC_M.write_text(
    "# 独立复核员 merged 夹具\n\n"
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "候选产物：`_msv_fixtures/_msv_alpha.dat`、`_msv_fixtures/_msv_beta.dat`。\n"
    "`_msv_fixtures/_msv_beta.dat` 复制自 `_msv_fixtures/_msv_alpha.dat`。\n"
    % (HEX, NB), encoding="utf-8")
text_m = DOC_M.read_text(encoding="utf-8")
prob_m, warn_m, rec_m = re.link_triple(text_m, W, HEX, NB, root=REPO)
say("B1 link() verdict=%s problems=%r warnings_n=%d" %
    (rec_m["samedoc_link"]["verdict"], prob_m, len(warn_m)))
say("B2 merged rec KEYS = %s" % sorted(rec_m.keys()))
say("B3 merged rec KEY COUNT = %d" % len(rec_m))
for k in ("verified_path", "recomputed", "bytes"):
    say("B4 MISSING KEY %-14s : %s" % (k, k not in rec_m))
say("B5 path=%r match=%r tier=%r members_n=%d" %
    (rec_m.get("path"), rec_m.get("match"), rec_m.get("tier"),
     len(rec_m.get("members") or [])))
say("B6 members (sha12,bytes) = %s" %
    [(m["sha"][:12], m["bytes"]) for m in (rec_m.get("members") or [])])
say("B7 samedoc_link.reverify=%r" % rec_m["samedoc_link"]["reverify"])
say("B8 declared==HEX? %s ; 全体 member sha==declared? %s" %
    (rec_m.get("declared") == HEX,
     all(m["sha"] == HEX for m in rec_m["members"])))
assert rec_m["samedoc_link"]["verdict"] == "merged"
assert sorted(rec_m.keys()) == ["decl_lines", "declared", "match", "members",
                               "path", "samedoc_link", "tier"]
assert all(k not in rec_m for k in ("verified_path", "recomputed", "bytes"))
assert rec_m["path"] is None and rec_m["match"] is True
assert rec_m["tier"] == "SAMEDOC_LINK_EQ" and len(rec_m["members"]) == 2
say("B_RESULT MERGED_REC_ASSERTS_OK = True")

DOC_U = W / "_msv_unique_doc.md"
DOC_U.write_text(
    "# 独立复核员 unique 夹具\n\n"
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "唯一产物：`_msv_fixtures/_msv_uniq.dat`。\n"
    % (UHEX, len(UNIQ)), encoding="utf-8")
prob_u, warn_u, rec_u = re.link_triple(DOC_U.read_text(encoding="utf-8"), W, UHEX,
                                      len(UNIQ), root=REPO)
say("B9 unique rec KEYS = %s ; verdict=%s path=%r match=%r tier=%r" %
    (sorted(rec_u.keys()), rec_u["samedoc_link"]["verdict"],
     rec_u.get("path"), rec_u.get("match"), rec_u.get("tier")))
say("B10 unique 含 verified_path/recomputed/bytes = %s" %
    [k in rec_u for k in ("verified_path", "recomputed", "bytes")])
assert rec_u["samedoc_link"]["verdict"] == "unique"
assert rec_u.get("path") and rec_u.get("match") is True
assert all(k in rec_u for k in ("verified_path", "recomputed", "bytes"))

DOC_X = W / "_msv_multi_doc.md"
DOC_X.write_text(
    "# 独立复核员 multi 夹具\n\n"
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "产物：`_msv_fixtures/_msv_alpha.dat` 与 `_msv_fixtures/_msv_beta.dat`。\n"
    % (HEX, NB), encoding="utf-8")
prob_x, warn_x, rec_x = re.link_triple(DOC_X.read_text(encoding="utf-8"), W, HEX,
                                      NB, root=REPO)
say("B11 multi rec KEYS = %s ; verdict=%s path=%r match=%r tier=%r" %
    (sorted(rec_x.keys()), rec_x["samedoc_link"]["verdict"],
     rec_x.get("path"), rec_x.get("match"), rec_x.get("tier")))
assert rec_x["samedoc_link"]["verdict"] == "multi"
assert rec_x.get("path") is None and rec_x.get("match") is None
assert "members" not in rec_x
say("B_RESULT THREE_SHAPES_BUILT = True")

# ============================ ③ 原件 :21-29 逐行 + 真实注入崩点 ============================
say()
say("=== C. _f2v_verify9.py:21-29 逐行语义 + 真实注入原件 ===")
b = dict(rec_m)
say("C0 :21 match is not True ? %s （False ⇒ 不 continue）" % (b.get("match") is not True))
src = b.get("alt") or b
say("C1 :23 alt=%r ; src is b = %s" % (b.get("alt"), src is b))
try:
    vp = Path(src.get("verified_path") or src.get("path"))
    say("C2 :24 无异常 vp=%r" % vp)
except Exception as e:
    say("C2 :24 %s: %s" % (type(e).__name__, e))
try:
    _ = src["bytes"]
    say("C3 :29 无异常")
except Exception as e:
    say("C3 :29 %s: %r" % (type(e).__name__, e))
try:
    _ = "%s" % src["bytes"]
    say("C4 :34 无异常")
except Exception as e:
    say("C4 :34 %s: %r" % (type(e).__name__, e))
try:
    _ = b["declared"].lower()
    say("C5 :28 无异常（declared 存在）")
except Exception as e:
    say("C5 :28 %s: %r" % (type(e).__name__, e))
try:
    _ = len(b"dummy") == src["bytes"]
except Exception as e:
    say("C6 绕过 :24 后单独求值 :29 → %s: %r" % (type(e).__name__, e))

V9_TEXT = (R11 / "_f2v_verify9.py").read_text(encoding="utf-8")
V9_CAND = (W / "_ms_v9_candidate.py").read_text(encoding="utf-8")
HEAD_OLD = """j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))
n = 0
for i, r in enumerate(j["results_30"]):
    p = REPO / r["rel"]
    text = p.read_text(encoding="utf-8")
    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
"""
say("C7 HEAD_OLD 在原件 count=%d 在候选 count=%d" %
    (V9_TEXT.count(HEAD_OLD), V9_CAND.count(HEAD_OLD)))
assert V9_TEXT.count(HEAD_OLD) == 1 and V9_CAND.count(HEAD_OLD) == 1


def inject_head(text, cases, tag):
    """等行数（6 行）替换 :14-19，保持后续行号与原件一致；注入自造 bindings。"""
    payload = json.dumps(cases, ensure_ascii=False, default=str)
    head_new = ("MSV_BINDINGS = json.loads(%r)\n" % payload
                + "n = 0\n"
                + "for i, (CASE_NAME, pb) in enumerate(MSV_BINDINGS):\n"
                + "    print(\"CASE %d %s\" % (i, CASE_NAME))\n"
                + "    text = \"\"\n"
                + "    pp, pw = [], []\n")
    return text.replace(HEAD_OLD, head_new, 1)


# C8：原件注入 merged → 期望崩在 :24 TypeError
orig_inj = W / "_msv_v9_orig_inject.py"
orig_inj.write_text(inject_head(V9_TEXT, [("merged", [dict(rec_m)])], "orig"), encoding="utf-8")
ast.parse(orig_inj.read_text(encoding="utf-8"))
r8 = run_py(orig_inj)
say("C8 原件注入 merged EXIT=%d stdout=%r" % (r8.returncode, r8.stdout.strip()[:160]))
for ln in r8.stderr.strip().splitlines():
    if "_msv_v9_orig_inject.py" in ln or "Error" in ln:
        say("C8stderr %s" % ln.strip())

# C9：绕过 :24（把该行换成一个真实存在的 path），仍应在 :29 掉 KeyError
BYPASS_OLD = '        vp = Path(src.get("verified_path") or src.get("path"))\n'
BYPASS_NEW = '        vp = Path(str(MA))\n'
orig_byp = W / "_msv_v9_orig_bypass24.py"
txt_byp = inject_head(V9_TEXT, [("merged", [dict(rec_m)])], "bypass")
assert txt_byp.count(BYPASS_OLD) == 1
txt_byp = txt_byp.replace(BYPASS_OLD, BYPASS_NEW, 1)
txt_byp = txt_byp.replace("import json\n", "import json\nMA = Path(r\"%s\")\n" % str(MA), 1)
# 上面多插了一行会偏移行号；改为把 MA 定义并入第 14 行之前的同行走法：用内置常量
# 重新生成：把 MA 定义放进 head_new 的第 14 行之前会偏移，所以这里只报告相对行号
orig_byp.write_text(txt_byp, encoding="utf-8")
ast.parse(orig_byp.read_text(encoding="utf-8"))
r9 = run_py(orig_byp)
say("C9 绕过 :24 后 EXIT=%d stdout=%r" % (r9.returncode, r9.stdout.strip()[:160]))
for ln in r9.stderr.strip().splitlines():
    if "Error" in ln or "_msv_v9_orig_bypass24.py" in ln:
        say("C9stderr %s" % ln.strip())

# ============================ ⑦ 三形态 + 缺键注射，跑改后候选真实代码路径 ============================
say()
say("=== D. 改后 _f2v_verify9 三形态/缺键注射（注入候选副本真实代码） ===")
ast.parse(V9_TEXT)
ast.parse(V9_CAND)
say("D0 原件/候选 ast.parse 均 OK")
r10 = run_py(W / "_ms_v9_candidate.py")
say("D1 候选整件真实 30 件 EXIT=%d ; 末行=%r ; sha_ok=True 计数=%d ; MISMATCH 计数=%d" %
    (r10.returncode, (r10.stdout.strip().splitlines() or [""])[-1],
     r10.stdout.count("sha_ok=True"), r10.stdout.count("*** MISMATCH ***")))
say("D1b stderr=%r" % (r10.stderr[:200] if r10.stderr else ""))

SHAPES = [
    ("unique", dict(rec_u)),
    ("merged", dict(rec_m)),
    ("multi(match=None)", dict(rec_x)),
    ("multi(合成 match=True,无path,无members)",
     {"declared": HEX, "path": None, "match": True, "tier": None, "alt": None}),
    ("merged 缺 member.bytes",
     dict(rec_m, members=[dict(rec_m["members"][0]),
                          {k: v for k, v in rec_m["members"][1].items() if k != "bytes"}])),
    ("merged members=None", dict(rec_m, members=None)),
    ("unique 缺 bytes", {k: v for k, v in rec_u.items() if k != "bytes"}),
    ("merged 缺 declared", {k: v for k, v in rec_m.items() if k != "declared"}),
]
cand_inj = W / "_msv_v9_cand_inject.py"
cand_inj.write_text(inject_head(V9_CAND, [(n, [c]) for n, c in SHAPES], "cand"), encoding="utf-8")
ast.parse(cand_inj.read_text(encoding="utf-8"))
r11 = run_py(cand_inj)
say("D2 候选注入 8 例 EXIT=%d ; stderr=%r" % (r11.returncode, r11.stderr[:300]))
say("D3 候选注入 8 例 CASE 行数=%d ; SKIP 行数=%d ; MATCH 行数=%d ; 末行=%r" %
    (r11.stdout.count("CASE "), r11.stdout.count("SKIP#"),
     r11.stdout.count("MATCH#"), (r11.stdout.strip().splitlines() or [""])[-1]))
for ln in r11.stdout.splitlines():
    if ln.startswith("CASE ") or "sha_ok=" in ln or ln.startswith("SKIP#"):
        say("    %s" % ln.strip())
say("D_RESULT ALL_EIGHT_NO_EXCEPTION = %s" % (r11.returncode == 0 and "Traceback" not in r11.stderr))
assert r11.returncode == 0

# ============================ ④ 补丁后 check_deliverable 返回值结构 ============================
say()
say("=== E. 补丁后 check_deliverable 返回值结构（★硬要求：零键增删） ===")
G9_TEXT = (REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py").read_text(encoding="utf-8")
BEFORE_R11 = """    r11_items = 1 + len(bindings)  # 存在性强制项 1 + 每条绑定行回验
    r11_verdict = "FAIL" if r11_problems else "PASS"
"""
AFTER_R11 = """    r11_items = 1 + len(bindings)  # 存在性强制项 1 + 每条绑定行回验
    n_match_no_path = sum(1 for b in bindings
                          if b.get("match") is True and not b.get("path"))
    if n_match_no_path:
        r11_problems = list(r11_problems) + ["R11 回验缺口：%d 条绑定行 match=True 但无单一回验路径（merged 副本群不得默认放行），须人工锚定" % n_match_no_path]
    r11_verdict = "FAIL" if r11_problems else "PASS"
"""
say("E0 BEFORE 片段在原件 count=%d" % G9_TEXT.count(BEFORE_R11))
assert G9_TEXT.count(BEFORE_R11) == 1
OWN_G9 = W / "_msv_g9_own.py"
OWN_G9.write_text(G9_TEXT.replace(BEFORE_R11, AFTER_R11, 1), encoding="utf-8")
ast.parse(OWN_G9.read_text(encoding="utf-8"))
say("E1 自造补丁副本（按 DESIGN §三(b) 自己写的 4 行）ast.parse=OK")
import difflib
diff = [x for x in difflib.unified_diff(G9_TEXT.splitlines(),
                                        OWN_G9.read_text(encoding="utf-8").splitlines(),
                                        lineterm="") if x.startswith("+") and not x.startswith("+++")]
say("E2 difflib added lines = %r" % diff)
say("E3 difflib added lines count=%d" % len(diff))

OLD = load("_msv_g9_old", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NEW = load("_msv_g9_new", W / "_ms_g9_candidate.py")
OWN = load("_msv_g9_own", OWN_G9)
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "已入账", "放行 N-5"]
CASES = [("merged 夹具", DOC_M, W), ("unique 夹具", DOC_U, W),
         ("multi 夹具", DOC_X, W),
         ("真实件 B_EXECUTION_SPEC.md",
          REPO / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", None)]


def shape(o):
    """递归结构签名：键集 + 容器类型，不含值。"""
    if isinstance(o, dict):
        return {k: shape(v) for k, v in sorted(o.items())}
    if isinstance(o, list):
        return ["LIST", shape(o[0]) if o else None]
    return type(o).__name__


rows = []
for tag, p, dd in CASES:
    if not p.is_file():
        say("E ABSENT %s SKIP" % tag)
        continue
    kw = {} if dd is None else {"doc_dir": dd}
    ro = OLD.check_deliverable(p, REQ, FORB, **kw)
    rn = NEW.check_deliverable(p, REQ, FORB, **kw)
    rz = OWN.check_deliverable(p, REQ, FORB, **kw)
    same_top = sorted(ro.keys()) == sorted(rn.keys()) == sorted(rz.keys())
    same_pd = sorted(ro["predicates"].keys()) == sorted(rn["predicates"].keys()) == sorted(rz["predicates"].keys())
    same_all = all(sorted(ro["predicates"][k].keys()) == sorted(rn["predicates"][k].keys())
                   == sorted(rz["predicates"][k].keys()) for k in ro["predicates"])
    same_types = all(type(ro[k]) is type(rn[k]) is type(rz[k]) for k in ro)
    say("E4 %-28s top=%s predicates=%s all_pred_keys=%s types=%s verdict old/new=%s/%s" %
        (tag, same_top, same_pd, same_all, same_types, ro["verdict"], rn["verdict"]))
    rows.append((same_top, same_pd, same_all, same_types, ro["verdict"] == rn["verdict"]))
say("E5 无注入 4 案：结构全同=%s verdict 零漂移=%s" %
    (all(all(r[:4]) for r in rows), all(r[4] for r in rows)))

# ============================ ⑤ 反例：旧 PASS / 新 FAIL ============================
say()
say("=== F. 反例：旧 PASS / 新 FAIL（自造交付件 + 自造注入，自己实跑） ===")


def inject(mod, rec_):
    mod.g7.r11_scan = lambda t, dd, root=None, recompute=None: ([], [], [dict(rec_)])


OLD_I = load("_msv_g9_old_i", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NEW_I = load("_msv_g9_new_i", W / "_ms_g9_candidate.py")
OWN_I = load("_msv_g9_own_i", OWN_G9)
for mod in (OLD_I, NEW_I, OWN_I):
    inject(mod, rec_m)
rio = OLD_I.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
rin = NEW_I.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
riz = OWN_I.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
for tag, x in (("OLD+", rio), ("NEW+", rin), ("OWN+", riz)):
    R = x["predicates"]["R11"]
    say("F1 %-5s verdict=%s R11=%s reverified=%d match_true=%d R11 problems=%r" %
        (tag, x["verdict"], R["verdict"], R["reverified"], R["match_true"], R["problems"]))
say("F2 OLD+ overall problems=%r" % [p["msg"] for p in rio["problems"]])
say("F3 NEW+ overall problems=%r" % [p["msg"] for p in rin["problems"]])
say("F4 注入后 TOP KEYS old=%s" % sorted(rio.keys()))
say("F5 注入后 R11 KEYS old=%s" % sorted(rio["predicates"]["R11"].keys()))
say("F6 top keys old==new==own : %s" %
    (sorted(rio.keys()) == sorted(rin.keys()) == sorted(riz.keys())))
say("F7 R11 keys old==new==own : %s" %
    (sorted(rio["predicates"]["R11"].keys()) == sorted(rin["predicates"]["R11"].keys())
     == sorted(riz["predicates"]["R11"].keys())))
say("F8 全谓词 keys old==new==own : %s" %
    all(sorted(rio["predicates"][k].keys()) == sorted(rin["predicates"][k].keys())
        == sorted(riz["predicates"][k].keys()) for k in rio["predicates"]))
say("F9 递归结构签名 old==new==own : %s" % (shape(rio) == shape(rin) == shape(riz)))
say("F10 JSON 可序列化 old/new/own : %s" %
    all(isinstance(json.dumps(x, ensure_ascii=False), str) for x in (rio, rin, riz)))
say("F11 顶层逐键类型 = %s" %
    [(k, type(rio[k]).__name__, type(rin[k]).__name__, type(riz[k]).__name__)
     for k in sorted(rio.keys())])
ce_ok = (rio["verdict"] == "PASS" and rin["verdict"] == "FAIL"
         and riz["verdict"] == "FAIL"
         and rio["predicates"]["R11"]["verdict"] == "PASS"
         and rin["predicates"]["R11"]["verdict"] == "FAIL")
say("F_RESULT COUNTEREXAMPLE_OK = %s" % ce_ok)
assert ce_ok
STRUCT_OK = (sorted(rio.keys()) == sorted(rin.keys()) == sorted(riz.keys())
             and sorted(rio["predicates"]["R11"].keys())
             == sorted(rin["predicates"]["R11"].keys())
             == sorted(riz["predicates"]["R11"].keys())
             and shape(rio) == shape(rin) == shape(riz))
say("E_RESULT STRUCTURE_UNCHANGED = %s" % STRUCT_OK)
say("F12 无注入 OLD verdict=%s NEW verdict=%s（缺陷属未来接入面）" %
    (OLD.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)["verdict"],
     NEW.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)["verdict"]))

# ============================ ⑥ 安全集边界判据 ============================
say()
say("=== G. 安全集边界：崩 vs 静默错 + 汇聚点论断核对 ===")
sha_ok = (rec_m.get("recomputed") or "").lower() == rec_m["declared"].lower()
plus_path = sum(1 for x in [rec_m] if x.get("path"))
plus_match = sum(1 for x in [rec_m] if x.get("match") is True)
collected = sum(1 for x in [rec_m] if x.get("path"))
tiers = {}
for x in [rec_m]:
    if x.get("match") is True:
        tiers[x.get("tier")] = tiers.get(x.get("tier"), 0) + 1
s4 = rec_m.get("verified_path", "").endswith("_f2_r11plus.py")
vpath = rec_m.get("verified_path", "") or ""
rc = rec_m.get("recomputed", "") or ""
say("G1 _f2w_checks.py:29 sha_ok=%r（合法 match=True 被记 sha 不一致，静默）" % sha_ok)
say("G2 _f2_compare.py:67-69 (plus_path,plus_match)=(%d,%d)" % (plus_path, plus_match))
say("G3 _f2v_final.py:54,57-58 collected=%d tiers=%r" % (collected, tiers))
say("G4 _f2_selftest.py:110 endswith(...)=%r" % s4)
say("G5 _f2w_extract.py:26-33 verified=%r recomputed=%r bytes=%r" %
    (vpath, (rc[:16] + "...") if rc else "-", rec_m.get("bytes", "-")))
say("G6 link_triple problems=%r ⇒ 门禁只读 problems 不会 FAIL" % prob_m)
say("G7 6 个静默表达式全部未抛异常（fail-open）；C2/C3/C4 抛异常（fail-closed）")

# 关键：DESIGN 称「6 件静默误读全读 _f2_compare.py:100 写出的同一 JSON」，逐件实读核对
DOWNSTREAM = ["_f2w_checks.py", "_f2_selftest.py", "_f2_compare.py", "_f2v_final.py",
              "_f2v_run.py", "_f2w_dogfood.py", "_f2w_extract.py", "_f2w_pass.py"]
reads_json, calls_plus = [], []
for fn in DOWNSTREAM:
    t = (R11 / fn).read_text(encoding="utf-8")
    rj = "_f2_compare_out.json" in t
    cp = "r11_scan_plus(" in t
    (reads_json if rj else []).append(fn)
    (calls_plus if cp else []).append(fn)
    say("G8 %-22s 读 _f2_compare_out.json=%-5s 直接调 r11_scan_plus=%s" % (fn, rj, cp))
say("G9 读 JSON 的件数=%d %s" % (len(reads_json), reads_json))
say("G10 直接调 r11_scan_plus 的件数=%d %s" % (len(calls_plus), calls_plus))
DESIGN = (W / "_ms_DESIGN.md").read_text(encoding="utf-8")
say("G11 DESIGN 含『6 件静默误读全读 _f2_compare.py:100 写出的同一 JSON』: %s" %
    ("6 件静默误读全读" in DESIGN))
say("G12 DESIGN 含『一处汇聚点覆盖 6 件静默误读』: %s" %
    ("一处汇聚点覆盖 6 件" in DESIGN))
AUD = (REPO / "lead" / "merged_consumer_audit_20261109" /
       "MERGED_CONSUMER_AUDIT.md").read_text(encoding="utf-8")
say("G13 AUDIT:79 原文『读者=这 3 件（加 _f2w_extract.py:13）』: %s" %
    ("读者=这 3 件（加 `_f2w_extract.py:13`）" in AUD))
say("G14 AUDIT §5.2 六条计数=%d ; 含『1–3（代码必做）+ 5–6（治理/审计必做）』: %s" %
    (sum(("\n%d. " % i) in AUD for i in range(1, 7)),
     "1–3（代码必做）+ 5–6（治理/审计必做）" in AUD))
for needle in ["静默错比崩更该进安全集", "崩 = **fail-closed**", "静默错 = **fail-open**",
               "两项不足以称「够」", "结论：代码补丁 = 2 项", "fail-open"]:
    say("G15 DESIGN 含 %r : %s" % (needle, needle in DESIGN))
say("G16 _mc_AUDIT.md 含『7 处静默误读』: %s" %
    ("7 处静默误读" in (REPO / "lead" / "merged_consumer_audit_20261109" /
                      "_mc_AUDIT.md").read_text(encoding="utf-8")))

# ============================ ⑧ 越界检查 ============================
say()
say("=== H. 越界检查：末轮指纹 / 只读域 .pyc / 既有件未改 ===")
FP_LAST = fps()
say("H1 ALL_EIGHT_UNCHANGED = %s" % (FP_FIRST == FP_LAST))
for rel, _, _ in BASE:
    say("    %s %s %d" % (rel, FP_LAST[rel][0], FP_LAST[rel][1]))
for d in [R11, REPO / "lead" / "gate_r9r12_20261109",
          REPO / "lead" / "r33e_merge_20261109",
          REPO / "lead" / "merged_consumer_audit_20261109"]:
    pycs = sorted(str(x.relative_to(REPO)) for x in d.rglob("*.pyc"))
    say("H2 %-32s *.pyc count=%d %s" % (d.name, len(pycs), pycs[:3]))
say("H3 原件仍含逐字 :24 = %s" %
    ('vp = Path(src.get("verified_path") or src.get("path"))' in V9_TEXT))
say("H4 门禁原件仍含逐字 :160 = %s" %
    ('r11_verdict = "FAIL" if r11_problems else "PASS"' in G9_TEXT))
say("H5 本复核员写域新增件 = %s" % sorted(x.name for x in W.glob("_msv_*")))
say("H_RESULT NO_TAMPER = %s" % (FP_FIRST == FP_LAST))

(W / "_msv_check_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_msv_check_out.txt"))
