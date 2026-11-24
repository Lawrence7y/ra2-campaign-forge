# -*- coding: utf-8 -*-
# _sv_numcheck.py — 复核员独立数值核对（纯只读；台账/R3 输出现解析，回件断言硬编码比对）
import re, os, statistics, time
BASE = r"D:\Project\ra2-campaign-forge"
def rd(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8")
LED = rd(os.path.join(BASE, "lead/GOAL_THREE_TARGETS_20261018.md"))
R3O = rd(os.path.join(BASE, "lead/slowframe_r3_20261108/_r3_recompute_out.txt"))

def num(cell):
    s = cell.replace("−", "-").replace("*", "").replace("ms", "").replace("`", "").strip()
    if re.search(r"[A-Za-z\u4e00-\u9fff]", s):
        return None
    m = re.search(r"[-+]?\d*\.?\d+", s)
    return float(m.group()) if m else None

L = LED.splitlines()
led = {}   # win -> [fd, fg, sd, sg, diff]  (台账 :9705-9720 数据行)
for i in range(9704, 9721):
    line = L[i - 1]
    m = re.search(r"([a-z0-9]+_\d+/w\d)", line)
    if not m:
        continue
    win = m.group(1)
    vals = [v for v in (num(c) for c in line.split("|")) if v is not None]
    if len(vals) >= 5:
        led[win] = vals[:5]

r3 = {}    # win -> [fd, fg, sd, sg, diff]  (R3 [B] 复算列)
r3tab = {} # win -> R3 [B] 第三列录入的台账值（交叉验证 R3 脚本 TABLE 录入）
for line in R3O.splitlines():
    parts = line.replace("−", "-").split("|")
    if len(parts) >= 3 and re.match(r"^\s*[a-z0-9]+_\d+/w\d\s*$", parts[0]) and parts[0].strip() != "window":
        ns = re.findall(r"[-+]?\d+\.\d+", parts[1])
        if len(ns) == 5:
            r3[parts[0].strip()] = [float(x) for x in ns]
            r3tab[parts[0].strip()] = [float(x) for x in re.findall(r"[-+]?\d+\.\d+", parts[2])]

order = ["l1c_20261021/w0","l1c_20261021/w1","l1c_20261021/w2",
         "l1d_20261021/w0","l1d_20261021/w1","l1d_20261021/w2",
         "l1e_20261021/w0","l1e_20261021/w1","l1e_20261021/w2",
         "l3_20261021/w0","l3_20261021/w1","l3_20261021/w2",
         "t55k_20261020/w0","t55k_20261020/w1","t55k_20261020/w2"]
print("[0] 解析：台账表窗数 =", len(led), " R3[B]窗数 =", len(r3))

# 回件 §3 逐窗对照表期望: (台账diff, 复算diff, 偏离量=复算-台账, Δfg=台账fg-复算fg, Δsg=台账sg-复算sg)
REP = {
"l1c_20261021/w0": (0.032, 0.1080, 0.0760, 0.0275, -0.0505),
"l1c_20261021/w1": (0.028, 0.0790, 0.0510, 0.0355, -0.0135),
"l1c_20261021/w2": (0.030, 0.0670, 0.0370, 0.0110, -0.0260),
"l1d_20261021/w0": (0.049, 0.0640, 0.0150, 0.0150, 0.0010),
"l1d_20261021/w1": (0.022, 0.0380, 0.0160, 0.0130, -0.0050),
"l1d_20261021/w2": (0.025, 0.0550, 0.0300, 0.0190, -0.0160),
"l1e_20261021/w0": (0.003, 0.0320, 0.0290, 0.0110, -0.0210),
"l1e_20261021/w1": (0.035, 0.0480, 0.0130, 0.0090, -0.0090),
"l1e_20261021/w2": (0.018, 0.0340, 0.0160, 0.0100, -0.0140),
"l3_20261021/w0": (-0.002, 0.0880, 0.0900, 0.0430, -0.0450),
"l3_20261021/w1": (0.037, 0.0960, 0.0590, 0.0220, -0.0340),
"l3_20261021/w2": (0.002, 0.1030, 0.1010, 0.0490, -0.0540),
"t55k_20261020/w0": (-0.013, 0.0260, 0.0390, 0.0225, -0.0235),
"t55k_20261020/w1": (-0.006, 0.0255, 0.0315, 0.0150, -0.0205),
"t55k_20261020/w2": (0.0, 0.0065, 0.0065, 0.0010, -0.0055),
}
E = 1e-9
errs = []
print("[1] 逐窗 5 列核对（台账diff/复算diff/偏离量/Δfg/Δsg vs 回件§3表）：")
for w in order:
    fd, fg, sd, sg, df = led[w]
    rfd, rfg, rsd, rsg, rdiff = r3[w]
    ed, er, edv, efg, esg = REP[w]
    got = (df, rdiff, rdiff - (df if abs(df) > E else 0.0), fg - rfg, sg - rsg)
    exp = (ed, er, edv, efg, esg)
    ok = all(abs(a - b) < 5e-5 for a, b in zip(got, exp))
    if not ok:
        errs.append((w, got, exp))
    print("   ", w, "OK" if ok else "MISMATCH got={} exp={}".format(got, exp))

# R3 [B] 第三列录入的台账值 vs 台账原文（验 R3 脚本 TABLE 录入无误）
print("[2] R3[B] 第三列台账录入 vs 台账原文：", end="")
t = all(abs(a - b) < 5e-5 for w in order for a, b in zip(r3tab[w], led[w]))
print("一致 15/15" if t else "不一致!")

# --- 汇总统计 vs 回件 drift 断言 ---
devs = [r3[w][4] - (led[w][4] if abs(led[w][4]) > E else 0.0) for w in order]
r3d = [r3[w][4] for w in order]
dfg = [led[w][1] - r3[w][1] for w in order]
dsg = [led[w][3] - r3[w][3] for w in order]
print("[3] 复算diff>台账diff 窗数 =", sum(1 for w in order if r3[w][4] > (led[w][4] if abs(led[w][4]) > E else 0.0)), "/15  (回件称 15/15)")
print("[4] 偏离量(复算-台账): 中位 = {:+.4f} 最小 = {:+.4f} 最大 = {:+.4f}  (回件称 +0.0315/+0.0065/+0.1010)".format(statistics.median(devs), min(devs), max(devs)))
print("[5] 复算diff: 中位 = {:+.4f} 最小 = {:+.4f} 最大 = {:+.4f}  (回件称 +0.0550/+0.0065/+0.1080)".format(statistics.median(r3d), min(r3d), max(r3d)))
pos = sum(1 for v in r3d if v > E); neg = sum(1 for v in r3d if v < -E)
lpos = sum(1 for v in led.values() if v[4] > E); lneg = sum(1 for v in led.values() if v[4] < -E)
lzero = 15 - lpos - lneg
print("[6] 复算正={}负={} ; 表正={}负={}零={}  (回件称 复算15正 vs 表11正3负1零)".format(pos, neg, lpos, lneg, lzero))
up_f = sum(1 for v in dfg if v > 0); up_f_v = [v for v in dfg if v > 0]
lo_s = sum(1 for v in dsg if v < 0)
print("[7] 快空档列被抬高(Δfg>0) = {}/15, 范围 +{:.4f}..+{:.4f}  (回件称 15/15, +0.001..+0.049)".format(up_f, min(up_f_v), max(up_f_v)))
print("[8] 慢空档列被压低(Δsg<0) = {}/15  (回件称 13/15; 无阈值实算在此)".format(lo_s))
print("    |Δsg|<=0.0055 的格 = {} 个: {}".format(sum(1 for v in dsg if abs(v) <= 0.0055 + E), [round(v, 4) for v in dsg if abs(v) <= 0.0055 + E]))
print("    |Δsg|<=0.0050 的格 = {} 个: {}".format(sum(1 for v in dsg if abs(v) <= 0.0050 + E), [round(v, 4) for v in dsg if abs(v) <= 0.0050 + E]))
print("    排除+0.0010与-0.0050两格后压低 = {}  ; 排除+0.0010与-0.0055后压低 = {}".format(
    sum(1 for v in dsg if v < 0 and abs(v) > 0.0050 + E), sum(1 for v in dsg if v < 0 and abs(v) > 0.0055 - E and abs(v) > 0.0050 + E)))
tol_hits = sum(1 for w in order if abs(led[w][1] - r3[w][1]) < 0.005 + E) + sum(1 for w in order if abs(led[w][3] - r3[w][3]) < 0.005 + E)
tol_d = sum(1 for w in order if abs(led[w][0] - r3[w][0]) < 0.05 + E) + sum(1 for w in order if abs(led[w][2] - r3[w][2]) < 0.05 + E)
rnd_g = sum(1 for w in order if abs(round(r3[w][1], 2) - led[w][1]) < E) + sum(1 for w in order if abs(round(r3[w][3], 2) - led[w][3]) < E)
rnd_d = sum(1 for w in order if abs(round(r3[w][0], 1) - led[w][0]) < E) + sum(1 for w in order if abs(round(r3[w][2], 1) - led[w][2]) < E)
rnd_x = sum(1 for w in order if abs(round(r3[w][4], 3) - (led[w][4] if abs(led[w][4]) > E else 0.0)) < E)
print("[9] 空档列容差命中 = {}/30 (不命中 {}) ; 时长列容差命中 = {}/30  (回件称 空档27/30不命中、时长30/30)".format(tol_hits, 30 - tol_hits, tol_d))
print("[10] round判等: 时长 {}/30 空档 {}/30 空档差 {}/15  (R3[B2]称 30/30, 3/30, 0/15)".format(rnd_d, rnd_g, rnd_x))
print("[11] 空档列最大偏差 = {:.4f} ms  (回件称 0.0540)".format(max(max(abs(v) for v in dfg), max(abs(v) for v in dsg))))
ints = [abs((led[w][4] if abs(led[w][4]) > E else 0.0) - (led[w][3] - led[w][1])) for w in order]
print("[12] [INT] 台账diff列 vs 自家两空档列 max|Δ| = {:.4f}  (回件称 0.0080<=0.010)".format(max(ints)))
in_l = sum(1 for w in order if 0.003 - E <= led[w][4] <= 0.049 + E)
in_r = sum(1 for w in order if 0.003 - E <= r3[w][4] <= 0.049 + E)
print("[13] :9724 区间[+0.003,+0.049]: 表值落入 = {}/15, 复算落入 = {}/15  (回件/引[F][V5]称 表10/15、复算7/15)".format(in_l, in_r))
print("[14] 表内严格正差最小值 = {:+.4f} (l3/w2, 回件称 +0.002 低于下界+0.003)".format(min(v[4] for v in led.values() if v[4] > E)))
rat_t = [led[w][2] / led[w][0] for w in order]
rat_r = [r3[w][2] / r3[w][0] for w in order]
wmax_t = order[rat_t.index(max(rat_t))]; wmax_r = order[rat_r.index(max(rat_r))]
print("[15] 倍率 表值: 中位 = {:.4f} 最大 = {:.4f}@{} l3/w0 = {:.4f}  (回件引[E]:75/:76 称 2.1927/2.4887@l1d/w2/2.1393)".format(statistics.median(rat_t), max(rat_t), wmax_t, rat_t[order.index("l3_20261021/w0")]))
print("[16] 倍率 实算: 中位 = {:.4f} 最大 = {:.4f}@{} l3/w0 = {:.4f}  (回件引[E]:74 称 2.1906/2.4878@l1d/w2/2.1379)".format(statistics.median(rat_r), max(rat_r), wmax_r, rat_r[order.index("l3_20261021/w0")]))

# --- 台账关键行文本断言 ---
print("[17] 台账行文本: :9724 含全正区间 =", ("+0.003 ~ +0.049" in L[9723]),
      "; :9725 含「3 窗为负」=", ("3 窗为负" in L[9724]),
      " 且括号列举项数 =", len(re.findall(r"`[^`]+`", L[9724].split("（")[-1])),
      "; :9723 含「最大 `l3/w0`」=", ("最大 `l3/w0`" in L[9722]), " 含 2.14 =", ("2.14" in L[9722]))

# --- 语料 15 件 os.stat（mtime/bytes vs R3[A]登记） ---
EXP_B = {"l1c_20261021/w0":257797,"l1c_20261021/w1":260075,"l1c_20261021/w2":260507,
"l1d_20261021/w0":260734,"l1d_20261021/w1":260644,"l1d_20261021/w2":262470,
"l1e_20261021/w0":261506,"l1e_20261021/w1":261855,"l1e_20261021/w2":263067,
"l3_20261021/w0":247450,"l3_20261021/w1":249000,"l3_20261021/w2":256142,
"t55k_20261020/w0":272285,"t55k_20261020/w1":272141,"t55k_20261020/w2":272095}
C = os.path.join(BASE, "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
print("[18] 语料 15 件 os.stat（回件称 t55k mtime=2026-10-20 09:21-09:22、其余 2026-10-21 19:04-21:14；bytes 与[A]同）：")
bm = 0
for w in order:
    trip, wn = w.split("/")
    p = os.path.join(C, trip, "measure_w{}.json".format(wn[1]))
    st = os.stat(p)
    okb = st.st_size == EXP_B[w]
    bm += okb
    print("    {} bytes={} (match={}) mtime={}".format(w, st.st_size, okb, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))
print("[19] bytes 与 [A] 登记一致 {}/15".format(bm))
print("[20] 逐窗对照表 MISMATCH 数 =", len(errs))
