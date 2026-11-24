# -*- coding: utf-8 -*-
"""独立复核员 · 第5项三读法自写复算（不复用 _n8r_item5_7maps.py / _n8_variants*）。

直接从 _w2_matrix.tsv 原始字节解析：
  - 87 数据行 / p50 有效行 / None 行
  - distinct map（9?）/ 慢图排除集 {f3bb0a4e,0add791d} 后其余 7 图
  - R3 图中位读法：每图 p50 中位 → 全图 min/max/极差
  - R2 窗级读法：7 图全部有效 p50 行 → min/max/极差
  - R4 w0-only 读法：仅 window==w0 的有效行 → min/max/极差
  - R1 台账 :6020 端点 31.64/32.38 的来源核对
  - 补充：图最大/图最小读法（检验"自然口径族中唯一复现"是否成立）
  - 补充：7 稳定图非 w0 行明细（archive_T38/w1 定位）
只读；唯一写 = 本目录 _verify_B_out.txt。
"""
import hashlib
import io
import os
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
MTSV = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_matrix.tsv")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


b = open(MTSV, "rb").read()
P("[H] _w2_matrix.tsv SHA256=%s 字节数=%d" % (hashlib.sha256(b).hexdigest(), len(b)))
txt = b.decode("utf-8")
# 自写解析：按 \n 切、去 \r、去尾部空行
rows_raw = [ln.rstrip("\r") for ln in txt.split("\n")]
while rows_raw and rows_raw[-1] == "":
    rows_raw.pop()
hdr = rows_raw[0].split("\t")
P("[H] 表头 = %s" % hdr)
col = {name: i for i, name in enumerate(hdr)}
data = [ln.split("\t") for ln in rows_raw[1:]]
P("[D] 数据行=%d  distinct trip=%d" % (len(data), len({r[col["trip"]] for r in data})))


def is_valid(r):
    v = r[col["frame_ms_p50"]].strip()
    return v not in ("", "None")


valid = [r for r in data if is_valid(r)]
none_rows = [r for r in data if not is_valid(r)]
P("[D] p50 有效行=%d  None 行=%d  distinct map(全部)=%d" %
  (len(valid), len(none_rows), len({r[col["map_sha8"]] for r in data})))

# 按 map 聚合有效行
bymap = {}
for r in valid:
    bymap.setdefault(r[col["map_sha8"]], []).append(r)

SLOW = {"f3bb0a4e", "0add791d"}
stable = {m: v for m, v in bymap.items() if m not in SLOW}
P("[S] 慢图排除=%s；其余图数=%d；其有效行数=%d" %
  (sorted(SLOW), len(stable), sum(len(v) for v in stable.values())))
P("    各稳定图有效行数：%s" % {m: len(v) for m, v in sorted(stable.items())})

# ---------- R3 图中位读法 ----------
P("")
P("[R3] 图中位读法：每图 p50 中位")
meds = {}
for m in sorted(stable):
    vs = [float(r[col["frame_ms_p50"]]) for r in stable[m]]
    meds[m] = statistics.median(vs)
    P("    %s n=%d 中位=%.4f 行min=%.4f 行max=%.4f" %
      (m, len(vs), meds[m], min(vs), max(vs)))
r3min, r3max = min(meds.values()), max(meds.values())
P("    → 区间 = %.4f–%.4f ms，极差 = %.4f ms" % (r3min, r3max, r3max - r3min))

# ---------- R2 窗级读法 ----------
P("")
P("[R2] 窗级读法：7 稳定图全部有效行")
allv = []
for m, vv in stable.items():
    for r in vv:
        allv.append((float(r[col["frame_ms_p50"]]), r[col["trip"]], r[col["window"]], m, r))
r2min, r2max = min(allv), max(allv)
P("    行数=%d → 区间 = %.4f–%.4f ms，极差 = %.4f ms" %
  (len(allv), r2min[0], r2max[0], r2max[0] - r2min[0]))
P("    min 行 = %s/%s (%s) p50=%.4f" % (r2min[1], r2min[2], r2min[3], r2min[0]))
P("    max 行 = %s/%s (%s) p50=%.4f" % (r2max[1], r2max[2], r2max[3], r2max[0]))

# ---------- R4 w0-only ----------
P("")
P("[R4] w0-only 读法：仅 window==w0 的有效行")
w0v = [x for x in allv if x[2] == "w0"]
w4min, w4max = min(w0v), max(w0v)
P("    行数=%d → 区间 = %.4f–%.4f ms，极差 = %.4f ms" %
  (len(w0v), w4min[0], w4max[0], w4max[0] - w4min[0]))
P("    min 行 = %s/%s (%s) p50=%.4f" % (w4min[1], w4min[2], w4min[3], w4min[0]))
P("    max 行 = %s/%s (%s) p50=%.4f" % (w4max[1], w4max[2], w4max[3], w4max[0]))

# ---------- 额外：图最大 / 图最小读法（检验"唯一复现"） ----------
P("")
P("[RX] 补充读法（检验「自然口径族中唯一复现」的强断言）")
mapmax = {m: max(float(r[col["frame_ms_p50"]]) for r in vv) for m, vv in stable.items()}
mapmin = {m: min(float(r[col["frame_ms_p50"]]) for r in vv) for m, vv in stable.items()}
P("    图最大读法：区间 = %.4f–%.4f 极差=%.4f" %
  (min(mapmax.values()), max(mapmax.values()), max(mapmax.values()) - min(mapmax.values())))
P("    图最小读法：区间 = %.4f–%.4f 极差=%.4f" %
  (min(mapmin.values()), max(mapmin.values()), max(mapmin.values()) - min(mapmin.values())))

# ---------- R1 台账端点来源 ----------
P("")
P("[R1] 台账 :6020 端点 31.64–32.38（端点差=0.74）来源核对")
P("    下端点 31.64 ←→ min=%.4f round2=%.2f → %s" %
  (r2min[0], round(r2min[0], 2), "吻合" if round(r2min[0], 2) == 31.64 else "不吻合"))
P("    上端点 32.38 逐读法 round2：")
for label, val in [("R2 窗级", r2max[0]), ("R3 图中位", r3max),
                    ("R4 w0-only", w4max[0]), ("图最大", max(mapmax.values())),
                    ("图最小", max(mapmin.values()))]:
    P("      %-12s max=%.4f round2=%.2f → %s" %
      (label, val, round(val, 2), "吻合" if round(val, 2) == 32.38 else "不吻合"))

# ---------- 非 w0 行明细 ----------
P("")
P("[X] 7 稳定图中非 w0 有效行（R4 排除项）")
for x in sorted([y for y in allv if y[2] != "w0"]):
    r = x[4]
    P("    %s/%s (%s) p50=%.4f fps_avg=%s logic_frames=%s max_stall_s=%s" %
      (x[1], x[2], x[3], x[0], r[col["fps_avg"]], r[col["logic_frames"]], r[col["max_stall_s"]]))

# ---------- 定性 ----------
P("")
P("[Q] 「极差<1ms」定性：R3=%.4f R2=%.4f R4=%.4f 是否全<1 = %s" %
  (r3max - r3min, r2max[0] - r2min[0], w4max[0] - w4min[0],
   all(x < 1 for x in [r3max - r3min, r2max[0] - r2min[0], w4max[0] - w4min[0]])))
P("    台账端点差 32.38-31.64 = %.2f" % (32.38 - 31.64))

P("")
P("VERIFY_B DONE")
with io.open(os.path.join(HERE, "_verify_B_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\n".join(OUT))
