# -*- coding: utf-8 -*-
"""_re_run10_diff.py — J4 并入版行为回归：F2-d 十条真实无路径绑定行（+2 附加对照
+1 合成 invalid_hex）原实现 _sl_link.py vs 并入版 _re_linked.py 逐条双跑。
断言：
  (1) unique/zero/invalid_hex 及未触发 J4 的 multi：两实现输出 JSON 逐字节全等
      （逐条记录两输出规范化 JSON 的 sha256 作证）；
  (2) 条3 multi->merged：成员数守恒、reverify 恒 None、members 全列（path/sha/bytes）、
      decl_hits 带声明行号与原文；
  (3) link_triple 四态契约：条1 zero rec 全等、条2 unique rec 全等、条3 merged rec
      新形态（tier=SAMEDOC_LINK_EQ、match=True、path=None、无单对象字段）。
喂入同 _sl_run10.py:65-92（bytes_decl 取自绑定行 BYTES_RE；hex 用清单预期值）。
输出落本写域 _re_run10_out.json。零真机、零采样代码；-B 防 __pycache__。"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SL_DIR = ROOT / "lead" / "samedoc_link_20261109"
RE_DIR = ROOT / "lead" / "r33e_merge_20261109"
OUT = RE_DIR / "_re_run10_out.json"

_b = (SL_DIR / "_sl_link.py").read_bytes()
guard_sl = {"file": "lead/samedoc_link_20261109/_sl_link.py",
            "sha256": hashlib.sha256(_b).hexdigest(), "bytes": len(_b),
            "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
            "expect_bytes": 12475}
if not (guard_sl["sha256"] == guard_sl["expect_sha"] and guard_sl["bytes"] == guard_sl["expect_bytes"]):
    raise SystemExit("GUARD FAIL: original fingerprint drifted: %r" % guard_sl)

sys.path.insert(0, str(SL_DIR))
sys.path.insert(0, str(RE_DIR))
import _sl_link as SL   # noqa: E402  只读原件
import _re_linked as RE  # noqa: E402  并入版

MOTHER = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
CAND = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
SPEC = "cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306"
R1 = "3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125"
TEN = [
    ("t1", ROOT / "lead" / "a_residual_n1_20261108" / "A_RESIDUAL_REFERENCES.md", 130, R1),
    ("t2", ROOT / "lead" / "b2b_isolated_20261107" / "INTEGRATION_REPORT.md", 31, CAND),
    ("t3", ROOT / "lead" / "b2b_isolated_20261107" / "_integ_INTEGRATION_REPORT.md", 5, CAND),
    ("t4", ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", 51, MOTHER),
    ("t5", ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", 52, CAND),
    ("t6", ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", 53, SPEC),
    ("t7", ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", 228, MOTHER),
    ("t8", ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md", 229, CAND),
    ("t9", ROOT / "lead" / "bexec_n4_20261108" / "_n4_SPEC_N4_B2B_MATRIX.md", 28, MOTHER),
    ("t10", ROOT / "lead" / "bexec_n4_20261108" / "_n4_SPEC_N4_B2B_MATRIX.md", 29, CAND),
]
EXTRA = [
    ("exA", ROOT / "lead" / "b2b_isolated_20261107" / "INTEGRATION_REPORT.md", 147, CAND),
    ("exB", ROOT / "lead" / "b2b_isolated_20261107" / "_integ_INTEGRATION_REPORT.md", 6, MOTHER),
]
HEX_RE = re.compile(r"[0-9a-fA-F]{64}")


def run_one(tag, doc, line_no, exp_hex):
    raw = doc.read_bytes()
    line = raw.decode("utf-8").splitlines()[line_no - 1]
    hexes = HEX_RE.findall(line)
    align = "MATCH" if (hexes and hexes[0].lower() == exp_hex) else "MISMATCH"
    bm = SL.BYTES_RE.search(line)
    bytes_decl = int(SL._COMMA.sub("", bm.group(1))) if bm else None
    ro = SL.link(raw.decode("utf-8"), doc.parent, exp_hex, bytes_decl)
    rm = RE.link(raw.decode("utf-8"), doc.parent, exp_hex, bytes_decl)
    so = json.dumps(ro, ensure_ascii=False, sort_keys=True)
    sm2 = json.dumps(rm, ensure_ascii=False, sort_keys=True)
    eq = rm.get("eq") or {}
    return {"tag": tag, "doc": str(doc), "line": line_no, "hex": exp_hex,
            "bytes_decl": bytes_decl, "hex_align_guard": align,
            "doc_sha12": hashlib.sha256(raw).hexdigest()[:12], "doc_bytes": len(raw),
            "line_excerpt": line[:110],
            "verdict_orig": ro["verdict"], "verdict_merged": rm["verdict"],
            "identical": so == sm2,
            "sha_json_orig": hashlib.sha256(so.encode("utf-8")).hexdigest(),
            "sha_json_merged": hashlib.sha256(sm2.encode("utf-8")).hexdigest(),
            "anchors_orig": len(ro.get("anchors", [])),
            "anchors_merged": len(rm.get("anchors", [])),
            "reverify_equal": ro.get("reverify") == rm.get("reverify"),
            "decl_lines_merged": eq.get("decl_lines"),
            "members_merged": len(eq.get("members", [])) if eq else None,
            "out_orig": ro, "out_merged": rm}


rows = [run_one(t, d, ln, hx) for t, d, ln, hx in TEN]
extras = [run_one(t, d, ln, hx) for t, d, ln, hx in EXTRA]
bad = run_one("invalid_hex", TEN[2][1], 5, "zzzz-not-hex")


A = []
def chk(name, cond, detail=""):
    A.append({"name": name, "ok": bool(cond), "detail": detail})


chk("unique_set_unchanged",
    [r["tag"] for r in rows if r["verdict_orig"] == "unique"]
    == [r["tag"] for r in rows if r["verdict_merged"] == "unique"])
chk("zero_set_unchanged",
    [r["tag"] for r in rows if r["verdict_orig"] == "zero"]
    == [r["tag"] for r in rows if r["verdict_merged"] == "zero"])
for r in rows + extras + [bad]:
    if r["verdict_orig"] in ("unique", "zero", "invalid_hex"):
        chk(r["tag"] + " output_identical", r["identical"])
    elif r["verdict_orig"] == "multi" and r["verdict_merged"] == "multi":
        chk(r["tag"] + " multi_not_fired_identical", r["identical"])
    elif r["verdict_orig"] == "multi" and r["verdict_merged"] == "merged":
        chk(r["tag"] + " members_conserved", r["members_merged"] == r["anchors_orig"],
            "members=%d anchors=%d" % (r["members_merged"], r["anchors_orig"]))
        m = r["out_merged"]
        chk(r["tag"] + " merged_disciplines",
            m.get("reverify") is None and bool(m["eq"]["decl_lines"])
            and all(d.get("text") for d in m["eq"]["decl_hits"])
            and all(set(x) == {"path", "sha", "bytes"} for x in m["eq"]["members"]))
    else:
        chk(r["tag"] + " unexpected_pair", False, r["verdict_orig"] + "->" + r["verdict_merged"])
chk("invalid_hex_passthrough_identical", bad["identical"] and bad["verdict_orig"] == "invalid_hex")


trip = {}
for tag, doc, ln, hx in TEN:
    if tag not in ("t1", "t2", "t3"):
        continue
    raw = doc.read_bytes().decode("utf-8")
    line = raw.splitlines()[ln - 1]
    bm = SL.BYTES_RE.search(line)
    bd = int(SL._COMMA.sub("", bm.group(1))) if bm else None
    po, wo, reco = SL.link_triple(raw, doc.parent, hx, bd)
    pm, wm, recm = RE.link_triple(raw, doc.parent, hx, bd)
    trip[tag] = {"orig": {"tier": reco["tier"], "match": reco["match"], "path": reco["path"]},
                 "merged": {"tier": recm["tier"], "match": recm["match"], "path": recm["path"],
                            "members_n": len(recm.get("members") or []),
                            "decl_lines": recm.get("decl_lines"),
                            "no_single_object_fields": not ({"verified_path", "recomputed", "bytes"} & set(recm))},
                 "rec_equal": json.dumps(reco, sort_keys=True) == json.dumps(recm, sort_keys=True)}
chk("triple_t1_zero_rec_equal", trip["t1"]["rec_equal"] is True)
chk("triple_t2_unique_rec_equal", trip["t2"]["rec_equal"] is True)
chk("triple_t3_merged_shape",
    trip["t3"]["merged"]["tier"] == "SAMEDOC_LINK_EQ"
    and trip["t3"]["merged"]["match"] is True
    and trip["t3"]["merged"]["path"] is None
    and trip["t3"]["merged"]["members_n"] == 2
    and trip["t3"]["merged"]["no_single_object_fields"] is True)


def vc(rs):
    d = {}
    for r in rs:
        k = r["verdict_orig"] + "->" + r["verdict_merged"]
        d[k] = d.get(k, 0) + 1
    return d


summary = {
    "ten_counts": vc(rows),
    "extra_counts": vc(extras + [bad]),
    "unique_count_orig": sum(1 for r in rows if r["verdict_orig"] == "unique"),
    "unique_count_merged": sum(1 for r in rows if r["verdict_merged"] == "unique"),
    "zero_count_orig": sum(1 for r in rows if r["verdict_orig"] == "zero"),
    "zero_count_merged": sum(1 for r in rows if r["verdict_merged"] == "zero"),
    "multi_to_merged": [r["tag"] for r in rows if r["verdict_orig"] == "multi" and r["verdict_merged"] == "merged"],
    "multi_kept_multi": [r["tag"] for r in rows if r["verdict_orig"] == "multi" and r["verdict_merged"] == "multi"],
    "identical_rows": [r["tag"] for r in rows + extras + [bad] if r["identical"]],
    "changed_rows": [r["tag"] for r in rows + extras + [bad] if not r["identical"]],
}


hist = json.loads((SL_DIR / "_sl_run10_out.json").read_text(encoding="utf-8"))
hist_v = {r["tag"]: r["verdict"] for r in hist["ten"]}
hk = {"t1": "条1", "t2": "条2", "t3": "条3", "t4": "条4", "t5": "条5",
      "t6": "条6", "t7": "条7", "t8": "条8", "t9": "条9", "t10": "条10"}
history_cross = [{"tag": r["tag"], "historical": hist_v.get(hk[r["tag"]]),
                  "live_orig": r["verdict_orig"], "live_merged": r["verdict_merged"]} for r in rows]

full = {}
for r in rows + extras + [bad]:
    if r["tag"] in ("t1", "t2", "t3", "invalid_hex"):
        full[r["tag"]] = {"orig": r["out_orig"], "merged": r["out_merged"]}

out = {"guard_sl": guard_sl, "summary": summary, "history_cross_check": history_cross,
       "ten": [{k: v for k, v in r.items() if k not in ("out_orig", "out_merged")} for r in rows],
       "extras": [{k: v for k, v in r.items() if k not in ("out_orig", "out_merged")} for r in extras + [bad]],
       "full_outputs": full, "link_triple_spot": trip, "assertions": A}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

for r in rows:
    print("%-4s %-28s:%-4s bd=%-7s %s->%s identical=%s members=%s decl=%s" % (
        r["tag"], Path(r["doc"]).name, r["line"], r["bytes_decl"],
        r["verdict_orig"], r["verdict_merged"], r["identical"],
        r["members_merged"], r["decl_lines_merged"]))
for r in extras + [bad]:
    print("%-8s %-28s:%-4s %s->%s identical=%s" % (r["tag"], Path(r["doc"]).name, r["line"],
                                                   r["verdict_orig"], r["verdict_merged"], r["identical"]))
print("SUMMARY:", json.dumps(summary, ensure_ascii=False))
print("HISTORY:", " ".join("%s:%s|%s->%s" % (h["tag"], h["historical"], h["live_orig"], h["live_merged"]) for h in history_cross))
print("ASSERTIONS:", sum(1 for a in A if a["ok"]), "/", len(A), "passed")
for a in A:
    if not a["ok"]:
        print("  FAIL:", a["name"], a.get("detail", ""))
print("OUT:", OUT)
sys.exit(0 if all(a["ok"] for a in A) else 1)
