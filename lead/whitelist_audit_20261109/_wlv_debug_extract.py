# -*- coding: utf-8 -*-
import ast, json, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
p = ROOT / ".zcode/workflow-runs" / "dwfrun-962827dd-a748-45ed-b80c-6076f87c9a55.mjs"
t = p.read_text(encoding="utf-8", errors="replace")
i = t.find("export const payload = ")
low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
lowered = low["lowered"]
k = lowered.find("const GATE_CODE = [")
m = re.search(r"\]\s*\.join", lowered[k:])
body = lowered[k + len("const GATE_CODE = ["): k + m.start()]
parts = []
STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
for sm in STR_RE.finditer(body):
    try:
        parts.append(json.loads('"' + sm.group(1) + '"'))
    except Exception:
        parts.append(sm.group(1))
src = "\n".join(parts)
print("n parts", len(parts), "src len", len(src))
print("--- first 14 lines ---")
for j, l in enumerate(src.split("\n")[:14]):
    print(j, repr(l))
print("--- lines with PRE_ / gateSha / template concatenation ---")
for j, l in enumerate(src.split("\n")):
    if "PRE_" in l or "gateSha" in l or "tplSha" in l:
        print(j, repr(l))
try:
    ast.parse(src)
    print("AST OK")
except SyntaxError as e:
    print("AST SyntaxError:", e)
    lines = src.split("\n")
    if e.lineno:
        for j in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
            print("  around", j + 1, repr(lines[j]))
