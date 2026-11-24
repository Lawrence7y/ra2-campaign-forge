# -*- coding: utf-8 -*-
"""Lead 独立复算：批次 A 的 NDJSON（不复用作者 analyze_probe.py）。

只读文件，不启动任何进程。
"""
import json
import sys
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe")


def load(p):
    recs = []
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception as e:
                print("   !! 第 %d 行解析失败: %s" % (i, e))
    return recs


def analyze(path):
    print("=" * 96)
    print("文件: %s" % path.name)
    recs = load(path)
    if not recs:
        print("  (空)")
        return
    print("  总行数 = %d" % len(recs))
    print("  首行字段 = %s" % sorted(recs[0].keys()))

    # 只取有 frame 的拍
    ok = [r for r in recs if r.get("read_status") == "ok" and isinstance(r.get("frame"), int)]
    bad = [r for r in recs if r.get("read_status") != "ok"]
    print("  read_status: ok=%d  fail=%d  (fail 类型: %s)" % (
        len(ok), len(bad), sorted({str(r.get("read_status")) for r in bad})))

    # 门控非零统计
    gate_keys = [k for k in ("g1", "g2", "g3", "g4") if k in recs[0]]
    print("  门控字段 = %s" % gate_keys)
    for k in gate_keys:
        nz = [r for r in ok if r.get(k) not in (0, None)]
        print("    %s 非零 = %d / %d (%.3f%%)" % (k, len(nz), len(ok), 100.0 * len(nz) / max(1, len(ok))))

    # 帧推进判定：用独立计算，不用作者的 frame_advanced 字段
    advance = []  # (t_ns, prev_frame, frame, gates_all_zero)
    for i in range(1, len(ok)):
        a, b = ok[i - 1], ok[i]
        ta, tb = a.get("t_mono_ns"), b.get("t_mono_ns")
        if not isinstance(ta, int) or not isinstance(tb, int):
            continue
        gates_zero = all(b.get(g) in (0, None) for g in gate_keys) if gate_keys else True
        advance.append((tb - ta, b["frame"] != a["frame"], b["frame"] - a["frame"], gates_zero))

    n_stop = sum(1 for d, adv, _, _ in advance if not adv)
    n_stop_gz = sum(1 for d, adv, _, gz in advance if (not adv) and gz)
    print("  相邻拍对 = %d；未推进 = %d；其中四门控全 0 = %d" % (len(advance), n_stop, n_stop_gz))

    # 最长的「未推进」连续段（按拍聚合，用真实 ns 差）
    runs = []
    cur = None
    for idx, (d, adv, delta, gz) in enumerate(advance):
        if not adv:
            if cur is None:
                cur = {"n": 0, "span_ns": 0, "gz_all": True, "start_idx": idx}
            cur["n"] += 1
            cur["span_ns"] += d
            cur["gz_all"] = cur["gz_all"] and gz
        else:
            if cur:
                runs.append(cur); cur = None
    if cur:
        runs.append(cur)
    runs.sort(key=lambda r: -r["span_ns"])
    print("  未推进连续段 = %d 个；最长 3 个：" % len(runs))
    for r in runs[:3]:
        print("    拍数=%-5d 真实跨度=%.3f ms  全程四门控为0=%s" % (
            r["n"], r["span_ns"] / 1e6, r["gz_all"]))

    # 推进速率（区间估计，非逐帧）
    if len(ok) >= 2 and isinstance(ok[0].get("t_mono_ns"), int):
        span = (ok[-1]["t_mono_ns"] - ok[0]["t_mono_ns"]) / 1e9
        dframe = ok[-1]["frame"] - ok[0]["frame"]
        print("  区间推进速率: Δframe=%d / 实测 %.3f s = %.3f 计数/s（非逐帧 FPS）" % (
            dframe, span, dframe / span if span > 0 else 0))

    # 失焦期间是否仍推进
    fg = [r for r in recs if "win_foreground" in r]
    if fg:
        nf = [r for r in recs if r.get("win_foreground") is False]
        print("  失焦拍数 = %d" % len(nf))
        if nf:
            # 失焦段内帧是否变化
            frames_nf = [r.get("frame") for r in nf if isinstance(r.get("frame"), int)]
            print("    失焦段内 frame 取值数 = %d，范围 [%s..%s]" % (
                len(set(frames_nf)), min(frames_nf) if frames_nf else None,
                max(frames_nf) if frames_nf else None))

    # remark 分段
    rm = {}
    for r in recs:
        k = str(r.get("remark"))
        rm[k] = rm.get(k, 0) + 1
    print("  remark 分布: %s" % sorted(rm.items(), key=lambda x: -x[1])[:8])


files = sorted(BASE.glob("out/*.ndjson")) + sorted(BASE.glob("out/out/*.ndjson"))
if not files:
    print("未找到 ndjson"); sys.exit(2)
for p in files:
    analyze(p)
print("=" * 96)
print("说明：本脚本只读 ndjson；未启动游戏、未 attach、未读活进程。")
