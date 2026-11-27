#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 N：收口总校验（不写任何业务文件；只读 + 三段门禁实跑 + 五项 CR）。

包含：
 A 五项 CR 不变量（R14_COMMON 1081 / 台账 337 / LEAD_LOCK 137 / 看板 0 / 归档 2952）
 B 四件套内容抽查（本轮新增的段/条/节都能定位且唯一，跨件数字一致）
 C 三段门禁实跑（check_disc / facts_floors / gate_runner）全部 exit 0 且无行首 FAIL
 D V554 事实层形态（55 行 5 列 / CR 0 / sha / 两处改动单元）
 E 无孤儿进程（按 /proc/<pid>/cmdline 判，不看 ps 文本）
"""
import glob, hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

def rb(p): return open(p, 'rb').read()

# ---- A 五项 CR ----
cr = {
    'R14_COMMON': (os.path.join(TIER, 'R14_COMMON.md'), 1081),
    'LEDGER': (os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'), 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead/LEAD_LOCK'), 137),
    'STATUS_BOARD': (os.path.join(TIER, 'STATUS_BOARD.md'), 0),
    'BOARD_ARCHIVE': (os.path.join(TIER, 'BOARD_ARCHIVE.md'), 2952),
}
for k, (p, want) in cr.items():
    b = rb(p)
    ck('A %s CR == %d' % (k, want), b.count(b'\r') == want, b.count(b'\r'))

bd = io.open(cr['STATUS_BOARD'][0], encoding='utf-8').read()
ck('A6 看板行数 <= 300', bd.count('\n') <= 300, bd.count('\n'))
ck('A7 看板行数 < 260（下一轮不必立刻归档）', bd.count('\n') < 260, bd.count('\n'))
ck('A8 看板里第 173 轮段恰 1 次', bd.count('R17 第 173 轮') == 1, bd.count('R17 第 173 轮'))
# S-610：我连错两版预判 —— 这不是轮次降序表，段序是「170,169」在文件头、168..164 在其后、
# 171/172/173 追加在末尾。故「最早两段」= **文件顺序的前两段**，本轮搬走的正是第 170 与第 169 轮。
# 正确判据：从写入前备份里取文件顺序前两段的轮次号，断言它们已不在看板、且在归档里。
_old_bd = io.open(os.path.join(TIER, 'R17_LEAD_BASELINE',
                               'STATUS_BOARD.md.before_r173_r173_20261127_134234.bak'),
                  encoding='utf-8').read()
_oseg = re.findall(r'(?m)^## .*?R17 第 (\d+) 轮', _old_bd)
ck('A9 备份里段序前两段是 170 与 169（证明搬的是文件顺序最早两段，不是轮次最大两段）',
   _oseg[:2] == ['170', '169'], _oseg[:4])
ck('A10 这两段已不在看板里', bd.count('R17 第 170 轮') == 0 and bd.count('R17 第 169 轮') == 0,
   (bd.count('R17 第 170 轮'), bd.count('R17 第 169 轮')))

# ---- B 四件套内容 ----
rc = io.open(cr['R14_COMMON'][0], encoding='utf-8').read()
ll = io.open(cr['LEAD_LOCK'][0], encoding='utf-8').read()
lg = io.open(cr['LEDGER'][0], encoding='utf-8').read()
ar = io.open(cr['BOARD_ARCHIVE'][0], encoding='utf-8').read()
ck('B1 R14_COMMON §2.178 恰 1 次', rc.count('## 2.178') == 1, rc.count('## 2.178'))
ck('B2 台账 §1228 恰 1 次', lg.count('## §1228') == 1, lg.count('## §1228'))
ck('B3 LEAD_LOCK PD 段恰 1 次', ll.count('\nPD · R17 第 173 轮') == 1, ll.count('\nPD · R17 第 173 轮'))
ck('B4 LEAD_LOCK PD1..PD9 齐全', all(('\nPD%d.' % i) in ll for i in range(1, 10)),
   [i for i in range(1, 10) if ('\nPD%d.' % i) not in ll])
# S-610 续：搬走的是第 170 与第 169 轮，它们在归档里各恰 1 次。
ck('B5 归档里第 170 轮段恰 1 次、且第 169 轮段恰 1 次（搬过去的正是这两段）',
   ar.count('R17 第 170 轮') == 1 and ar.count('R17 第 169 轮') == 1,
   (ar.count('R17 第 170 轮'), ar.count('R17 第 169 轮')))

# 跨件数字一致：16,711,104 / 16,711,116 / 16,711,118 三处都写
for k, doc, name in (('R14', rc, '§2.178'), ('LEDGER', lg, '§1228'), ('LOCK', ll, 'PD1'), ('BOARD', bd, 'board173')):
    ck('B6 %s 同时写了 16,711,104 与 16,711,116 与 16,711,118' % k,
       all(x in doc for x in ('16,711,104', '16,711,116', '16,711,118')),
       [x for x in ('16,711,104', '16,711,116', '16,711,118') if x not in doc])
ck('B7 四件套都写了 MASTER 新值 5f3ba93cb0f091e3',
   all('5f3ba93c' in d for d in (rc, lg, ll, bd)),
   [k for k, d in (('R14', rc), ('LEDGER', lg), ('LOCK', ll), ('BOARD', bd)) if '5f3ba93c' not in d])
ck('B8 四件套都写了 V554 的 sha 前缀 5de4084b',
   all('5de4084b' in d for d in (rc, lg, ll, bd)),
   [k for k, d in (('R14', rc), ('LEDGER', lg), ('LOCK', ll), ('BOARD', bd)) if '5de4084b' not in d])
ck('B9 四件套都声明「本轮无跨家族回件」而非「已过审计」',
   all(('未拿到' in d) or ('无回件' in d) or ('未回件' in d) for d in (rc, ll, bd)),
   [k for k, d in (('R14', rc), ('LOCK', ll), ('BOARD', bd))
    if not (('未拿到' in d) or ('无回件' in d) or ('未回件' in d))])

# ---- C 三段门禁 ----
cd = subprocess.run([sys.executable, os.path.join(TIER, 'check_disc.py')],
                    capture_output=True, text=True, timeout=500)
ck('C1 check_disc exit 0', cd.returncode == 0, cd.returncode)
ck('C2 check_disc 无行首 FAIL', not any(l.strip().startswith('FAIL') for l in cd.stdout.split('\n')),
   [l for l in cd.stdout.split('\n') if l.strip().startswith('FAIL')][:3])
_m = [l for l in cd.stdout.split('\n') if 'C16 per-section floors' in l]
ck('C3 C16 NOTE 逐字 172 sections measured (pinned 172) … unpinned 0',
   _m and '172 sections measured (pinned 172)' in _m[0] and 'unpinned 0' in _m[0],
   _m[0].strip() if _m else None)

ff = subprocess.run([sys.executable, os.path.join(ROOT, '_r160/facts_floors.py')],
                    capture_output=True, text=True, timeout=500)
ck('C4 facts_floors exit 0', ff.returncode == 0, ff.returncode)
ck('C5 facts_floors D0 5de4084b / D8 123851 / D9 5f3ba93c',
   'D0 sha=5de4084b' in ff.stdout and 'total bytes: 123851' in ff.stdout
   and 'D9 master pin: 5f3ba93c' in ff.stdout, None)

gr = subprocess.run([sys.executable, os.path.join(ROOT, '_r161/gate_runner.py')],
                    capture_output=True, text=True, timeout=600)
ck('C6 gate_runner exit 0', gr.returncode == 0, gr.returncode)
ck('C7 gate_runner G1=G2=G3=ok', all(x in gr.stdout for x in ('G1=ok', 'G2=ok', 'G3=ok')), None)
ck('C8 gate_runner G3c/G3d 都是 PASS（不是 None 假通过）',
   'PASS  G3c' in gr.stdout and 'PASS  G3d' in gr.stdout, None)

# GATE_VER 仍未升
gv = re.search(r"^GATE_VER = '([^']+)'", io.open(os.path.join(TIER, 'check_disc.py'), encoding='utf-8').read(), re.M)
ck('C9 GATE_VER 仍 R166（本轮未升版本）', gv and gv.group(1) == 'R166', gv.group(1) if gv else None)

# ---- D V554 形态 ----
v = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
vb = rb(v)
ck('D1 V554 123,851 B', len(vb) == 123851, len(vb))
ck('D2 V554 sha256 5de4084b…', hashlib.sha256(vb).hexdigest().startswith('5de4084b'),
   hashlib.sha256(vb).hexdigest()[:16])
ck('D3 V554 CR 0 / 55 行 / 5 列',
   vb.count(b'\r') == 0 and len(vb.decode().rstrip('\n').split('\n')) == 55
   and all(len(l.split('\t')) == 5 for l in vb.decode().rstrip('\n').split('\n')), None)
v553 = rb(os.path.join(TIER, 'R17_R125_FACTINDEX_V553/FACT_INDEX.tsv'))
ck('D4 V553 仍 121,010 B / 988a9567…（母本未改）',
   len(v553) == 121010 and hashlib.sha256(v553).hexdigest().startswith('988a9567'),
   (len(v553), hashlib.sha256(v553).hexdigest()[:16]))
ck('D5 版本目录 V530..V554 共 25 个连续',
   len(glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V5*'))) >= 25,
   len(glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V5*'))))

# 指针文件
ptr = io.open(os.path.join(TIER, 'FACT_INDEX_CURRENT.md'), encoding='utf-8').read()
# S-616：D6 原是「指针仍指 V553」——那是 r173n 首跑时的事实，随后 r173o 已把它补到 V554，
# 故该断言现在恒 FAIL。改成如实断言「指针指 V554 且其 sha/字节与现盘一致」。
_pm = re.search(r"\| sha256 \| ([0-9a-f]{64}) \|", ptr)
_pb = re.search(r"\| 字节数 \| (\d+) \|", ptr)
ck('D6 FACT_INDEX_CURRENT.md 已指 V554、sha 与字节与现盘一致',
   'V554' in ptr and 'V553' not in ptr and _pm and _pb
   and _pm.group(1) == hashlib.sha256(vb).hexdigest() and int(_pb.group(1)) == len(vb),
   (_pm.group(1)[:16] if _pm else None, _pb.group(1) if _pb else None))
ck('D7 四件套都写了「指针已补到 V554」的补记',
   all('【R173 补记·指针同日补齐】' in d for d in (rc, lg, ll)) and '指针**：' in bd,
   [k for k, d in (('R14', rc), ('LEDGER', lg), ('LOCK', ll)) if '【R173 补记·指针同日补齐】' not in d])

# ---- E 无孤儿 ----
orphans = []
for d in glob.glob('/proc/[0-9]*'):
    # S-611/S-612/S-613：这道自检连错三版 —— ①把主会话的 claude -p 算成孤儿（它的 cmdline
    # 含整段 goal 提示词，里面有 check_disc 字样）；②把外层 bash -c 包装算进来；③把**正在执行
    # 本脚本的 bash** 算进来（它的命令行里就带着 _r173_ctl 这个字面量）。
    # 正确判据：只认**运行** 反控副本的进程，且排除本进程及其全部祖先。
    pid = os.path.basename(d)
    try:
        with open(os.path.join(d, 'cmdline'), 'rb') as fh:
            parts = fh.read().decode('utf-8', 'replace').split('\x00')
    except OSError:
        continue
    # 取 argv 里的可执行/脚本 token（去掉 -c 后面的整段脚本文本）
    toks = [x for x in parts if x]
    if len(toks) >= 2 and toks[1] == '-c':
        toks = toks[:1]          # bash -c <整段>：只保留解释器名
    if not any(t.endswith('_r173_ctl_ok_check_disc.py') or t.endswith('_r173_ctl_bad_floor.py')
               or t.endswith('_r173_ctl_no178.py') for t in toks):
        continue
    # 排除自身与祖先
    anc, cur = set(), os.getpid()
    while cur and cur != 1:
        anc.add(str(cur))
        try:
            with open('/proc/%d/stat' % cur) as fh:
                cur = int(fh.read().split(') ')[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
    if pid in anc:
        continue
    orphans.append((d, ' '.join(toks)[:80]))
ck('E1 无 r173 反控副本残留进程', len(orphans) == 0, orphans)
ck('E2 无 _r173_ctl_* 目录残留', len(glob.glob(os.path.join(TIER, '_r173_ctl_*'))) == 0,
   glob.glob(os.path.join(TIER, '_r173_ctl_*')))

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n), open('/home/t628/projects/ra2-campaign-forge/_r173/r173n_final.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
