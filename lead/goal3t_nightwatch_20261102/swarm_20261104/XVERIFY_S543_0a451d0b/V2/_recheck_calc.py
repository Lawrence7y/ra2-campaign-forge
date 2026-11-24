# -*- coding: utf-8 -*-
"""
复核员-V2 独立复算脚本
完全只读原始母本数据，仅在 V2 目录内写入中间输出。
"""
import glob
import hashlib
import json
import os
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V2"

# 1. 根目录与子目录全量 JSON 盘点
subdir_jsons = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
root_jsons = sorted(glob.glob(os.path.join(BASE, "measure_w*.json")))
all_jsons = subdir_jsons + root_jsons

print(f"=== 1. 全量 measure_w*.json 盘点 ===")
print(f"子目录 JSON 数: {len(subdir_jsons)}")
print(f"根目录 JSON 数: {len(root_jsons)}")
print(f"总计 JSON 数: {len(all_jsons)}")
for rj in root_jsons:
    print(f"  根目录文件: {os.path.basename(rj)}")

# 详细分类
parsed = []
for p in all_jsons:
    is_root = (os.path.dirname(p) == BASE)
    trip = "<root>" if is_root else os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        parsed.append({"path": p, "trip": trip, "fname": fname, "error": str(e), "valid": False})
        continue

    ed = j.get("frame_edges") or []
    if not ed:
        parsed.append({"path": p, "trip": trip, "fname": fname, "empty_edges": True, "valid": False, "raw": j})
        continue

    f0 = ed[0][0]
    f1 = ed[-1][0]
    df = f1 - f0
    stats = j.get("stats") or {}
    fps_avg = stats.get("fps_avg")
    max_stall_s = stats.get("max_stall_s")
    logic_frames = stats.get("logic_frames")
    span_s = j.get("span_s") or 0.0
    counters = j.get("counters") or []
    gate = j.get("gate") or {}

    parsed.append({
        "path": p,
        "trip": trip,
        "fname": fname,
        "valid": True,
        "f0": f0,
        "f1": f1,
        "df": df,
        "span_s": span_s,
        "fps_avg": fps_avg,
        "max_stall_s": max_stall_s,
        "logic_frames": logic_frames,
        "counters": counters,
        "gate": gate,
        "is_root": is_root,
        "raw": j
    })

valid_records = [r for r in parsed if r.get("valid")]
invalid_records = [r for r in parsed if not r.get("valid")]

print(f"\n有效窗口: {len(valid_records)}, 无效/空边窗口: {len(invalid_records)}")
for inv in invalid_records:
    print(f"  无效: {inv['trip']}/{inv['fname']} (empty_edges={inv.get('empty_edges')})")

adv = [r for r in valid_records if r["df"] > 0]
frz = [r for r in valid_records if r["df"] == 0 and r["f0"] != 0]
load_frz = [r for r in valid_records if r["df"] == 0 and r["f0"] == 0]
neg = [r for r in valid_records if r["df"] < 0]

print(f"\n有效窗口分类 (全口径，含根目录):")
print(f"  有推进 (df > 0): {len(adv)}")
print(f"  战斗段冻结 (df == 0 and f0 != 0): {len(frz)}")
print(f"  加载段冻结 (df == 0 and f0 == 0): {len(load_frz)}")
print(f"  帧号回退 (df < 0): {len(neg)}")

# 子目录口径对比
adv_sub = [r for r in adv if not r["is_root"]]
frz_sub = [r for r in frz if not r["is_root"]]
print(f"\n仅子目录口径 (上一道核验员 V2 扫到的口径):")
print(f"  有推进: {len(adv_sub)}")
print(f"  冻结: {len(frz_sub)}")
print(f"  根目录中遗漏的冻结窗: {[r['fname'] for r in frz if r['is_root']]}")

# 2. 63 个有推进窗分析：健康 vs 慢窗，及慢窗中的截断窗
adv_healthy = [r for r in adv if (r["fps_avg"] or 0) >= 28.0]
adv_slow = [r for r in adv if (r["fps_avg"] or 0) < 28.0]
print(f"\n=== 2. 有推进窗分档 (共 {len(adv)} 窗) ===")
print(f"  fps_avg >= 28.0 (健康/贴帽): {len(adv_healthy)}")
print(f"  fps_avg < 28.0 (慢窗候选): {len(adv_slow)}")

# 审查 38 个慢窗中，是否有「终局截断窗」
# 判据：窗内发生推进，但在窗内某个时间点停止递增，末尾处于停摆（max_stall_s 较大，或下一窗停在同一帧）
print(f"\n--- 慢窗尾部停摆/截断分析 ---")
truncated_candidates = []
for r in adv_slow:
    trip = r["trip"]
    fname = r["fname"]
    f0, f1 = r["f0"], r["f1"]
    span_s = r["span_s"]
    fps_avg = r["fps_avg"]
    max_stall = r["max_stall_s"] or 0.0
    # 查找同趟的下一窗
    w_idx = int(fname.replace("measure_w", "").replace(".json", ""))
    next_fname = f"measure_w{w_idx + 1}.json"
    next_match = [x for x in valid_records if x["trip"] == trip and x["fname"] == next_fname]
    next_f0 = next_match[0]["f0"] if next_match else None
    next_df = next_match[0]["df"] if next_match else None
    
    # 如果下个窗停留在当前窗的末帧 f1，且下个窗 df==0，说明当前窗正是进入终局的截断窗！
    is_trunc = (next_f0 == f1 and next_df == 0) or (max_stall > 10.0 and f1 < 1000)
    if is_trunc:
        truncated_candidates.append((trip, fname, f0, f1, r["df"], fps_avg, max_stall, next_f0, next_df))

print(f"在 38 个慢窗中，被确认为「终局截断窗」（对局结束截断而非战场卡顿）的数量: {len(truncated_candidates)}")
for tc in truncated_candidates:
    print(f"  截断窗: {tc[0]} {tc[1]}: f=[{tc[2]}..{tc[3]}], df={tc[4]}, fps={tc[5]:.2f}, stall={tc[6]:.2f}s, next_w: f0={tc[7]}, df={tc[8]}")
