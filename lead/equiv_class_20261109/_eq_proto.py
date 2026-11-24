# -*- coding: utf-8 -*-
"""_eq_proto.py — 等价类判据（J4「声明背书级」）可执行原型。

【定位】只做判据原型验证：以只读谓词 lead/samedoc_link_20261109/_sl_link.py 的 link()
为被驱动件（导入前 hashlib 实算守卫，期望 a4ae4dc1…/12475），在其输出上做纯后处理，
演示「同文档 multi → 溯源声明行覆盖 → merged / 维持 multi」的判据行为。
不改被驱动件、不改任何真实件；本件与夹具只写 lead/equiv_class_20261109/。
零真机、零采样代码、不 commit、不 push。

【判据（原型版）】
  仅当 link() verdict = multi（≥2 个现盘文件 hash+字节数皆符）时介入：
  D = {行 L : L 含溯源声明词（复制自 | 复制为 | COPY_IDENTICAL = True）}
  若存在 L ∈ D 使 ≥2 个 multi 成员的锚定 token 行号集合含 L，且这些 L 覆盖全体成员
  （全或无），则 verdict = merged（同一内容的声明背书副本群）；否则维持 multi。
  unique / zero 一律不介入（unique 不因等价类降级为 multi）。
  溯源词组刻意不含「逐字节同一/相同」——Q4_RELATION.md:85/:168 的真实反例表明
  纯等同词会把「不同趟次证据件恰好同哈希」的发现性表述误当复制声明。"""

import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True

ROOT = r"D:\Project\ra2-campaign-forge"
SL_DIR = os.path.join(ROOT, "lead", "samedoc_link_20261109")
OUT = os.path.join(ROOT, "lead", "equiv_class_20261109", "_eq_proto_out.json")

# ---- 守卫：被驱动谓词件指纹（只读件） ----
SL_PY = os.path.join(SL_DIR, "_sl_link.py")
_b = open(SL_PY, "rb").read()
guard = {"file": SL_PY,
         "sha256": hashlib.sha256(_b).hexdigest(), "bytes": len(_b),
         "expect_sha": "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5",
         "expect_bytes": 12475}
guard["match"] = (guard["sha256"] == guard["expect_sha"]
                  and guard["bytes"] == guard["expect_bytes"])
if not guard["match"]:
    raise SystemExit("GUARD FAIL: driver fingerprint drifted: %r" % guard)

sys.path.insert(0, SL_DIR)
import _sl_link as SL  # noqa: E402  (-B 已禁 pycache，不落只读目录)

# ---- J4 判据后处理 ----
DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")


def eq_merge(text, res):
    """返回 (最终res, 说明info)。仅 multi 介入；声明行覆盖全体成员才合并（全或无）。"""
    if res.get("verdict") != "multi":
        return res, {"applied": False, "reason": "not multi (rule only fires on multi)"}
    members = res["anchors"]
    kset = {m["key"] for m in members}
    cov = {}
    for m in members:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set()).add(m["key"])
    decl_hits = []
    for i, ln in enumerate(text.splitlines()):
        if DECL_RE.search(ln):
            ck = cov.get(i + 1, set())
            if len(ck) >= 2:
                decl_hits.append({"line": i + 1, "covers": sorted(ck),
                                  "text": ln.strip()[:160]})
    if not decl_hits:
        return res, {"applied": False,
                     "reason": "no provenance-declaration line covering >=2 members"}
    group = set()
    for d in decl_hits:
        group |= set(d["covers"])
    if group != kset:
        return res, {"applied": False,
                     "reason": "declaration coverage partial -> all-or-nothing rule keeps multi",
                     "decl_hits": decl_hits}
    out = dict(res)
    out["verdict"] = "merged"
    out["eq"] = {"rule": "J4 same-doc provenance-declared byte-identical copy class",
                 "decl_lines": [d["line"] for d in decl_hits],
                 "decl_hits": decl_hits,
                 "members": [{"path": m["path"], "sha": m["sha"], "bytes": m["size"]}
                             for m in members]}
    out["warning"] = (
        "同文档联查多命中 → 等价类合并（warning 级）：同文档第 %s 行存在溯源声明"
        "（复制自/复制为/COPY_IDENTICAL=True），全部 %d 个同 hash 现盘文件的锚定 token "
        "在该(些)行同现，机器逐字节核实同值 → 合并为同一内容的声明背书副本群；"
        "未做单一对象主张（path=None），角色归属留人工判定。成员：%s"
        % (",".join(str(d["line"]) for d in decl_hits), len(members),
           "；".join(m["path"] for m in members)))
    return out, {"applied": True}


def run_case(name, text, doc_dir, hexv, nbytes):
    res = SL.link(text, doc_dir, hexv, nbytes, root=ROOT)
    merged, info = eq_merge(text, res)
    return {"case": name,
            "raw_verdict": res["verdict"], "final_verdict": merged["verdict"],
            "raw_anchor_count": len(res.get("anchors", [])),
            "raw_anchor_paths": [m["path"] for m in res.get("anchors", [])],
            "decl_lines_in_doc": [i + 1 for i, ln in enumerate(text.splitlines())
                                  if DECL_RE.search(ln)],
            "eq_info": info,
            "final_warning": (merged.get("warning") or "")[:500]}


results = []

# 1) 真实条3：_integ_INTEGRATION_REPORT.md + ca23c116…/412759
_p = os.path.join(ROOT, "lead", "b2b_isolated_20261107", "_integ_INTEGRATION_REPORT.md")
_t = open(_p, encoding="utf-8").read()
results.append(run_case("real_item3", _t, os.path.dirname(_p),
                        "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2",
                        412759))

# 2) 真实反例：Q4_RELATION.md（同文档引用 6 个不同真机趟的同 hash 转储件）
_p = os.path.join(ROOT, "lead", "re_line_20261105", "W9_SINGLESTEP_7CFC9F",
                  "Q4_RELATION.md")
_t = open(_p, encoding="utf-8").read()
for nb in (26405, None):
    results.append(run_case("real_q4_dumps_bytes%d" % (nb if nb is not None else -1),
                            _t, os.path.dirname(_p),
                            "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251",
                            nb))

# 3) 构造夹具 F1/F3/F4（本写域 _eq_fixtures/）
FX = os.path.join(ROOT, "lead", "equiv_class_20261109", "_eq_fixtures")
blob = b"EQ-FIXTURE-MARKER-20261109\n"
_h = hashlib.sha256(blob).hexdigest()
_templates = {
    "F1_nodecl": ("被核对象 SHA256 = %s，字节数 = %d\n\n"
                  "见 `a_one.py` 与 `b_two.py`（不同趟次产物，无复制关系声明）。\n"),
    "F3_partial": ("被核对象 SHA256 = %s，字节数 = %d\n\n"
                   "`a_one.py` 复制自外部原件。\n\n另有 `b_two.py`。\n"),
    "F4_unique": ("被核对象 SHA256 = %s，字节数 = %d\n\n对象为 `b_two.py`。\n"),
}
for _name, _tpl in _templates.items():
    _d = os.path.join(FX, _name)
    os.makedirs(_d, exist_ok=True)
    for _fn in ("a_one.py", "b_two.py"):
        with open(os.path.join(_d, _fn), "wb") as f:
            f.write(blob)
    _t = _tpl % (_h, len(blob))
    with open(os.path.join(_d, "doc.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(_t)
    results.append(run_case(_name, _t, _d, _h, len(blob)))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"guard": guard, "decl_vocab": str(DECL_RE.pattern),
               "results": results}, f, ensure_ascii=False, indent=2)

for r in results:
    print("%-28s raw=%-7s -> final=%-7s anchors=%d decl_lines=%s applied=%s"
          % (r["case"], r["raw_verdict"], r["final_verdict"], r["raw_anchor_count"],
             r["decl_lines_in_doc"], (r["eq_info"] or {}).get("applied")))
print("OUT:", OUT)
