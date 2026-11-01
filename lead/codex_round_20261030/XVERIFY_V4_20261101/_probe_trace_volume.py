# -*- coding: utf-8 -*-
"""XVERIFY_V4 探针 2：h8_wait_trace.json 体积/性能/t_rel 精度评估。
- 60k 样本（500Hz×120s 上限）代表形 JSON 序列化体积实测
- json.dumps / write_text / 回读解析耗时实测
- 逐拍 append 开销实测（对照 _doze 2ms 周期）
- t_rel 4 位小数精度对切换定位的分辨力推演（§500 切换 ≤1s / 停滞段 175-250ms / 31fps 帧长 32ms）
python -I -B -X utf8 本文件。
"""
import json
import sys
import tempfile
import time
from pathlib import Path

FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


N = 60000  # 500Hz × 120s 上限（批卡口径）
# 代表形：t_rel 单调步进 ~2ms（500Hz 名义，C-R3 实测 284-347Hz 只会更稀疏），
# frame 0→800 内随机推进+停滞段（滞态）混排——两态都入样。
samples = []
f = 0
t = 0.0
i = 0
while i < N:
    if (i // 500) % 2 == 0:      # 滞态段：frame 不动（停滞），2ms 一拍
        step = 0.002
    else:                        # 快态段：~31fps ⇒ 32ms 帧沿，+1 帧
        step = 0.032
    samples.append([round(t, 4), f])
    t += step
    if (i // 500) % 2 == 1:
        f += 1
    i += 1
check("V1 样本条数 = 60000", len(samples) == N, len(samples))
check("V2 含滞态/快态两形态", any(s[1] == 0 for s in samples[:500]) and any(s[1] > 0 for s in samples[-500:]))

payload = {"n": 800, "verdict": "ok", "wait_s": round(t, 3), "samples": samples}
t0 = time.perf_counter()
s = json.dumps(payload, ensure_ascii=False)
t_dump = time.perf_counter() - t0
size = len(s.encode("utf-8"))
print("序列化耗时 = %.1f ms；UTF-8 体积 = %d B = %.2f MB（每样本均 %0.1f B）"
      % (t_dump * 1e3, size, size / 1048576, size / N))

d = Path(tempfile.mkdtemp(prefix="xv4vol_"))
p = d / "h8_wait_trace.json"
t0 = time.perf_counter()
p.write_text(s, encoding="utf-8")
t_write = time.perf_counter() - t0
t0 = time.perf_counter()
j = json.loads(p.read_text(encoding="utf-8"))
t_parse = time.perf_counter() - t0
t0 = time.perf_counter()
p.write_text(s, encoding="utf-8")
t_write2 = time.perf_counter() - t0
disk = p.stat().st_size
print("write_text = %.1f ms / 回读解析 = %.1f ms / 二次写 = %.1f ms；盘上 %d B"
      % (t_write * 1e3, t_parse * 1e3, t_write2 * 1e3, disk))

# C-R3 实测 284-347Hz ⇒ 样本更稀疏的等价量级（34-41k 条）
sparse = [[round(i / 347.0, 4), i % 900] for i in range(34110)]
s2 = json.dumps({"n": 800, "verdict": "ok", "wait_s": 98.3, "samples": sparse},
                ensure_ascii=False)
print("C-R3 实测率 347Hz×98s ≈ %d 条 ⇒ %d B = %.2f MB"
      % (len(sparse), len(s2.encode()), len(s2.encode()) / 1048576))

check("V3 60k 上限体积在 ~1-1.5MB 量级（批卡 ~1.2MB 主张量级成立）",
      0.9e6 <= size <= 1.6e6, "%.2f MB" % (size / 1048576))
check("V4 单次序列化 <100ms（等待退出路径一次性开销，不逐拍）", t_dump < 0.1, "%.1fms" % (t_dump * 1e3))
check("V5 单次写盘 <500ms（一次性）", t_write < 0.5, "%.1fms" % (t_write * 1e3))

# 逐拍 append 开销（对照 500Hz 拍距 2ms）
t0 = time.perf_counter()
lst = []
pc = time.perf_counter
for k in range(N):
    lst.append([round(pc() - t0, 4), k])
t_app = time.perf_counter() - t0
per_poll_us = t_app / N * 1e6
print("逐拍 append（含 perf_counter+round+建表）=%d 拍共 %.1f ms ⇒ %.2f µs/拍"
      % (N, t_app * 1e3, per_poll_us))
check("V6 逐拍开销 < 1% 拍距（500Hz 拍距 2ms）", per_poll_us < 20, "%.2fµs" % per_poll_us)

# t_rel 4 位小数分辨力推演
res = 0.05e-3   # 4 位小数最大舍入误差 5e-5 s
check("V7 4 位小数舍入误差 ≤0.05ms ≪ 拍距 2ms（相对 2.5%）", res * 1000 <= 0.05)
check("V8 拍距 2ms ≪ §500 停滞段 175-250ms（每段 87-125 拍）", 0.002 * 87 <= 0.175)
check("V9 拍距 2ms < 31fps 帧长 ≈32ms（帧沿单帧可辨）", 0.002 < 0.032)
check("V10 拍距 2ms ≪ §500 切换锐度 ≤1s（切换跨 ~500 拍，定位裕量 500×）", 1.0 / 0.002 >= 500)
check("V11 50Hz 旋钮（拍距 20ms）仍 < 32ms 帧长（对照趟也不丢帧沿）", 0.02 < 0.032)

print()
print("FAILS =", FAILS)
sys.exit(0 if not FAILS else 1)
