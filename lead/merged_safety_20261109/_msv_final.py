# -*- coding: utf-8 -*-
"""_msv_final.py — 第三轮：决定性判定（键集纯比对 / 三形态完整输出 / 汇聚点 / 越界）。

零真机、零采样。python -I -X utf8 -B + 绝对路径。写域前缀 _msv_。
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
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


# ---------- 1. 决定性：键集纯比对（列表内容完全不参与） ----------
say("=== 1 决定性返回值结构：仅比对每层 dict 的键集 ===")


def keyset(o):
    if isinstance(o, dict):
        return ("D", tuple((k, keyset(v)) for k, v in sorted(o.items())))
    if isinstance(o, list):
        return ("L",)  # 列表统一，不因空/非空或元素形态而变
    return ("S", type(o).__name__)


OLD = load("_msv_f_old", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NEW = load("_msv_f_new", W / "_ms_g9_candidate.py")
OWN = load("_msv_f_own", W / "_msv_g9_own.py")
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "已入账", "放行 N-5"]
DOC_M = W / "_msv_merged_doc.md"
BODY = b"INDEPENDENT-REVIEWER-COPIED-BODY-20261109-v3\n"
HEX = hashlib.sha256(BODY).hexdigest()
rec_merged = {"declared": HEX, "path": None, "match": True, "tier": "SAMEDOC_LINK_EQ",
              "members": [{"path": str(W / "_msv_fixtures" / "_msv_alpha.dat"),
                           "sha": HEX, "bytes": len(BODY)}]}


def inject(mod, rec):
    mod.g7.r11_scan = lambda t, dd, root=None, recompute=None: ([], [], [dict(rec)])


OI = load("_msv_f_old_i", REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py")
NI = load("_msv_f_new_i", W / "_ms_g9_candidate.py")
ZI = load("_msv_f_own_i", W / "_msv_g9_own.py")
for m in (OI, NI, ZI):
    inject(m, rec_merged)
rio = OI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
rin = NI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
riz = ZI.check_deliverable(DOC_M, REQ, FORB, doc_dir=W)
say("1.1 keyset(old) == keyset(new) : %s" % (keyset(rio) == keyset(rin)))
say("1.2 keyset(old) == keyset(own) : %s" % (keyset(rio) == keyset(riz)))
say("1.3 顶层键集 = %s" % sorted(rio.keys()))
say("1.4 R11 键集 = %s" % sorted(rio["predicates"]["R11"].keys()))
say("1.5 合并视图 problems 元素键集 old=%s new=%s" %
    ([sorted(x.keys()) for x in rio["problems"]],
     [sorted(x.keys()) for x in rin["problems"]]))
say("1.6 OLD+ verdict=%s NEW+ verdict=%s OWN+ verdict=%s" %
    (rio["verdict"], rin["verdict"], riz["verdict"]))
say("1_RESULT STRUCTURE_UNCHANGED_DECISIVE = %s" %
    (keyset(rio) == keyset(rin) == keyset(riz)
     and rio["verdict"] == "PASS" and rin["verdict"] == "FAIL"))

# ---------- 2. 三形态完整输出（含 bytes_ok / SKIP 计数） ----------
say()
say("=== 2 三形态 + 缺键注射：候选副本完整 stdout ===")
r = subprocess.run([sys.executable, "-I", "-X", "utf8", "-B",
                    str(W / "_msv_v9_cand_inject.py")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
say("2.1 EXIT=%d stderr=%r" % (r.returncode, r.stderr[:200]))
lines = r.stdout.splitlines()
cur = None
cases = {}
for ln in lines:
    if ln.startswith("CASE "):
        cur = ln.strip()
        cases[cur] = []
    elif cur:
        cases[cur].append(ln.strip())
for k, v in cases.items():
    hits = [x for x in v if "sha_ok=" in x or x.startswith("SKIP#") or "MISMATCH" in x]
    say("2.2 %-46s 输出行数=%d 关键行=%r" % (k, len(v), hits))
say("2.3 全局：TypeError/KeyError/Traceback 出现 = %s" %
    any(t in r.stdout + r.stderr for t in ("TypeError", "KeyError", "Traceback")))
say("2.4 注意：『merged members=None』与『multi(match=None)』两例无任何输出行"
    "（前者静默空跑、后者由 :21 match 守卫跳过），"
    "DESIGN §二(d) 称『merged members=None → SKIP』与实跑不符")

# ---------- 3. 未来接入面：g7.r11_scan 不产 merged rec + 两条 grep ----------
say()
say("=== 3 两缺陷是否当下可达 ===")
g7 = load("_msv_f_g7", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
prob, warn, bind = g7.r11_scan(DOC_M.read_text(encoding="utf-8"), W, root=REPO)
say("3.1 对我的 merged 交付件跑 g7.r11_scan : bindings=%r" % bind)
say("3.2 r11_scan 是否产 merged rec = %s" %
    any(b.get("tier") == "SAMEDOC_LINK_EQ" or b.get("members") for b in bind))
say("3.3 problems=%r warnings=%r（R3-3b 只 warning）" % (prob, warn))
G9 = (REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py").read_text(encoding="utf-8")
PLUS = (R11 / "_f2_r11plus.py").read_text(encoding="utf-8")
say("3.4 _g9_gate.py 含 'r11_scan_plus' / 'link_triple' / '_re_linked' : %s" %
    [x in G9 for x in ("r11_scan_plus", "link_triple", "_re_linked")])
say("3.5 _f2_r11plus.py 含 'link_triple' / '_re_linked' : %s" %
    [x in PLUS for x in ("link_triple", "_re_linked")])
say("3.6 _f2_r11plus.py:303-305 现仍是 rec['tier']=None + R3-3b warning : %s" %
    ('rec["tier"] = None' in PLUS and "绑定行缺显式路径，需人工锚定" in PLUS))
say("3.7 原件 _f2v_verify9.py 原样基线：")
r0 = subprocess.run([sys.executable, "-I", "-X", "utf8", "-B",
                     str(R11 / "_f2v_verify9.py")],
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
say("    EXIT=%d 末行=%r MATCH 行数=%d" %
    (r0.returncode, (r0.stdout.strip().splitlines() or [""])[-1],
     r0.stdout.count("sha_ok=True")))

# ---------- 4. 交付件尺寸 / 写域文件核对 ----------
say()
say("=== 4 被核对象回件『what』字段所称尺寸与实盘核对 ===")
for name in ["_ms_DESIGN.md", "_ms_probe.py", "_ms_regress.py", "_ms_tight.py",
             "_ms_counterexample.py", "_ms_v9_candidate.py",
             "_ms_v9_candidate_v2.py", "_ms_g9_candidate.py"]:
    p = W / name
    say("4.1 %-28s bytes=%d sha256=%s" %
        (name, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()[:16]))
say("4.2 回件 what 字段称 _ms_DESIGN.md = 34021 B；实盘 = %d B ⇒ %s" %
    ((W / "_ms_DESIGN.md").stat().st_size,
     "MATCH" if (W / "_ms_DESIGN.md").stat().st_size == 34021 else "MISMATCH"))

# ---------- 5. 末轮指纹（第四轮） ----------
say()
say("=== 5 末轮八件指纹（本次会话第 3 次实算） ===")
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
say("5.1 ALL_EIGHT_UNCHANGED = %s" % ok)
say("5.2 未 commit / 未 push：本会话未执行 git commit / git push（工具调用记录）")
(W / "_msv_final_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_msv_final_out.txt"))
