# D-16 本轮审计记录（2026-11-05）

本记录只记本次裁决实际读、实际跑及其限度。唯一文档产物是本文件与同目录 `RULING_D16.md`。没有启动 gamemd.exe / ra2loader.exe / YURI，没有 taskkill、活进程内存读取、采样/注入/Hook/栈采集代码，没有 git add / commit。所有 Python 都是 `python -I -X utf8 -c` 内联离线读盘，路径绝对；未执行现成发射器、harness 或其他核验脚本。

## 1. 读取范围与证据层级

已用 Read 读：

- `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md`：本轮实际行 1–243，含 D-16 原版、55 行起订正块、D-15 全文。
- `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md`：4470–5068，覆盖 §545–§549 全文。
- `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md` 全文，尤其 §3 的 11 条表。
- `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md` 全文；D15_IMPLEMENTATION_CANDIDATE.md 的 1–285、290–829；D13_MECHANISM_GAP_AND_OFFLINE_CARD.md 全文。
- `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/T42E4_FORENSIC_085458ab/SUMMARY.md`、`02_verify.md` 全文。
- `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_scorecensus.py`、`_leader_scorecensus_out.txt` 全文。仅阅读公式，未导入/执行该脚本。

Read 亲自目视的完整文件列表如下，根 D=`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`：

| 相对 D 的实际路径 | 本轮看到的内容 |
|---|---|
| archive_T33/measure_w2_end_x.png | 主菜单立绘，无计分表 |
| archive_T42/measure_w1_end_x.png | 同上 |
| archive_T42/measure_w2_end_x.png | 同上 |
| archive_T45/measure_w2_end_x.png | 同上 |
| l1_20261023e4/measure_w2_end_x.png | ZCode 桌面客户端与 BuddySwitch 弹窗 |
| archive_T33/measure_w1_end_x.png | 计分表，00:00:24 |
| archive_T45/measure_w1_end_x.png | 计分表，00:00:28 |
| archive_T34/measure_w1_end_x.png | 计分表，00:00:10；不支持“两图双方四项全零”的概括 |
| archive_T41/measure_w1_end_x.png | 计分表，00:00:28；上行失败数可见非零 5 |
| archive_T35/frame_target_01.png | 计分表，旧“战斗帧”对照标签不能照收 |
| l3_1101v3a/frame_target_01.png | 加载简报，非计分表 |

**9 张末图+2 张对照**，没有 OCR，没有全量 25/27 张目视验收。P 的全量像素计算不能充当全量语义目视。GLM V:114–126 对其余末图内容的判读属他方核验，本轮未全部重做；其 V:181 标题“13 张”与后表范围不一致，V:206 又明记 T36/w1 未单独打开，故不把“全 25 文件逐张打开”记作已验收。

## 2. K：指定 a–e 的实际命令（退出码 0）

以下代码原样经 Bash 执行，无文件写入：

```bash
python -I -X utf8 -c '
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
group = ["archive_T33/measure_w2_end_x.png", "archive_T42/measure_w1_end_x.png", "archive_T42/measure_w2_end_x.png", "archive_T45/measure_w2_end_x.png"]
hashes = []
for rel in group:
    h = sha(root / rel)
    hashes.append(h)
    print("a", rel, h)
print("a all_four_equal =", len(set(hashes)) == 1)
for rel in ["archive_T33/measure_w1_end_x.png", "archive_T45/measure_w1_end_x.png"]:
    h = sha(root / rel)
    print("b", rel, h, "different_from_group =", h != hashes[0])
local = timezone(timedelta(hours=8))
cut = datetime(2026, 10, 18, 16, 10, 15, tzinfo=local).timestamp()
t42 = root / "archive_T42"
files = sorted(p for p in t42.rglob("*") if p.is_file())
old = [p for p in files if p.stat().st_mtime < cut]
print("c", json.dumps({"timezone": "+08:00", "cutoff": "2026-10-18T16:10:15+08:00", "recursive_files": len(files), "immediate_files": len([p for p in t42.iterdir() if p.is_file()]), "old_files": len(old)}, ensure_ascii=False))
for p in old:
    print("c old", p.relative_to(t42).as_posix(), datetime.fromtimestamp(p.stat().st_mtime, local).isoformat(timespec="microseconds"))
p = root / "archive_T34/measure_w0.json"
d = json.loads(p.read_text(encoding="utf-8-sig"))
c = d["counters"]
s = d["stats"]
print("d", json.dumps({"path": p.as_posix(), "gate.units0": d["gate"]["units0"], "counters[0].b": c[0]["b"], "counter_count": len(c), "distinct_b": sorted({x["b"] for x in c}), "stats.fps_avg": s["fps_avg"], "stats.fps_p50": s["fps_p50"], "stats.logic_frames": s["logic_frames"], "stats.max_stall_s": s["max_stall_s"]}, ensure_ascii=False))
dirs = sorted(p for p in root.rglob("archive_T*") if p.is_dir())
zeros = []
missing = []
for directory in dirs:
    p = directory / "measure_w0.json"
    if not p.is_file():
        missing.append(p.as_posix())
        print("e", directory.relative_to(root).as_posix(), "缺 measure_w0.json")
        continue
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    c = d.get("counters") or []
    b = c[0].get("b", "缺") if c else "缺"
    if b == 0:
        zeros.append(directory.relative_to(root).as_posix())
    if b == "缺":
        missing.append(p.as_posix())
    print("e", json.dumps({"trip": directory.relative_to(root).as_posix(), "gate.units0": (d.get("gate") or {}).get("units0", "缺"), "counters[0].b": b, "distinct_b": sorted({x["b"] for x in c if "b" in x})}, ensure_ascii=False))
print("e", json.dumps({"archive_directories": len(dirs), "zero_first_b": zeros, "missing": missing}, ensure_ascii=False))
'
```

实际 stdout 的 a–d 和 14 份可核 w0 行如下（原样摘录；23 个缺件行在下一块完整列出，末尾冗长的 missing 绝对路径数组不重复粘贴）：

```text
a archive_T33/measure_w2_end_x.png f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b
a archive_T42/measure_w1_end_x.png f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b
a archive_T42/measure_w2_end_x.png f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b
a archive_T45/measure_w2_end_x.png f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b
a all_four_equal = True
b archive_T33/measure_w1_end_x.png fd1378bba8731002f288b2c6c494402585c748ff2ee896f54c079d30222c65ff different_from_group = True
b archive_T45/measure_w1_end_x.png bc34f315e1f8e9f5baf3674c39d286462a46897fbbc269bf6d90394e737230b9 different_from_group = True
c {"timezone": "+08:00", "cutoff": "2026-10-18T16:10:15+08:00", "recursive_files": 61, "immediate_files": 61, "old_files": 30}
c old navsig_burst_01_g.png 2026-10-18T12:17:37.854703+08:00
c old navsig_burst_01_x.png 2026-10-18T12:56:58.759924+08:00
c old navsig_burst_02_x.png 2026-10-18T12:57:03.960033+08:00
c old navsig_burst_03_x.png 2026-10-18T12:57:09.164301+08:00
c old navsig_burst_04_x.png 2026-10-18T12:57:14.329113+08:00
c old navsig_nav_menu_post_00_g.png 2026-10-18T16:07:33.530068+08:00
c old navsig_nav_menu_pre_12_g.png 2026-10-18T12:56:41.081060+08:00
c old navsig_nav_setup_post_00_g.png 2026-10-18T16:07:37.317520+08:00
c old navsig_nav_setup_post_02_g.png 2026-10-18T11:45:02.604527+08:00
c old navsig_nav_setup_post_03_g.png 2026-10-18T09:12:19.481105+08:00
c old navsig_nav_setup_post_04_x.png 2026-10-18T08:28:27.808015+08:00
c old navsig_nav_setup_post_05_x.png 2026-10-18T08:28:28.898591+08:00
c old navsig_nav_setup_post_06_x.png 2026-10-18T08:28:29.990744+08:00
c old navsig_nav_setup_post_07_x.png 2026-10-18T08:28:31.082418+08:00
c old navsig_nav_setup_post_08_x.png 2026-10-18T08:28:32.172212+08:00
c old navsig_nav_setup_post_09_x.png 2026-10-18T08:28:33.263141+08:00
c old navsig_nav_setup_post_10_x.png 2026-10-18T08:28:34.347568+08:00
c old navsig_nav_setup_post_11_x.png 2026-10-18T08:28:35.430823+08:00
c old navsig_nav_setup_post_12_x.png 2026-10-18T08:28:36.539846+08:00
c old navsig_nav_setup_post_13_x.png 2026-10-18T08:28:37.668809+08:00
c old navsig_nav_setup_post_14_x.png 2026-10-18T08:28:38.772294+08:00
c old navsig_nav_setup_post_15_x.png 2026-10-18T08:28:39.886905+08:00
c old navsig_nav_setup_post_16_x.png 2026-10-18T08:28:40.978109+08:00
c old navsig_nav_setup_post_17_x.png 2026-10-18T08:28:42.072793+08:00
c old navsig_nav_setup_post_18_x.png 2026-10-18T08:28:43.158138+08:00
c old navsig_nav_setup_post_19_x.png 2026-10-18T08:28:44.247950+08:00
c old navsig_nav_setup_post_20_x.png 2026-10-18T08:28:45.333898+08:00
c old navsig_nav_start_pre_00_g.png 2026-10-18T16:07:48.170201+08:00
c old navsig_nav_start_pre_02_g.png 2026-10-18T11:45:05.067316+08:00
c old navsig_nav_start_pre_03_g.png 2026-10-18T06:11:16.084261+08:00
d {"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json", "gate.units0": 242, "counters[0].b": 41, "counter_count": 25, "distinct_b": [41], "stats.fps_avg": 0.36000229681454066, "stats.fps_p50": 31.608659530882008, "stats.logic_frames": 9, "stats.max_stall_s": 24.734761}
e {"trip": "archive_T32", "gate.units0": 241, "counters[0].b": 43, "distinct_b": [43, 44, 45]}
e {"trip": "archive_T33", "gate.units0": 241, "counters[0].b": 43, "distinct_b": [43, 44, 45]}
e {"trip": "archive_T34", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41]}
e {"trip": "archive_T36", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41]}
e {"trip": "archive_T38", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43, 44]}
e {"trip": "archive_T39", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43, 44]}
e {"trip": "archive_T40", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43]}
e {"trip": "archive_T41", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43]}
e {"trip": "archive_T42", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43]}
e {"trip": "archive_T43", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41]}
e {"trip": "archive_T44", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43]}
e {"trip": "archive_T45", "gate.units0": 242, "counters[0].b": 41, "distinct_b": [41, 42, 43]}
e {"trip": "archive_T47", "gate.units0": 251, "counters[0].b": 41, "distinct_b": [41]}
e {"trip": "archive_T49_u0800", "gate.units0": 491, "counters[0].b": 0, "distinct_b": [0, 1, 2]}
```

K 中实际输出的 23 个缺件行（顺序如原输出，移到一块便于查阅）：

```text
e archive_T10 缺 measure_w0.json
e archive_T11 缺 measure_w0.json
e archive_T12 缺 measure_w0.json
e archive_T13 缺 measure_w0.json
e archive_T14 缺 measure_w0.json
e archive_T15_ABORTED 缺 measure_w0.json
e archive_T15B 缺 measure_w0.json
e archive_T16 缺 measure_w0.json
e archive_T17 缺 measure_w0.json
e archive_T18 缺 measure_w0.json
e archive_T19 缺 measure_w0.json
e archive_T20 缺 measure_w0.json
e archive_T21 缺 measure_w0.json
e archive_T22 缺 measure_w0.json
e archive_T23 缺 measure_w0.json
e archive_T31 缺 measure_w0.json
e archive_T35 缺 measure_w0.json
e archive_T37 缺 measure_w0.json
e archive_T5 缺 measure_w0.json
e archive_T6 缺 measure_w0.json
e archive_T7 缺 measure_w0.json
e archive_T8 缺 measure_w0.json
e archive_T9 缺 measure_w0.json
```

K 最后一行实际 JSON 的 `archive_directories=37`、`zero_first_b=["archive_T49_u0800"]`，missing 数组为上述 23 个目录下的绝对 `measure_w0.json` 路径。可核文件是 14 份，缺的 23 份没有补造。这一范围限制已进入裁决事实表和动作验收。

## 3. S：全 104 JSON、集合归属与采集字段（退出码 0）

实际命令：

```bash
python -I -X utf8 -c '
from pathlib import Path
from collections import Counter
import json, hashlib
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
files = sorted(root.rglob("measure_w*.json"))
levels = Counter()
positive = []
zero = []
insufficient = []
negative = []
for p in files:
    levels[len(p.relative_to(root).parts) - 1] += 1
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    sample = d.get("samples") or {}
    f, t = sample.get("f") or [], sample.get("t") or []
    row = (p, d)
    if len(f) < 2 or len(f) != len(t):
        insufficient.append(row)
    elif f[-1] > f[0]:
        positive.append(row)
    elif f[-1] == f[0]:
        zero.append(row)
    else:
        negative.append(row)
p25 = [(p, d) for p, d in positive if d.get("span_s") == 25.0]
p4 = [(p, d) for p, d in positive if d.get("span_s") == 4.0]
control = [(p, d) for p, d in p25 if d["stats"]["fps_avg"] >= 28]
low = [(p, d) for p, d in p25 if d["stats"]["fps_avg"] < 28]
steady = [(p, d) for p, d in low if d["stats"]["fps_p50"] < 28]
stopped = [(p, d) for p, d in low if d["stats"]["fps_p50"] >= 28]
trip_s = {d["trip_id"] for p, d in steady}
trip_b = {d["trip_id"] for p, d in stopped}
live_low = 0
for p, d in steady:
    e = d["frame_edges"]
    live = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1])
    live_low += live < 28
stalls = [d["stats"]["max_stall_s"] for p, d in steady]
print("S census", json.dumps({"all": len(files), "levels": dict(sorted(levels.items())), "positive": len(positive), "positive25": len(p25), "positive4": len(p4), "control25": len(control), "low25": len(low), "steady25": len(steady), "steady_trips": len(trip_s), "steady_live_lt28": live_low, "stopped25": len(stopped), "stopped_trips": len(trip_b), "trip_overlap": len(trip_s & trip_b), "insufficient": len(insufficient), "negative": len(negative), "zero": len(zero), "zero_nonzero_first": sum(d["samples"]["f"][0] != 0 for p, d in zero), "steady_stall_min": min(stalls), "steady_stall_max": max(stalls), "steady_stall_ge1": sum(x >= 1 for x in stalls)}, ensure_ascii=False))
for p, d in stopped:
    print("S stopped", p.relative_to(root).as_posix(), "df =", d["samples"]["f"][-1] - d["samples"]["f"][0])
print("S f0_zero", [p.relative_to(root).as_posix() for p, d in zero if d["samples"]["f"][0] == 0])
for rel in ["archive_T42/measure_w1.json", "archive_T42/measure_w2.json", "l1_20261023e4/measure_w1.json", "l1_20261023e4/measure_w2.json"]:
    p = root / rel
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    f, t = d["samples"]["f"], d["samples"]["t"]
    print("S detail", json.dumps({"file": rel, "samples": len(f), "first": f[0], "last": f[-1], "distinct_f": sorted(set(f)), "sample_span": t[-1] - t[0], "nominal_span": d.get("span_s"), "error": d.get("error"), "logic_frames": d["stats"].get("logic_frames"), "zero32_member": any(p == q and e["samples"]["f"][0] != 0 for q, e in zero), "stopped11_member": any(p == q for q, e in stopped)}, ensure_ascii=False))
for trip in ["archive_T33", "archive_T42", "archive_T45", "l1_20261023e4"]:
    rows = json.loads((root / trip / "qc151_fields.json").read_text(encoding="utf-8-sig"))
    for index, row in enumerate(rows):
        name = row.get("name", row.get("key", ""))
        if "forensics" in str(row.get("field", name)) or "forensics" in str(name):
            value = row.get("value")
            if isinstance(value, dict):
                keep = {k: value.get(k, "缺") for k in ["game_hwnd", "game_title", "fg_hwnd", "fg_title", "focus_ok", "current_frame", "empty_window", "forensics_png", "capture_ok"]}
                print("S capture", json.dumps({"trip": trip, "index": index, "name": name, "field": row.get("field"), "ts": row.get("ts"), "value": keep}, ensure_ascii=False))
print("S images", json.dumps({"end_pngs_recursive": len(list(root.rglob("measure_w*_end_x.png"))), "root_end_pngs": len(list(root.glob("measure_w*_end_x.png")))}, ensure_ascii=False))
'
```

实际 stdout 摘录（未粘贴 e4/w1 的 113 值 distinct 长数组及全部 12 条采集记录；未省略影响本次集合裁定的值）：

```text
S census {"all": 104, "levels": {"0": 3, "1": 101}, "positive": 63, "positive25": 58, "positive4": 5, "control25": 25, "low25": 33, "steady25": 22, "steady_trips": 8, "steady_live_lt28": 22, "stopped25": 11, "stopped_trips": 11, "trip_overlap": 0, "insufficient": 5, "negative": 1, "zero": 35, "zero_nonzero_first": 32, "steady_stall_min": 0.103742, "steady_stall_max": 0.749879, "steady_stall_ge1": 0}
S stopped archive_T32/measure_w0.json df = 482
S stopped archive_T33/measure_w0.json df = 444
S stopped archive_T34/measure_w0.json df = 9
S stopped archive_T36/measure_w0.json df = 178
S stopped archive_T38/measure_w1.json df = 29
S stopped archive_T39/measure_w1.json df = 32
S stopped archive_T43/measure_w0.json df = 182
S stopped archive_T47/measure_w0.json df = 575
S stopped archive_T49_u0800/measure_w0.json df = 317
S stopped l3_20261023q/measure_w2.json df = 120
S stopped l3_20261023r/measure_w1.json df = 484
S f0_zero ['l1_20261023e4/measure_w2.json', 'l3_1101v4f/measure_w0.json', 'l3_1101v4g/measure_w0.json']
S detail {"file": "archive_T42/measure_w1.json", "samples": 12501, "first": 883, "last": 883, "distinct_f": [883], "sample_span": 24.997712000011234, "nominal_span": 25.0, "error": null, "logic_frames": 0, "zero32_member": true, "stopped11_member": false}
S detail {"file": "archive_T42/measure_w2.json", "samples": 12501, "first": 883, "last": 883, "distinct_f": [883], "sample_span": 24.999480999977095, "nominal_span": 25.0, "error": null, "logic_frames": 0, "zero32_member": true, "stopped11_member": false}
S detail {"file": "l1_20261023e4/measure_w2.json", "samples": 5949, "first": 0, "last": 0, "distinct_f": [0], "sample_span": 11.894575000002078, "nominal_span": 25.0, "error": "ReadProcessMemory 失败 6190 次（有效样本 5949）", "logic_frames": 0, "zero32_member": false, "stopped11_member": false}
S capture {"trip": "archive_T42", "index": 170, "name": "measure_forensics_w1", "field": null, "ts": "2026-10-18T16:12:05+08:00", "value": {"game_hwnd": 9177688, "game_title": "Yuri's Revenge", "fg_hwnd": 9177688, "fg_title": "Yuri's Revenge", "focus_ok": true, "current_frame": 883, "empty_window": true, "forensics_png": "measure_w1_end_x.png", "capture_ok": true}}
S capture {"trip": "archive_T42", "index": 174, "name": "measure_forensics_w2", "field": null, "ts": "2026-10-18T16:12:30+08:00", "value": {"game_hwnd": 9177688, "game_title": "Yuri's Revenge", "fg_hwnd": 9177688, "fg_title": "Yuri's Revenge", "focus_ok": true, "current_frame": 883, "empty_window": true, "forensics_png": "measure_w2_end_x.png", "capture_ok": true}}
S capture {"trip": "l1_20261023e4", "index": 382, "name": "measure_forensics_w2", "field": null, "ts": "2026-10-26T20:00:48+08:00", "value": {"game_hwnd": 662272, "game_title": "", "fg_hwnd": 198964, "fg_title": "BuddySwitch 整合预览版", "focus_ok": false, "current_frame": null, "empty_window": true, "forensics_png": "measure_w2_end_x.png", "capture_ok": true}}
S images {"end_pngs_recursive": 27, "root_end_pngs": 2}
```

另两条实际 S capture 的关键值（此段是字段摘要，不伪装原始 stdout）：T33/w2 idx=160、ts=2026-10-18T11:46:35+08:00、hwnd=16582032、frame=738、focus/capture=true；T45/w2 idx=443、ts=2026-10-18T17:48:34+08:00、hwnd=21695114、frame=845、focus/capture=true。e4/w1 的实际 S detail 为首帧 3557、末帧 0、logic_frames=-3557、12501 样点、span=24.998100000000704、两个集合 member 均 false。没有把负推进当零推进。

## 4. P：27 张末图颜色比例，随后附加对照检查失败（整条退出码 1）

下面是**实际执行但未整体通过**的命令。全部 27 末图的循环和计数已完成；进入额外 frame_target 对照时在 archive_T12 的不可解码文件报错，后面的时间戳部分未执行，后由 P2 补查。不得把 P 整体标 PASS。

```bash
python -I -X utf8 -c '
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image
import json, hashlib
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
def panel(p):
    with Image.open(p) as im:
        pixels = list(im.convert("RGB").crop((85, 108, 630, 275)).getdata())
    hit = sum(1 for r, g, b in pixels if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150)
    return hit, len(pixels), hit / len(pixels)
images = sorted(root.rglob("measure_w*_end_x.png"))
counts = {"all": len(images), "root": 0, "child": 0, "high_p": 0, "high_p_root": 0, "high_p_child": 0, "high_p_and_f0_nonzero_df0": 0}
for p in images:
    hit, n, value = panel(p)
    layer = "root" if p.parent == root else "child"
    counts[layer] += 1
    if value >= .30:
        counts["high_p"] += 1
        counts["high_p_" + layer] += 1
        d = json.loads(p.with_name(p.name.replace("_end_x.png", ".json")).read_text(encoding="utf-8-sig"))
        f = d["samples"]["f"]
        counts["high_p_and_f0_nonzero_df0"] += bool(f and f[0] != 0 and f[-1] == f[0])
    print("P end", p.relative_to(root).as_posix(), "hits =", hit, "pixels =", n, "p =", repr(value))
print("P count", json.dumps(counts, ensure_ascii=False))
controls = [(panel(p)[2], p) for p in root.glob("*/frame_target_01.png")]
print("P frame_target_count =", len(controls))
for value, p in sorted(controls, key=lambda x: x[0], reverse=True)[:5]:
    print("P highest_frame_target", p.relative_to(root).as_posix(), repr(value))
local = timezone(timedelta(hours=8))
for rel in ["archive_T33/measure_w2_end_x.png", "archive_T42/measure_w1_end_x.png", "archive_T42/measure_w2_end_x.png", "archive_T45/measure_w2_end_x.png"]:
    p = root / rel
    q = p.with_name(p.name.replace("_end_x.png", ".json"))
    d = json.loads(q.read_text(encoding="utf-8-sig"))
    print("P time", json.dumps({"file": rel, "mtime": datetime.fromtimestamp(p.stat().st_mtime, local).isoformat(timespec="microseconds"), "png_minus_json_mtime_ms": 1000 * (p.stat().st_mtime - q.stat().st_mtime), "png_minus_nominal_window_end_s": p.stat().st_mtime - (d["t_abs0"] + d["span_s"])}, ensure_ascii=False))
for rel in ["archive_T42/_launch_result.json", "archive_T42/T42_console.log"]:
    p = root / rel
    print("P file", rel, "exists =", p.exists(), "size =", p.stat().st_size if p.is_file() else "缺")
d = json.loads((root / "l1_20261023e4/_launch_result.json").read_text(encoding="utf-8-sig"))
print("P e4_launch", json.dumps({k: d.get(k, "缺") for k in ["rc", "duration_s", "leftover_procs"]}, ensure_ascii=False))
d = json.loads((root / "l1_20261023e4/measure_w2.json").read_text(encoding="utf-8-sig"))
t = d["samples"]["t"]
print("P e4_window_missing_tail_s =", d["span_s"] - (t[-1] - t[0]))
'
```

实际已完成的 27 张输出：

```text
P end archive_T33/measure_w1_end_x.png hits = 31753 pixels = 91015 p = 0.34887655880898755
P end archive_T33/measure_w2_end_x.png hits = 3619 pixels = 91015 p = 0.03976267648189859
P end archive_T34/measure_w1_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T34/measure_w2_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T36/measure_w1_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T36/measure_w2_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T38/measure_w1_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T38/measure_w2_end_x.png hits = 31747 pixels = 91015 p = 0.3488106356095149
P end archive_T39/measure_w2_end_x.png hits = 31748 pixels = 91015 p = 0.348821622809427
P end archive_T40/measure_w1_end_x.png hits = 31746 pixels = 91015 p = 0.3487996484096028
P end archive_T40/measure_w2_end_x.png hits = 31746 pixels = 91015 p = 0.3487996484096028
P end archive_T41/measure_w1_end_x.png hits = 31984 pixels = 91015 p = 0.3514146019886832
P end archive_T41/measure_w2_end_x.png hits = 31984 pixels = 91015 p = 0.3514146019886832
P end archive_T42/measure_w1_end_x.png hits = 3619 pixels = 91015 p = 0.03976267648189859
P end archive_T42/measure_w2_end_x.png hits = 3619 pixels = 91015 p = 0.03976267648189859
P end archive_T43/measure_w1_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T43/measure_w2_end_x.png hits = 31756 pixels = 91015 p = 0.34890952040872386
P end archive_T44/measure_w1_end_x.png hits = 31746 pixels = 91015 p = 0.3487996484096028
P end archive_T44/measure_w2_end_x.png hits = 31746 pixels = 91015 p = 0.3487996484096028
P end archive_T45/measure_w1_end_x.png hits = 31753 pixels = 91015 p = 0.34887655880898755
P end archive_T45/measure_w2_end_x.png hits = 3619 pixels = 91015 p = 0.03976267648189859
P end archive_T49_u0800/measure_w1_end_x.png hits = 31732 pixels = 91015 p = 0.3486458276108334
P end archive_T49_u0800/measure_w2_end_x.png hits = 31732 pixels = 91015 p = 0.3486458276108334
P end l1_20261023e4/measure_w2_end_x.png hits = 251 pixels = 91015 p = 0.0027577871779377026
P end l3_20261023r/measure_w2_end_x.png hits = 31613 pixels = 91015 p = 0.3473383508212932
P end measure_w1_end_x.png hits = 31683 pixels = 91015 p = 0.3481074548151404
P end measure_w2_end_x.png hits = 31683 pixels = 91015 p = 0.3481074548151404
P count {"all": 27, "root": 2, "child": 25, "high_p": 22, "high_p_root": 2, "high_p_child": 20, "high_p_and_f0_nonzero_df0": 21}
```

实际 stderr：

```text
<string>:9: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
Traceback (most recent call last):
  File "<string>", line 26, in <module>
  File "<string>", line 8, in panel
  File "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\Lib\site-packages\PIL\Image.py", line 3711, in open
    raise UnidentifiedImageError(msg)
PIL.UnidentifiedImageError: cannot identify image file 'D:\\Project\\ra2-campaign-forge\\out\\re_work\\work_chain\\CONTINUE_20261003\\lead\\qc161_u0400_trip\\archive_T12\\frame_target_01.png'
```

这里计算的是颜色比值与数值阈值命中，不是重新训练或验证语义分类器；22/27 的完整图像身份还参考 V 的逐窗表，不能混称本轮已全量目视。

## 5. P2：补查坏对照文件与时间/缺件（退出码 0）

因 P 失败而作的有边界补查，未修改坏文件，没有开启 Pillow 截断容忍来伪造成功解码。实际命令：

```bash
python -I -X utf8 -c '
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, UnidentifiedImageError
import json
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
def panel(p):
    with Image.open(p) as im:
        pixels = list(im.convert("RGB").crop((85, 108, 630, 275)).getdata())
    return sum(1 for r, g, b in pixels if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150) / len(pixels)
controls = []
failed = []
paths = sorted(root.glob("*/frame_target_01.png"))
for p in paths:
    try:
        controls.append((panel(p), p))
    except (OSError, UnidentifiedImageError) as error:
        failed.append(p.relative_to(root).as_posix())
        print("P2 unreadable", p.relative_to(root).as_posix(), "size =", p.stat().st_size, "error =", type(error).__name__)
print("P2 frame_target", json.dumps({"found": len(paths), "decoded": len(controls), "unreadable": len(failed)}, ensure_ascii=False))
for value, p in sorted(controls, key=lambda x: x[0], reverse=True)[:5]:
    print("P2 highest_frame_target", p.relative_to(root).as_posix(), repr(value))
local = timezone(timedelta(hours=8))
for rel in ["archive_T33/measure_w2_end_x.png", "archive_T42/measure_w1_end_x.png", "archive_T42/measure_w2_end_x.png", "archive_T45/measure_w2_end_x.png"]:
    p = root / rel
    q = p.with_name(p.name.replace("_end_x.png", ".json"))
    d = json.loads(q.read_text(encoding="utf-8-sig"))
    print("P2 time", json.dumps({"file": rel, "mtime": datetime.fromtimestamp(p.stat().st_mtime, local).isoformat(timespec="microseconds"), "png_minus_json_mtime_ms": 1000 * (p.stat().st_mtime - q.stat().st_mtime), "png_minus_nominal_window_end_s": p.stat().st_mtime - (d["t_abs0"] + d["span_s"])}, ensure_ascii=False))
for rel in ["archive_T42/_launch_result.json", "archive_T42/T42_console.log"]:
    p = root / rel
    print("P2 file", rel, "exists =", p.exists(), "size =", p.stat().st_size if p.is_file() else "缺")
d = json.loads((root / "l1_20261023e4/_launch_result.json").read_text(encoding="utf-8-sig"))
print("P2 e4_launch", json.dumps({k: d.get(k, "缺") for k in ["rc", "duration_s", "leftover_procs"]}, ensure_ascii=False))
d = json.loads((root / "l1_20261023e4/measure_w2.json").read_text(encoding="utf-8-sig"))
t = d["samples"]["t"]
print("P2 e4_window_missing_tail_s =", d["span_s"] - (t[-1] - t[0]))
'
```

实际 stdout：

```text
P2 unreadable archive_T12/frame_target_01.png size = 65 error = UnidentifiedImageError
P2 unreadable archive_T13/frame_target_01.png size = 65 error = UnidentifiedImageError
P2 unreadable archive_T14/frame_target_01.png size = 65 error = UnidentifiedImageError
P2 unreadable archive_T15B/frame_target_01.png size = 65 error = UnidentifiedImageError
P2 unreadable archive_T5/frame_target_01.png size = 11216 error = OSError
P2 unreadable archive_T8/frame_target_01.png size = 11252 error = OSError
P2 unreadable archive_T9/frame_target_01.png size = 11252 error = OSError
P2 frame_target {"found": 58, "decoded": 51, "unreadable": 7}
P2 highest_frame_target l1_20261023e1/frame_target_01.png 0.4024281711805746
P2 highest_frame_target l1_20261023hb/frame_target_01.png 0.4024281711805746
P2 highest_frame_target l1_20261023k/frame_target_01.png 0.4024281711805746
P2 highest_frame_target l3_1101v3a/frame_target_01.png 0.4024281711805746
P2 highest_frame_target l3_1101v3b/frame_target_01.png 0.4024281711805746
P2 time {"file": "archive_T33/measure_w2_end_x.png", "mtime": "2026-10-18T11:46:35.784015+08:00", "png_minus_json_mtime_ms": 70.68848609924316, "png_minus_nominal_window_end_s": 0.08993697166442871}
P2 time {"file": "archive_T42/measure_w1_end_x.png", "mtime": "2026-10-18T16:12:05.859326+08:00", "png_minus_json_mtime_ms": 66.82395935058594, "png_minus_nominal_window_end_s": 0.08123540878295898}
P2 time {"file": "archive_T42/measure_w2_end_x.png", "mtime": "2026-10-18T16:12:30.942672+08:00", "png_minus_json_mtime_ms": 66.77675247192383, "png_minus_nominal_window_end_s": 0.08334612846374512}
P2 time {"file": "archive_T45/measure_w2_end_x.png", "mtime": "2026-10-18T17:48:34.219313+08:00", "png_minus_json_mtime_ms": 65.86980819702148, "png_minus_nominal_window_end_s": 0.07980108261108398}
P2 file archive_T42/_launch_result.json exists = False size = 缺
P2 file archive_T42/T42_console.log exists = True size = 0
P2 e4_launch {"rc": 0, "duration_s": 275.4, "leftover_procs": []}
P2 e4_window_missing_tail_s = 13.105424999997922
```

P2 的实际 stderr 只有同一 Pillow getdata 弃用警告。退出码 0 表示检查已把缺件如实枚举，并不表示 58 个对照文件都能解码或具有正确战斗语义。13.105425 秒是“名义 25 秒减有效样点首末跨度”的派生量，不是已测进程退出时刻。

## 6. I：写入前受保护件内容指纹（退出码 0）

I 在本轮全部写入之前执行；其之前只有读工具与只读检查。核对 146 件：指定核心文书及 `.git/index`、D 下所有 `measure_*` 的 JSON/PNG、四趟 qc151_fields。未覆盖全仓或全部 frame_target PNG，不能宣传为全仓哈希审计。

实际命令：

```bash
python -I -X utf8 -c '
from pathlib import Path
import hashlib, json
root = Path("D:/Project/ra2-campaign-forge")
data = root / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
base = root / "lead/goal3t_nightwatch_20261102/swarm_20261104"
core = [root / "lead/PENDING_DECISIONS.md", root / "lead/GOAL_THREE_TARGETS_20261018.md", base / "S544_TRI_MODEL_VERDICT_20261104.md", base / "ADJUDICATE_a70d00e5/RULING.md", base / "ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md", base / "ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md", base / "T42E4_FORENSIC_085458ab/SUMMARY.md", base / "T42E4_FORENSIC_085458ab/02_verify.md", base / "_leader_scorecensus.py", base / "_leader_scorecensus_out.txt", root / ".git/index"]
protected = set(core)
protected.update(p for p in data.rglob("measure_*") if p.is_file() and p.suffix in (".json", ".png"))
protected.update(data / t / "qc151_fields.json" for t in ["archive_T33", "archive_T42", "archive_T45", "l1_20261023e4"])
manifest = hashlib.sha256()
for p in sorted(protected):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest.update((p.relative_to(root).as_posix() + "\t" + str(p.stat().st_size) + "\t" + h + "\n").encode("utf-8"))
    if p in core:
        print("I core", p.relative_to(root).as_posix(), h)
print("I manifest", json.dumps({"files": len(protected), "sha256": manifest.hexdigest()}, ensure_ascii=False))
'
```

实际 stdout：

```text
I core .git/index 22ee331b5319fa41b023d6e972fc770d67f9020dd34deea0619a040c507dcc8c
I core lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_scorecensus.py 514b20bdce6199a225b65f86c30e14d17b565bc21073c74f16acd2f78ece25e2
I core lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_scorecensus_out.txt 0aead2b7781369c08aa602edc72828942129ae7e0790e48a5aebe4a96b3f0f68
I core lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md 7d71b576e087151efcf64100212b070fdf3dc82804039276435b0688142b48f1
I core lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md 9dc632304a0ab28efc2f2bd1613fd0e3b52c22b53b18cd839f90dd0214699c4b
I core lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md 6ad01107460d355b5d8eae1f4c581bc37a6d1f514fa524de6b4ed68b1f012652
I core lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md 7ac8c4e16f13432bf90bc0ba48190e37118807a6ba618ea2d9deee93baed14a4
I core lead/goal3t_nightwatch_20261102/swarm_20261104/T42E4_FORENSIC_085458ab/02_verify.md e2a261232d6960c7d85cf23c01e14133af8734c3ff6deb5aa6e45431fbc83490
I core lead/goal3t_nightwatch_20261102/swarm_20261104/T42E4_FORENSIC_085458ab/SUMMARY.md 2286ec17f946b18e49eb35919094472629366567eb5bc1f09484b166cfdc88e5
I core lead/GOAL_THREE_TARGETS_20261018.md 97f1b315ad86dbee34de75551e021a5467900415f7c6a1b966bc66205a8e3c54
I core lead/PENDING_DECISIONS.md 7d0085cb9dece817bed52b58fb748eb32b662b2d2b690a2e6fc9c8a5edea159d
I manifest {"files": 146, "sha256": "fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b"}
```

## 7. S544 §3 十一条逐条阅读后的控制

| 原错误编号（原件 113–123 行） | 本轮处理及限度 |
|---|---|
| 1 T38 时钟 30/32 秒抄错 | 不以旧 30 秒作证；本轮未打开该图核时钟，沿用已撤回状态。 |
| 2 T38/w1 残留误作时序错位 | 不把旧图当本窗证据；T42 30 旧件本轮全清点。T38 残留哈希/mtime本轮未重算。 |
| 3 31.2 当结算时钟常数 | 不用两组恰好相近的除法恢复全局常数；计分表身份与时钟关系分开。 |
| 4 比分 146/171 抄错 | 不复用旧比分作证；本轮原图还否定了后来“两图全零”概括，不发布全表 OCR 值。 |
| 5 漏根两图的 20/25 | P 实际枚举 27=25+2，分别输出高 p 20/25 和 22/27；语义身份不是本轮全量目视。 |
| 6 p50 替换主指标 | S 维持 avg；T34 avg=0.36/p50=31.61 仍归停摆，不给健康判定。 |
| 7 跨版本/负载/地图/相位混杂 | 不凭 22/8 分层推机制或同负载效应，昨日 EX-1 五列要求继续有效。 |
| 8 相关同义反复、未报口径/伪重复 | 按窗/趟分报；未复算 §549 相关，不用相关系数补机制。 |
| 9 argv 24/21 漏参 | 本轮不复核 argv，不在本裁决恢复同命令或版本因果解释。 |
| 10 异常残件误作崩溃 | 未重算 107 份；不以 e4 except_post 推退出方式，缺项照记。 |
| 11 glob 漏层级 | K 递归发现 37 archive 目录、23 缺 w0；S 全递归 104=根3+子101；P 全递归末图 27=25+2。 |

## 8. 检查与交付状态

- K：已执行、退出 0，a–d 数值一致；e 仅现存 14 件数值一致，另外 23 目录缺 w0 的范围限制已裁入正文。
- S：已执行、退出 0，全 104 件分层与集合归属复算通过；stats 全量重建未运行。
- P：已执行、**退出 1**；27/27 末图颜色计算已完成，有实际输出；额外对照循环失败，整条不得记通过。
- P2：已执行、退出 0；58 个对照路径中 7 不可解码已列明；四图 mtime/采集字段吻合，不绝对排除拷贝。
- I：已执行、退出 0；146 件内容指纹如上。
- I2：已执行、退出 0，146 件内容指纹与 I 完全一致，输出目录恰为指定两件；实际命令和输出见下节。
- 未运行：全量 25/27 目视或 OCR、全库逐样点 stats 重建、§549 相关/分箱、1734 事件/87.7%、107 异常件、静态反汇编、项目测试、E3 或真机。
- 初始查找用 `pwd`、`rg --files`、`git status --short --untracked-files=no`；全树 `rg --files --hidden -g AGENTS.md -g '!\.git/**'` 无 AGENTS 命中。对目标输出目录的首次 rg 返回“系统找不到指定的路径”，表示当时尚未创建，后由 Write 创建指定两文件；不是证据件缺失。
- 本轮两次 Write 的目标均在用户指定白名单。台账/PENDING 的登记、后继候选正文、EX-5 落实验收及异族全量目视均为**后续动作，尚未执行**。

## 9. I2 写后指纹复验

已在两份文档创建后实际执行，退出码 0。只读 146 个受保护件，并对本输出目录列文件名；没有读取活进程，没有重写原件。实际命令：

```bash
python -I -X utf8 -c '
from pathlib import Path
import hashlib, json
root = Path("D:/Project/ra2-campaign-forge")
data = root / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
base = root / "lead/goal3t_nightwatch_20261102/swarm_20261104"
core = [root / "lead/PENDING_DECISIONS.md", root / "lead/GOAL_THREE_TARGETS_20261018.md", base / "S544_TRI_MODEL_VERDICT_20261104.md", base / "ADJUDICATE_a70d00e5/RULING.md", base / "ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md", base / "ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md", base / "T42E4_FORENSIC_085458ab/SUMMARY.md", base / "T42E4_FORENSIC_085458ab/02_verify.md", base / "_leader_scorecensus.py", base / "_leader_scorecensus_out.txt", root / ".git/index"]
protected = set(core)
protected.update(p for p in data.rglob("measure_*") if p.is_file() and p.suffix in (".json", ".png"))
protected.update(data / t / "qc151_fields.json" for t in ["archive_T33", "archive_T42", "archive_T45", "l1_20261023e4"])
manifest = hashlib.sha256()
for p in sorted(protected):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest.update((p.relative_to(root).as_posix() + "\t" + str(p.stat().st_size) + "\t" + h + "\n").encode("utf-8"))
    if p in core:
        print("I2 core", p.relative_to(root).as_posix(), h)
expected = "fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b"
matched = len(protected) == 146 and manifest.hexdigest() == expected
print("I2 manifest", json.dumps({"files": len(protected), "sha256": manifest.hexdigest(), "matches_baseline": matched}, ensure_ascii=False))
output = root / "lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33"
actual = sorted(p.name for p in output.iterdir() if p.is_file())
print("I2 output_files", json.dumps(actual, ensure_ascii=False))
assert matched
assert actual == ["AUDIT.md", "RULING_D16.md"]
'
```

实际 stdout 摘录（11 条 I2 core 哈希均与第 6 节 I core 逐项一致）：

```text
I2 manifest {"files": 146, "sha256": "fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b", "matches_baseline": true}
I2 output_files ["AUDIT.md", "RULING_D16.md"]
```

之后只在已获准的本 AUDIT 文件补记这次实际复验，不改变受保护集合。146 件内容零变更这一检查已通过；它不证明未纳入集合的全仓文件都做过哈希。指定两件产物以外，本裁决未进行文件写入。

## 10. 独立审校员审查（2026-11-05，本次 ask）

**判定：NEEDS_REVISION。problems 共 1 条：RULING_D16.md:63 把跨三趟的四张同字节图写成了“T42 四图”。** 本节由未参与裁决的审校员补入；第 1–9 节是裁决员已有的自核记录，不当作审校员亲跑记录。审校员只修改本 AUDIT.md，RULING_D16.md 保持只读。本节中的“亲核”均指本次 ask 实际执行的检查。

### 10.1 问题：原句、应改内容、依据

- **原句**（`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md:63`）：
  > T42 四图本轮 p=`0.03976267648189859`，e4 图 p=`0.0027577871779377026`，实际内容分别是主菜单和桌面；判读依赖原图与采集字段，不是负向阈值。
- **应改成**：
  > 四张同字节主菜单图（T33/w2、T42/w1、T42/w2、T45/w2）本轮 p 均为 `0.03976267648189859`，其中 T42 有两张；e4/w2 图 p 为 `0.0027577871779377026`，内容是桌面。判读依赖原图与采集字段，不是负向阈值。
- **依据**：裁决书自身 `:31` 已正确列明四图跨三趟；台账 `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md:4536` 至 `:4539`、GLM 原件 `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/T42E4_FORENSIC_085458ab/02_verify.md:80` 同样列这四个文件。本次亲跑下列命令，退出 0，T42 实际只有两张末图；本节 C 命令独立复算四文件的 p 值均相同。问题是样本归属/数量写错，p 的数值本身正确。不得据此新增两张不存在的 T42 图。

```bash
rg --files D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42 -g '*end*png'
```

实际 stdout：

```text
D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42\measure_w2_end_x.png
D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42\measure_w1_end_x.png
```

独立 JSON 字段/文件枚举另实得 `T42_END_FILES ["measure_w1_end_x.png", "measure_w2_end_x.png"]`。这是与 S544 §3 第 1、5 条同类的数字/样本指代差错，需要修正后再判 PASS；不要求重开已明确的方案选择。

### 10.2 六项判据逐条结论

下表 R16、P、L、M、R15、C15、C13、V、G 的绝对路径分别为本裁决书证据索引第 13–19 行所列原件；本次均实际读取。路径中的 R16 是本目录只读的 `RULING_D16.md`。

| 判据 | 本次核对结果与依据 |
|---|---|
| 1. 落在既有选项、修正有理由 | **通过**。D-16 原 A/B/C 在 `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md:39`、`:45`、`:47`；订正在 `:55` 起。R16:53–57 明选限定 A，明确删去“全盘回退”和“e4 属于 11 窗”的错误前提，并以全量分层复算和昨日 R15:5、:111 已有限定为理由。不是未说明理由的新第四项。D-15 在 P:118–124 的 A/B/C 内继受修正 A，R16:95–101 明列采用和不采用部分；不借原 A 的 E3 文字授予新权限。 |
| 2. 数字/新增事实 | **未通过，只有 10.1 所列问题**。本次不仅复用自核表，还独立重算哈希、T42 61/30、37/14/23、T34 帧差/avg/最长等值平台、全 104 JSON 分层与 22 窗 live、27 图 p、58 对照解码。结果见 A/B/C。原存 p50/max_stall 与样点重建量分别标示；没有把二者差约 1 微秒伪装为全同。R16:63 的跨趟“四图”误称仍须改。 |
| 3. 三个事项有无回避 | **通过**。p 的正向适用域与低 p 不可反推在战，R16:61–67、:79–81 有正文要求；目视顺序明确选“先登记、全量异族目视后置”，R16:85、:89、:119；D-15 明确继续修正 A、不再待裁，R16:95、:103–107。未知机制/缺图列为证据缺口，没有把任一方案选择写成“待议”。R16:71 明写“在过渡画面及其余未知窗阶段证据缺失的前提下裁定”。 |
| 4. 是否越权批准侵入操作 | **通过**。R16:7、:107、:144 明确禁止真机发射、活进程读取、E3、MiniDump、SuspendThread、StackWalk 及相应采样候选代码；:107 又明确材料齐备或 Lead 验收不放宽权限。动作表 :111、:116–120 的台账/候选/离线目视安排均限定后续获准写域和维护轮，本轮没有执行令。审校员本次也未执行上述任何操作。 |
| 5. PENDING/台账/母本是否改动 | **在实测范围内通过**。独立 I 检查的 146 件内容指纹与作者写前 I、写后 I2 完全一致；核心件 mtime 见 10.6。两棵数据树全部 2370 个 PNG/measure JSON 的 mtime 均早于裁决书 mtime。全仓 git status 共 1186 行，与本次审校开始时逐字相同；三份 MM 是开场已存在状态，不能据此归责本轮。索引 SHA 未变、HEAD 未变。裁决前历史行为的额外全仓指纹没有提供，不冒称完成那种检查。 |
| 6. S544 §3 十一条错误 | **已逐条比对，见 10.3**。没有重犯判据反向、用 p50 洗健康、漏根层或残件当新证据；仍有 10.1 的归属数量误写，因此本项不能据“11 条均已控制”免除修改。 |

R16:73 的否决按其上游原候选解释“**四屋零建筑**”（L:4651、:4726）理解：T34 的 b 全程 41 足以反驳该全零前提；R16:73、:142 同时保留其他设置/玩家和 T49 规则是否触发的缺口，没有据此认定全部 ShortGame 规则永远不可能触发。原件未给逐屋判负链，审校未补造。

### 10.3 与 M §3 的 11 条错误逐项比对

原表绝对路径：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md:109`；第 1–11 条原文在 :113–123，本次已读。

| # | 本案是否重犯及本次依据 |
|---|---|
| 1 T38 秒数抄错 | R16 没有恢复 30 秒值；但 :63 发生另一处数字/文件归属误写，列为唯一 problem。本次未打开 T38 图重读秒数，不声称独立验收其 32 秒。 |
| 2 T38 残留件当新图 | R16:118–119 要求旧图/未对齐归未知、T38/w1 单列残留；没有依该残件定位当前停顿。C15:665 与 V:81、:90 给出残件原证据，本次读取但未重算该哈希/时差。 |
| 3 31.2 通用时钟常数 | R16:117 明禁；没有用两张计分图拟合常数或重建机制。 |
| 4 比分抄错/全零概括 | R16:45 撤回 L:4633 全零概括。本次 Read 打开 T41/w1，确有上行失败数 5；T34/w1 下行也有非零建造数。没有发布完整比分 OCR 表，也未以旧 146/171 作证。 |
| 5 20/25 与 22/27 混引 | 本次 C 实算 root=2、child=25、high_p_root=2、high_p_child=20、合计 22/27。R16:89–91、:119 分开列分母并限定语义身份；唯一“四图”错误仍须改。 |
| 6 p50 替代主指标 | R16:34、:103 保留 T34 为低 avg 停摆观测，:103 明定 avg 主指标。本次 A 重算 T34 avg≈0.360002304、最长等值平台≈24.734760 秒，B 维持 33=22+11。 |
| 7 负载/版本/地图/相位混杂 | R16:118 继续 EX-1 的 47 行五字段要求，没有以分层得出单因机制；R15:166 原要求已读。未另复算相关配对。 |
| 8 相关系数无口径/伪重复 | R16:133、:143 明说 §549 未复算，不拿它补机制；:37、:103 分报 22 窗与 8 趟。本次 B 独立确认趟数、两个总体零重叠。 |
| 9 argv 24/21 被说成同命令 | R16 未恢复该断言，:130 明列这类旧信息未全复核；本次未重跑 argv 对账。 |
| 10 107 异常残件当崩溃 | R16:138 把 e4 退出确切时刻/方式写缺，没有以 except 孤证认定崩溃；:130 披露未复核 107 件。本次未重跑 107 件普查。 |
| 11 glob/目录层级漏扫 | 本次 A 递归 37 个 archive 目录并明确 23 缺 w0；B 104=根3+子101；C 27=根2+子25，均与 R16:35–37、:89 一致。M 原表的历史 101 不是本轮 104，R16 没有混用。 |

p 判据语义另核：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_scorecensus.py:19` 固定检测矩形，:22–27 只是颜色比例，:83 的自动命名不构成通用语义验证。R16:61–67 已把原图识别、颜色阈值、采图时刻、整窗/前窗原因区分。审校员本次 Read 的 6 张末图是 T41/w1、T34/w1、T42/w1、e4/w2、T33/w1、T45/w1；另打开 T35 与 v3a 两张 frame_target，分别确为计分表和加载简报。未完成 25/27 张逐文件目视，不冒称替 R16 的后置独立事项验收。

### 10.4 独立重算 A：哈希、T42 目录、archive 覆盖、T34 样点

以下是本次实际 Bash 命令，退出 0；没有写脚本文件或导入 harness。

```bash
python -I -X utf8 -c 'from pathlib import Path; import json,hashlib; from datetime import datetime,timezone,timedelta; r=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"); group=["archive_T33/measure_w2_end_x.png","archive_T42/measure_w1_end_x.png","archive_T42/measure_w2_end_x.png","archive_T45/measure_w2_end_x.png"]; hashes={s:hashlib.sha256((r/s).read_bytes()).hexdigest() for s in group+["archive_T33/measure_w1_end_x.png","archive_T45/measure_w1_end_x.png"]}; print("HASH",json.dumps(hashes,ensure_ascii=False)); cut=datetime(2026,10,18,16,10,15,tzinfo=timezone(timedelta(hours=8))).timestamp(); files=[p for p in (r/"archive_T42").rglob("*") if p.is_file()]; print("T42",json.dumps({"recursive":len(files),"direct":sum(p.is_file() for p in (r/"archive_T42").iterdir()),"old":sum(p.stat().st_mtime<cut for p in files),"launch_exists":(r/"archive_T42/_launch_result.json").exists(),"console_size":(r/"archive_T42/T42_console.log").stat().st_size})); archives=sorted(p for p in r.rglob("archive_T*") if p.is_dir()); present={}; missing=[]
for a in archives:
 p=a/"measure_w0.json"
 if not p.is_file(): missing.append(a.relative_to(r).as_posix()); continue
 j=json.loads(p.read_text(encoding="utf-8-sig")); c=j.get("counters") or []; present[a.relative_to(r).as_posix()]={"units0":j["gate"].get("units0"),"first_b":c[0].get("b") if c else "缺","distinct_b":sorted(set(v.get("b") for v in c))}
print("ARCHIVE",json.dumps({"dirs":len(archives),"w0_count":len(present),"missing_count":len(missing),"present":present,"missing":missing},ensure_ascii=False)); j=json.loads((r/"archive_T34/measure_w0.json").read_text(encoding="utf-8-sig")); f=j["samples"]["f"]; t=j["samples"]["t"]; df=f[-1]-f[0]; span=t[-1]-t[0]; runs=[]; start=0
for i in range(1,len(f)):
 if f[i]!=f[i-1]: runs.append((t[i-1]-t[start],f[start])); start=i
runs.append((t[-1]-t[start],f[start])); print("T34_RECALC",json.dumps({"samples":len(f),"counters":len(j["counters"]),"f_first":f[0],"f_last":f[-1],"df":df,"sample_span_s":span,"avg_recomputed":df/span,"stored_avg":j["stats"]["fps_avg"],"stored_p50":j["stats"]["fps_p50"],"stored_logic":j["stats"]["logic_frames"],"longest_equal_sample_run_s":max(runs)[0],"longest_run_frame":max(runs)[1],"stored_max_stall_s":j["stats"]["max_stall_s"],"sample_gaps_gt10ms":sum(y-x>.01 for x,y in zip(t,t[1:]))},ensure_ascii=False))'
```

实际 stdout 关键完整行：

```text
HASH {"archive_T33/measure_w2_end_x.png": "f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b", "archive_T42/measure_w1_end_x.png": "f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b", "archive_T42/measure_w2_end_x.png": "f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b", "archive_T45/measure_w2_end_x.png": "f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b", "archive_T33/measure_w1_end_x.png": "fd1378bba8731002f288b2c6c494402585c748ff2ee896f54c079d30222c65ff", "archive_T45/measure_w1_end_x.png": "bc34f315e1f8e9f5baf3674c39d286462a46897fbbc269bf6d90394e737230b9"}
T42 {"recursive": 61, "direct": 61, "old": 30, "launch_exists": false, "console_size": 0}
T34_RECALC {"samples": 12502, "counters": 25, "f_first": 293, "f_last": 302, "df": 9, "sample_span_s": 24.999840000004042, "avg_recomputed": 0.36000230401468747, "stored_avg": 0.36000229681454066, "stored_p50": 31.608659530882008, "stored_logic": 9, "longest_equal_sample_run_s": 24.734759999992093, "longest_run_frame": 302, "stored_max_stall_s": 24.734761, "sample_gaps_gt10ms": 0}
```

ARCHIVE 行实际输出字段为 dirs=37、w0_count=14、missing_count=23；14 份每趟的 units0/first_b/distinct_b 与本文件第 2 节 :132–145 的原表逐项相同；missing 名单与 :151–173 相同。T32/T33 首拍 43，其余 11 份首拍 41，唯一首拍 0 为 T49_u0800、distinct_b=[0,1,2]。这是本次独立枚举，不把 23 缺件补成零值。T34 的 avg 和最长平台是从原始样点重新计算，已超过“至少两项自己重算”的最低要求；原存 p50 仅回读核对。

### 10.5 独立重算 B/C：全 JSON 与全部末图

B 的实际命令，退出 0：

```bash
python -I -X utf8 -c 'from pathlib import Path; from collections import Counter; import json; r=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"); totals=Counter(); rows=[]; full=sorted(r.rglob("measure_w*.json"))
for p in full:
 j=json.loads(p.read_text(encoding="utf-8-sig")); f=(j.get("samples") or {}).get("f") or []; t=(j.get("samples") or {}).get("t") or []; totals["all"]+=1; totals["root" if p.parent==r else "child"]+=1
 if len(f)<2 or len(f)!=len(t): totals["insufficient"]+=1; continue
 df=f[-1]-f[0]
 if df<0: totals["negative"]+=1; continue
 if df==0: totals["zero"]+=1; totals["zero_nonzero_first"]+=f[0]!=0; continue
 totals["positive"]+=1; span=j.get("span_s"); totals["positive_"+str(span)]+=1
 if span!=25: continue
 avg=(f[-1]-f[0])/(t[-1]-t[0]); e=j["frame_edges"]; live=(e[-1][0]-e[0][0])/(e[-1][1]-e[0][1]); s=j["stats"]; kind="control" if avg>=28 else "steady" if s["fps_p50"]<28 else "stopped"; totals[kind]+=1; rows.append({"path":p.relative_to(r).as_posix(),"trip":j["trip_id"],"kind":kind,"df":df,"avg_recomputed":avg,"stored_avg":s["fps_avg"],"live":live,"p50":s["fps_p50"],"stall":s["max_stall_s"]})
steady=[x for x in rows if x["kind"]=="steady"]; stopped=[x for x in rows if x["kind"]=="stopped"]; print("CENSUS",json.dumps(dict(totals),sort_keys=True)); print("PARTITIONS",json.dumps({"steady_trip_count":len(set(x["trip"] for x in steady)),"stopped_trip_count":len(set(x["trip"] for x in stopped)),"trip_overlap":len(set(x["trip"] for x in steady)&set(x["trip"] for x in stopped)),"steady_live_lt28":sum(x["live"]<28 for x in steady),"steady_max_stall":max(x["stall"] for x in steady),"steady_ge1":sum(x["stall"]>=1 for x in steady),"avg_max_abs_difference":max(abs(x["avg_recomputed"]-x["stored_avg"]) for x in rows)},ensure_ascii=False)); print("STOPPED",json.dumps([{k:v for k,v in x.items() if k in ("path","df")} for x in stopped],ensure_ascii=False))
for rel in ["archive_T42/measure_w1.json","archive_T42/measure_w2.json","l1_20261023e4/measure_w1.json","l1_20261023e4/measure_w2.json"]:
 j=json.loads((r/rel).read_text(encoding="utf-8-sig")); f=j["samples"]["f"]; t=j["samples"]["t"]; print("DETAIL",json.dumps({"file":rel,"n":len(f),"first":f[0],"last":f[-1],"df":f[-1]-f[0],"all_zero":all(x==0 for x in f),"observed_span_s":t[-1]-t[0],"error":j.get("error"),"in_stopped11":any(x["path"]==rel for x in stopped)},ensure_ascii=False))'
```

实际 stdout 摘录：

```text
CENSUS {"all": 104, "child": 101, "control": 25, "insufficient": 5, "negative": 1, "positive": 63, "positive_25.0": 58, "positive_4.0": 5, "root": 3, "steady": 22, "stopped": 11, "zero": 35, "zero_nonzero_first": 32}
PARTITIONS {"steady_trip_count": 8, "stopped_trip_count": 11, "trip_overlap": 0, "steady_live_lt28": 22, "steady_max_stall": 0.749879, "steady_ge1": 0, "avg_max_abs_difference": 1.1261364569747911e-06}
STOPPED [{"path": "archive_T32/measure_w0.json", "df": 482}, {"path": "archive_T33/measure_w0.json", "df": 444}, {"path": "archive_T34/measure_w0.json", "df": 9}, {"path": "archive_T36/measure_w0.json", "df": 178}, {"path": "archive_T38/measure_w1.json", "df": 29}, {"path": "archive_T39/measure_w1.json", "df": 32}, {"path": "archive_T43/measure_w0.json", "df": 182}, {"path": "archive_T47/measure_w0.json", "df": 575}, {"path": "archive_T49_u0800/measure_w0.json", "df": 317}, {"path": "l3_20261023q/measure_w2.json", "df": 120}, {"path": "l3_20261023r/measure_w1.json", "df": 484}]
DETAIL {"file": "l1_20261023e4/measure_w1.json", "n": 12501, "first": 3557, "last": 0, "df": -3557, "all_zero": false, "observed_span_s": 24.998100000000704, "error": null, "in_stopped11": false}
DETAIL {"file": "l1_20261023e4/measure_w2.json", "n": 5949, "first": 0, "last": 0, "df": 0, "all_zero": true, "observed_span_s": 11.894575000002078, "error": "ReadProcessMemory 失败 6190 次（有效样本 5949）", "in_stopped11": false}
```

T42/w1 与 w2 的 DETAIL 另实得 f=883→883、n=12501、in_stopped11=false，均属于 32 个 f0 非零的零推进窗。故 P:62–63 的“11 窗内含 e4，一个加十个”确实错误；R16:43、:56 的纠正有原件支持。B 以样点跨度重算 avg、首末帧沿跨度重算 live，未重建所有 p50 和 max_stall；原存 avg 与样点差商最大差约 1.13e-6，不改变任何阈值分类。

C 的实际命令，退出 0：

```bash
python -I -X utf8 -c 'from pathlib import Path; from PIL import Image; import json; from datetime import datetime,timezone,timedelta; r=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"); images=sorted(r.rglob("measure_w*_end_x.png")); counts={"all":len(images),"root":0,"child":0,"high_p_root":0,"high_p_child":0,"high_p_f0_nonzero_df0":0}; values={}
def panel(p):
 with Image.open(p) as im: raw=im.convert("RGB").crop((85,108,630,275)).tobytes()
 hit=sum(b>red+18 and b>g+10 and 40<=b<=190 and red<150 for red,g,b in zip(raw[0::3],raw[1::3],raw[2::3])); return hit,len(raw)//3,hit/(len(raw)//3)
for p in images:
 hit,n,v=panel(p); values[p.relative_to(r).as_posix()]=v; layer="root" if p.parent==r else "child"; counts[layer]+=1
 if v>=.30:
  counts["high_p_"+layer]+=1; j=json.loads(p.with_name(p.name.replace("_end_x.png",".json")).read_text(encoding="utf-8-sig")); f=j["samples"]["f"]; counts["high_p_f0_nonzero_df0"]+=bool(f and f[0]!=0 and f[-1]==f[0])
print("P_COUNTS",json.dumps(counts)); print("P_VALUES",json.dumps(values,ensure_ascii=False)); controls=sorted(r.glob("*/frame_target_01.png")); bad=[]
for p in controls:
 try: panel(p)
 except OSError as e: bad.append({"path":p.relative_to(r).as_posix(),"error":type(e).__name__})
print("CONTROLS",json.dumps({"total":len(controls),"decoded":len(controls)-len(bad),"bad":bad,"v3a_p":panel(r/"l3_1101v3a/frame_target_01.png")[2]},ensure_ascii=False)); tz=timezone(timedelta(hours=8))
for rel in ["archive_T33/measure_w2_end_x.png","archive_T42/measure_w1_end_x.png","archive_T42/measure_w2_end_x.png","archive_T45/measure_w2_end_x.png"]:
 p=r/rel; q=p.with_name(p.name.replace("_end_x.png",".json")); rows=json.loads((p.parent/"qc151_fields.json").read_text(encoding="utf-8-sig")); captures=[{"index":i,"ts":v.get("ts"),"data":{k:v["value"].get(k) for k in ("forensics_png","capture_ok","game_hwnd","game_title","fg_title","focus_ok","current_frame","empty_window")}} for i,v in enumerate(rows) if isinstance(v.get("value"),dict) and v["value"].get("forensics_png")==p.name]; print("TIME",json.dumps({"file":rel,"mtime":datetime.fromtimestamp(p.stat().st_mtime,tz).isoformat(timespec="microseconds"),"delta_json_ms":(p.stat().st_mtime_ns-q.stat().st_mtime_ns)/1e6,"captures":captures},ensure_ascii=False))'
```

实际 stdout 摘录：

```text
P_COUNTS {"all": 27, "root": 2, "child": 25, "high_p_root": 2, "high_p_child": 20, "high_p_f0_nonzero_df0": 21}
CONTROLS {"total": 58, "decoded": 51, "bad": [{"path": "archive_T12/frame_target_01.png", "error": "UnidentifiedImageError"}, {"path": "archive_T13/frame_target_01.png", "error": "UnidentifiedImageError"}, {"path": "archive_T14/frame_target_01.png", "error": "UnidentifiedImageError"}, {"path": "archive_T15B/frame_target_01.png", "error": "UnidentifiedImageError"}, {"path": "archive_T5/frame_target_01.png", "error": "OSError"}, {"path": "archive_T8/frame_target_01.png", "error": "OSError"}, {"path": "archive_T9/frame_target_01.png", "error": "OSError"}], "v3a_p": 0.4024281711805746}
```

P_VALUES 全 27 项均与第 4 节 :325–351 的旧输出逐值一致，本次额外核得四个主菜单文件值均为 0.03976267648189859、e4/w2 为 0.0027577871779377026。TIME 原始输出的 `delta_json_ms` 按上述四图顺序分别是 70.6885、66.8239、66.7766、65.8696；采集声明 index=160/170/174/443，ts=2026-10-18T11:46:35/16:12:05/16:12:30/17:48:34+08:00，与原图 mtime 同秒；game_hwnd=16582032/9177688/9177688/21695114，capture_ok/focus_ok 均 true。纳秒整数差与作者浮点秒差末位有亚微秒舍入差，R16:46 的 65.87–70.69ms 范围成立，不据此绝对排除拷贝或缓存。

e4 采集字段另一次实际命令，退出 0：

```bash
python -I -X utf8 -c 'from pathlib import Path; import json; root=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"); rows=json.loads((root/"l1_20261023e4/qc151_fields.json").read_text(encoding="utf-8-sig"))
for i,row in enumerate(rows):
 v=row.get("value")
 if isinstance(v,dict) and v.get("forensics_png")=="measure_w2_end_x.png": print("E4_CAPTURE",json.dumps({"index":i,"ts":row.get("ts"),"value":{k:v.get(k,"缺") for k in ("forensics_png","capture_ok","game_title","fg_title","focus_ok","current_frame","empty_window")}},ensure_ascii=False))
p=root/"archive_T42"; print("T42_END_FILES",json.dumps(sorted(q.name for q in p.rglob("*end*png")),ensure_ascii=False))'
```

实际 stdout：

```text
E4_CAPTURE {"index": 382, "ts": "2026-10-26T20:00:48+08:00", "value": {"forensics_png": "measure_w2_end_x.png", "capture_ok": true, "game_title": "", "fg_title": "BuddySwitch 整合预览版", "focus_ok": false, "current_frame": null, "empty_window": true}}
T42_END_FILES ["measure_w1_end_x.png", "measure_w2_end_x.png"]
```

### 10.6 独立完整性检查：内容指纹、mtime、git status

I 的实际命令，退出 0；集合与裁决员 I/I2 一致，另新建 mtime 摘要供审校结束时比对：

```bash
python -I -X utf8 -c 'from pathlib import Path; import hashlib,json,datetime; root=Path("D:/Project/ra2-campaign-forge"); data=root/"out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"; base=root/"lead/goal3t_nightwatch_20261102/swarm_20261104"; core=[root/"lead/PENDING_DECISIONS.md",root/"lead/GOAL_THREE_TARGETS_20261018.md",base/"S544_TRI_MODEL_VERDICT_20261104.md",base/"ADJUDICATE_a70d00e5/RULING.md",base/"ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md",base/"ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md",base/"T42E4_FORENSIC_085458ab/SUMMARY.md",base/"T42E4_FORENSIC_085458ab/02_verify.md",base/"_leader_scorecensus.py",base/"_leader_scorecensus_out.txt",root/".git/index"]; protected=set(core); protected.update(p for p in data.rglob("measure_*") if p.is_file() and p.suffix in (".json",".png")); protected.update(data/t/"qc151_fields.json" for t in ["archive_T33","archive_T42","archive_T45","l1_20261023e4"]); manifest=hashlib.sha256(); timing=hashlib.sha256(); ruling=root/"lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md"; recent=[]
for p in sorted(protected):
 h=hashlib.sha256(p.read_bytes()).hexdigest(); s=p.stat(); rel=p.relative_to(root).as_posix(); manifest.update((rel+"\t"+str(s.st_size)+"\t"+h+"\n").encode()); timing.update((rel+"\t"+str(s.st_mtime_ns)+"\n").encode())
 if s.st_mtime_ns>=ruling.stat().st_mtime_ns: recent.append(rel)
 if p in core: print("CORE",json.dumps({"path":rel,"sha256":h,"mtime_ns":s.st_mtime_ns,"mtime_utc":datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat()},ensure_ascii=False))
print("INTEGRITY",json.dumps({"files":len(protected),"content_sha256":manifest.hexdigest(),"matches_author_I_I2":manifest.hexdigest()=="fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b","mtime_sha256":timing.hexdigest(),"mtime_at_or_after_ruling":recent},ensure_ascii=False))'
```

实际 stdout 汇总行：

```text
INTEGRITY {"files": 146, "content_sha256": "fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b", "matches_author_I_I2": true, "mtime_sha256": "ccb3cafb2a50e6f56247c77a537860be778e467b7254527592f64c3227905f83", "mtime_at_or_after_ruling": []}
```

CORE 亲读的 mtime（UTC；不是将开场 MM 解释为本次修改）：

| 文件 | mtime UTC |
|---|---|
| PENDING_DECISIONS.md | 2026-11-04T15:56:10.968197+00:00 |
| GOAL_THREE_TARGETS_20261018.md | 2026-11-04T23:28:36.604338+00:00 |
| 旧 ADJUDICATE_a70d00e5/RULING.md | 2026-11-04T12:59:22.221927+00:00 |
| S544_TRI_MODEL_VERDICT_20261104.md | 2026-11-04T12:15:30.052295+00:00 |
| D15_IMPLEMENTATION_CANDIDATE.md | 2026-11-04T14:34:00.821974+00:00 |
| D13_MECHANISM_GAP_AND_OFFLINE_CARD.md | 2026-11-04T13:32:19.237605+00:00 |
| .git/index | 2026-11-02T14:53:29.001156+00:00 |

两树**全部 PNG 与 measure_*.json**的 mtime 检查实际命令，退出 0：

```bash
python -I -X utf8 -c 'from pathlib import Path; import json,datetime; root=Path("D:/Project/ra2-campaign-forge"); ruling=root/"lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md"; cutoff=ruling.stat().st_mtime_ns
for rel in ["out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip","lead/qc161_u0400_trip"]:
 base=root/rel; files=sorted(p for p in base.rglob("*") if p.is_file() and (p.suffix.lower()==".png" or (p.name.startswith("measure_") and p.suffix.lower()==".json"))); latest=max(files,key=lambda p:p.stat().st_mtime_ns); print("SOURCE_MTIME",json.dumps({"root":base.as_posix(),"files":len(files),"png":sum(p.suffix.lower()==".png" for p in files),"measure_json":sum(p.suffix.lower()==".json" for p in files),"latest_path":latest.relative_to(base).as_posix(),"latest_mtime_utc":datetime.datetime.fromtimestamp(latest.stat().st_mtime,datetime.timezone.utc).isoformat(),"at_or_after_ruling":[p.relative_to(base).as_posix() for p in files if p.stat().st_mtime_ns>=cutoff]},ensure_ascii=False))'
```

实际 stdout：

```text
SOURCE_MTIME {"root": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip", "files": 2277, "png": 2173, "measure_json": 104, "latest_path": "l3_1101v4h/measure_w0.json", "latest_mtime_utc": "2026-11-04T10:26:53.700400+00:00", "at_or_after_ruling": []}
SOURCE_MTIME {"root": "D:/Project/ra2-campaign-forge/lead/qc161_u0400_trip", "files": 93, "png": 81, "measure_json": 12, "latest_path": "c2ab_x/20261031T154139_9001_P3e_E12_T1/shots/post_close_end.png", "latest_mtime_utc": "2026-10-31T07:42:04.480331+00:00", "at_or_after_ruling": []}
```

git 状态：审校开场实际执行 `git -C D:/Project/ra2-campaign-forge status --porcelain=v1 --untracked-files=all`，输出过长由工具自动保留在下述临时日志；审校员没有主动创建该日志。后续实际运行的比较命令如下，退出 0。git 子命令使用 `--no-optional-locks`，不刷新写入索引：

```bash
python -I -X utf8 -c 'from pathlib import Path; import subprocess,hashlib,json,datetime; root=Path("D:/Project/ra2-campaign-forge"); cmd=["git","--no-optional-locks","-C",root.as_posix(),"status","--porcelain=v1","--untracked-files=all"]; result=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",check=True); initial=Path("C:/Users/Administrator/AppData/Local/Temp/zcode-bash-vYaZG2/sess_dwf-dwfrun-cccd2ce0-efb9-49a2-b4bd-73987a15fa33-actor_2_1/call_8a66e83a1b4e4caab9dbed1948cc963d-stdout.log").read_text(encoding="utf-8"); print("GIT_COMMAND",subprocess.list2cmdline(cmd)); print("GIT_SUMMARY",json.dumps({"exit":result.returncode,"lines":len(result.stdout.splitlines()),"normalized_sha256":hashlib.sha256(result.stdout.encode()).hexdigest(),"same_as_review_start":result.stdout==initial},ensure_ascii=False)); selected=[x for x in result.stdout.splitlines() if any(p in x for p in ("lead/PENDING_DECISIONS.md","lead/GOAL_THREE_TARGETS_20261018.md","lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md","RULING_D16_7a15fa33/","ADJUDICATE_a70d00e5/RULING.md","ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md","ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md"))]; print("GIT_SELECTED",json.dumps(selected,ensure_ascii=False)); head=subprocess.run(["git","--no-optional-locks","-C",root.as_posix(),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip(); print("HEAD",head)
for rel in ["lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md","lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md"]:
 p=root/rel; s=p.stat(); print("EXTRA_BASELINE",json.dumps({"file":rel,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"mtime_ns":s.st_mtime_ns,"mtime_utc":datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat()},ensure_ascii=False))'
```

实际 stdout：

```text
GIT_COMMAND git --no-optional-locks -C D:/Project/ra2-campaign-forge status --porcelain=v1 --untracked-files=all
GIT_SUMMARY {"exit": 0, "lines": 1186, "normalized_sha256": "00310feae6ff51eb33ad1bdfefaa91eecb9efcde6800d3a477b3f01d4c195f60", "same_as_review_start": true}
GIT_SELECTED ["MM lead/GOAL_THREE_TARGETS_20261018.md", "MM lead/PENDING_DECISIONS.md", "MM lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md", "?? lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md", "?? lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md", "?? lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md", "?? lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/AUDIT.md", "?? lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md"]
HEAD 26574589aa8401e8f3f2934680a1ea7109bafa2d
EXTRA_BASELINE {"file": "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md", "sha256": "06a419ae5e788b4c08a64c7875c35067e3858083e2a4cbf554debf4095c45e0a", "mtime_ns": 1793749562583609000, "mtime_utc": "2026-11-03T23:46:02.583609+00:00"}
EXTRA_BASELINE {"file": "lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33/RULING_D16.md", "sha256": "ef41f64f0a0bac4016763007a4d2a50f5be78f507a8fc85cc878e8269dcebcba", "mtime_ns": 1793835634570926500, "mtime_utc": "2026-11-04T23:40:34.570926+00:00"}
```

审校员没有运行项目测试、全量 25/27 图目视/OCR、全库逐样点 p50/max_stall 重建、§549 相关/分箱、107 异常件普查、静态反汇编或旧 1734 事件统计。这些不记作本次通过；本次没有真机、taskkill、活进程读取、采样/注入/Hook/转储/挂线程代码，也没有 add/commit。

### 10.7 审校写入后的只读复验

上述审校内容写入后已实际运行下列命令，退出 0，所有 assert 通过。检查不读取本 AUDIT 的内容、不改原件或索引；检查后仅补记本段。

```bash
python -I -X utf8 -c 'from pathlib import Path; import hashlib,json,subprocess; root=Path("D:/Project/ra2-campaign-forge"); data=root/"out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"; base=root/"lead/goal3t_nightwatch_20261102/swarm_20261104"; core=[root/"lead/PENDING_DECISIONS.md",root/"lead/GOAL_THREE_TARGETS_20261018.md",base/"S544_TRI_MODEL_VERDICT_20261104.md",base/"ADJUDICATE_a70d00e5/RULING.md",base/"ADJUDICATE_a70d00e5/D15_IMPLEMENTATION_CANDIDATE.md",base/"ADJUDICATE_a70d00e5/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md",base/"T42E4_FORENSIC_085458ab/SUMMARY.md",base/"T42E4_FORENSIC_085458ab/02_verify.md",base/"_leader_scorecensus.py",base/"_leader_scorecensus_out.txt",root/".git/index"]; files=set(core); files.update(p for p in data.rglob("measure_*") if p.is_file() and p.suffix in (".json",".png")); files.update(data/t/"qc151_fields.json" for t in ["archive_T33","archive_T42","archive_T45","l1_20261023e4"]); content=hashlib.sha256(); times=hashlib.sha256()
for p in sorted(files):
 rel=p.relative_to(root).as_posix(); s=p.stat(); h=hashlib.sha256(p.read_bytes()).hexdigest(); content.update((rel+"\t"+str(s.st_size)+"\t"+h+"\n").encode()); times.update((rel+"\t"+str(s.st_mtime_ns)+"\n").encode())
out=root/"lead/goal3t_nightwatch_20261102/swarm_20261105/RULING_D16_7a15fa33"; ruling=out/"RULING_D16.md"; log=root/"lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"; git=subprocess.run(["git","--no-optional-locks","-C",root.as_posix(),"status","--porcelain=v1","--untracked-files=all"],capture_output=True,text=True,encoding="utf-8",check=True).stdout; head=subprocess.run(["git","--no-optional-locks","-C",root.as_posix(),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip(); result={"protected_files":len(files),"content_sha256":content.hexdigest(),"mtime_sha256":times.hexdigest(),"ruling_sha256":hashlib.sha256(ruling.read_bytes()).hexdigest(),"ruling_mtime_ns":ruling.stat().st_mtime_ns,"round_log_sha256":hashlib.sha256(log.read_bytes()).hexdigest(),"round_log_mtime_ns":log.stat().st_mtime_ns,"git_status_sha256":hashlib.sha256(git.encode()).hexdigest(),"git_status_lines":len(git.splitlines()),"head":head,"output_files":sorted(p.name for p in out.iterdir() if p.is_file())}; print("FINAL_READONLY",json.dumps(result,ensure_ascii=False)); assert result["protected_files"]==146; assert result["content_sha256"]=="fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b"; assert result["mtime_sha256"]=="ccb3cafb2a50e6f56247c77a537860be778e467b7254527592f64c3227905f83"; assert result["ruling_sha256"]=="ef41f64f0a0bac4016763007a4d2a50f5be78f507a8fc85cc878e8269dcebcba"; assert result["ruling_mtime_ns"]==1793835634570926500; assert result["round_log_sha256"]=="06a419ae5e788b4c08a64c7875c35067e3858083e2a4cbf554debf4095c45e0a"; assert result["round_log_mtime_ns"]==1793749562583609000; assert result["git_status_sha256"]=="00310feae6ff51eb33ad1bdfefaa91eecb9efcde6800d3a477b3f01d4c195f60"; assert head=="26574589aa8401e8f3f2934680a1ea7109bafa2d"; assert result["output_files"]==["AUDIT.md","RULING_D16.md"]'
```

实际 stdout：

```text
FINAL_READONLY {"protected_files": 146, "content_sha256": "fc020ce57cc9d7a76f119665219cf3df08d7d29bcc0b49cd00168ab7b943e35b", "mtime_sha256": "ccb3cafb2a50e6f56247c77a537860be778e467b7254527592f64c3227905f83", "ruling_sha256": "ef41f64f0a0bac4016763007a4d2a50f5be78f507a8fc85cc878e8269dcebcba", "ruling_mtime_ns": 1793835634570926500, "round_log_sha256": "06a419ae5e788b4c08a64c7875c35067e3858083e2a4cbf554debf4095c45e0a", "round_log_mtime_ns": 1793749562583609000, "git_status_sha256": "00310feae6ff51eb33ad1bdfefaa91eecb9efcde6800d3a477b3f01d4c195f60", "git_status_lines": 1186, "head": "26574589aa8401e8f3f2934680a1ea7109bafa2d", "output_files": ["AUDIT.md", "RULING_D16.md"]}
```

146 件的内容和 mtime 摘要均未变；裁决书本体、另一份日志台账、git 索引及 HEAD 未变，全量 git status 与审校开始时相同。输出目录仍仅两份指定 Markdown。审校员的写操作仅有本 AUDIT.md 的审校补记；没有修正只读裁决书，10.1 的问题仍存在，最终判定保持 **NEEDS_REVISION**。
