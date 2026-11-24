# -*- coding: utf-8 -*-
"""_oc_binding_verify.py : cross-check _oc_binding.py's 20 strings against the
archived CLAIMS array. The CLAIMS text lives inside payload.lowered (a JSON
string), so we JSON-decode that first. Read-only, no path computation.
"""
import re, json, hashlib, importlib.util

ROOT = "D:/Project/ra2-campaign-forge"
MJS = ROOT + "/.zcode/workflow-runs/dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs"
BIND = ROOT + "/lead/orch_claims_20261109/_oc_binding.py"

src = open(MJS, encoding="utf-8").read()

# payload.lowered is a JSON string; decode it to get real JS source text
m = re.search(r'"lowered"\s*:\s*"((?:[^"\\]|\\.)*)"', src, re.S)
assert m, "lowered string not found"
lowered = json.loads('"' + m.group(1) + '"')

m2 = re.search(r"const CLAIMS = \[(.*?)\]\.join\(", lowered, re.S)
assert m2, "CLAIMS block not found"
body = m2.group(1)

# now strings are plain JS double-quoted literals
parts, buf, in_str, esc = [], [], False, False
for ch in body:
    if not in_str:
        if ch == '"':
            in_str, buf = True, []
        continue
    if esc:
        buf.append(ch); esc = False; continue
    if ch == "\\":
        esc = True; buf.append(ch); continue
    if ch == '"':
        parts.append("".join(buf)); in_str = False; continue
    buf.append(ch)

def js_unescape(x):
    out, i = [], 0
    while i < len(x):
        if x[i] == "\\" and i + 1 < len(x):
            n = x[i+1]
            if n == "n": out.append("\n"); i += 2
            elif n == '"': out.append('"'); i += 2
            elif n == "\\": out.append("\\"); i += 2
            elif n == "u": out.append(chr(int(x[i+2:i+6], 16))); i += 6
            else: out.append(n); i += 2
        else:
            out.append(x[i]); i += 1
    return "".join(out)

archive = [js_unescape(p) for p in parts]
arch_num = [c for c in archive if re.match(r"^\d+\.\s", c)]

spec = importlib.util.spec_from_file_location("ocbind", BIND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
local = mod.CLAIMS

raw_arch = "\n".join(arch_num).encode("utf-8")
raw_local = "\n".join(local).encode("utf-8")

diffs = [i for i, (a, b) in enumerate(zip(arch_num, local)) if a != b]
print(json.dumps({
    "archive_literals": len(archive),
    "archive_numbered": len(arch_num),
    "local_numbered": len(local),
    "line_by_line_equal": arch_num == local,
    "diff_indices": diffs[:10],
    "archive_bytes": len(raw_arch),
    "archive_sha256": hashlib.sha256(raw_arch).hexdigest(),
    "local_bytes": len(raw_local),
    "local_sha256": hashlib.sha256(raw_local).hexdigest(),
    "MATCH": raw_arch == raw_local,
}, ensure_ascii=False, indent=2))
