# -*- coding: utf-8 -*-
r"""_rj_context_dump.py — 逐域导出「仍报问题」的命中原句 + 要素/绑定行在场证据（只读）。
输出：lead/gate_rejudge32_20261109/_rj_context_dump_out.txt
"""
import json
import re
import ast
import glob
import os
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
base = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dn_regate_out.json").read_text(encoding="utf-8"))
runs = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

def gate_src(low):
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    body = low[k + len("const GATE_CODE = ["):end]
    lit = re.compile(r'"((?:[^"\\]|\\.)*)"')
    parts = []
    for m in lit.finditer(body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else None

LOOP_RE = re.compile(r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)")
BANNED_RE = re.compile(r"for bad in (\[[^\]]+\]):")
SECT_RE = re.compile(r"for s in (\[[^\]]+\]):")

lines = []
def w(s=""):
    lines.append(s)

for r in base["rows"]:
    if not r["gateProblems"]:
        continue
    dom = r["domain"]
    dom_short = dom.rstrip("/").split("/")[-1]
    main = r["main"]
    mp = ROOT / dom.rstrip("/") / main
    text = mp.read_text(encoding="utf-8", errors="replace")
    doclines = text.split("\n")
    w("=" * 100)
    w("DOMAIN %s  MAIN %s  bytes=%d" % (dom, main, len(mp.read_bytes())))
    w("gateProblems = %s" % json.dumps(r["gateProblems"], ensure_ascii=False))
    w("bindings(baseline)=%s bindingRegex=%r" % (r["bindings"], r["params"]["bindingRegex"]))
    w("banned = %s" % json.dumps(r["params"]["banned"], ensure_ascii=False))
    # 要素清单
    p = runs.get(r["run"])
    elems = []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        v, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
        src = gate_src(v.get("lowered", "")) or ""
        for m in LOOP_RE.finditer(src):
            try:
                elems += ast.literal_eval(m.group(2))
            except Exception:
                pass
    w("required_elements = %s" % json.dumps(elems, ensure_ascii=False))
    for k in elems:
        w("   elem %-30r raw_present=%s" % (k, k in text))
    # 每个禁词的全部出现
    for tok in r["params"]["banned"]:
        hits = list(re.finditer(re.escape(tok), text))
        for m in hits:
            ln = text.count("\n", 0, m.start()) + 1
            s = text.rfind("\n", 0, m.start()) + 1
            e = text.find("\n", m.start())
            if e < 0:
                e = len(text)
            w("   HIT %-14r line=%-4d pos=%-6d :: %s" % (tok, ln, m.start(), text[s:e][:420]))
    # 绑定行搜索：任何含 SHA256 的行
    B = [(i + 1, ln) for i, ln in enumerate(doclines)
         if "SHA256" in ln or "字节数" in ln]
    w("   --- lines containing SHA256/字节数 (%d) ---" % len(B))
    for n, ln in B[:25]:
        w("   L%-4d %s" % (n, ln[:300]))
    w()

(WDIR / "_rj_context_dump_out.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print("\nWROTE", WDIR / "_rj_context_dump_out.txt", "lines", len(lines))
