#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 脚本 s01：② 早窗 3 趟 —— 会话同源性 / sha 复算 / 闩与退出证明 / 值域 / 间隔重算。
只读原始 JSON，不采信执行线总结。写域=lead/codex_round_20261030/XVERIFY_TRIPS_20261030/
"""
import json, hashlib, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "lead", "qc161_u0400_trip", "c2ab_x")
TRIPS = {
    "hold13": "20261030T211741_9001_P3e_E12_T1",
    "hold14": "20261030T212148_9001_P3e_E12_T1",
    "hold15": "20261030T212233_9001_P3e_E12_T1",
}
# 台账/交付件自报 sha 前缀
CLAIM_REC = {"hold13": "7e02d38f", "hold14": "26b6b33b", "hold15": "be90b0ac"}
CLAIM_TL = {"hold13": "0cf92e49", "hold14": "751df9a3", "hold15": "7dfe8bd9"}
CLAIM = {  # 台账 §474 / GOAL2 自报读数
    "hold13": dict(closed_at_s=14.131, latch=True, latch_row_index=77, latch_after_close_s=7.736,
                   exit_after_close_s=9.74, final_exitcode=0, exit_kind="natural"),
    "hold14": dict(closed_at_s=14.997, latch=True, latch_row_index=70, latch_after_close_s=7.032,
                   exit_after_close_s=9.04, final_exitcode=0, exit_kind="natural"),
    "hold15": dict(closed_at_s=16.272, latch=False, close_rows_n=1195, exitstate_domain={0},
                   killed_on_cleanup=[[19512, "rc4_loader.exe"], [61092, "gamemd.exe"]]),
}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def J(tag, name):
    return json.load(open(os.path.join(BASE, TRIPS[tag], name), encoding="utf-8"))

out = {}
print("### (1) sha256 前缀复算 + 同会话 boot 墙钟")
boots = {}
for tag in TRIPS:
    recp = os.path.join(BASE, TRIPS[tag], "_rec.json")
    tlp = os.path.join(BASE, TRIPS[tag], "timeline.json")
    rs, ts = sha(recp)[:8], sha(tlp)[:8]
    rec = J(tag, "_rec.json")
    boots[tag] = rec["boot_wallclock_ms_at_start"]
    print(f"  {tag} {TRIPS[tag]}")
    print(f"    rec_sha8={rs} claim={CLAIM_REC[tag]} -> {'MATCH' if rs==CLAIM_REC[tag] else 'MISMATCH'}")
    print(f"    tl_sha8 ={ts} claim={CLAIM_TL[tag]}  -> {'MATCH' if ts==CLAIM_TL[tag] else 'MISMATCH'}")
    print(f"    rec_full_sha={sha(recp)[:64]}")
    print(f"    tl_full_sha ={sha(tlp)[:64]}")
    print(f"    boot_wallclock_ms_at_start={rec['boot_wallclock_ms_at_start']} boot_ms_at_start={rec['boot_ms_at_start']} wallclock_ms_at_start={rec['wallclock_ms_at_start']}")
vals = sorted(boots.values())
print(f"  boot_wallclock 极差 = {vals[-1]-vals[0]} ms (claim 13) -> {'MATCH' if vals[-1]-vals[0]==13 else 'DIFF'}")
print(f"  boot_reference 一致性: " + json.dumps({t: J(t,'_rec.json').get('boot_reference') for t in TRIPS}, ensure_ascii=False))

print("\n### (2)(3)(6) 逐趟原始重算")
for tag in TRIPS:
    rec, tl = J(tag, "_rec.json"), J(tag, "timeline.json")
    rows = tl["close_rows"]
    print(f"--- {tag}: close_rows={len(rows)} (rec.close_rows_n={rec['close_rows_n']}) "
          f"latch_detected={rec['latch_detected']} idx={rec['latch_row_index']} after={rec['latch_after_close_s']}")
    # exitstate 值域（全行）
    dom, dict_rows, bad = {}, [], []
    for i, r in enumerate(rows):
        v = r.get("exitstate")
        if isinstance(v, dict):
            dict_rows.append((i, v)); dom[f"dict:{v.get('state')}"] = dom.get(f"dict:{v.get('state')}", 0) + 1
        else:
            dom[v] = dom.get(v, 0) + 1
    print(f"    exitstate 值域(自算,含dict态) = {dom}")
    print(f"    exitstate==1 行号 = {[i for i,r in enumerate(rows) if r.get('exitstate')==1][:10]}")
    # wait 值域
    wdom = {}
    for r in rows:
        wdom[r.get("wait")] = wdom.get(r.get("wait"), 0) + 1
    print(f"    wait 值域(自算) = {wdom}")
    # code 值域
    cdom = {}
    for r in rows:
        cdom[repr(r.get("code")) + "/ok=" + str(r.get("code_read_ok"))] = cdom.get(repr(r.get("code")) + "/ok=" + str(r.get("code_read_ok")), 0) + 1
    print(f"    code 值域(自算) = {cdom}")
    # hwnd / singleton 归零时点
    def first_zero(key):
        for i, r in enumerate(rows):
            if r.get(key) == 0:
                return i, r["t"]
        return None, None
    zi, zt = first_zero("hwnd"); si, st = first_zero("singleton")
    print(f"    hwnd 首次=0 行={zi} t={zt}; singleton 首次=0 行={si} t={st}; 末行 hwnd={rows[-1].get('hwnd')} singleton={rows[-1].get('singleton')} frame={rows[-1].get('frame')} tick={rows[-1].get('tick')}")
    print(f"    首行 t={rows[0]['t']} 末行 t={rows[-1]['t']} 观察跨度={round(rows[-1]['t']-rows[0]['t'],3)} s watch_s={rec['watch_s']}")
    # 闩行独立复算
    if rec["latch_detected"]:
        li = rec["latch_row_index"]
        print(f"    闩行 rows[{li}].exitstate={rows[li].get('exitstate')} t={rows[li]['t']} ; 前一行 rows[{li-1}].exitstate={rows[li-1].get('exitstate')}")
        print(f"    自算 latch_after_close = rows[{li}].t - rows[0].t = {round(rows[li]['t']-rows[0]['t'],3)} s (claim {rec['latch_after_close_s']})")
        print(f"    自算 闩→退 = rows[-1].t - rows[{li}].t = {round(rows[-1]['t']-rows[li]['t'],3)} s")
        print(f"    (台账口径 exit_after_close - latch_after_close = {round(rec['exit_after_close_s']-rec['latch_after_close_s'],3)})")
    print(f"    exited={rec['exited']} exit_kind={rec['exit_kind']} exit_after_close_s={rec['exit_after_close_s']} final_exitcode={rec.get('final_exitcode')}")
    print(f"    自算 exit_after_close = rows[-1].t - rows[0].t = {round(rows[-1]['t']-rows[0]['t'],3)} s")
    print(f"    末行 wait={rows[-1]['wait']} (WAIT_OBJECT_0=0) code={rows[-1].get('code')} code_read_ok={rows[-1].get('code_read_ok')}")
    print(f"    killed_on_cleanup = {rec.get('killed_on_cleanup','ABSENT')} ; stop_triggered={rec['stop_triggered']} ; verdict={rec['verdict']}")
    print(f"    a8_verdict={rec.get('a8_verdict')} a8_remaining={rec.get('a8_remaining')} a8_enum_ok={rec.get('a8_enum_ok')} carrier_deleted={rec.get('carrier_deleted')} except_changed={rec.get('except_changed')}")
    print(f"    loader_pid={rec.get('loader_pid')} gamemd_pid={rec.get('gamemd_pid')} hwnd={rec.get('hwnd')} window_tid={rec.get('window_tid')}")
    print(f"    hold_tl_n={rec['hold_tl_n']} hold_tl[0].t={tl['hold_tl'][0]['t']} hold_tl[-1].t={tl['hold_tl'][-1]['t']}")
    print(f"    close_delivery.t={rec['close_delivery']['t']} closed_at_s={rec['closed_at_s']} => t0≈{round(rec['close_delivery']['t']-rec['closed_at_s'],3)}")
    print(f"    e2_fork_label={rec.get('e2_fork_label')} hook6_state={rec.get('hook6_state')} hook6_state_counts={rec.get('hook6_state_counts')}")
    print(f"    ws_delta_kb={rec.get('ws_delta_kb')} cpu_delta_median_s={rec.get('cpu_delta_median_s')} slow_rows_n={rec.get('slow_rows_n')}")
    hd = {}
    for r in tl["hold_tl"]:
        v = r.get("exitstate")
        k = f"dict:{v.get('state')}" if isinstance(v, dict) else v
        hd[k] = hd.get(k, 0) + 1
    print(f"    hold_tl exitstate 值域={hd} hook6值域={set(r.get('hook6') if isinstance(r.get('hook6'),str) else 'dict' for r in tl['hold_tl'])}")
    print(f"    hold_tl ws_kb 序列={[r.get('ws_kb') for r in tl['hold_tl']]}")

print("\n### (4)(5) 边界与绝对时钟重算")
for tag in ("hold13", "hold14", "hold15"):
    rec, tl = J(tag, "_rec.json"), J(tag, "timeline.json")
    rows = tl["close_rows"]
    t0 = rec["close_delivery"]["t"] - rec["closed_at_s"]
    first, last = rows[0]["t"], rows[-1]["t"]
    li = rec["latch_row_index"]
    lab = None if li is None else round(rows[li]["t"] - t0, 3)
    print(f"  {tag}: closed_at(自算 rows[0]-t0)={round(first - t0,3)} 闩绝对时刻={lab} "
          f"观察窗绝对区间=[{round(first-t0,3)}, {round(last-t0,3)}] "
          f"覆盖 21~22s? {'YES' if (first-t0) <= 21.0 and (last-t0) >= 22.0 else 'NO'}")
