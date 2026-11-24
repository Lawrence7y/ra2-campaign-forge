# -*- coding: utf-8 -*-
"""D-19 第 4 条要求的「新增负担量化」——用**既有 87 个 25 s 窗的真实读数**离线算。

只读 `out/re_work/.../qc161_u0400_trip/*/measure_w*.json`。零真机、零采样实现。
输出直接喂 `A2_EDGE_BURDEN.md`。
"""
import glob
import io
import json
import os

GLOB = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/*/measure_w*.json'
FULL_SPAN = 25.0
FRAME_VA_READS = 1     # 既有：每拍 1 次 CurrentFrame 读
NEW_VA = 4             # 候选件每沿追加读 4 个 u32

files = sorted(glob.glob(GLOB))
print("glob:", GLOB)
print("files matched:", len(files))
assert files, "no measure_w*.json found"

rows = []
bad = []
for p in files:
    try:
        d = json.load(io.open(p, encoding='utf-8'))
    except Exception as exc:
        bad.append((p, repr(exc)))
        continue
    st = d.get('stats') or {}
    rows.append({
        "path": p,
        "trip": d.get('trip_id'),
        "window": d.get('window'),
        "span_s": d.get('span_s'),
        "verdict": d.get('verdict'),
        "samples": st.get('samples'),
        "hz_eff": st.get('hz_effective'),
        "n_edges": st.get('n_edges'),
        "n_multi": st.get('n_multi_advance'),
        "logic": st.get('logic_frames'),
        "p50": st.get('frame_ms_p50'),
        "max_stall": st.get('max_stall_s'),
    })

print("parsed:", len(rows), " parse_errors:", len(bad))
for p, e in bad[:5]:
    print("  ERR", p, e)

full = [r for r in rows if r.get("span_s") == FULL_SPAN and (r.get("samples") or 0) > 0]
print("full 25s windows with samples:", len(full))

# ---------------- 1) 沿数分布 ----------------
edges = sorted(r["n_edges"] for r in full)
print("\n=== 1. 帧沿数分布（87 个 25 s 窗）===")
for q in (0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0):
    idx = min(len(edges) - 1, int(len(edges) * q))
    print("  p%-3d = %d" % (int(q * 100), edges[idx]))

# ---------------- 2) df>1（漏沿）真实发生率 ----------------
multi = [r for r in full if (r.get("n_multi") or 0) > 0]
tot_e = sum(r["n_edges"] for r in full)
tot_m = sum((r.get("n_multi") or 0) for r in full)
print("\n=== 2. df>1 漏沿的真实发生率 ===")
print("  windows with n_multi>0 : %d / %d" % (len(multi), len(full)))
print("  total edges=%d  total multi=%d  rate=%.5f%%" % (tot_e, tot_m, 100.0 * tot_m / max(1, tot_e)))
for r in multi:
    print("    %s w%s edges=%d multi=%d p50=%s" %
          (r["trip"], r["window"], r["n_edges"], r["n_multi"],
           None if r["p50"] is None else round(r["p50"], 2)))

# ---------------- 3) 追加读取负担 ----------------
tot_s = sum(r["samples"] for r in full)
print("\n=== 3. 每沿 +%d 次读的负担（按真实沿数）===" % NEW_VA)
print("  既有读次合计（samples）= %d" % tot_s)
print("  追加读次合计 = %d × %d = %d" % (NEW_VA, tot_e, NEW_VA * tot_e))
print("  相对增幅 = +%.3f%%" % (100.0 * NEW_VA * tot_e / max(1, tot_s)))
worst = max(full, key=lambda r: r["n_edges"])
best = min(full, key=lambda r: r["n_edges"])
print("  最坏单窗：%s w%s edges=%d samples=%d → +%d 读 = +%.2f%%" %
      (worst["trip"], worst["window"], worst["n_edges"], worst["samples"],
       NEW_VA * worst["n_edges"],
       100.0 * NEW_VA * worst["n_edges"] / max(1, worst["samples"])))
print("  最省单窗：%s w%s edges=%d → +%d 读" %
      (best["trip"], best["window"], best["n_edges"], NEW_VA * best["n_edges"]))

# ---------------- 4) 字节与速率 ----------------
print("\n=== 4. 字节与每秒速率 ===")
print("  每沿 4 VA × u32 = %d 字节" % (16))
print("  最坏单窗字节 = %d B / 25 s = %.1f B/s" %
      (16 * worst["n_edges"], 16 * worst["n_edges"] / FULL_SPAN))
print("  87 窗合计字节 = %d B" % (16 * tot_e))
print("  最坏窗额外读速率 = %.1f reads/s" % (NEW_VA * worst["n_edges"] / FULL_SPAN))

# ---------------- 5) 帧沿档的真实频次（=当前帧率） ----------------
eff = sorted(1000.0 / r["p50"] for r in full if r["p50"])
print("\n=== 5. 帧沿档真实触发频次（=1000/p50）===")
if eff:
    for q in (0.0, 0.10, 0.50, 0.90, 1.0):
        idx = min(len(eff) - 1, int(len(eff) * q))
        print("  p%-3d = %.2f Hz" % (int(q * 100), eff[idx]))
    print("  ⇒ 「帧沿档频次自适应于帧率」在 87 窗上成立：慢窗 %.1f Hz / 快窗 %.1f Hz"
          % (eff[0], eff[-1]))

# ---------------- 6) 冻结窗：帧沿档**完全无样本** ----------------
zero = [r for r in full if (r.get("logic") or 0) <= 0]
print("\n=== 6. ★ 帧沿档的结构性盲区：冻结窗 ===")
print("  logic_frames<=0 的窗（帧号整窗不动）= %d / %d" % (len(zero), len(full)))
print("  这些窗 n_edges 的取值集合 = %s" %
      sorted(set(r["n_edges"] for r in zero)))
print("  这些窗 max_stall_s 取值集合（前 8）= %s" %
      sorted(set(round(r["max_stall"] or 0, 3) for r in zero))[:8])
print("  ⇒ 帧号冻结时 **一次沿都不会触发**，四 VA **一个样本都拿不到**；")
print("     这不是缺陷（冻结窗本就不是目标），但必须在卡片里明写：")
print("     「帧沿档在冻结窗零样本，不能据此说该窗的 C1–C4 为零成本」。")

# ---------------- 7) 一致性自查 ----------------
print("\n=== 7. 一致性自查：n_edges 与 logic_frames 的关系 ===")
mism = [(r["trip"], r["window"], r["n_edges"], r["logic"])
        for r in full if (r.get("logic") or 0) > 0
        and abs((r["n_edges"] - 1) - r["logic"]) > (r.get("n_multi") or 0) + 1]
print("  n_edges ≠ logic+1（超出 multi 容差）的窗数 = %d" % len(mism))
for t in mism[:8]:
    print("    %s w%s edges=%s logic=%s" % t)
by_multi = {}
for r in full:
    if (r.get("logic") or 0) > 0:
        key = r["n_edges"] - r["logic"]
        by_multi[key] = by_multi.get(key, 0) + 1
print("  (n_edges - logic_frames) 的分布 = %s" % sorted(by_multi.items()))
print("\nDONE")
