# -*- coding: utf-8 -*-
"""R177 收口后置校验：四项不变量 + 三段门禁当场重跑 + 无孤儿进程 + §2.182 声明值与实测一致。"""
import csv, hashlib, io, os, re, subprocess, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

INV = {'lead/next_re_20261117_r14/R14_COMMON.md': 1081,
       'lead/LEAD_LOCK': 137,
       'lead/GOAL_THREE_TARGETS_20261018.md': 337,
       'lead/next_re_20261117_r14/STATUS_BOARD.md': 0,
       'lead/next_re_20261117_r14/BOARD_ARCHIVE.md': 2952}
for rel, exp in INV.items():
    raw = open(os.path.join(ROOT, rel), 'rb').read()
    ck('CR %-46s == %d' % (os.path.basename(rel), exp), raw.count(b'\r') == exp, raw.count(b'\r'))
b = open(os.path.join(R14, 'STATUS_BOARD.md'), 'rb').read()
ck('看板行数 <= 300', b.count(b'\n') <= 300, b.count(b'\n'))
ck('看板行数 < 260（已归档）', b.count(b'\n') < 260, b.count(b'\n'))

# 三段门禁当场跑
def run(cmd, timeout=300):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or '') + (r.stderr or '')

rc1, o1 = run('python3 %s/_r160/facts_floors.py' % ROOT)
ck('facts_floors exit 0', rc1 == 0, rc1)
ck('facts D0 现算 = ede48f3c', 'D0 sha=ede48f3c32048040' in o1)
ck('facts D8 130510', 'D8 total bytes: 130510' in o1)
ck('facts D9 db88d9b8', 'D9 master pin: db88d9b87ffdd8d0' in o1)
ck('facts 无 FAIL 行', '  FAIL ' not in o1)

rc2, o2 = run('python3 %s/check_disc.py' % os.path.join(R14))
ck('check_disc exit 0', rc2 == 0, rc2)
m = re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\)[^,]*,[^,]*,[^,]*, unpinned (\d+)', o2)
ck('C16 NOTE 解析成功', m is not None)
if m:
    ck('C16 measured 176', m.group(1) == '176', m.group(1))
    ck('C16 pinned 176', m.group(2) == '176', m.group(2))
    ck('C16 unpinned 0', m.group(3) == '0', m.group(3))
ck('check_disc 无行首 FAIL', not re.search(r'(?m)^\s*FAIL', o2))

rc3, o3 = run('python3 %s/_r161/gate_runner.py' % ROOT)
ck('gate_runner exit 0', rc3 == 0, rc3)
ck('gate_runner G1=G2=G3=ok', 'GATE_VER=R166  G1=ok  G2=ok  G3=ok' in o3)
ck('gate_runner G3f db88d9b8', 'db88d9b87ffdd8d0' in o3)

# V560 结构 + 声明值 = 实测值（不动点）
rows = list(csv.reader(io.StringIO(open(os.path.join(R14, 'R17_R128_FACTINDEX_V560/FACT_INDEX.tsv'),
                                       encoding='utf-8').read()), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}
ck('V560 55 行 5 列', len(rows) == 55 and all(len(r) == 5 for r in rows))
T = '6 个不同桩体'
ck('F29.lim 实测该串 3 次 = 段内声明 3（不动点）', d['F29'][4].count(T) == 3, d['F29'][4].count(T))
ck('F29.stmt 恒 1', d['F29'][1].count(T) == 1)
ck('F29.lim 段内写「limitations 仍为 3」', 'limitations 仍为 **3**' in d['F29'][4])
ck('F29.lim 段内写「合计 4」', '合计 **4**' in d['F29'][4])
ck('V560 与 V559 只差 F29', True)
v559 = list(csv.reader(io.StringIO(open(os.path.join(R14, 'R17_R128_FACTINDEX_V559/FACT_INDEX.tsv'),
                                       encoding='utf-8').read()), delimiter='\t'))
diff = [(a[0], [i for i in range(5) if a[i] != b[i]]) for a, b in zip(v559, rows) if a != b]
ck('V559->V560 差分行恰 F29 差列恰 [4]', diff == [('F29', [4])], repr(diff))

# 指针
pt = open(os.path.join(R14, 'FACT_INDEX_CURRENT.md'), encoding='utf-8').read()
ck('指针指 V560', 'R17_R128_FACTINDEX_V560' in pt)
ck('指针 sha = V560 sha', 'ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4' in pt)
ck('指针声明轮次 R177', '| 声明轮次 | R177 |' in pt)

# 无孤儿进程：按 /proc/<pid>/cmdline 判，排除自身与主会话
me = os.getpid()
_self_chain = None
orphans = []
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) == me:
        continue
    try:
        cmd = open('/proc/%s/cmdline' % pid, 'rb').read().decode('utf-8', 'replace').replace('\x00', ' ').strip()
    except Exception:
        continue
    if not cmd:
        continue
    # S-650：首版把「正在跑本脚本的自己 + 其外层 bash + timeout 包装」都算成孤儿
    # （与 S-611..S-613 同族第三次复发）。排除链：自身 pid、自身 ppid/祖父（经 PPid 回溯到 init）、
    # 以及 cmdline 里出现本脚本文件名的进程。
    if _self_chain is None:
        _self_chain = set()
        cur = me
        for _ in range(8):
            _self_chain.add(cur)
            try:
                st = open('/proc/%d/status' % cur, encoding='utf-8', errors='replace').read()
            except Exception:
                break
            mm = re.search(r'^PPid:\s*(\d+)', st, re.M)
            if not mm:
                break
            cur = int(mm.group(1))
            if cur <= 1:
                _self_chain.add(cur); break
    if int(pid) in _self_chain:
        continue
    if 'r177p_postverify.py' in cmd:
        continue
    if '_r177/' in cmd and ('python3' in cmd) and ('r177' in cmd):
        orphans.append((pid, cmd[:110]))
print('  疑似残留 r177 进程:', orphans)
ck('无 r177 残留进程', orphans == [], orphans[:3])

print('---- %d PASS / %d FAIL ----' % (P, F))
sys.exit(1 if F else 0)
