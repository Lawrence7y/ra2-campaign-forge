# -*- coding: utf-8 -*-
"""_re_parity_extra.py — 并入版补充全量回归（补 _re_run10_diff.py / _re_j4_cases.py 未覆盖面）。

零真机、零采样代码；只读 lead/samedoc_link_20261109/ 的谓词与夹具，只写本写域。
命令：python -I -B -X utf8 <绝对路径>/_re_parity_extra.py

补充四类：
  (1) J4 不介入 unique / zero / invalid_hex 的正控制：构造「同文档确含溯源声明行、
      且该行同现 >=2 个带路径 token」但 verdict 非 multi 的样本，断言两实现输出
      JSON 逐字节全等、并入版不产 eq 键（若有人把 J4 放在分支外就会失败）。
  (2) members 全列压测：15 个同 hash 不同文件 + 1 条覆盖全体的声明行 → merged，
      eq.members 必须 15（不因 max_detail=12 截断），anchors 仍按原实现为 12。
  (3) multi 的 link_triple 契约：Q4 六趟真件原/并 rec 逐字节全等（tier 仍
      SAMEDOC_LINK、match=None、path=None）；merged 的 triple 新形态再核一遍。
  (4) 原 _sl_selftest.py 的 8 个调用面（读只读夹具，不重跑其写盘段）双跑逐条比对：
      multi/unique/zero 全覆盖，并与 _sl_selftest_out.json 的历史判定交叉核对。

输出落本写域 _re_parity_extra_out.json；断言全过 exit 0，否则 exit 1。"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
FIX = SL_DIR / "_sl_fixtures"
FXD = RE_DIR / "_re_fixtures"
OUT = RE_DIR / "_re_parity_extra_out.json"

EXPECT_SL_SHA = "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5"
EXPECT_SL_BYTES = 12475


def fp(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


guard = {"sl_link": dict(zip(("sha256", "bytes"), fp(SL_DIR / "_sl_link.py"))),
         "re_linked": dict(zip(("sha256", "bytes"), fp(RE_DIR / "_re_linked.py")))}
guard["sl_link"]["expect_sha"] = EXPECT_SL_SHA
guard["sl_link"]["expect_bytes"] = EXPECT_SL_BYTES
guard["sl_link"]["match"] = (guard["sl_link"]["sha256"] == EXPECT_SL_SHA
                             and guard["sl_link"]["bytes"] == EXPECT_SL_BYTES)
if not guard["sl_link"]["match"]:
    raise SystemExit("GUARD FAIL: read-only original drifted")

sys.path.insert(0, str(SL_DIR))
sys.path.insert(0, str(RE_DIR))
import _sl_link as SL    # noqa: E402
import _re_linked as RE  # noqa: E402

DECL = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")
HEX64 = re.compile(r"[0-9a-fA-F]{64}")
A = []


def chk(name, cond, detail=""):
    A.append({"name": name, "ok": bool(cond), "detail": str(detail)[:400]})


chk("closed_vocab_identical",
    RE.DECL_RE.pattern == r"复制自|复制为|COPY_IDENTICAL\s*=\s*True" == DECL.pattern,
    RE.DECL_RE.pattern)


def jd(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def dbl(text, ddir, hx, bd=None, root=SL.REPO_ROOT):
    ro = SL.link(text, ddir, hx, bd, root)
    rm = RE.link(text, ddir, hx, bd, root)
    po, wo, reco = SL.link_triple(text, ddir, hx, bd, root)
    pm, wm, recm = RE.link_triple(text, ddir, hx, bd, root)
    return {"vo": ro["verdict"], "vm": rm["verdict"],
            "identical": jd(ro) == jd(rm),
            "sha_orig": hashlib.sha256(jd(ro).encode("utf-8")).hexdigest(),
            "sha_merged": hashlib.sha256(jd(rm).encode("utf-8")).hexdigest(),
            "has_eq": "eq" in rm,
            "anchors_orig": len(ro.get("anchors", [])),
            "anchors_merged": len(rm.get("anchors", [])),
            "triple_rec_identical": jd(reco) == jd(recm),
            "tier_orig": reco["tier"], "tier_merged": recm["tier"],
            "match_merged": recm["match"], "path_merged": recm["path"],
            "members_merged": len(recm.get("members") or []),
            "ro": ro, "rm": rm, "reco": reco, "recm": recm}


rows = []
# ---------------------------------------------------------------- (1) 夹具
BLOB = b"R33E-PARITY-MARKER-20261109\n"
BLOB2 = b"R33E-PARITY-MARKER-DIFFERENT-BYTES-20261109\n"
FH, NB = hashlib.sha256(BLOB).hexdigest(), len(BLOB)
FH2, NB2 = hashlib.sha256(BLOB2).hexdigest(), len(BLOB2)


def mk(name, text, files):
    d = FXD / name
    d.mkdir(parents=True, exist_ok=True)
    for fn, blob in files.items():
        (d / fn).write_bytes(blob)
    (d / "doc.md").write_text(text, encoding="utf-8", newline="\n")
    return d, (d / "doc.md").read_text(encoding="utf-8")


# (1a) unique + 声明行（该行同现 2 个带路径 token，但只有 1 件 hash 相符）
d_u, t_u = mk(
    "Pu_unique_with_decl",
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "两份产物 `a_one.py` 与 `b_two.py`；`a_one.py` 复制自 `b_two.py`。\n" % (FH, NB),
    {"a_one.py": BLOB, "b_two.py": BLOB2})
r = dbl(t_u, d_u, FH, NB)
decl_lines_u = [i + 1 for i, l in enumerate(t_u.splitlines()) if DECL.search(l)]
toks_line4 = [(it["token"], it["lines"]) for it in SL.iter_path_items(t_u)]
rows.append({"case": "Pu_unique_with_decl", "expect": "unique", **{k: v for k, v in r.items()
            if k not in ("ro", "rm", "reco", "recm")}})
chk("Pu_stays_unique_identical", r["vo"] == "unique" and r["vm"] == "unique"
    and r["identical"] and not r["has_eq"] and r["triple_rec_identical"],
    "vo=%s vm=%s identical=%s eq=%s" % (r["vo"], r["vm"], r["identical"], r["has_eq"]))
chk("Pu_decl_line_really_present_and_covers_2_tokens",
    decl_lines_u != [] and sum(1 for tok, lns in toks_line4 if decl_lines_u[0] in lns) >= 2,
    "decl_lines=%s tokens=%s" % (decl_lines_u, toks_line4))

# (1b) zero + 声明行（绑定 hex 不在盘）
ghost = hashlib.sha256(b"R33E-PARITY-GHOST-NEVER-ON-DISK").hexdigest()
d_z, t_z = mk(
    "Pz_zero_with_decl",
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "两份产物 `a_one.py` 与 `b_two.py`；`a_one.py` 复制自 `b_two.py`。\n" % (ghost, NB),
    {"a_one.py": BLOB, "b_two.py": BLOB})
r = dbl(t_z, d_z, ghost, NB)
rows.append({"case": "Pz_zero_with_decl", "expect": "zero", **{k: v for k, v in r.items()
            if k not in ("ro", "rm", "reco", "recm")}})
chk("Pz_stays_zero_identical", r["vo"] == "zero" and r["vm"] == "zero"
    and r["identical"] and not r["has_eq"] and r["triple_rec_identical"],
    "vo=%s vm=%s identical=%s eq=%s" % (r["vo"], r["vm"], r["identical"], r["has_eq"]))

# (1c) invalid_hex + 声明行
d_i, t_i = mk(
    "Pi_invalid_hex_with_decl",
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "`a_one.py` 复制自 `b_two.py`。\n" % (ghost, NB),
    {"a_one.py": BLOB, "b_two.py": BLOB})
r = dbl(t_i, d_i, "not-a-hex", NB)
rows.append({"case": "Pi_invalid_hex_with_decl", "expect": "invalid_hex",
             **{k: v for k, v in r.items() if k not in ("ro", "rm", "reco", "recm")}})
chk("Pi_stays_invalid_hex_identical", r["vo"] == "invalid_hex" and r["vm"] == "invalid_hex"
    and r["identical"] and not r["has_eq"], "vo=%s vm=%s" % (r["vo"], r["vm"]))

# ---------------------------------------------------------------- (2) 15 成员压测
N = 15
names = ["f%02d.py" % i for i in range(N)]
line = " ".join("`%s`" % n for n in names)
d_m, t_m = mk(
    "Pm_15_members_all_listed",
    "被核对象 SHA256 = %s，字节数 = %d\n\n%s 均复制自同一原件。\n" % (FH, NB, line),
    {n: BLOB for n in names})
r = dbl(t_m, d_m, FH, NB)
eq = r["rm"].get("eq") or {}
memb = eq.get("members") or []
rows.append({"case": "Pm_15_members_all_listed", "expect": "merged",
             "members_count": len(memb), "anchors_shown": r["anchors_merged"],
             "decl_lines": eq.get("decl_lines"),
             **{k: v for k, v in r.items() if k not in ("ro", "rm", "reco", "recm")}})
chk("Pm_merged", r["vo"] == "multi" and r["vm"] == "merged", "%s->%s" % (r["vo"], r["vm"]))
chk("Pm_members_all_15_not_truncated", len(memb) == N
    and len({m["path"] for m in memb}) == N
    and r["anchors_merged"] == 12
    and all(set(m) == {"path", "sha", "bytes"} and m["sha"] == FH and m["bytes"] == NB
            for m in memb),
    "members=%d anchors(max_detail)=%d" % (len(memb), r["anchors_merged"]))
chk("Pm_warning_lists_all_members",
    all(n in r["rm"]["warning"] for n in [m["path"] for m in memb]), "warning len=%d" % len(r["rm"]["warning"]))
chk("Pm_disciplines", r["rm"]["reverify"] is None and r["rm"]["problems"] == []
    and r["tier_merged"] == "SAMEDOC_LINK_EQ" and r["match_merged"] is True
    and r["path_merged"] is None and r["members_merged"] == N
    and not ({"verified_path", "recomputed", "bytes"} & set(r["recm"]))
    and "禁止由 merged 推导任何授权结论" in r["rm"]["warning"],
    "tier=%s match=%s path=%s" % (r["tier_merged"], r["match_merged"], r["path_merged"]))
chk("Pm_decl_line_covers_all_15", eq.get("decl_lines") == [3]
    and len({c for d in eq.get("decl_hits", []) for c in d["covers"]}) == N,
    json.dumps(eq.get("decl_lines"), ensure_ascii=False))

# ---------------------------------------------------------------- (3) Q4 multi 真件 triple
Q4 = ROOT / "lead" / "re_line_20261105" / "W9_SINGLESTEP_7CFC9F" / "Q4_RELATION.md"
tq = Q4.read_bytes().decode("utf-8")
qh = "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251"
for bd in (26405, None):
    r = dbl(tq, Q4.parent, qh, bd)
    tag = "Q4_multi_bytes_%s" % bd
    rows.append({"case": tag, "expect": "multi", **{k: v for k, v in r.items()
                if k not in ("ro", "rm", "reco", "recm")}})
    chk(tag + "_identical_and_triple_equal",
        r["vo"] == "multi" and r["vm"] == "multi" and r["identical"]
        and r["triple_rec_identical"] and r["tier_merged"] == "SAMEDOC_LINK"
        and r["match_merged"] is None and r["path_merged"] is None
        and r["anchors_merged"] == 6 and not r["has_eq"],
        "anchors=%d tier=%s" % (r["anchors_merged"], r["tier_merged"]))

# ---------------------------------------------------------------- (4) 原 selftest 8 调用面
cand = ROOT / "lead" / "b2b_candidate_lf_20261107" / "qc151_trip.candidate_lf.py"
sha_a, n_a = fp(FIX / "multi" / "dup_alpha.txt")
sha_t, n_t = fp(FIX / "uniq" / "target_one.txt")
sha_l, n_l = fp(FIX / "res" / "sub" / "local.txt")
sha_r, n_r = fp(FIX / "rootonly.txt")
sha_sub, n_sub = fp(FIX / "res" / "sub" / "both.txt")
sha_root, n_root = fp(FIX / "both.txt")
sha_c, n_c = fp(cand)
doc_c = (FIX / "zero" / "doc_zero.md").read_text(encoding="utf-8")
marker = HEX64.findall(doc_c)[0]

SELFTEST = [
    ("sl_a_multi", FIX / "multi" / "doc_multi.md", sha_a, n_a, SL.REPO_ROOT, "multi"),
    ("sl_b_unique", FIX / "uniq" / "doc_uniq.md", sha_t, n_t, SL.REPO_ROOT, "unique"),
    ("sl_c_zero", FIX / "zero" / "doc_zero.md", marker, None, SL.REPO_ROOT, "zero"),
    ("sl_d1_unique", FIX / "res" / "sub" / "doc_d1.md", sha_l, n_l, SL.REPO_ROOT, "unique"),
    ("sl_d2_unique", FIX / "res" / "sub" / "doc_d2.md", sha_r, n_r, FIX, "unique"),
    ("sl_d3a_unique", FIX / "res" / "sub" / "doc_d3.md", sha_sub, n_sub, FIX, "unique"),
    ("sl_d3b_zero", FIX / "res" / "sub" / "doc_d3.md", sha_root, n_root, FIX, "zero"),
    ("sl_d4_unique", FIX / "res" / "sub" / "doc_d4.md", sha_c, n_c, ROOT, "unique"),
]
history = json.loads((SL_DIR / "_sl_selftest_out.json").read_text(encoding="utf-8"))
for tag, doc, hx, bd, rt, expect in SELFTEST:
    text = doc.read_bytes().decode("utf-8")
    r = dbl(text, doc.parent, hx, bd, rt)
    rows.append({"case": tag, "expect": expect, **{k: v for k, v in r.items()
                if k not in ("ro", "rm", "reco", "recm")}})
    chk(tag + "_parity", r["vo"] == expect and r["vm"] == expect and r["identical"]
        and r["triple_rec_identical"] and not r["has_eq"],
        "vo=%s vm=%s identical=%s" % (r["vo"], r["vm"], r["identical"]))

selftest_hist = [{"case": x["case"], "pass": x["pass"]} for x in history]
chk("selftest_history_all_pass", all(x["pass"] for x in history)
    and len(history) == 9, json.dumps(selftest_hist, ensure_ascii=False)[:300])

summary = {
    "cases": len(rows),
    "assertions_passed": sum(1 for x in A if x["ok"]),
    "assertions_total": len(A),
    "verdict_pairs": {k: sum(1 for r in rows if r["vo"] + "->" + r["vm"] == k)
                      for k in sorted({r["vo"] + "->" + r["vm"] for r in rows})},
    "identical_cases": [r["case"] for r in rows if r["identical"]],
    "changed_cases": [r["case"] for r in rows if not r["identical"]],
    "unique_unaffected": all(r["vm"] == "unique" and r["identical"]
                             for r in rows if r["vo"] == "unique"),
    "zero_unaffected": all(r["vm"] == "zero" and r["identical"]
                           for r in rows if r["vo"] == "zero"),
}
out = {"guard": guard, "decl_vocab": RE.DECL_RE.pattern, "fixture_blob":
       {"sha256": FH, "bytes": NB, "sha256_diff": FH2, "bytes_diff": NB2},
       "summary": summary, "selftest_history": selftest_hist,
       "cases": rows, "assertions": A}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

for r in rows:
    print("%-28s expect=%-11s %s->%s identical=%s eq=%s anchors=%s triple_eq=%s" % (
        r["case"], r["expect"], r["vo"], r["vm"], r["identical"], r["has_eq"],
        r["anchors_merged"], r["triple_rec_identical"]))
print("SUMMARY:", json.dumps(summary, ensure_ascii=False))
print("ASSERTIONS:", summary["assertions_passed"], "/", summary["assertions_total"], "passed")
for x in A:
    if not x["ok"]:
        print("  FAIL:", x["name"], x["detail"])
print("OUT:", OUT)
sys.exit(0 if all(x["ok"] for x in A) else 1)
