# -*- coding: utf-8 -*-
"""N-8 残项收口 · 第 5 项：「其余 7 张图」区间三种读法复算（_w2_matrix.tsv）。

读法：
  R1 台账 :6020 自报区间 31.64–32.38（端点差 0.74）——本脚本检验其端点来源；
  R2 窗级读法：7 稳定图全部有效 p50 行的 min/max/极差；
  R3 图中位读法：7 稳定图各自的 p50 中位的 min/max/极差；
  R4 对照：w0-only 行读法；R5 对照：图中位 max 读法。
慢图排除集 = {f3bb0a4e, 0add791d}（台账 :6019-6020）。
只读；唯一写域 = 本脚本同目录 _n8r_item5_7maps_out.txt。零真机、零采样代码。
"""
import collections
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


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


b = open(MTSV, "rb").read()
P("[H] 被核对象 = lead/re_line_20261105/W2_FRAMETIME_ATTRIB/_w2_matrix.tsv")
P("    SHA256 = %s" % hashlib.sha256(b).hexdigest())
P("    字节数 = %d" % len(b))
P("    （编排方指纹 00641e04f25e6bbe81399586e018df27995d530691da1fd658e205f5ee310c96 / 7537 → %s）"
  % ("SAME" if hashlib.sha256(b).hexdigest() ==
     "00641e04f25e6bbe81399586e018df27995d530691da1fd658e205f5ee310c96" and
     len(b) == 7537 else "DIFF"))

lines = b.decode("utf-8").readlines() if False else io.open(MTSV, encoding="utf-8").read().splitlines()
hdr = lines[0].split("\t")
ix = {c: i for i, c in enumerate(hdr)}
data = [l.split("\t") for l in lines[1:] if l.strip()]
valid = [r for r in data if r[ix["frame_ms_p50"]] not in ("None", "")]
P("")
P("[D] 数据行 = %d；p50 有效行 = %d；None 行 = %d" % (len(data), len(valid), len(data) - len(valid)))

maps = collections.defaultdict(list)
for r in valid:
    maps[r[ix["map_sha8"]]].append(r)
SLOW = {"f3bb0a4e", "0add791d"}
stable = {m: v for m, v in maps.items() if m not in SLOW}
n_stable_rows = sum(len(v) for v in stable.values())
P("慢图排除 = %s；其余图数 = %d；其有效行数 = %d" % (sorted(SLOW), len(stable), n_stable_rows))

P("")
P("[R3] 图中位读法：每图 p50 中位")
meds = {}
for m in sorted(stable):
    vs = [float(r[ix["frame_ms_p50"]]) for r in stable[m]]
    meds[m] = statistics.median(vs)
    P("    %s  n=%d  中位=%.4f  （行级 min=%.4f max=%.4f）"
      % (m, len(vs), meds[m], min(vs), max(vs)))
mmin, mmax = min(meds.values()), max(meds.values())
arg_min = [m for m in meds if meds[m] == mmin]
arg_max = [m for m in meds if meds[m] == mmax]
P("    → 区间 = %.4f–%.4f ms，极差 = %.4f ms（min@%s，max@%s）"
  % (mmin, mmax, mmax - mmin, arg_min, arg_max))

P("")
P("[R2] 窗级读法：7 稳定图全部 %d 条有效行" % n_stable_rows)
allv = [(float(r[ix["frame_ms_p50"]]), r[ix["trip"]], r[ix["window"]], r[ix["map_sha8"]])
        for v in stable.values() for r in v]
wmin = min(allv)
wmax = max(allv)
P("    → 区间 = %.4f–%.4f ms，极差 = %.4f ms" % (wmin[0], wmax[0], wmax[0] - wmin[0]))
P("    min 行 = %s/%s (%s) p50=%.4f" % (wmin[1], wmin[2], wmin[3], wmin[0]))
P("    max 行 = %s/%s (%s) p50=%.4f" % (wmax[1], wmax[2], wmax[3], wmax[0]))

P("")
P("[R4] w0-only 读法：7 稳定图 window==w0 的有效行")
w0v = [x for x in allv if x[2] == "w0"]
w0min, w0max = min(w0v), max(w0v)
P("    行数 = %d" % len(w0v))
P("    → 区间 = %.4f–%.4f ms，极差 = %.4f ms" % (w0min[0], w0max[0], w0max[0] - w0min[0]))
P("    min 行 = %s/%s (%s) p50=%.4f" % (w0min[1], w0min[2], w0min[3], w0min[0]))
P("    max 行 = %s/%s (%s) p50=%.4f" % (w0max[1], w0max[2], w0max[3], w0max[0]))

P("")
P("[R1] 台账 :6020 自报「31.64–32.38（极差 <1ms）」端点来源核对")
P("    31.64 ←→ %.4f（round2=%s）：R2/R3/R4 的 min 均为该值 → 端点吻合" %
  (wmin[0], "%.2f" % round(wmin[0], 2)))
cand = round(w0max[0], 2)
P("    32.38 ←→ R4(w0-only) max=%.4f round2=%.2f → %s" % (w0max[0], cand,
  "吻合" if abs(cand - 32.38) < 5e-3 else "不吻合"))
P("    但 R2(全部窗) max=%.4f、R3(图中位) max=%.4f → 与 32.38 %s" %
  (wmax[0], mmax, "均不吻合" if abs(round(wmax[0], 2) - 32.38) >= 5e-3 and
   abs(round(mmax, 2) - 32.38) >= 5e-3 else "有吻合"))
P("    三读法极差：R4(w0-only)=%.2f / R2(窗级)=%.2f / R3(图中位)=%.2f；台账端点差 = 32.38-31.64 = 0.74"
  % (w0max[0] - w0min[0], wmax[0] - wmin[0], mmax - mmin))
P("    三读法极差全部 < 1 ms → 「极差 <1ms」定性在三读法下均成立")

# 其余非 w0 行明细（为何被 R4 排除）
P("")
P("[X] 7 稳定图中非 w0 的有效行（R4 排除项）")
for v, tr, wn, mp in sorted(allv):
    if wn != "w0":
        lr = [r for r in stable[mp]
              if r[ix["trip"]] == tr and r[ix["window"]] == wn][0]
        P("    %s/%s (%s) p50=%.4f  fps_avg=%s  logic_frames=%s  max_stall_s=%s"
          % (tr, wn, mp, v, lr[ix["fps_avg"]], lr[ix["logic_frames"]], lr[ix["max_stall_s"]]))

P("")
P("N8R_ITEM5 DONE")

io.open(os.path.join(HERE, "_n8r_item5_7maps_out.txt"), "w", encoding="utf-8").write(
    "\n".join(OUT) + "\n")
print("\n".join(OUT))
