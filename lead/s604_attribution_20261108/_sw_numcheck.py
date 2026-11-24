# -*- coding: utf-8 -*-
"""_sw_numcheck.py — 归属撰写员独立核验（只读语料与上游件，零真机零采样）。
1) 自实现主口径（edge + k=n//3 + maxgap + median）从 15 份语料 JSON 复算 fd/fg/sd/sg/diff；
2) 直接解析台账 :9706-9720 原文表值（不经任何中间转抄）；
3) 三方对数：本人复算 vs R3[B] vs _sa[S]；
4) 逐窗对照表 + 偏离统计 + round 判等 + [INT] 表内自洽 + :9723/:9724/:9725 判定复算；
5) 语料 15 件 SHA256/bytes/mtime vs R3[A] 登记；
6) 双锚点 l1c/w0 全帧 med_edge/med_span；
7) 收尾台账/PENDING 指纹（未改核对）。"""
import json, os, re, math, hashlib, statistics, datetime

BASE = r"D:\Project\ra2-campaign-forge"
GOAL = BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md"
R3OUT = BASE + r"\lead\slowframe_r3_20261108\_r3_recompute_out.txt"
SAOUT = BASE + r"\lead\s604_attribution_20261108\_sa_probe_out.txt"
CORPUS = BASE + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
WINS = [(t, w) for t in TRIPS for w in (0, 1, 2)]
NUM = re.compile(r'[-+−]?\d+(?:\.\d+)?')
def norm(s): return s.replace('−', '-').replace('*','').replace('ms','').strip()
def fnum(s):
    m = NUM.search(norm(s));  return float(m.group()) if m else None

def sha256_file(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()

# ---------- 1. 台账原文表值解析（1-based 行 9706-9720） ----------
led = {}
with open(GOAL, encoding='utf-8') as fh: glines = fh.readlines()
for i in range(9705, 9720):  # 0-based idx → 1-based 9706..9720
    cells = [c.strip() for c in glines[i].split('|')]
    cells = [c for c in cells if c != '']
    name = cells[0].strip('`')
    vals = [fnum(c) for c in cells[1:6]]
    assert all(v is not None for v in vals), (i+1, cells)
    led[name] = tuple(vals)
print(f"[P1] 台账 :9706-9720 直接解析 15 行 OK（U+2212 已归一）: {len(led)} 窗")
print(f"[P1] 例: l1c_20261021/w0 -> {led['l1c_20261021/w0']} ; t55k_20261020/w2 -> {led['t55k_20261020/w2']}")

# ---------- 2. 本人独立复算（主口径 edge + floor 三分 + maxgap + median） ----------
mine = {}
for trip, w in WINS:
    name = f'{trip}/w{w}'
    path = f'{CORPUS}\\{trip}\\measure_w{w}.json'
    raw = open(path,'rb').read()
    d = json.loads(raw.decode('utf-8'))
    t = d['samples']['t']; f = d['samples']['f']; edges = d['frame_edges']
    e0 = edges[0]
    assert isinstance(e0[0], int) and isinstance(e1t := e0[1], float), (name, e0)  # (fid:int, t_edge:float)
    groups = {}
    for fi, ti in zip(f, t): groups.setdefault(fi, []).append(ti)
    extra_f = sorted(set(f) - {e[0] for e in edges})
    assert not extra_f, (name, extra_f[:5])
    frame_ids = [e[0] for e in edges]; edge_t = {e[0]: e[1] for e in edges}
    n_frames = len(frame_ids)
    maxgap = {}; dur_edge = {}; dur_span = {}
    for i, fid in enumerate(frame_ids):
        ts = sorted(groups.get(fid, []))
        if len(ts) >= 2:
            maxgap[fid] = max(ts[j+1]-ts[j] for j in range(len(ts)-1))
        dur_span[fid] = (max(ts)-min(ts)) if ts else None
        if i+1 < n_frames:
            dur_edge[fid] = edge_t[frame_ids[i+1]] - edge_t[fid]
    def thirds(dmap):
        ids = sorted([fid for fid in frame_ids if dmap.get(fid) is not None], key=lambda x:(dmap[x], x))
        n = len(ids); k = n // 3
        fast, slow = ids[:k], ids[n-k:]
        fd = statistics.median([dmap[i] for i in fast]) * 1000.0
        sd = statistics.median([dmap[i] for i in slow]) * 1000.0
        fg = statistics.median([maxgap[i] for i in fast]) * 1000.0
        sg = statistics.median([maxgap[i] for i in slow]) * 1000.0
        return fd, fg, sd, sg, sg - fg, k, n
    fd, fg, sd, sg, df, k, n = thirds(dur_edge)
    med_edge_all = statistics.median(list(dur_edge.values())) * 1000.0
    med_span_all = statistics.median([v for v in dur_span.values() if v is not None]) * 1000.0
    mine[name] = dict(fd=fd, fg=fg, sd=sd, sg=sg, diff=df, k=k, n=n,
                      n_frames=n_frames, med_edge_all=med_edge_all, med_span_all=med_span_all,
                      sha=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                      mtime=datetime.datetime.fromtimestamp(os.stat(path).st_mtime))
print(f"[P2] 本人主口径复算 15 窗完成（floor 三分，k=n//3，末帧剔除）")

# ---------- 3. R3[B] 与 _sa[S] 输出件解析（三方对数） ----------
with open(R3OUT, encoding='utf-8') as fh: r3l = fh.readlines()
r3 = {}
for i in range(40, 55):  # 1-based 41..55
    seg = [s.strip() for s in r3l[i].split('|')]
    name = seg[0].split()[0]
    vals = [fnum(x) for x in seg[1].split()]          # 复算 5 数
    ledt = [fnum(x) for x in seg[2].split()]          # R3 转抄台账 5 数
    r3[name] = (vals, ledt)
with open(SAOUT, encoding='utf-8') as fh: sal = fh.readlines()
sa = {}
for i in range(6, 21):  # 1-based 7..21
    seg = [s.strip() for s in sal[i].split('|')]
    name = seg[0].split()[0]
    fg, sg, df = [fnum(x) for x in seg[1].split()]    # 复算 fg/sg/diff
    sa[name] = (fg, sg, df)
# 输出件打印 4 位小数 ⇒ 判等须按「我的值格式化到 4 位」与解析值比较（1e-9），而非原始浮点直比
def eq4(a, b): return abs(float(f'{a:.4f}') - b) < 1e-9
mism_r3 = sum(0 if eq4(mine[k]['fd'],r3[k][0][0]) and eq4(mine[k]['fg'],r3[k][0][1])
              and eq4(mine[k]['sd'],r3[k][0][2]) and eq4(mine[k]['sg'],r3[k][0][3])
              and eq4(mine[k]['diff'],r3[k][0][4]) else 1 for k in mine)
mism_sa = sum(0 if eq4(mine[k]['fg'],sa[k][0]) and eq4(mine[k]['sg'],sa[k][1])
              and eq4(mine[k]['diff'],sa[k][2]) else 1 for k in mine)
mism_led_trans = sum(0 if led[k]==tuple(r3[k][1]) else 1 for k in led)
print(f"[P3] 三方对数（按 4 位显示精度判等）：本人复算 vs R3[B] 五列不一致 = {mism_r3}/15；"
      f"vs _sa[S] fg/sg/diff 不一致 = {mism_sa}/15；我解析台账 vs R3[B]转抄台账 不一致 = {mism_led_trans}/15")
worst = max((max(abs(mine[k][q]-r3[k][0][i]) for i,q in enumerate(('fd','fg','sd','sg','diff'))) for k in mine))
print(f"[P3] 本人原始浮点 vs R3[B]解析值 最大绝对差 = {worst:.6f}（≤0.00005 即纯显示舍入量级）")

# ---------- 4. 逐窗对照表 + 偏离统计 ----------
print("[P4] 逐窗对照（偏离量 = 复算 − 台账）")
rows = []
for name in led:
    fd0,fg0,sd0,sg0,d0 = led[name]; m = mine[name]
    dev = m['diff'] - d0
    if d0 < 0: direc = '符号相反'
    elif d0 == 0: direc = '零值 vs 正'
    else: direc = f"同号·{abs(m['diff']/d0):.1f}×"
    rows.append((name, d0, m['diff'], direc, dev, fg0-m['fg'], sg0-m['sg']))
    print(f"  {name:18s} 台账 {d0:+.3f}  复算 {m['diff']:+.4f}  {direc:12s} 偏离 {dev:+.4f}  Δfg {fg0-m['fg']:+.4f}  Δsg {sg0-m['sg']:+.4f}")
devs = sorted(r[4] for r in rows)
n_up = sum(1 for r in rows if r[4] > 0)
print(f"[P4] 复算>台账 窗数 = {n_up}/15；偏离量 中位 {statistics.median(devs):+.4f} 最小 {devs[0]:+.4f} 最大 {devs[-1]:+.4f}")
myd = sorted(m['diff'] for m in mine.values())
print(f"[P4] 复算 diff：中位 {statistics.median(myd):+.4f} 最小 {myd[0]:+.4f} 最大 {myd[-1]:+.4f} 严格<0 窗数 {sum(1 for x in myd if x<0)}")
ld = [r[1] for r in rows]
print(f"[P4] 台账 diff：中位 {statistics.median(ld):+.4f} 最小 {min(ld):+.4f} 最大 {max(ld):+.4f} 严格<0 {sum(1 for x in ld if x<0)}  ≤0 {sum(1 for x in ld if x<=0)}")
dfg = [r[5] for r in rows]; dsg = [r[6] for r in rows]
print(f"[P4] 快空档列 Δfg>0（被抬高）= {sum(1 for x in dfg if x>0)}/15；Δfg≤0.0010+1e-9 的格 = {sum(1 for x in dfg if x<=0.0010+1e-9)}；min Δfg = {min(dfg):+.4f}")
print(f"[P4] 慢空档列 Δsg<0（被压低）= {sum(1 for x in dsg if x<0)}/15；|Δsg|≤0.0055 的格 = {sum(1 for x in dsg if abs(x)<=0.0055)}")

# ---------- 5. round 判等 ----------
dur_ok = gap_ok = diff_ok = 0
for name in led:
    fd0,fg0,sd0,sg0,d0 = led[name]; m = mine[name]
    dur_ok  += (round(m['fd'],1)==round(fd0,1)) + (round(m['sd'],1)==round(sd0,1))
    gap_ok  += (round(m['fg'],2)==round(fg0,2)) + (round(m['sg'],2)==round(sg0,2))
    diff_ok += (round(m['diff'],3)==round(d0,3))
print(f"[P5] round 判等：时长列 {dur_ok}/30；空档列 {gap_ok}/30；空档差列 {diff_ok}/15")

# ---------- 6. [INT] 台账表内自洽 ----------
mx = 0; mxname = ''
for name in led:
    fd0,fg0,sd0,sg0,d0 = led[name]
    delta = abs(d0 - (sg0 - fg0))
    if delta > mx: mx, mxname = delta, name
print(f"[P6] [INT] |diff列 − (慢gap−快gap)| 最大 = {mx:.4f} @ {mxname}（显示舍入上限 0.010）")

# ---------- 7. :9724 / :9725 / :9723 ----------
in_re = sum(1 for m in mine.values() if 0.003 <= m['diff'] <= 0.049)
below_re = sum(1 for m in mine.values() if m['diff'] < 0.003)
above_re = sum(1 for m in mine.values() if m['diff'] > 0.049)
in_led = sum(1 for x in ld if 0.003 <= x <= 0.049)
print(f"[P7] :9724 区间[+0.003,+0.049]：复算侧 命中 {in_re}/15（低于 {below_re}，高于 {above_re}）；台账表侧 命中 {in_led}/15")
rat_led = sorted(((led[n][2]/led[n][0], n) for n in led))   # 表值倍率 = 慢dur[2] / 快dur[0]
rat_my  = sorted(((mine[n]['sd']/mine[n]['fd'], n) for n in led))
print(f"[P7] :9723 倍率：表值 中位 {statistics.median([r[0] for r in rat_led]):.4f} 最大 {rat_led[-1][0]:.4f}@{rat_led[-1][1]} l3/w0 {[r[0] for r in rat_led if r[1]=='l3_20261021/w0'][0]:.4f}")
print(f"[P7]          实算 中位 {statistics.median([r[0] for r in rat_my]):.4f} 最大 {rat_my[-1][0]:.4f}@{rat_my[-1][1]} l3/w0 {[r[0] for r in rat_my if r[1]=='l3_20261021/w0'][0]:.4f}")
sd_max = max(led, key=lambda n: led[n][2]); sd_max_my = max(led, key=lambda n: mine[n]['sd'])
print(f"[P7] 慢1/3 时长绝对值最大窗：表值 {sd_max} ({led[sd_max][2]})；实算 {sd_max_my} ({mine[sd_max_my]['sd']:.1f})")

# ---------- 8. 语料 15 件 vs R3[A] 登记 ----------
reg = {}
for i in range(7, 37, 2):  # 1-based 8..37 奇数行=info，偶数行=sha
    info = r3l[i]; shal = r3l[i+1]
    nm = info.split(':')[0].strip()
    nf = int(re.search(r'n_frames=(\d+)', info).group(1))
    sha = re.search(r'sha256=([0-9a-f]{64})', shal).group(1)
    byt = int(re.search(r'bytes=(\d+)', shal).group(1))
    reg[nm] = (sha, byt, nf)
ok = 0
for name in led:
    trip, w = name.split('/w'); trip_win = f'{trip}/w{w}'
    m = mine[trip_win]; rg = reg[trip_win]
    good = (m['sha']==rg[0]) and (m['bytes']==rg[1]) and (m['n_frames']==rg[2])
    ok += good
    print(f"  [P8] {trip_win:18s} sha={'OK' if m['sha']==rg[0] else 'MISMATCH'} bytes={m['bytes']}({'OK' if m['bytes']==rg[1] else 'MISMATCH'})"
          f" n_frames={m['n_frames']}({'OK' if m['n_frames']==rg[2] else 'MISMATCH'}) mtime={m['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")
print(f"[P8] 语料 15 件 SHA256+bytes+n_frames 与 R3[A] 登记 全吻合 = {ok}/15")

# ---------- 9. 双锚点 ----------
a = mine['l1c_20261021/w0']
print(f"[P9] 双锚点 l1c_20261021/w0：med_edge_all={a['med_edge_all']:.4f} ms  med_span_all={a['med_span_all']:.4f} ms  n_frames={a['n_frames']}")
print(f"[P9] 台账 :9613 行原文：{glines[9612].strip()}")
print(f"[P9] 台账 :9535 行原文：{glines[9534].strip()}")

# ---------- 10. 收尾指纹 ----------
print(f"[P10] 收尾 台账 SHA256 = {sha256_file(GOAL)} bytes = {os.path.getsize(GOAL)} mtime = {datetime.datetime.fromtimestamp(os.stat(GOAL).st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
print("[done] _sw_numcheck")
