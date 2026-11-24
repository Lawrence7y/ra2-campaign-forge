# -*- coding: utf-8 -*-
# _siv_payload_cmp.py — 括号配平提取 payload 对象 -> json.loads -> GATE_CODE 与撰写人还原件逐字比对。只读。
import json
from pathlib import Path

WD = Path(r"D:\Project\ra2-campaign-forge\lead\gate_subject_id_20261109")
MJS_CP = Path(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs\dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs")
MJS_SELF = Path(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs\dwfrun-a7468d6e-e9f6-4050-896a-7bff15c96903.mjs")
out = {}

def load_payload(p: Path):
    t = p.read_text(encoding="utf-8", errors="ignore")
    i = t.find("export const payload")
    if i < 0:
        return None
    j = t.find("{", i)
    depth = 0
    k = j
    in_str = False
    esc = False
    while k < len(t):
        c = t[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(t[j:k + 1])
        k += 1
    return None

def unesc(s):
    r = s.replace("\\\\", "\x00")
    r = r.replace("\\n", "\n")
    r = r.replace("\\t", "\t")
    r = r.replace("\\'", "'")
    r = r.replace('\\"', '"')
    r = r.replace("\x00", "\\")
    return r

for mjs, extracted in [(MJS_CP, WD / "_si_gate_counterpart_extracted.py"), (MJS_SELF, WD / "_si_gate_self_extracted.py")]:
    pl = load_payload(mjs)
    if not isinstance(pl, dict):
        print("PARSE FAIL " + mjs.name + " " + repr(pl)[:200])
        continue
    code = pl.get("GATE_CODE", "")
    ext = extracted.read_text(encoding="utf-8")
    same = (code == ext)
    same_u = (unesc(code) == ext)
    print("=== " + mjs.name)
    print("  payload keys: " + repr(list(pl.keys())))
    print("  GATE_CODE len=" + str(len(code)) + "  extracted len=" + str(len(ext)) + "  exact=" + str(same) + "  unesc=" + str(same_u))
    if not same and not same_u:
        ce = unesc(code)
        n = min(len(ce), len(ext))
        d = 0
        while d < n and ce[d] == ext[d]:
            d = d + 1
        print("  first_diff@" + str(d) + "  payload=" + repr(ce[max(0, d - 50):d + 50]))
        print("                    extracted=" + repr(ext[max(0, d - 50):d + 50]))
    out[mjs.name] = {"keys": list(pl.keys()), "gateLen": len(code), "exact": same, "unesc": same_u}

pl = load_payload(MJS_CP)
if isinstance(pl, dict):
    for key in pl.keys():
        v = pl.get(key)
        if isinstance(v, str) and ("COUNTERPART_FIX.md" in v) and key != "GATE_CODE":
            i = v.find("COUNTERPART_FIX.md")
            print("payload field '" + key + "' contains COUNTERPART_FIX.md, ctx: " + repr(v[max(0, i - 110):i + 30]))
            out["docNameField"] = key
            break

w = WD / "_siv_payload_cmp_out.json"
w.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("written=" + str(w))
