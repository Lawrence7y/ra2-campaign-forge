# -*- coding: utf-8 -*-
# N-10 问题卡登记件 独立复核（只读；唯一产物=本脚本，前缀 _verify_）
# 运行：python -I -X utf8 <绝对路径>
import hashlib, os, re, subprocess

BASE = 'D:/Project/ra2-campaign-forge/'
CARD = BASE + 'lead/d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md'
FPOUT = BASE + 'lead/d13d14_cards_20261108/_n10_fingerprint_out.txt'
PEND = BASE + 'lead/PENDING_DECISIONS.md'


def read(p):
    return open(p, encoding='utf-8').read()


def lines(p):
    return read(p).splitlines()


card = read(CARD)
cl = lines(CARD)
pend = lines(PEND)

print('=== A. 被核对象指纹（hashlib 实算） ===')
b = open(CARD, 'rb').read()
print('CARDS sha256 =', hashlib.sha256(b).hexdigest())
print('CARDS bytes  =', len(b))

print()
print('=== B. 逐字转录：D-13 / D-14 ===')
i1 = next(i for i, L in enumerate(cl) if '### 1.1 D-13' in L)
i2 = next(i for i, L in enumerate(cl) if '证据路径勘误' in L)
j1 = next(i for i, L in enumerate(cl) if '### 1.2 D-14' in L)
j2 = next(i for i, L in enumerate(cl) if '该条目位于' in L)
b13 = [L[2:] if L.startswith('> ') else L[1:] for L in cl[i1:i2] if L.startswith('>')]
b14 = [L[2:] if L.startswith('> ') else L[1:] for L in cl[j1:j2] if L.startswith('>')]
print('D-13 PENDING:22-45 EXACT =', b13 == pend[21:45], '(card', len(b13), 'lines / source', len(pend[21:45]), ')')
print('D-14 PENDING:47-64 EXACT =', b14 == pend[46:64], '(card', len(b14), 'lines / source', len(pend[46:64]), ')')

print()
print('=== C. RULING_D24 / GOAL_RE_CONTINUOUS / NEXT_STEPS 引文逐字核对 ===')
d24 = lines(BASE + 'lead/re_line_20261105/D24_RULING/RULING_D24.md')
goal = lines(BASE + 'lead/re_line_20261105/GOAL_RE_CONTINUOUS.md')
nxt = lines(BASE + 'lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md')
checks = [
    ('RULING_D24:63', d24[62]), ('RULING_D24:70', d24[69]),
    ('RULING_D24:71', d24[70]), ('RULING_D24:78', d24[77]),
    ('GOAL:89', goal[88]), ('GOAL:91', goal[90]), ('GOAL:96', goal[95]),
    ('NEXT_STEPS:95', nxt[94]), ('NEXT_STEPS:97', nxt[96]),
]
for name, src in checks:
    # card quotes drop leading list/bold/indent markers; test core substring presence
    core = src.strip().lstrip('->| ').strip('*').strip()
    # use a distinctive 20-char window
    win = core[10:40] if len(core) > 40 else core
    print(name, 'source-window-in-card =', win in card, '|', repr(win[:28]))

print()
print('=== D. 7 卡「当前状态」枚举（proposed / decided 分离） ===')
for q in range(1, 8):
    tag = '### N10-C%02d' % q
    i = card.find(tag)
    j = card.find('### N10-C%02d' % (q + 1))
    blk = card[i:j if j > 0 else card.find('\n---\n', i)]
    m = re.search(r'\*\*当前状态\*\*：(.+)', blk)
    print('N10-C%02d' % q, '->', m.group(1).strip()[:150] if m else 'MISSING')

print()
print('=== E. proposed 卡内是否误写「已裁/decided」 ===')
for q in [1, 2, 3, 4, 6, 7]:
    tag = '### N10-C%02d' % q
    i = card.find(tag)
    j = card.find('### N10-C%02d' % (q + 1))
    blk = card[i:j if j > 0 else card.find('\n---\n', i)]
    status = re.search(r'\*\*当前状态\*\*：(.+)', blk)
    s = status.group(1) if status else ''
    bad = ('decided' in s.lower()) or ('已裁' in s and 'proposed' not in s)
    print('N10-C%02d' % q, 'status-line-has-decided =', bad, '|', s.strip()[:110])

print()
print('=== F. D-14 双口径：四系数是否在 §4.1 表内并列，是否有单报 ===')
t = card[card.find('## 4 任务 3'):card.find('## 5 任务 4')]
vals = ['−0.0403', '−0.040268', '+0.0395', '+0.039451',
        '+0.3474', '+0.347432', '+0.3461', '+0.346119']
for v in vals:
    print(' ', v, 'in §4.1 =', v in t)
print('  §4.1 同时含 64 moving 与 97 全量 =', ('64 moving' in t and '97 全量' in t))
print('  §4.1 含「裁前双口径、不单报」 =', '裁前双口径、不单报' in t)
print('  §4.1 含「不单报」 =', '不单报' in t)
# 全文中该 8 值出现次数（单报检测：看是否只有其中一套）
print('  full-card occurrence counts:')
for v in vals:
    print('   ', v, card.count(v))
print('  full-card 64 moving count =', card.count('64 moving'), '| 97 全量 count =', card.count('97 全量'))

print()
print('=== G. 禁语 / 实施采集 / 解除暂停 / 代提交 扫描 ===')
forbidden = ['gamemd.exe', 'ra2loader', 'YURI.exe', 'taskkill',
             'MiniDump', 'SuspendThread', 'StackWalk', 'OpenProcess',
             'ReadProcessMemory', 'ctypes', '探针注入']
for f in forbidden:
    n = card.count(f)
    # 所有出现处应位于「不实施/不授权/不写」声明语境
    print('  token', f, 'count =', n)
print('  含「不实施采集」 =', '不实施采集' in card)
print('  含「不解除暂停」 =', '不解除暂停' in card)
print('  含「登记完成 ≠ 获得实施授权」 =', '登记完成 ≠ 获得实施授权' in card)
print('  含「不代用户把问题卡提交给裁决会话」 =', '不代用户把问题卡提交给裁决会话' in card)
print('  含「不代提交」 =', '不代提交' in card)
# 检查是否有肯定式「已实施/已提交/已解除」
for bad in ['已实施采集', '已解除暂停', '已提交裁决会话', '已代为提交', '已放行采集']:
    print('  bad-phrase', bad, '=', bad in card)

print()
print('=== H. 写域文件清单 + 指纹输出件内容 ===')
wd = BASE + 'lead/d13d14_cards_20261108/'
print('  write-domain files =', sorted(os.listdir(wd)))
print('  --- _n10_fingerprint_out.txt ---')
print(read(FPOUT))

print()
print('=== I. PENDING 指纹（是否等于编排方清单 7f68…） ===')
pb = open(PEND, 'rb').read()
print('  PENDING sha256 =', hashlib.sha256(pb).hexdigest(), 'bytes =', len(pb))
print('  matches orchestrator =', hashlib.sha256(pb).hexdigest() ==
      '7f68fc6c6ed1ab6ba16210b611906c6189ad0af90a84b46b263a19379fbfcd48')

print()
print('=== J. git HEAD / status（只读） ===')
r = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=BASE, capture_output=True, text=True)
print('  HEAD =', r.stdout.strip(), '| exit', r.returncode)
r = subprocess.run(['git', 'status', '--porcelain', '-uall', '--',
                    'lead/PENDING_DECISIONS.md', 'lead/d13d14_cards_20261108/'],
                   cwd=BASE, capture_output=True, text=True)
print('  git status (PENDING + write-domain):')
for L in r.stdout.splitlines():
    print('   ', L)
print('  exit', r.returncode)
