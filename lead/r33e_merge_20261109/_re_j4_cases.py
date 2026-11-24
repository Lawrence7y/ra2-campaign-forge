# -*- coding: utf-8 -*-
"""_re_j4_cases.py — 第四步：验证 J4 只在应该合并时合并。
(a) 条3 真件 -> merged（2 成员，声明行 13，纪律面全查）；
(b) Q4 六趟 except 转储 -> 保持 multi（封闭集 decl 词行 = 0），bytes=26405 与 None 两喂入；
(c) 构造「有声明行但只覆盖部分成员」夹具 Fp1（覆盖 1/2）、Fp2（覆盖 2/3）-> 必须 multi；
(d) 构造「有声明行但用纯等同词（逐字节同一）」夹具 Fd -> 必须 multi（封闭集排除）；
(e) 正控制夹具 Ffull（声明覆盖全体）-> merged（对照 (c)(d) 的反差别）。
判读用独立重算：运行方自抄一份封闭集正则 + 自建覆盖图，与谓词判定交叉核对。
夹具落本写域 _re_fixtures/；输出落本写域 _re_j4_out.json。零真机、零采样代码。"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
FXD = RE_DIR / "_re_fixtures"
OUT = RE_DIR / "_re_j4_out.json"

_b = (SL_DIR / "_sl_link.py").read_bytes()
guard = {"sha256": hashlib.sha256(_b).hexdigest(), "bytes": len(_b),
         "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
         "expect_bytes": 12475}
if not (guard["sha256"] == guard["expect_sha"] and guard["bytes"] == guard["expect_bytes"]):
    raise SystemExit("GUARD FAIL: %r" % guard)
sys.path.insert(0, str(SL_DIR))
sys.path.insert(0, str(RE_DIR))
import _sl_link as SL   # noqa: E402
import _re_linked as RE  # noqa: E402

CAND = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
Q4HEX = "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251"
RUNNER_DECL = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")

A = []
def chk(name, cond, detail=""):
    A.append({"name": name, "ok": bool(cond), "detail": detail})


def analyze(text, res):
    """运行方独立重算：kset/覆盖图/封闭集词行/覆盖>=2 的行。"""
    kset = {m["key"] for m in res["anchors"]}
    cov = {}
    for m in res["anchors"]:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set()).add(m["key"])
    lines = text.splitlines()
    decl = [i + 1 for i, ln in enumerate(lines) if RUNNER_DECL.search(ln)]
    cover2 = sorted(ln for ln, ks in cov.items() if len(ks) >= 2)
    return {"kset_n": len(kset), "decl_word_lines": decl, "cover_ge2_lines": cover2,
            "decl_cover_detail": [{"line": ln, "covers_n": len(cov.get(ln, set())),
                                   "covers_all": cov.get(ln, set()) == kset} for ln in decl]}


def both(text, ddir, hx, bd):
    ro = SL.link(text, ddir, hx, bd)
    rm = RE.link(text, ddir, hx, bd)
    return ro, rm, json.dumps(ro, ensure_ascii=False, sort_keys=True) == json.dumps(
        rm, ensure_ascii=False, sort_keys=True)

# ---- 夹具构建（本写域 _re_fixtures/）----
BLOB = b"R33E-FIXTURE-MARKER-20261109\n"
FH = hashlib.sha256(BLOB).hexdigest()
NB = len(BLOB)
TEMPLATES = {
    "Ffull_merged": "被核对象 SHA256 = %s，字节数 = %d\n\n两个产物：`a_one.py` 与 `b_two.py`。\n`b_two.py` 复制自 `a_one.py`。\n",
    "Fp1_decl_covers_one": "被核对象 SHA256 = %s，字节数 = %d\n\n两个产物：`a_one.py`、`b_two.py`。\n`a_one.py` 复制自外部原件。\n",
    "Fp2_partial_two_of_three": "被核对象 SHA256 = %s，字节数 = %d\n\n三个产物：`a_one.py`、`b_two.py`、`c_three.py`。\n`a_one.py` 复制自 `b_two.py`（声明行仅覆盖两件）。\n",
    "Fd_equiv_words": "被核对象 SHA256 = %s，字节数 = %d\n\n两个产物：`a_one.py` 与 `b_two.py`，二者逐字节同一。\n",
}
FILES = {"Ffull_merged": 2, "Fp1_decl_covers_one": 2,
         "Fp2_partial_two_of_three": 3, "Fd_equiv_words": 2}
made = {}
for name, tpl in TEMPLATES.items():
    d = FXD / name
    d.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate(["a_one.py", "b_two.py", "c_three.py"]):
        if i < FILES[name]:
            (d / fn).write_bytes(BLOB)
    (d / "doc.md").write_text(tpl % (FH, NB), encoding="utf-8", newline="\n")
    made[name] = d

results = {}

# ---- (a) 条3 真件 -> merged ----
doc3 = ROOT / "lead" / "b2b_isolated_20261107" / "_integ_INTEGRATION_REPORT.md"
t3 = doc3.read_bytes().decode("utf-8")
ro, rm, idt = both(t3, doc3.parent, CAND, 412759)
an = analyze(t3, rm)
eq = rm.get("eq") or {}
line13 = t3.splitlines()[12].strip()
results["a_real_item3"] = {
    "verdict_orig": ro["verdict"], "verdict_merged": rm["verdict"],
    "members": eq.get("members"), "decl_lines": eq.get("decl_lines"),
    "decl_hits": eq.get("decl_hits"), "reverify_is_none": rm.get("reverify") is None,
    "warning": rm.get("warning"), "analysis": an, "decl_line13_actual_text": line13}
chk("a_item3_merged", ro["verdict"] == "multi" and rm["verdict"] == "merged")
chk("a_item3_members2", len(eq.get("members", [])) == 2)
chk("a_item3_decl_line13_with_text",
    eq.get("decl_lines") == [13] and len(eq.get("decl_hits", [])) == 1
    and eq["decl_hits"][0]["text"] == line13, line13[:80])
chk("a_item3_disciplines",
    rm.get("reverify") is None
    and all(set(x) == {"path", "sha", "bytes"} for x in eq.get("members", []))
    and "未做单一对象主张" in (rm.get("warning") or "")
    and "禁止由 merged 推导任何授权结论" in (rm.get("warning") or ""))
pm, wm, recm = RE.link_triple(t3, doc3.parent, CAND, 412759)
chk("a_item3_triple_shape",
    recm["tier"] == "SAMEDOC_LINK_EQ" and recm["match"] is True and recm["path"] is None
    and len(recm.get("members", [])) == 2 and recm.get("decl_lines") == [13])
chk("a_item3_runner_crosscheck",
    an["kset_n"] == 2 and 13 in an["decl_word_lines"]
    and an["cover_ge2_lines"] == [13]
    and [d for d in an["decl_cover_detail"] if d["covers_n"] >= 2]
    == [{"line": 13, "covers_n": 2, "covers_all": True}])

# ---- (b) Q4 六趟 except 转储 -> 保持 multi ----
docq = ROOT / "lead" / "re_line_20261105" / "W9_SINGLESTEP_7CFC9F" / "Q4_RELATION.md"
tq = docq.read_bytes().decode("utf-8")
qres = {}
for bd in (26405, None):
    ro, rm, idt = both(tq, docq.parent, Q4HEX, bd)
    an = analyze(tq, rm)
    qres["bytes_%s" % bd] = {"verdict_orig": ro["verdict"], "verdict_merged": rm["verdict"],
                             "identical": idt, "anchors": len(rm.get("anchors", [])),
                             "analysis": an}
    chk("b_q4_bytes%s_stays_multi" % bd,
        ro["verdict"] == "multi" and rm["verdict"] == "multi" and idt)
    chk("b_q4_bytes%s_no_decl_words" % bd, an["decl_word_lines"] == [])
results["b_q4_six_dumps"] = qres

# ---- (c)(d)(e) 夹具案例 ----
def fixture_case(name, expect):
    d = made[name]
    text = (d / "doc.md").read_text(encoding="utf-8")
    ro, rm, idt = both(text, d, FH, NB)
    an = analyze(text, rm)
    eq = rm.get("eq") or {}
    rec = {"verdict_orig": ro["verdict"], "verdict_merged": rm["verdict"],
           "identical": idt, "anchors": [m["path"].split("_re_fixtures")[-1] for m in rm.get("anchors", [])],
           "decl_lines": eq.get("decl_lines"), "analysis": an,
           "warning_head": (rm.get("warning") or "")[:100]}
    chk("%s_%s" % (name, expect),
        ro["verdict"] == "multi" and rm["verdict"] == expect and
        (idt if expect == "multi" else True),
        json.dumps(rec["analysis"], ensure_ascii=False))
    return rec

results["c_Fp1_decl_covers_one"] = fixture_case("Fp1_decl_covers_one", "multi")
results["c_Fp2_partial_two_of_three"] = fixture_case("Fp2_partial_two_of_three", "multi")
results["d_Fd_equiv_words"] = fixture_case("Fd_equiv_words", "multi")
results["e_Ffull_merged"] = fixture_case("Ffull_merged", "merged")

# 细化判读：
# (c)-Fp1：声明词行存在但仅覆盖 1 个成员 -> 条件(ii)不满足
chk("c_Fp1_decl_line_covers_only_one",
    results["c_Fp1_decl_covers_one"]["analysis"]["decl_word_lines"] != []
    and all(x["covers_n"] < 2 for x in results["c_Fp1_decl_covers_one"]["analysis"]["decl_cover_detail"]))
# (c)-Fp2：声明词行覆盖 2/3 成员（部分覆盖）-> 条件(iii)不满足，全或无
chk("c_Fp2_decl_line_partial_coverage",
    results["c_Fp2_partial_two_of_three"]["analysis"]["decl_cover_detail"][0]["covers_n"] == 2
    and results["c_Fp2_partial_two_of_three"]["analysis"]["decl_cover_detail"][0]["covers_all"] is False
    and results["c_Fp2_partial_two_of_three"]["analysis"]["kset_n"] == 3)
# (d)-Fd：逐字节同一行确实同现 2 成员（cover>=2），但封闭集不收纯等同词 -> 唯一拦点是词组
chk("d_Fd_line_covers2_but_vocab_excludes",
    results["d_Fd_equiv_words"]["analysis"]["cover_ge2_lines"] != []
    and results["d_Fd_equiv_words"]["analysis"]["decl_word_lines"] == [])
# (e)-Ffull：正控制 —— 声明覆盖全体成员才 merged
chk("e_Ffull_decl_covers_all_then_merged",
    results["e_Ffull_merged"]["analysis"]["decl_cover_detail"][0]["covers_all"] is True
    and results["e_Ffull_merged"]["verdict_merged"] == "merged")

# 封闭集记录：本件与 _eq_proto.py:47 的词组逐字符一致，未扩词
chk("closed_vocab_unchanged",
    RE.DECL_RE.pattern == r"复制自|复制为|COPY_IDENTICAL\s*=\s*True"
    and RUNNER_DECL.pattern == RE.DECL_RE.pattern, RE.DECL_RE.pattern)

out = {"guard": guard, "decl_vocab": RE.DECL_RE.pattern, "fixtures_made":
       {k: str(v) for k, v in made.items()}, "results": results, "assertions": A}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

for k, v in results.items():
    if k == "b_q4_six_dumps":
        for bk, bv in v.items():
            print("%-28s %-18s %s->%s identical=%s anchors=%d decl_words=%s" % (
                k, bk, bv["verdict_orig"], bv["verdict_merged"], bv["identical"],
                bv["anchors"], bv["analysis"]["decl_word_lines"]))
    else:
        print("%-28s %s->%s decl=%s members=%d" % (
            k, v["verdict_orig"], v["verdict_merged"], v.get("decl_lines"),
            len((v.get("members") or []))))
print("ASSERTIONS:", sum(1 for x in A if x["ok"]), "/", len(A), "passed")
for x in A:
    if not x["ok"]:
        print("  FAIL:", x["name"], x.get("detail", "")[:200])
print("FIXTURE_HASH: sha256=%s bytes=%d" % (FH, NB))
print("OUT:", OUT)
sys.exit(0 if all(x["ok"] for x in A) else 1)
