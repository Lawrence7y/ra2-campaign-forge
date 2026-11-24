# -*- coding: utf-8 -*-
"""_mc_count.py — 精确计数 (a)(b)(c) + 逐件判定（只读）。
分类口径：
  PRODUCER = 定义 link()/link_triple() 的模块本身（_re_linked.py / _sl_link.py）
  AUDIT    = 本审计写域 _mc_*.py（我自己写的，不算现盘既有消费方）
  其余 = 现盘既有「读 link()/link_triple() 返回值」的件
  按装载模块分：RE(可产 merged, 装 _re_linked) / SL(原件, 装 _sl_link, 永不产 merged)
"""
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
DEPTH_CAP = 6
PRUNE = {".git", "__pycache__", ".mimosa", "node_modules", ".tmp"}
MAXB = 400000

# 真调用（排除注释/docstring）：形如 XX.link( 或 XX.link_triple( 或裸 link(
CALL_LINK = re.compile(r"(?<![A-Za-z_])link\s*\(")
CALL_TRIPLE = re.compile(r"link_triple\s*\(")
# rec 字段直接下标 / .get
SUB_PATH = re.compile(r"""\[\s*['"]path['"]\s*\]""")
SUB_VP = re.compile(r"""\[\s*['"]verified_path['"]\s*\]""")
GET_PATH = re.compile(r"""\.get\(\s*['"]path['"]""")
GET_VP = re.compile(r"""\.get\(\s*['"]verified_path['"]""")
REVERIFY_PATH = re.compile(r"""reverify[^\n]*\[\s*['"]path['"]\s*\]""")
ANCHOR_PATH = re.compile(r"""\[\s*['"]path['"]\s*\]""")
# match=True 后假设 path 非空：同一行/相邻行 if match ... 且用 verified_path。粗判 + 已实证单列
MATCH_TRUE = re.compile(r"""\[\s*['"]match['"]\s*\]\s*(?:is|==)\s*True|\.get\(['"]match['"]\)\s*is\s*True|is not True""")

def files():
    base = len(LEAD.parts)
    for dp, dns, fns in os.walk(LEAD):
        d = Path(dp)
        dns[:] = [x for x in dns if x not in PRUNE]
        if len(d.parts) - base > DEPTH_CAP:
            dns[:] = []
            continue
        for fn in fns:
            if fn.endswith(".py"):
                p = d / fn
                try:
                    if p.stat().st_size <= MAXB:
                        yield p
                except OSError:
                    pass

def load_kind(t):
    kinds = set()
    if re.search(r"import _re_linked|_re_linked\.py\"|_re_linked\.py'|r33e_merge.*_re_linked", t):
        kinds.add("RE")
    if re.search(r"import _sl_link|_sl_link\.py\"|_sl_link\.py'", t):
        kinds.add("SL")
    return kinds

rows = []
for p in files():
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    t = p.read_text(encoding="utf-8", errors="replace")
    # 只取代码行（去掉整行注释 + docstring 粗略：去掉以 # 开头、含三引号段落的保守做法）
    code_lines = []
    for ln in t.splitlines():
        s = ln.strip()
        if s.startswith("#") or s.startswith("*") or s.startswith('"""') or s.startswith("'''"):
            continue
        code_lines.append(ln)
    code = "\n".join(code_lines)
    producer = rel.endswith("/_re_linked.py") or rel.endswith("/_sl_link.py")
    audit = "/merged_consumer_audit_20261109/" in rel
    n_link = len(CALL_LINK.findall(code))
    n_triple = len(CALL_TRIPLE.findall(code))
    if not (n_link or n_triple):
        continue
    kinds = load_kind(t)
    read_path = bool(SUB_PATH.search(code) or GET_PATH.search(code) or REVERIFY_PATH.search(code))
    read_vp = bool(SUB_VP.search(code) or GET_VP.search(code))
    rows.append({
        "file": rel, "producer": producer, "audit": audit,
        "kinds": sorted(kinds), "link": n_link, "triple": n_triple,
        "read_path": read_path, "read_vp": read_vp,
    })

real = [r for r in rows if not r["producer"] and not r["audit"]]
print("=== (a) 现盘既有「读 link()/link_triple() 返回值」的件（排除 producer 模块 + 本审计写域）===")
print("COUNT(a) = %d" % len(real))
by_kind = {}
for r in real:
    k = "+".join(r["kinds"]) if r["kinds"] else "?"
    by_kind.setdefault(k, []).append(r["file"])
for k in sorted(by_kind):
    print("  [%s] n=%d" % (k, len(by_kind[k])))
    for f in sorted(by_kind[k]):
        print("      " + f)

print("\n=== (b) 其中读 rec['path'] / rec['verified_path']（含 reverify['path']/anchors[]['path']）的件 ===")
b = [r for r in real if r["read_path"] or r["read_vp"]]
print("COUNT(b) = %d" % len(b))
for r in sorted(b, key=lambda x: x["file"]):
    print("  %s | read_path=%s read_vp=%s | loads=%s" %
          (r["file"], r["read_path"], r["read_vp"], "+".join(r["kinds"])))

print("\n=== (c) 「match=True ⇒ path 非空」危险模式（实证 + 静态）===")
print("  EMPIRICAL (本会话 _mc_empirical.py 实跑，真实 merged rec 喂入):")
print("    _f2v_verify9.py:21-29 → TypeError: Path(None)  【会崩】")
print("    （该件不在 (a) 内：它调用 r11_scan_plus，不调用 link();属未来接入面）")
print("  STATIC 粗筛（real 件中同时读 match 与 verified_path/bytes 直接下标）:")
for r in sorted(real, key=lambda x: x["file"]):
    t = (ROOT / r["file"]).read_text(encoding="utf-8", errors="replace")
    if MATCH_TRUE.search(t) and (SUB_VP.search(t) or re.search(r"""\[\s*['"]bytes['"]\s*\]""", t)):
        print("    %s" % r["file"])

print("\n=== SUMMARY COUNTS ===")
print("scanned_files(all .py)=%d  rows_with_link_call=%d  real_consumers(a)=%d  read_path_or_vp(b)=%d" %
      (sum(1 for _ in files()), len(rows), len(real), len(b)))
