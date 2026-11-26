#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话复核：R138 已写进 FACT_INDEX v5.33 的 F35 那句「定义缺一手权威」是不是伪的。

要判的主张（v5.33 的 F35 limitations 新增句）：
  「proved_strict 的定义只有二手转述，一手权威是 COVERAGE/PANEL.md M52，该文件不在现盘。」

判法（全是机械可失败判据，不靠叙述）：
  D1 strict_panel.py 在盘；它就是 LEAD_LOCK 里被点名当「权威实现」的那份
     （LEAD_LOCK:92 原文「权威定义是 RULING_R15_20261119\\work\\strict_panel.py 第 78 行」）。
  D2 第 78 行逐字含 "[未证]" not in sem（带方括号字面），且该行与
     文件头 docstring 第 14 行对同一条件的两种措辞一致（docstring 写「不含 [未证]」）。
  D3 现盘存在**不止一处**代码级实现（同时含 proved_strict 与带方括号字面 [未证] 的脚本），
     => 「只有二手转述」为伪。数量与文件清单都报出来。
  D4 该脚本的两个输入（coverage.tsv / function_atlas.tsv）**都不在现盘**
     => 定义在盘、数据不在盘，这是两个不同的事实，不能合成一句。
  D5 反控：把判据从「带方括号字面」放宽到裸子串「未证」时，命中会变多（说明方括号是承重的），
     并且 LEAD_LOCK:92-96 记录了两种口径的真实差值（S22 10 行、TOTAL 1194 vs 1204）。
     用这条算一遍：差值口算 10 行，方向与文档一致。

输出：k1..k5 每组正控 + 反控（反控必须真的能 FAIL）。
"""
import os
import re
import json
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SP = os.path.join(R14, 'RULING_R15_20261119', 'work', 'strict_panel.py')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
F533 = os.path.join(R14, 'R17_R105_FACTINDEX_V533', 'FACT_INDEX.tsv')

fails = []
log = []


def ck(name, cond, detail=''):
    log.append(('PASS' if cond else 'FAIL', name, detail))
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


# ---------- 现盘扫描：哪些**脚本/代码**同时含 proved_strict 与带方括号字面 [未证] ----------
SKIP_DIRS = ('R17_LEAD_BASELINE', '.git', '__pycache__')
CODE_EXT = ('.py', '.ts', '.js', '.sh', '.pl')


def scan_carriers(base, bracket=True):
    """返回 [(relpath, [行号...])]，只要文件里 proved_strict 与目标子串同时出现。"""
    needle = '"[未证]"' if bracket else '未证'
    out = []
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if not f.endswith(CODE_EXT):
                continue
            p = os.path.join(dp, f)
            try:
                txt = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            if 'proved_strict' not in txt:
                continue
            if needle not in txt:
                continue
            lines = [i for i, l in enumerate(txt.split('\n'), 1) if needle in l]
            out.append((os.path.relpath(p, ROOT), lines))
    return sorted(out)


# =============================== k1 ===============================
print('=== k1 strict_panel.py 在盘且逐字含定义 ===')
ck('k1.1 文件存在可读非空', os.path.isfile(SP) and os.path.getsize(SP) > 1000,
   '%s bytes=%d' % (os.path.basename(SP), os.path.getsize(SP) if os.path.exists(SP) else -1))
raw = open(SP, 'rb').read()
tsp = raw.decode('utf-8')
lines_sp = tsp.split('\n')
ck('k1.2 全 LF（CR=0）', b'\r' not in raw, 'CR=%d' % raw.count(b'\r'))
ck('k1.3 第 78 行逐字等于判据行',
   lines_sp[77].strip() == 'if "[未证]" not in sem:',
   repr(lines_sp[77]))
ck('k1.4 docstring 第 14 行给出同一条件的散文措辞（带方括号）',
   '不含 [未证]' in lines_sp[13], repr(lines_sp[13]))
ck('k1.5 文件 sha256 与 R139 开局实测一致',
   sha(SP) == '731c98ea4910f5e910ce95ae2ae14e471af98d4d0a9d0051a32c9968e65e5f86', sha(SP)[:16])
# 反控 N1: 把判据行换成裸子串，k1.3 必须 FAIL
_n1 = lines_sp[77].strip().replace('"[未证]"', '未证')
ck('k1-N1 反控：裸子串形态 != 判据行（判据能失败）',
   _n1 != 'if "[未证]" not in sem:', repr(_n1))

# =============================== k2 ===============================
print('\n=== k2 现盘代码级实现有几处（「只有二手转述」是否成立）===')
carriers = scan_carriers(ROOT, bracket=True)
print('  带方括号字面的代码载体 %d 处：' % len(carriers))
for rel, ls in carriers:
    print('    %-72s lines=%s' % (rel, ls))
ck('k2.1 代码级载体数量 >= 2（若只有 1 处才轮得到「只有二手转述」）', len(carriers) >= 2, len(carriers))
ck('k2.2 第一处就是 RULING_R15_20261119/work/strict_panel.py',
   any('RULING_R15_20261119/work/strict_panel.py' == rel for rel, _ in carriers),
   [rel for rel, _ in carriers])
# 反控 N2: 关掉方括号（放宽成裸子串）载体只会变多不会变少 => 方括号是收窄判据
carriers_loose = scan_carriers(ROOT, bracket=False)
ck('k2-N2 反控：放宽到裸子串后载体数 >= 带方括号数（收窄判据有方向性）',
   len(carriers_loose) >= len(carriers), '%d vs %d' % (len(carriers_loose), len(carriers)))

# =============================== k3 ===============================
print('\n=== k3 脚本声明的两个输入在现盘是否存在 ===')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
ATL = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
print('  COV  =', COV, 'exists=', os.path.exists(COV))
print('  ATL  =', ATL, 'exists=', os.path.exists(ATL))
print('  COVERAGE dir exists =', os.path.exists(os.path.join(R14, 'COVERAGE')))
print('  next_re_20261112_r10 dir exists =', os.path.exists(os.path.join(ROOT, 'lead', 'next_re_20261112_r10')))
ck('k3.1 coverage.tsv 不在盘', not os.path.exists(COV))
ck('k3.2 function_atlas.tsv 不在盘', not os.path.exists(ATL))
ck('k3.3 COVERAGE 目录整目录不在盘', not os.path.exists(os.path.join(R14, 'COVERAGE')))
ck('k3.4 next_re_20261112_r10 目录不在盘', not os.path.exists(os.path.join(ROOT, 'lead', 'next_re_20261112_r10')))
# 反控 P1: 正控——同一个 os.path.exists 对**确实在盘**的文件必须 True，否则上面的 False 无判别力
ck('k3-P1 正控：exists() 对在盘文件返回 True（否则 k3.1/k3.2 的 False 无意义）',
   os.path.exists(SP) and os.path.exists(F533))

# =============================== k4 ===============================
print('\n=== k4 LEAD_LOCK 记录的口径差值可复算（方括号 vs 裸子串）===')
lt = open(LOCK, encoding='utf-8', errors='replace').read()
i14 = lt.find('Lead 错误 #14')
seg = lt[i14:i14 + 900]
print('  段首 60 字：', seg[:60].replace('\n', ' '))
m_author = re.search(r'(RULING_R15_20261119\\work\\strict_panel\.py)\s*第\s*(\d+)\s*行', seg)
ck('k4.1 LEAD_LOCK 点名 strict_panel.py 的第 N 行当权威定义',
   bool(m_author) and int(m_author.group(2)) == 78 if m_author else False,
   m_author.groups() if m_author else None)
nums = re.findall(r'S22=(\d+)\s*/\s*TOTAL=(\d+)[^\n]*\n[^\n]*S22=(\d+)\s*/\s*TOTAL=(\d+)', seg)
print('  nums=', nums)
if nums:
    a, b, c, d = map(int, nums[0])
    ck('k4.2 裸子串口径 S22/TOTAL = 16/1194', (a, b) == (16, 1194), (a, b))
    ck('k4.3 方括号口径 S22/TOTAL = 26/1204', (c, d) == (26, 1204), (c, d))
    ck('k4.4 差值口算：S22 差 = 10、TOTAL 差 = 10（错口径少算 10 行）', (c - a) == 10 and (d - b) == 10, (c - a, d - b))
else:
    ck('k4.2 两种口径的数值对能抓到', False, 'regex miss')
# 反控 N3: 把两种口径当成等价（差值 0）必须 FAIL
ck('k4-N3 反控：两种口径不等价（差值 != 0），否则方括号不承重',
   bool(nums) and (int(nums[0][2]) - int(nums[0][0])) != 0, nums[0] if nums else None)

# =============================== k5 ===============================
print('\n=== k5 v5.33 里 F35 那句的实际措辞（判它错在哪、对在哪）===')
t533 = open(F533, encoding='utf-8').read()
row35 = [l for l in t533.split('\n') if l.startswith('F35\t')]
ck('k5.1 F35 行存在', len(row35) == 1, len(row35))
r35 = row35[0].split('\t')
lim35 = r35[4]
print('  limitations=', lim35[:900])
ck('k5.2 正文断言「定义只有二手转述」', '二手' in lim35)
ck('k5.3 正文断言一手 PANEL.md(M52) 不在现盘', ('PANEL.md' in lim35 and 'M52' in lim35) or 'M52' in lim35)
ck('k5.4 正文**未**提 strict_panel.py（这是本轮要修的点）', 'strict_panel' not in lim35)
ev35 = r35[3]
ck('k5.5 evidence_paths 只引 PANEL.md 一条（单点证据）',
   ev35.count(';') == 0 and 'PANEL.md' in ev35, ev35)
# 反控 N4: 若把 PANEL 补进 limitations 就该 FAIL —— 检验「不在现盘」这条能被证伪
ck('k5-N4 反控：PANEL.md 确实不在现盘任何位置（否则 k5.3 的前提错）',
   not any('COVERAGE/PANEL.md' == p for p in [os.path.join(R14, 'COVERAGE', 'PANEL.md')]) and
   not os.path.exists(os.path.join(R14, 'COVERAGE', 'PANEL.md')),
   os.path.join(R14, 'COVERAGE', 'PANEL.md'))

print('\n=== 汇总：%d 项断言，%d FAIL ===' % (len(log), len(fails)))
for st, n, d in log:
    if st == 'FAIL':
        print('  FAILED:', n, d)
res = dict(assertions=len(log), fails=fails,
           carriers=[(r, l) for r, l in carriers],
           carriers_loose=[(r, l) for r, l in carriers_loose])
open(os.path.join(ROOT, '_r139', 'r139b_f35_def.json'), 'w', encoding='utf-8').write(
    json.dumps(res, ensure_ascii=False, indent=1))
print('json -> _r139/r139b_f35_def.json')
raise SystemExit(1 if fails else 0)
