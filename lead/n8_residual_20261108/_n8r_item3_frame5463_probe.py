# -*- coding: utf-8 -*-
"""N-8 残项收口 · 第 3 项补强：t55k_20261020/w1 帧号 f=5463 及其邻域帧的只读探查。
目的：核实该帧 3 个读数在样本流中的位置语义（分组是否有歧义），不改任何口径。
只读；唯一写域 = 本脚本同目录 _n8r_item3_frame5463_probe_out.txt。
"""
import collections
import io
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
JS = os.path.join(ROOT, "lead", "codex_round_20261030", "XVERIFY_H8_20261031")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


# 定位 t55k_20261020/w1 的 measure JSON（目录名匹配，verdict=ok 且 hz>=100）
import glob

found = None
for p in sorted(glob.glob(os.path.join(ROOT, "lead", "**", "t55k_20261020", "measure_w1.json"),
                          recursive=True)):
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    hz = (d.get("stats") or {}).get("hz_effective")
    if d.get("verdict") == "ok" and hz and hz >= 100:
        found = (p, d)
        break
P("[P] t55k_20261020/w1 文件 = %s" % found[0])
d = found[1]
s = d["samples"]
f, t = s["f"], s["t"]
g = collections.defaultdict(list)
for fi, ti in zip(f, t):
    g[fi].append(ti)
P("    该帧 f=5463 全窗读数 = %d 个：%s" %
  (len(g[5463]), ["%.6f" % x for x in sorted(g[5463])]))

# f 单调性（全窗）：back/jump 计数
back = sum(1 for i in range(1, len(f)) if f[i] < f[i - 1])
jump = sum(1 for i in range(1, len(f)) if f[i] - f[i - 1] > 1)
P("    全窗样本 = %d；f 回退=%d、跳号=%d（0 = 按 f 分组无歧义）" % (len(f), back, jump))

# 邻域帧（按实际存在的帧号，f=5463 前后各 3 个）的读数个数与 span
keys = sorted(g)
pos = keys.index(5463)
nb = keys[max(0, pos - 3):pos + 4]
P("")
P("    f      读数   span(ms)   首/末读数 t(s)")
for fi in nb:
    ts = sorted(g.get(fi, []))
    if not ts:
        P("    %d   (无读数)" % fi)
        continue
    P("    %d   %3d   %8.4f   %.6f / %.6f" %
      (fi, len(ts), (ts[-1] - ts[0]) * 1000.0, ts[0], ts[-1]))

# f=5463 是否为窗内最大帧号（窗尾帧）
P("")
P("    窗内帧号范围 = %d..%d（共 %d 个）；f=5463 是否最大帧号 = %s" %
  (keys[0], keys[-1], len(keys), 5463 == keys[-1]))
P("    全样本末读数 t = %.6f；f=5463 末读数 t = %.6f（两者 %s）" %
  (t[-1], max(g[5463]), "相同" if abs(t[-1] - max(g[5463])) < 1e-9 else "不同"))
P("    窗 stats.span_s = %s；samples 末读数与窗起点差 = %.4f s" %
  (d.get("span_s"), t[-1] - t[0]))

P("")
P("N8R_ITEM3_PROBE DONE")
io.open(os.path.join(HERE, "_n8r_item3_frame5463_probe_out.txt"), "w", encoding="utf-8").write(
    "\n".join(OUT) + "\n")
print("\n".join(OUT))
