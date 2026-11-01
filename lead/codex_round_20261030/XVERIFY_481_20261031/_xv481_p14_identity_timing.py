#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p14：驱动身份取证（三副本 normalize_hold_s 指纹排他）+ pyc 头部源锚 +
   carrier 拷贝 shutil.copy2 语义对 log mtime 的影响 + 进程残留只读复查。"""
import json, io, sys, os, struct, time, glob, hashlib, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CAND = "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate"
print("== 驱动身份排他指纹：hold 参数化（normalize_hold_s）在 3 个 e12 副本的有无 ==")
for f in sorted(glob.glob("lead/qc161_u0400_trip/**/_drive_c2_x_e12.py", recursive=True)):
    txt = open(f, encoding="utf-8", errors="replace").read()
    print(f"  {f}  sha={hashlib.sha256(open(f,'rb').read()).hexdigest()[:8]}  "
          f"normalize_hold_s 出现={txt.count('normalize_hold_s')}  hold_after_window_s 写 rec={('rec[\"e2_params\"][\"hold_after_window_s\"]' in txt)}")

print("\n== pyc 头部（PEP 552）：记录源 mtime/size vs 盘上源 —— 发射时源件是否已为此内容 ==")
for pyc in sorted(glob.glob(CAND + "/__pycache__/*.pyc")):
    head = open(pyc, "rb").read(16)
    magic, flags, mtime, size = struct.unpack("<IIII", head)
    src = os.path.join(os.path.dirname(os.path.dirname(pyc)), os.path.basename(pyc).split(".cpython")[0] + ".py")
    st = os.stat(src) if os.path.isfile(src) else None
    print(f"  {os.path.basename(pyc)}")
    print(f"      flags={flags} ({'hash-based/unchecked' if flags else 'timestamp-based'})  记录源 mtime={mtime} "
          f"({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))})  记录源 size={size}")
    if st:
        print(f"      盘上源 mtime={int(st.st_mtime)} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))}) "
              f"size={st.st_size}  与 pyc 记录一致={int(st.st_mtime) == mtime and st.st_size == size}")
    print(f"      pyc 自身 mtime={time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(pyc)))}"
          f"  （批前 07:1x 生成，早于本批发射 08:33 ⇒ 源件在批发射前未被改写）")

print("\n== carrier 母本 copy2 语义：guard log mtime 早于 close_delivery.t 是否合理 ==")
SRC = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
for name in ("ra2render.ini", "gamemd.exe"):
    p = os.path.join(SRC, name)
    if os.path.isfile(p):
        print(f"  母本 {name}: mtime={time.strftime('%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))}")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    r = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/_rec.json", encoding="utf-8"))
    lg = f"lead/qc161_u0400_trip/c2ab_x/{d}/ra2render_close_last.log"
    mtl = os.path.getmtime(lg)
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    print(f"  {tag}: log mtime={time.strftime('%m-%d %H:%M:%S', time.localtime(mtl))}  "
          f"相对 t0={mtl - t0:+.3f}s（t0={time.strftime('%H:%M:%S', time.localtime(t0))}）"
          f"  closed_at_s={r['closed_at_s']} ⇒ log 早于关窗投递 {round(r['closed_at_s'] - (mtl - t0), 3)}s")
    same = (mtl == os.path.getmtime(f"lead/qc161_u0400_trip/c2ab_x/{d}/ra2render_after_kill.log"))
    print(f"      close_last 与 after_kill 两 log mtime 相同={same} "
          f"sha 相同={hashlib.sha256(open(lg,'rb').read()).hexdigest() == hashlib.sha256(open(f'lead/qc161_u0400_trip/c2ab_x/{d}/ra2render_after_kill.log','rb').read()).hexdigest()}")

print("\n== 进程残留只读复查（GBK 解码，非趟内读数）==")
for img in ("gamemd.exe", "rc4_loader.exe"):
    p = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {img}"], capture_output=True)
    s = p.stdout.decode("gbk", errors="replace")
    hit = [l for l in s.splitlines() if img[:-4].lower() in l.lower()]
    print(f"  {img}: 匹配={len(hit)} {hit[:2] if hit else '(无残留进程)'}")

print("\n== §481 两趟 5 个 shot 时刻与 preflight mtime 的时序链 ==")
pf = os.path.getmtime("lead/codex_round_20261030/LEADER_battle/preflight_batch2_20261031.txt")
print(f"  preflight mtime={time.strftime('%m-%d %H:%M:%S', time.localtime(pf))}")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    r = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/_rec.json", encoding="utf-8"))
    chain = [("preflight", pf), ("wallclock_at_start", r["wallclock_ms_at_start"] / 1000),
             ("launch t0", r["close_delivery"]["t"] - r["closed_at_s"]),
             ("pre_close shot", [s for s in r["shots"] if s["tag"] == "pre_close"][0]["t"]),
             ("close_delivery", r["close_delivery"]["t"]),
             ("hwnd0", None), ("post_close_end shot", [s for s in r["shots"] if s["tag"] == "post_close_end"][0]["t"])]
    rows = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = next(i for i, x in enumerate(rows) if x.get("hwnd") == 0)
    chain[6] = ("hwnd0", rows[hz]["t"])
    chain.sort(key=lambda kv: (kv[1] is None, kv[1]))
    print(f"  {tag}: " + " → ".join(f"{k}@{time.strftime('%H:%M:%S', time.localtime(v)) if v else '?'}" for k, v in chain))
