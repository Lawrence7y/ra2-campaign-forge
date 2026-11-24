# -*- coding: utf-8 -*-
"""_rev_edge25.py — 复核员附加边界探查（不影响六项结论，仅登记实现与原型的一处已披露分叉）：
  并入版 J4 块用「全量 matches」建覆盖图（_re_linked.py:257-262 / :280-281），
  原型 eq_merge 用 res["anchors"]（_eq_proto.py:54，即 matches[:12]）。
  构造 25 成员夹具：12 条声明行各覆盖「1 个 anchor 成员 + 1 个非 anchor 成员」，
  再加 1 条声明行覆盖余下非 anchor 成员。
    - 原型：每条声明行的 anchor 侧覆盖数恒为 1（<2）→ 无 decl_hits → 保持 multi；
    - 并入版：每条声明行覆盖 2 个成员 → 有 hits，且并集 == 全体 25 成员 → merged。
  实跑记录两者差异，并核对并入版 members 全列 25 / anchors 仅 12 / 三纪律仍在。
  夹具落本写域 _rev_fixtures/；输出落本写域 _rev_edge25_out.json。零真机、零采样代码。"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
OUT = RE_DIR / "_rev_edge25_out.json"
A = []
def chk(n, c, d=""):
    A.append({"name": n, "ok": bool(c), "detail": str(d)})

def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m
SL = load("_rev_sl3", SL_DIR / "_sl_link.py")
RE = load("_rev_re3", RE_DIR / "_re_linked.py")

DECL = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")

def reviewer_proto(text, res):
    """据实读 _eq_proto.py:50-92 重写：members = res["anchors"]（≤12）。"""
    if res["verdict"] != "multi":
        return dict(res), {"applied": False}
    members = res["anchors"]
    kset = {m["key"] for m in members}
    cov = {}
    for m in members:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set()).add(m["key"])
    hits = []
    for i, lntext in enumerate(text.splitlines()):
        if DECL.search(lntext):
            ck = cov.get(i + 1, set())
            if len(ck) >= 2:
                hits.append({"line": i + 1, "covers": sorted(ck)})
    if not hits:
        return dict(res), {"applied": False, "reason": "no decl line covering >=2 anchors"}
    group = set()
    for d in hits:
        group |= set(d["covers"])
    if group != kset:
        return dict(res), {"applied": False, "reason": "partial", "hits": hits}
    out = dict(res)
    out["verdict"] = "merged"
    return out, {"applied": True, "members_n": len(members), "hits": hits}

BLOB = b"REV-EDGE25-FIXTURE-20261109\n"
FH = hashlib.sha256(BLOB).hexdigest()
NB = len(BLOB)
N = 25
toks = ["m%02d.py" % i for i in range(1, N + 1)]
d = RE_DIR / "_rev_fixtures" / "edge25_anchor_divergence"
d.mkdir(parents=True, exist_ok=True)
for t in toks:
    (d / t).write_bytes(BLOB)
lines = ["被核对象 SHA256 = %s，字节数 = %d" % (FH, NB), "",
         " ".join("`%s`" % t for t in toks) + " 为全部成员。"]
# 12 条：每条覆盖 1 个 anchor(m01..m12) + 1 个非 anchor(m13..m24)
for i in range(12):
    lines.append("`%s` 复制自 `%s`。" % (toks[i], toks[12 + i]))
# 第 13 条：覆盖余下两个非 anchor（m24 与 m25），使并集 == 全体 25
lines.append("`%s` 复制自 `%s`。" % (toks[23], toks[24]))
text = "\n".join(lines) + "\n"
(d / "doc.md").write_text(text, encoding="utf-8", newline="\n")

ro = SL.link(text, d, FH, NB)
rm = RE.link(text, d, FH, NB)
po, pi = reviewer_proto(text, json.loads(json.dumps(ro)))
pp, pw, recm = RE.link_triple(text, d, FH, NB)
eq = rm.get("eq") or {}
res = {
    "n_members": N, "fixture_dir": str(d), "blob_sha": FH, "blob_bytes": NB,
    "orig_verdict": ro["verdict"], "impl_verdict": rm["verdict"],
    "proto_reimpl_verdict": po["verdict"], "proto_info": pi,
    "anchors_orig": len(ro["anchors"]), "anchors_impl": len(rm["anchors"]),
    "impl_members": len(eq.get("members", [])),
    "impl_decl_lines": eq.get("decl_lines"),
    "triple": {"tier": recm["tier"], "path": recm["path"], "match": recm["match"],
               "keys": sorted(recm.keys()), "members_n": len(recm.get("members", []))},
    "reverify": rm.get("reverify"), "problems": rm["problems"],
    "warning_ban": "禁止由 merged 推导任何授权结论" in (rm.get("warning") or ""),
    "warning_path_none": "未做单一对象主张（path=None）" in (rm.get("warning") or ""),
}
chk("orig_is_multi_25", ro["verdict"] == "multi" and res["anchors_orig"] == 12)
chk("proto_reimpl_stays_multi", po["verdict"] == "multi", json.dumps(pi, ensure_ascii=False))
chk("impl_merges_due_to_full_matches", rm["verdict"] == "merged", rm["verdict"])
chk("divergence_real", po["verdict"] != rm["verdict"])
chk("impl_members_full_25", res["impl_members"] == 25 and res["anchors_impl"] == 12)
chk("impl_disciplines_hold", recm["path"] is None and rm["reverify"] is None
    and not ({"verified_path", "recomputed", "bytes"} & set(recm))
    and res["warning_ban"] and res["warning_path_none"] and rm["problems"] == [])
chk("members_sha_all_match_blob",
    all(set(m) == {"path", "sha", "bytes"} and m["sha"] == FH and m["bytes"] == NB
        for m in eq.get("members", [])))
OUT.write_text(json.dumps({"result": res, "decl_lines_text": [lines[i - 1] for i in eq.get("decl_lines", [])],
                           "assertions": A}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("ORIG:", ro["verdict"], "anchors=", res["anchors_orig"])
print("PROTO-REIMPL(anchors-limited):", po["verdict"], "|", json.dumps(pi, ensure_ascii=False))
print("IMPL(full matches):", rm["verdict"], "decl_lines=", res["impl_decl_lines"],
      "members=", res["impl_members"], "anchors=", res["anchors_impl"])
print("TRIPLE:", res["triple"])
print("ASSERTIONS:", sum(1 for x in A if x["ok"]), "/", len(A), "passed")
for x in A:
    if not x["ok"]:
        print("  FAIL:", x["name"], x["detail"][:300])
print("OUT:", OUT)
sys.exit(0 if all(x["ok"] for x in A) else 1)
