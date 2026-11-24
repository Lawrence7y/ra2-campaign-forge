# -*- coding: utf-8 -*-
"""独立复核员 · ③/⑤ 深核（自写，不复用分析员代码）。

[C] 检验「属口径选择」是否回避了本可算的量：
   语料中存在原始 W2 生成件（_w2_probe.py:264-291 / W2_FRAMETIME_ATTRIB.md:197,290,502
   / _w2_probe_out.txt:177-187），明确记载台账 :6020/:6040 的口径为「7 图跨 21 趟 / 各趟中位」。
   自写复算该「每趟中位」读法，检验是否也精确复现 31.64–32.38，从而核对回件
   「在自然口径族中唯一精确复现的是 w0-only」以及「端点数值来自 w0-only 行集」的强断言。
[D] ⑤ 纪律：15 合格窗 JSON 指纹核对、保护区 mtime、禁词扫描、commit/push 由外部 git 命令核。
只读；唯一写 = 本目录 _verify_C_out.txt。
"""
import collections
import hashlib
import io
import json
import os
import re
import glob
import statistics

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
MTSV = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_matrix.tsv")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


lines = [ln.rstrip("\r") for ln in io.open(MTSV, encoding="utf-8").read().split("\n")]
while lines and lines[-1] == "":
    lines.pop()
hdr = lines[0].split("\t")
c = {n: i for i, n in enumerate(hdr)}
data = [ln.split("\t") for ln in lines[1:]]
valid = [r for r in data if r[c["frame_ms_p50"]].strip() not in ("", "None")]
SLOW = {"f3bb0a4e", "0add791d"}
stable_rows = [r for r in valid if r[c["map_sha8"]] not in SLOW]

P("=" * 78)
P("[C1] 原始 W2 生成件所记载的口径（文件:行）")
P("=" * 78)
w2md = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "W2_FRAMETIME_ATTRIB.md")
w2out = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_probe_out.txt")
w2py = os.path.join(ROOT, "lead", "re_line_20261105", "W2_FRAMETIME_ATTRIB", "_w2_probe.py")
for path, nums in [(w2md, [197, 290, 344, 347]), (w2out, [177, 180, 184]),
                   (w2py, [280, 287, 288, 289, 327, 502])]:
    L = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    P("  %s（共 %d 行）" % (os.path.basename(path), len(L)))
    for n in nums:
        P("    :%d  %s" % (n, L[n - 1][:150]))
goal = os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md")
GL = io.open(goal, encoding="utf-8").read().split("\n")
for n in [6020, 6040]:
    P("  GOAL:%d  %s" % (n, GL[n - 1]))

# ---------- 每趟中位读法（21 趟） ----------
P("")
P("[C2] 自写复算「每趟中位」读法（语料文档口径：7 稳定图跨 21 趟）")
bytrip = collections.defaultdict(list)
bytrip_map = {}
for r in stable_rows:
    bytrip[r[c["trip"]]].append(float(r[c["frame_ms_p50"]]))
    bytrip_map[r[c["trip"]]] = r[c["map_sha8"]]
P("    7 稳定图有效行=%d  distinct trip（趟）=%d" % (len(stable_rows), len(bytrip)))
trip_med = {tr: statistics.median(v) for tr, v in bytrip.items()}
P("    逐趟中位（前 6）：")
for tr in sorted(trip_med)[:6]:
    P("      %-24s (%s) n=%d 中位=%.4f" % (tr, bytrip_map[tr], len(bytrip[tr]), trip_med[tr]))
tmin = min(trip_med.items(), key=lambda x: x[1])
tmax = max(trip_med.items(), key=lambda x: x[1])
P("    → 区间 = %.4f–%.4f ms（min@%s(%s)  max@%s(%s)），极差 = %.4f ms" %
  (tmin[1], tmax[1], tmin[0], bytrip_map[tmin[0]], tmax[0], bytrip_map[tmax[0]],
   tmax[1] - tmin[1]))
P("    round2 = %.2f–%.2f → 与台账 31.64–32.38 %s" %
  (round(tmin[1], 2), round(tmax[1], 2),
   "吻合" if (round(tmin[1], 2), round(tmax[1], 2)) == (31.64, 32.38) else "不吻合"))
P("    该读法极差 %.4f < 1ms = %s" % (tmax[1] - tmin[1], tmax[1] - tmin[1] < 1))

# 每趟中位 vs w0-only：哪些趟不同
w0 = collections.defaultdict(list)
for r in stable_rows:
    if r[c["window"]] == "w0":
        w0[r[c["trip"]]].append(float(r[c["frame_ms_p50"]]))
diff = [(tr, len(bytrip[tr]), trip_med[tr], w0[tr][0] if w0[tr] else None)
        for tr in bytrip if len(bytrip[tr]) > 1]
P("    多有效窗的趟（每趟中位与 w0 值不同的趟）= %d：" % len(diff))
for tr, n, med, w0v in diff:
    P("      %-24s n=%d 每趟中位=%.4f w0=%.4f" % (tr, n, med, w0v))

# ---------- 复现者计数（6 读法） ----------
P("")
P("[C3] 「唯一精确复现」检验：扩展读法族对台账上端点 32.38 的 round2")
bymap = collections.defaultdict(list)
for r in stable_rows:
    bymap[r[c["map_sha8"]]].append(float(r[c["frame_ms_p50"]]))
allv = [float(r[c["frame_ms_p50"]]) for r in stable_rows]
w0v = [float(r[c["frame_ms_p50"]]) for r in stable_rows if r[c["window"]] == "w0"]
readings = [
    ("R2 窗级(19行)", max(allv)),
    ("R3 图中位(7值)", max(statistics.median(v) for v in bymap.values())),
    ("R4 w0-only(15行)", max(w0v)),
    ("图最大(7值)", max(max(v) for v in bymap.values())),
    ("图最小(7值)", max(min(v) for v in bymap.values())),
    ("每趟中位(21趟)", max(trip_med.values())),
]
hit = 0
for name, mx in readings:
    ok = round(mx, 2) == 32.38
    hit += ok
    P("    %-20s max=%.4f round2=%.2f → %s" % (name, mx, round(mx, 2), "吻合" if ok else "不吻合"))
P("    复现 32.38 的读法数 = %d（其中「每趟中位」为语料明文记载的 21 趟口径）" % hit)
P("    ⇒ 回件「在自然口径族中唯一精确复现」若指其自定义的 5 读法则成立；")
P("      若把语料明文记载的「21 趟每趟中位」计入自然口径族，则 w0-only 非唯一。")

# ============================================================ [D] 纪律
P("")
P("=" * 78)
P("[D] ⑤ 纪律核对")
P("=" * 78)
# D1: 15 合格窗 JSON 指纹与回件 [H] 段逐件比对
hsec = []
L = io.open(os.path.join(HERE, "_n8r_item3_ratiomax_out.txt"), encoding="utf-8").read().splitlines()
in_h = False
for ln in L:
    if ln.startswith("[H]"):
        in_h = True
        continue
    if in_h:
        m = re.match(r"\s*([0-9a-f]{64})\s+bytes=(\d+)", ln)
        if m:
            hsec.append((m.group(1), int(m.group(2))))
        elif ln.strip() == "" or ln.startswith("N8R"):
            if hsec:
                break
qual = []
for p in sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True)):
    d = json.load(io.open(p, encoding="utf-8"))
    hz = (d.get("stats") or {}).get("hz_effective")
    if d.get("verdict") == "ok" and isinstance(hz, (int, float)) and hz >= 100:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        qual.append((h, os.path.getsize(p)))
P("[D1] 回件 [H] 段指纹数=%d；本机 15 合格窗实算指纹数=%d；集合相同=%s" %
  (len(hsec), len(qual), sorted(hsec) == sorted(qual)))

# D2: 保护区 mtime（全部须早于写域创建 18:01）
P("[D2] 保护区 mtime（写域最早 18:01；以下须更早）：")
import time
for rel in [
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/PENDING_DECISIONS.md",
    "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md",
    "lead/re_line_20261105/W2_FRAMETIME_ATTRIB/_w2_matrix.tsv",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/slowwindow_n8_20261108/_n8_recompute.py",
    "lead/slowwindow_n8_20261108/_verify_recompute_out.txt",
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
    "lead/t55k_20261020/measure_w1.json",
]:
    st = os.stat(os.path.join(ROOT, rel))
    P("    %s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), rel))

# D3: 零真机 / 零采样代码禁词扫描（9 件交付物）
P("[D3] 9 件交付物禁词扫描（真机启动/采样注入/动态解析）：")
bad = re.compile(r"gamemd\.exe|ra2loader|YURI\.exe|taskkill|MiniDump|SuspendThread|StackWalk|"
                 r"OpenProcess|ReadProcessMemory|ctypes|WriteProcessMemory|VirtualAlloc|"
                 r"CreateRemoteThread|SetWindowsHook|hook\s*=|注入探针")
for f in sorted(os.listdir(HERE)):
    if not f.startswith("_n8r_"):
        continue
    hits = [(i, l.strip()[:90]) for i, l in
            enumerate(io.open(os.path.join(HERE, f), encoding="utf-8", errors="replace").read().splitlines(), 1)
            if bad.search(l)]
    P("    %s → %d 命中" % (f, len(hits)))
    for i, l in hits:
        P("        :%d %s" % (i, l))

# D4: 因果归因 / 恢复已撤回断言 扫描（9 件交付物）
P("[D4] 9 件交付物因果归因/撤回断言扫描：")
pat = re.compile(r"慢窗更均匀|慢窗空档更小|恢复.{0,6}均匀慢|放行性能修复|CAUSAL_READY|"
                 r"斩死宿主降频|根因|因果解释力.{0,6}(成立|确认|证实)|定谳.{0,6}(C1|C2|C3|C4)")
for f in sorted(os.listdir(HERE)):
    if not f.startswith("_n8r_"):
        continue
    hits = [(i, l.strip()[:100]) for i, l in
            enumerate(io.open(os.path.join(HERE, f), encoding="utf-8", errors="replace").read().splitlines(), 1)
            if pat.search(l)]
    P("    %s → %d 命中" % (f, len(hits)))
    for i, l in hits:
        P("        :%d %s" % (i, l))
P("    注：第4项标题含「因果解释力」但句式均为「本任务不评/维持未验/不在可评范围」（否定式，非归因）。")

P("")
P("VERIFY_C DONE")
with io.open(os.path.join(HERE, "_verify_C_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\n".join(OUT))
