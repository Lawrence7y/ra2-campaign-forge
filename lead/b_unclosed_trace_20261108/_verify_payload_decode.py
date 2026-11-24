# -*- coding: utf-8 -*-
"""_verify_payload_decode.py — 独立解码两个命中 mjs 的 payload 单行 JSON 转义串，
打印可读全文（按行编号），并统计文件内是否含任何 agent 回答段（如 __host.report / agent( / submit_result）。
只读。
"""
import json, re, os, hashlib

RUNS = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"
FILES = [
    "dwfrun-a05ccb49-e10b-4004-8ce6-5f5b48d7820e.mjs",
    "dwfrun-a7c7b5f9-25d5-400a-bd45-6f32a262430b.mjs",
    "dwfrun-1a53f51e-3623-435c-8253-ff4aa9060d52.mjs",
    "dwfrun-4e7afb77-d61e-42ff-b669-b7cb6321a25b.mjs",
    "dwfrun-1c93b364-e57c-405d-a271-66cd59e4b850.mjs",
]

for fn in FILES:
    p = os.path.join(RUNS, fn)
    raw = open(p, "rb").read()
    t = raw.decode("utf-8")
    print("=" * 90)
    print(f"FILE {fn} bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()} lines={t.count(chr(10))+1}")
    st = os.stat(p)
    import datetime
    print("mtime =", datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat())
    # find DIR/DOC markers
    for k in ["DIR=", "DOC=", "lead/", "B_BREAKPOINT", "B_BREAKPOINTS", "R2_BREAKPOINTS_CLOSURE", "日志追溯员", "追溯复核员"]:
        c = t.count(k)
        if c:
            print(f"  marker {k!r} count={c}")
    # structural markers
    for k in ["__host.report", "submit_result", "agent(", "worldRead", "enterPhase", "report(", "await __host"]:
        c = t.count(k)
        if c:
            print(f"  struct {k!r} count={c}")
    # Print line 9 decoded payload if it is a JSON string literal
    lines = t.split("\n")
    if len(lines) >= 9:
        L9 = lines[8]
        print(f"  line9_len={len(L9)}")
        m = re.search(r'=\s*("(?:[^"\\]|\\.)*")\s*;', L9)
        # try JSON.loads on the first big string on line 9
        cand = None
        for mm in re.finditer(r'"((?:[^"\\]|\\.)*)"', L9):
            s = mm.group(1)
            if len(s) > 500:
                cand = s
                break
        if cand:
            try:
                dec = json.loads('"' + cand + '"')
                print("  --- decoded payload (lines) ---")
                for j, ln in enumerate(dec.split("\n"), 1):
                    print(f"  P{j:03d}| {ln}")
            except Exception as e:
                print("  JSON decode failed:", e)
        else:
            print("  no long JSON string found on line 9; line9 head:", L9[:400])
    else:
        print("  fewer than 9 lines")
