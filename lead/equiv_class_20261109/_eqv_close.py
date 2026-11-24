# _eqv_close.py — 复核员④独立实算闭合率 + ③J4 独立实现（不复用 _eq_proto.py 代码）。
# 基座 = 被核谓词 _sl_link.py（指纹守卫；该件此前已被独立复核会话 confirmed，
# 编排方基线指纹在本任务 _eqv_fp.py 已核对一致）。
# J4 判据按设计回件 §5.1 文字独立重写：仅 multi 介入；声明行 L 须被 >=2 个成员的
# 锚定 token 行号集覆盖；全体成员覆盖才合并（全或无）；unique/zero 不介入。
import hashlib
import json
import os
import re
import sys

ROOT = "D:/Project/ra2-campaign-forge"
SL_PY = ROOT + "/lead/samedoc_link_20261109/_sl_link.py"
RUN10 = ROOT + "/lead/samedoc_link_20261109/_sl_run10_out.json"

_b = open(SL_PY, "rb").read()
assert hashlib.sha256(_b).hexdigest() == "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5" and len(_b) == 12475, "GUARD FAIL"
sys.path.insert(0, ROOT + "/lead/samedoc_link_20261109")
sys.dont_write_bytecode = True
import _sl_link as SL  # noqa: E402

HEX64 = re.compile(r"[0-9a-fA-F]{64}")
DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")


def j4(text, res):
    """独立实现。返回 (final_verdict, info)。仅 multi 介入；全或无。"""
    if res.get("verdict") != "multi":
        return res["verdict"], {"applied": False, "reason": "not multi"}
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
                decl_hits.append({"line": i + 1, "covers": sorted(ck)})
    if not decl_hits:
        return "multi", {"applied": False, "reason": "no decl line covering >=2 members"}
    group = set()
    for d in decl_hits:
        group |= set(d["covers"])
    if group != kset:
        return "multi", {"applied": False, "reason": "partial coverage -> all-or-nothing keeps multi",
                         "decl_hits": decl_hits}
    return "merged", {"applied": True, "decl_lines": [d["line"] for d in decl_hits],
                      "n_members": len(kset)}


ten = json.load(open(RUN10, encoding="utf-8"))["ten"]
print("run10 记录条目数 =", len(ten))
BIND_RE = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")
counts = {"unique_closed": 0, "merged": 0, "multi_open": 0, "zero_open": 0, "other": 0}
rows = []
TEN_ONLY = [it for it in ten if re.match(r"^条\d+$", it.get("tag", ""))]
print("十条分母条目数 =", len(TEN_ONLY))
for it in ten:
    tag = it.get("tag", "?")
    doc = it["doc"]
    mx = HEX64.search(it.get("line_excerpt", ""))
    if not mx:
        # line_excerpt 为截断引文（如条2）→ 回该文档绑定行原文提取 hex
        lines = open(doc, encoding="utf-8").read().splitlines()
        bm = BIND_RE.search(lines[it["line"] - 1]) if it.get("line") and it["line"] <= len(lines) else None
        if not bm:
            counts["other"] += 1
            print("%-5s NO_HEX（跳过计数）" % tag)
            continue
        hexv = bm.group(1)
    else:
        hexv = mx.group(0)
    bd = it.get("bytes_decl")
    text = open(doc, encoding="utf-8").read()
    res = SL.link(text, os.path.dirname(doc), hexv, bd, root=ROOT)
    fin, info = j4(text, res)
    rec_verdict = it.get("verdict")
    agree = "AGREE" if rec_verdict == res["verdict"] else "DISAGREE"
    ok = bool(res.get("reverify") and res["reverify"].get("ok"))
    closed = (res["verdict"] == "unique" and ok) or fin == "merged"
    if not re.match(r"^条\d+$", tag):
        continue  # 附加对照行位不计入十条闭合统计
    if res["verdict"] == "unique" and ok:
        counts["unique_closed"] += 1
    elif fin == "merged":
        counts["merged"] += 1
    elif res["verdict"] == "multi":
        counts["multi_open"] += 1
    elif res["verdict"] == "zero":
        counts["zero_open"] += 1
    else:
        counts["other"] += 1
    rows.append((tag, "rec=" + str(rec_verdict), "raw=" + res["verdict"],
                 "final=" + fin, "closed=" + str(closed), agree))
    print("%-5s doc=%-58s rec=%-7s raw=%-7s final=%-7s closed=%-5s anchors=%d %s decl=%s"
          % (tag, os.path.basename(doc) + " (dir " + os.path.basename(os.path.dirname(doc)) + ")",
             rec_verdict, res["verdict"], fin, closed, len(res.get("anchors", [])),
             agree, info.get("decl_lines") or info.get("reason")))

print("\n统计：", json.dumps(counts, ensure_ascii=False))
base = counts["unique_closed"]
after = base + counts["merged"]
den = len(TEN_ONLY)
print("十条分母 =", den)
print("J4 前闭合（unique 且 reverify.ok）= %d/%d" % (base, den))
print("J4 后闭合（+merged）            = %d/%d" % (after, den))
