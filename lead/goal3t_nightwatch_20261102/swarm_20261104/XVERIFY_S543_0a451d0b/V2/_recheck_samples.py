# -*- coding: utf-8 -*-
"""
复核员-V2 样本深度复算脚本：
对抽取的具体样本进行字节级、像素级独立计算。
"""
import glob
import hashlib
import json
import os
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V2"

# 1. 扫描所有 measure_w*_end_x.png（含根目录）
all_pngs = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
root_pngs = sorted(glob.glob(os.path.join(BASE, "measure_w*_end_*.png")))
total_pngs = all_pngs + root_pngs

print(f"=== 1. 全量末截图盘点 ===")
print(f"子目录截图数: {len(all_pngs)}")
print(f"根目录截图数: {len(root_pngs)}")
print(f"总计截图数: {len(total_pngs)}")

png_records = []
for p in total_pngs:
    is_root = (os.path.dirname(p) == BASE)
    trip = "<root>" if is_root else os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    raw_bytes = open(p, "rb").read()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    im = Image.open(p)
    px_bytes = im.convert("RGB").tobytes()
    px_sha = hashlib.sha256(px_bytes).hexdigest()
    mtime = os.stat(p).st_mtime
    size = os.stat(p).st_size
    png_records.append({
        "path": p,
        "trip": trip,
        "fname": fname,
        "raw_sha": raw_sha,
        "px_sha": px_sha,
        "size": size,
        "mtime": mtime,
        "is_root": is_root,
        "im_size": im.size
    })

# 检查重复组
px_map = {}
for r in png_records:
    px_map.setdefault(r["px_sha"], []).append(r)

print(f"\n独立像素指纹数: {len(px_map)} / {len(png_records)}")
for sha, group in px_map.items():
    if len(group) > 1:
        print(f"\n重复指纹组 (px_sha={sha[:12]}, 共 {len(group)} 张):")
        for g in group:
            print(f"  {g['trip']}/{g['fname']} raw_sha={g['raw_sha'][:12]} size={g['size']} mtime={g['mtime']}")

# 2. 深入复算 Sample 1: archive_T34 (标准遭遇战终局结算屏)
print(f"\n==========================================")
print(f"=== 样本 1 独立复算: archive_T34 ===")
print(f"==========================================")
t34_dir = os.path.join(BASE, "archive_T34")
for w in [0, 1, 2]:
    jp = os.path.join(t34_dir, f"measure_w{w}.json")
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            jd = json.load(f)
        ed = jd.get("frame_edges", [])
        cnts = jd.get("counters", [])
        st = jd.get("stats", {})
        print(f"T34 w{w}: span={jd.get('span_s')}s, edges={len(ed)}, f0={ed[0][0] if ed else None}, f1={ed[-1][0] if ed else None}, df={ed[-1][0]-ed[0][0] if ed else None}")
        print(f"       fps_avg={st.get('fps_avg')}, max_stall={st.get('max_stall_s')}, logic_frames={st.get('logic_frames')}")
        if cnts:
            u_set = {c.get("units") for c in cnts}
            g_set = {c.get("g") for c in cnts}
            b_set = {c.get("b") for c in cnts}
            print(f"       counters: {len(cnts)} samples, units={u_set}, g={g_set}, b={b_set}")

# T34 图像与计时器
for w in [1, 2]:
    png_p = os.path.join(t34_dir, f"measure_w{w}_end_x.png")
    if os.path.exists(png_p):
        im = Image.open(png_p)
        # 裁剪计时器区域 (右上方，大约 x: 450..650, y: 110..150)
        # 实际位置根据前人探查：timer 在 (530, 118, 620, 138) 左右
        print(f"T34 w{w} 截图: 存在，size={im.size}")

# 3. 深入复算 Sample 2: archive_T38 (争议件：时序错位、残留重复件与计时器篡改)
print(f"\n==========================================")
print(f"=== 样本 2 独立复算: archive_T38 ===")
print(f"==========================================")
t38_dir = os.path.join(BASE, "archive_T38")
for w in [0, 1, 2]:
    jp = os.path.join(t38_dir, f"measure_w{w}.json")
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            jd = json.load(f)
        ed = jd.get("frame_edges", [])
        cnts = jd.get("counters", [])
        st = jd.get("stats", {})
        print(f"T38 w{w}: span={jd.get('span_s')}s, edges={len(ed)}, f0={ed[0][0] if ed else None}, f1={ed[-1][0] if ed else None}, df={ed[-1][0]-ed[0][0] if ed else None}")
        print(f"       fps_avg={st.get('fps_avg')}, max_stall={st.get('max_stall_s')}, logic_frames={st.get('logic_frames')}")

# 查 qc151_fields.json 对 T38 w1 的记录
f_p = os.path.join(t38_dir, "qc151_fields.json")
if os.path.exists(f_p):
    with open(f_p, "r", encoding="utf-8") as f:
        fields = json.load(f)
    forensics = [row for row in fields if "measure_forensics" in row.get("key", "")]
    for row in forensics:
        print(f"T38 qc151_fields forensics: {row.get('key')} -> {row.get('value')}")

# 查 T38 w1 和 w2 截图
t38_w1_png = os.path.join(t38_dir, "measure_w1_end_x.png")
t38_w2_png = os.path.join(t38_dir, "measure_w2_end_x.png")
t36_w1_png = os.path.join(BASE, "archive_T36", "measure_w1_end_x.png")

if os.path.exists(t38_w1_png) and os.path.exists(t36_w1_png):
    sha38_w1 = hashlib.sha256(open(t38_w1_png, "rb").read()).hexdigest()
    sha36_w1 = hashlib.sha256(open(t36_w1_png, "rb").read()).hexdigest()
    print(f"T38 w1 sha256: {sha38_w1}")
    print(f"T36 w1 sha256: {sha36_w1}")
    print(f"T38 w1 与 T36 w1 完全一致: {sha38_w1 == sha36_w1}")
    print(f"T38 w1 mtime: {os.stat(t38_w1_png).st_mtime}, T36 w1 mtime: {os.stat(t36_w1_png).st_mtime}")

# 4. 深入复算 Sample 3: l1_20261023e4 (进程崩溃而非冻结)
print(f"\n==========================================")
print(f"=== 样本 3 独立复算: l1_20261023e4 ===")
print(f"==========================================")
e4_dir = os.path.join(BASE, "l1_20261023e4")
for w in [0, 1, 2]:
    jp = os.path.join(e4_dir, f"measure_w{w}.json")
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            jd = json.load(f)
        ed = jd.get("frame_edges", [])
        cnts = jd.get("counters", [])
        st = jd.get("stats", {})
        err = jd.get("error")
        print(f"e4 w{w}: span={jd.get('span_s')}s, edges={len(ed)}, f0={ed[0][0] if ed else None}, f1={ed[-1][0] if ed else None}, df={ed[-1][0]-ed[0][0] if ed else None}")
        print(f"      fps_avg={st.get('fps_avg')}, max_stall={st.get('max_stall_s')}, logic_frames={st.get('logic_frames')}, error={err}")

# e4 w1 的瞬时跳跃与 w2 的 RPM 失败
w1_data = json.load(open(os.path.join(e4_dir, "measure_w1.json"), "r", encoding="utf-8"))
samples_f = w1_data["samples"]["f"]
samples_t = w1_data["samples"]["t"]
print(f"e4 w1 总采样点数: {len(samples_f)}")
for i in range(1, len(samples_f)):
    if samples_f[i] < samples_f[i-1]:
        print(f"  ★ 断崖点 index={i}: t={samples_t[i-1]} -> {samples_t[i]}, f={samples_f[i-1]} -> {samples_f[i]}")
        break

# e4 w2 的内存读取失败
w2_data = json.load(open(os.path.join(e4_dir, "measure_w2.json"), "r", encoding="utf-8"))
print(f"e4 w2 error: {w2_data.get('error')}")
print(f"e4 w2 counters[-1]: {w2_data['counters'][-1] if w2_data.get('counters') else None}")
