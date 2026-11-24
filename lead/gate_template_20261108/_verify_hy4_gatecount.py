# -*- coding: utf-8 -*-
# _verify_hy4_gatecount.py —— 核对「17 个门禁」与「无一做哈希值比对」两断言
import json, re, pathlib
ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
RUNS = ROOT/".zcode/workflow-runs"

def low(p):
    s=p.read_text(encoding="utf-8")
    i=s.find('{"lowered":')
    if i<0: return None
    try: return json.JSONDecoder().raw_decode(s[i:])[0].get("lowered","")
    except Exception: return None

def gate(src):
    m=re.search(r"const GATE_CODE\s*=\s*\[(.*?)\]\.join\(", src or "", re.S)
    return m.group(1) if m else None

rows=[]
for p in sorted(RUNS.glob("dwfrun-*.mjs")):
    src=low(p); g=gate(src)
    if g is None: continue
    rows.append({
        "run":p.name[:15],
        "gate_chars":len(g),
        "has_hexdigest":"hexdigest" in g,
        "has_sha256_read":"sha256(" in g and "read_bytes" in g,
        "has_st_size":"st_size" in g or "getsize" in g,
        "has_for_bad_in":"for bad in" in g,
        "has_版本锚":"版本锚" in g or "绑定锚" in g,
        "has_3343cfbe":"3343cfbe" in g,
        "has_字节数_findall":"字节数" in g and "findall" in g,
        "has_subprocess":"subprocess" in g,
    })
out={"n_dwfrun":len(list(RUNS.glob("dwfrun-*.mjs"))),
     "n_gate_code":len(rows),
     "n_with_hexdigest":sum(r["has_hexdigest"] for r in rows),
     "n_with_sha256_read":sum(r["has_sha256_read"] for r in rows),
     "n_with_st_size":sum(r["has_st_size"] for r in rows),
     "n_with_for_bad_in":sum(r["has_for_bad_in"] for r in rows),
     "n_with_版本锚":sum(r["has_版本锚"] for r in rows),
     "n_with_3343cfbe":sum(r["has_3343cfbe"] for r in rows),
     "n_with_字节数_findall":sum(r["has_字节数_findall"] for r in rows),
     "n_with_subprocess":sum(r["has_subprocess"] for r in rows),
     "rows":rows}
# 具体列出含 st_size 的门禁（确认是「计数/存在性」型而非「值比对」型）
out["st_size_gates"]=[r["run"] for r in rows if r["has_st_size"]]
# 全 .mjs（含 dwfeval）里 hexdigest 出现在 GATE_CODE 内吗
out["any_gate_hexdigest"]=any(r["has_hexdigest"] for r in rows)
print(json.dumps(out,ensure_ascii=False,indent=1))
