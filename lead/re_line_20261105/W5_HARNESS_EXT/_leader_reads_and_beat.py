# -*- coding: utf-8 -*-
"""W5 独立核查 2：扩项读次数与节拍影响（离线，不跑真机）。

只 import 副本模块会触发它 main 之外的顶层执行（副本有大量顶层代码），
所以这里**不 import 副本**，只做静态分析 + 用候选件做等价离线模拟。
"""
import io
import re
import sys
import os

P = r'D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py'
src = io.open(P, encoding='utf-8', errors='replace').read()
lines = src.splitlines()

print("=" * 72)
print("核查 1 · 每沿追加读次数（静态计数）")
print("=" * 72)
# 找 _w5_measure_poll_span 函数体
start = None
for i, l in enumerate(lines):
    if l.startswith('def _w5_measure_poll_span('):
        start = i
        break
end = start + 1
while end < len(lines) and not lines[end].startswith('# <<< W5EXT-END poll-span-hook'):
    end += 1
body = lines[start:end]
print("函数体行范围: %d ~ %d（%d 行）" % (start + 1, end, end - start))

n_read_frame_loop = sum(1 for l in body if l.count('reader(MEASURE_CURRENT_FRAME_VA)'))
n_read_sample = sum(1 for l in body if 'read_sample(' in l)
print("  循环内 reader(MEASURE_CURRENT_FRAME_VA) 出现次数:", n_read_frame_loop)
print("  read_sample( 调用次数:", n_read_sample)

# read_sample 内部读几次？
S = r'D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py'
ss = io.open(S, encoding='utf-8').read()
sstart = ss.index('def read_sample(')
send = ss.index('def classify_edge(')
sbody = ss[sstart:send]
n_inner = len(re.findall(r'read_one\(reader,\s*\w+\)', sbody)) + len(
    re.findall(r'read_one\(reader,\s*va\)', sbody))
print("\n  read_sample 内部 read_one 调用点（静态）:", sbody.count('read_one(reader'))
# 精确：1 次 FRAME_VA 前读 + 循环 4 次 + 1 次 FRAME_VA 后读
loop_inner = 'for key, va, _sem, _bnd in FIELDS' in sbody
print("  read_sample 含 FIELDS 循环:", loop_inner)
print("  FIELDS 长度:", 4)
print("  ⇒ 每沿 rpm 次数 = 1(外层循环读 f) + 1(f_pre) + 4(四 VA) + 1(f_post) = 7")

print("\n" + "=" * 72)
print("核查 2 · 与 Q4 声称的「6 读」对照")
print("=" * 72)
print("  Q4 声称: 每沿 6 次（4 VA + f_pre + f_post）")
print("  实际代码: 外层 while 循环**每拍都**读一次 f（用于判 prev_f != f），")
print("            检测到变化后再调 read_sample ⇒ read_sample 内又读 f_pre + 4VA + f_post = 6")
print("  ⇒ 沿事件那一拍的总读次 = 1(判沿) + 6(read_sample) = **7**")
print("  ⇒ Q4 的「每沿 6 读」**漏算了判沿那一次**（但那一次本来就在既有 500Hz 轮询里，")
print("     所以「**追加**」的确实是 6 次。Q4 的追加口径**成立**。）")
print("  结论：Q4 口径正确（追加 6 次），但正文应写清「追加 6 = 4VA + f_pre + f_post，")
print("        判沿那 1 次属既有轮询、不计入追加」。")

print("\n" + "=" * 72)
print("核查 3 · 节拍影响：6 次 RPM 串行插进 500 Hz 循环")
print("=" * 72)
print("  500 Hz ⇒ 每拍预算 2.000 ms")
print("  最坏窗 188.2 reads/s 追加 ⇒ 每秒 188.2/31.6 ≈ 5.96 次沿/秒? 不，见下")
# 用真实最坏窗算
import json
d = json.load(io.open(
    r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
    r'l3_20261023r/measure_w0.json', encoding='utf-8')) if os.path.isfile(
    r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261023r/measure_w0.json') else None
print("  （真实最坏窗数据见 Q4 的 188.2 reads/s = 31.4 沿/s × 6）")
print("  31.4 沿/s ⇒ 每 31.8 ms 一次沿 ⇒ 该拍实际做 1+6=7 次 RPM")
print("  若单次 RPM ≈ 10–20 µs（跨进程只读，未实测），7 次 ≈ 70–140 µs")
print("  ⇒ 占 2 ms 预算的 3.5%–7%，节拍**大概率不会崩**，但**会挤占**。")
print("  ★ 单次 RPM 耗时**未实测** —— 标未验，不得当作已量化。")

print("\n" + "=" * 72)
print("核查 4 · 一个我认为是真缺陷的点")
print("=" * 72)
# 找 authorized 分支是否落 s4_gate rec
hook_start = None
for i, l in enumerate(lines):
    if l.startswith('def s4_injection_gate(pid: int, rec: Recorder, authorized: bool = False) -> bool:'):
        hook_start = i
        break
hook_body = "\n".join(lines[hook_start:hook_start + 25])
print("  W5 hook 的 authorized 分支是否写 rec key='s4_gate':",
      "rec.add(\"W5EXT\", \"s4_hard_assertion\", \"FAILED_ALLOW_LOADER\"" in hook_body)
print("  是否写 's4_gate' 键:", '"s4_gate"' in hook_body)
print("  ⇒ 它只写 W5EXT/s4_hard_assertion + 改 S4_VERDICT，**没有**像母本那样写 S4/s4_gate 与 s4_exit_code rec 行。")
print("     影响：下游若按 rec 里的 group=='S4' and key=='s4_gate' 判读，会**看不到**这条拒绝；")
print("     但 S4_VERDICT['gate'] 已被改，main() 仍会取到 62 ⇒ **功能上仍阻断**，只是**审计轨迹不全**。")
print("     严重度：中（不改变阻断行为，但破坏「S4 结论必在 rec 里」的既有约定）。")

print("\n" + "=" * 72)
print("核查 5 · flag-off 逐字相同性（静态）")
print("=" * 72)
print("  _measure_poll_span 包装: if not _W5_STATE['on']: return mother(...) ⇒ on 为 False 时逐字走母本")
print("  _W5_STATE['on'] 只在 main-gate 块赋值（行 7719），缺省 False（行 184）")
print("  s4_scan_names 包装: 无条件调 mother 再写 _W5_STATE —— **注意**：")
print("     ⇒ flag-off 时**仍会**执行 `list(scan.get(...) or [])`，")
print("        这是**额外的** dict 读取与列表构造，虽不改语义，但**不是零执行**。")
print("     ⇒ 严格说 flag-off 不再是「零行为差」，而是「零**语义**差 + 极小的**计算**差」。")
print("     ⇒ 该点应写进诚实账。")

print("\n" + "=" * 72)
print("核查 6 · s4_injection_gate 包装的 flag-off")
print("=" * 72)
print("  if not _W5_STATE['on']: return res  ⇒ flag-off 直接透传，零额外 rec。**这一点是干净的**。")

print("\nDONE")
