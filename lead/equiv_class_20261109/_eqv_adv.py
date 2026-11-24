# _eqv_adv.py — 复核员③对抗夹具（J4 未覆盖分支）。
# 夹具只写本写域 _eqv_fixtures/。
import hashlib
import os
import re
import sys

ROOT = "D:/Project/ra2-campaign-forge"
FX = ROOT + "/lead/equiv_class_20261109/_eqv_fixtures"
SL_PY = ROOT + "/lead/samedoc_link_20261109/_sl_link.py"

_b = open(SL_PY, "rb").read()
assert hashlib.sha256(_b).hexdigest() == "a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5"
assert len(_b) == 12475

sys.dont_write_bytecode = True
sys.path.insert(0, ROOT + "/lead/samedoc_link_20261109")
import _sl_link as SL  # noqa: E402

BLOB = b"EQV-ADVERSARIAL-FIXTURE-20261109\n"
HEX = hashlib.sha256(BLOB).hexdigest()
N = len(BLOB)

DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")


def j4(text, res):
    """独立 J4 实现（规格 = 设计回件 §5.1）。"""
    if res.get("verdict") != "multi":
        return res["verdict"], {"applied": False, "reason": "not multi"}
    members = res["anchors"]
    kset = set()
    for m in members:
        kset.add(m["key"])
    cov = {}
    for m in members:
        for t in m["tokens"]:
            for ln in t["lines"]:
                cov.setdefault(ln, set())
                cov[ln].add(m["key"])
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
        group = group | set(d["covers"])
    if group != kset:
        return "multi", {"applied": False, "reason": "partial coverage -> keeps multi",
                         "decl_hits": decl_hits}
    lines = []
    for d in decl_hits:
        lines.append(d["line"])
    return "merged", {"applied": True, "decl_lines": lines}


def _w(name, fn, mode, data):
    fp = os.path.join(FX, name, fn)
    _root = os.path.abspath(FX)
    _abs = os.path.abspath(fp)
    if os.path.commonpath([_root, _abs]) != _root or ".." in os.path.relpath(_abs, _root):
        raise SystemExit("fixture path escape: %r" % fn)
    os.makedirs(os.path.dirname(_abs), exist_ok=True)
    with open(_abs, mode) as f:
        f.write(data)
    return _abs


def run(name):
    dp = os.path.join(FX, name, "doc.md")
    text = open(dp, encoding="utf-8").read()
    res = SL.link(text, os.path.join(FX, name), HEX, N, root=ROOT)
    fin, info = j4(text, res)
    print("%-16s raw=%-7s final=%-7s anchors=%d %s" % (
        name, res["verdict"], fin, len(res.get("anchors", [])),
        (info.get("decl_lines") or info.get("reason"))))


_w("E1_negation", "x_a.py", "wb", BLOB)
_w("E1_negation", "x_b.py", "wb", BLOB)
_w("E1_negation", "doc.md", "w",
   "被核对象 SHA256 = " + HEX + "，字节数 = " + str(N) + "\n\n"
   "授权边界：**禁止**把 `x_a.py` 复制为 `x_b.py`；两者角色对立，不得互指。\n")

_w("E2_partial3", "p1.py", "wb", BLOB)
_w("E2_partial3", "p2.py", "wb", BLOB)
_w("E2_partial3", "p3.py", "wb", BLOB)
_w("E2_partial3", "doc.md", "w",
   "被核对象 SHA256 = " + HEX + "，字节数 = " + str(N) + "\n\n"
   "`p1.py` 复制自 `p2.py`。\n\n另有 `p3.py`（同 hash 第三件，无任何声明）。\n")

_w("E3_unique_decl", "only_b.py", "wb", BLOB)
_w("E3_unique_decl", "doc.md", "w",
   "被核对象 SHA256 = " + HEX + "，字节数 = " + str(N) + "\n\n"
   "对象为 `only_b.py`（`ghost_a.py` 复制自 `only_b.py`，ghost 不在盘）。\n")

_w("E4_trunc4", "t1.py", "wb", BLOB)
_w("E4_trunc4", "t2.py", "wb", BLOB)
_w("E4_trunc4", "doc.md", "w",
   "见 `t1.py`（之一）。\n见 `t1.py`（之二）。\n见 `t1.py`（之三）。\n"
   "见 `t1.py`（之四）。\n见 `t1.py`（之五）。\n"
   "授权声明：`t1.py` 复制自 `t2.py`。\n"
   "被核对象 SHA256 = " + HEX + "，字节数 = " + str(N) + "\n")

_w("E5_positive", "y_a.py", "wb", BLOB)
_w("E5_positive", "y_b.py", "wb", BLOB)
_w("E5_positive", "doc.md", "w",
   "被核对象 SHA256 = " + HEX + "，字节数 = " + str(N) + "\n\n"
   "`y_a.py` 复制自 `y_b.py`（忠实复制）。\n")

print()
run("E1_negation")
run("E2_partial3")
run("E3_unique_decl")
run("E4_trunc4")
run("E5_positive")
