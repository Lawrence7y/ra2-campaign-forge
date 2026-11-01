#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p03：~21s 带口径一致性 + 批内产物侧可查项（冻结件 sha / preflight / selftest / 守卫日志全文）。
   针对 §481 的两处表述做集合口径重算，避免把 close 集与归零集混用。
"""
import json, io, sys, os, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
NOLATCH = [("E5h15", "20261030T072353_9001_P3e_E12_T1"), ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
           ("hold15", "20261030T212233_9001_P3e_E12_T1"), ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"),
           ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]

print("== 不闩族 5 点：close / hwnd 归零绝对（rows[0].t 基准）==")
data = []
for tag, d in NOLATCH:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0][0]
    dl = round(rows[hz]["t"] - rows[0]["t"], 3)
    ab = round(r["closed_at_s"] + dl, 3)
    data.append((tag, r["closed_at_s"], dl, ab, r.get("boot_wallclock_ms_at_start")))
    print(f"  {tag:<9} close={r['closed_at_s']:<8} Δ={dl:<7} 归零绝对={ab:<8} boot={r.get('boot_wallclock_ms_at_start')}")

sub4 = [x for x in data if x[1] <= 17.2]
print(f"\n  全 5 点: close 跨度 {min(x[1] for x in data):.3f}~{max(x[1] for x in data):.3f} "
      f"= {round(max(x[1] for x in data) - min(x[1] for x in data), 3)}s ; "
      f"归零跨度 {min(x[3] for x in data):.3f}~{max(x[3] for x in data):.3f} "
      f"= {round(max(x[3] for x in data) - min(x[3] for x in data), 3)}s")
print(f"  同集合口径（close≤17.2 的 {len(sub4)} 点）: close 跨度 "
      f"{min(x[1] for x in sub4):.3f}~{max(x[1] for x in sub4):.3f} = "
      f"{round(max(x[1] for x in sub4) - min(x[1] for x in sub4), 3)}s ; 归零跨度 "
      f"{min(x[3] for x in sub4):.3f}~{max(x[3] for x in sub4):.3f} = "
      f"{round(max(x[3] for x in sub4) - min(x[3] for x in sub4), 3)}s")
print(f"  §481 原句核对：『close 分布 16.09~17.17（跨 1.1s）』对应哪几趟? "
      + str([(t, c) for t, c, _d, _a, _b in data if 16.0 <= c <= 17.2]))
print(f"  『归零聚在 ~1.1s 窄带』的 1.1s 数值来源: 全 5 点归零跨度 "
      f"{round(max(x[3] for x in data) - min(x[3] for x in data), 3)}s（含 E5h20=21.651，其 close=21.249 不在 16.09~17.17 内）")
sess = sorted({x[4] for x in data if x[4]})
print(f"  不闩族可证会话数 = {len(sess)} {sess}（均非 None ⇒ 字段可证，跨 3 会话成立）")

print("\n== Δ 与「排队到 ~21.3s 边界」模型的一致性（Δ ≈ 21.3 − close？）==")
for tag, d in NOLATCH:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0][0]
    dl = round(rows[hz]["t"] - rows[0]["t"], 3)
    ab = round(r["closed_at_s"] + dl, 3)
    print(f"  {tag:<9} close={r['closed_at_s']:<8} Δ={dl:<7} 归零绝对={ab:<8}  (21.3−close={round(21.3 - r['closed_at_s'], 3)})")

print("\n== timeline 其余键（hold_tl / _e2）与本批主张 ==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    tl = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))
    ht = tl.get("hold_tl"); e2 = tl.get("_e2")
    print(f"  {tag}: hold_tl type={type(ht).__name__} len={len(ht) if hasattr(ht,'__len__') else '-'}  _e2={json.dumps(e2)[:300]}")
    if isinstance(ht, list) and ht:
        print(f"      hold_tl[0]={json.dumps(ht[0])[:220]}")
        print(f"      hold_tl[-1]={json.dumps(ht[-1])[:220]}")
        hv = sorted({x.get('hwnd') for x in ht if isinstance(x, dict)})
        print(f"      hold_tl hwnd 值域={hv}  （早窗内 hwnd 应恒非 0 → 关窗前窗口在）")

print("\n== 守卫日志全文（bail / 钩子计数）==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    for lg in ("ra2render_close_last.log", "ra2render_after_kill.log"):
        p = f"{CB}/{d}/{lg}"
        txt = open(p, encoding="utf-8", errors="replace").read()
        lines = txt.splitlines()
        print(f"  {tag} {lg} 行数={len(lines)}")
        for ln in lines:
            if any(k in ln for k in ("EnableRC4", "8/8", "bail", "Bail", "hook", "Hook", "Install", "安装")):
                print(f"      | {ln.strip()}")
        same = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        print(f"      sha256={same[:16]}…")

print("\n== 冻结件盘上 sha 复验（§474/§481 主张零字节）==")
FROZEN = {"_drive_c2_x_earlyclose.py": "2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1",
          "_drive_c2_x_probe_v2.py": "6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9"}
for name, want in FROZEN.items():
    hits = glob.glob(f"lead/**/{name}", recursive=True)
    print(f"  {name}: 盘上找到 {len(hits)} 份")
    for h in hits:
        got = hashlib.sha256(open(h, "rb").read()).hexdigest()
        print(f"      {h}  sha={got[:16]}…  match_at_import={got == want}")

print("\n== 批产物 preflight / selftest 留档（§481 主张 Y-3 整改完成）==")
for pat in ("lead/codex_round_20261030/LEADER_battle/*batch2*", "lead/codex_round_20261030/LEADER_battle/*20261031*"):
    for f in glob.glob(pat):
        print(f"  {f}  bytes={os.path.getsize(f)}  mtime={int(os.path.getmtime(f))}")
        txt = open(f, encoding="utf-8", errors="replace").read()
        print("      tail: " + " | ".join(txt.strip().splitlines()[-4:])[:400])
