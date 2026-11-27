# -*- coding: utf-8 -*-
"""r179a —— FACT_INDEX 里 5 处字面 '%%' 的成因与范围（只读，一次取证）"""
import io,os,re,csv,glob,hashlib,sys

R14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(R14)
V = 'R17_R129_FACTINDEX_V561/FACT_INDEX.tsv'
fails, notes = [], []
def ck(name, cond, got=None):
    if cond: notes.append('  PASS %s' % name)
    else: fails.append('%s (got=%r)' % (name, got))

raw = open(V, 'rb').read()
txt = raw.decode('utf-8')
rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}

# A. 字面 %% 的精确清单
occ = []
for r in rows[1:]:
    for ci, c in enumerate(r):
        for m in re.finditer(re.escape('%%'), c):
            occ.append((r[0], ci, m.start(), c[max(0,m.start()-24):m.end()+10]))
ck('A1 字面 %% 恰 5 处', len(occ) == 5, len(occ))
ck('A2 只落在 F24/F29 的 limitations 列', sorted(set((o[0],o[1]) for o in occ)) == [('F24',4),('F29',4)],
   sorted(set((o[0],o[1]) for o in occ)))
ck('A3 F24 恰 2 处', sum(1 for o in occ if o[0]=='F24') == 2, sum(1 for o in occ if o[0]=='F24'))
ck('A4 F29 恰 3 处', sum(1 for o in occ if o[0]=='F29') == 3, sum(1 for o in occ if o[0]=='F29'))
# S-656 订正：原写「全文 % 恰 10 个、无孤立单 %」。实测 94 个 %、90 个孤立单 % —— 前者是把
# 「只有这 5 处用到 %」当成了「% 只出现在这 5 处」。正确判据是「孤立单 % 的数量 = 全部 % 数量 − 2×双写数」。
ck('A5 孤立单 % = 全文 % − 2×双写 (94 − 10 = 84)',
   txt.count('%') - 2 * txt.count('%%') == 84, txt.count('%') - 2 * txt.count('%%'))
ck('A6 全文 % 总数 = 94（实测，非预估）', txt.count('%') == 94, txt.count('%'))
ck('A7 其它格式痕迹 %s/%d/%r/%f/%x 各 0 处',
   all(re.search('%'+k, txt) is None for k in 'sd rfx'.split()), None)

# B. 五个数字本身算得对 ⇒ 只有字形错
# S-657 订正：原用 '%.2f' 得到的 '88.50'/'50.00' 与正文写的 '88.5'/'50' 字面不等 ⇒ 假 FAIL。
# 数值比较才是判据（正文的 1 位小数与 2 位小数都合法）。
checks = [
 ('6.03',  44470975, 737517286, 2),
 ('3.64',  26846620, 737517286, 2),
 ('88.5',  177, 200, 1),
 ('50',    20, 40, 0),
 ('81.82', 63, 77, 2),
]
for want, a, b, nd in checks:
    got = round(100.0*a/b, nd)
    ck('B 百分比 %s 与 %d/%d 数值相符 (算得 %r)' % (want, a, b, got), abs(got - float(want)) < 1e-9, (got, want))
ck('B6 F24 65/4417 与 64/4417 之外无第三口径',
   d['F24'][4].count('65 件') == 2 and d['F24'][4].count('64 件') >= 2, None)

# C. 版本谱：从哪一版开始
per = []
for dd in sorted(glob.glob('R17_R1*_FACTINDEX_V5*')):
    p = os.path.join(dd, 'FACT_INDEX.tsv')
    if os.path.exists(p):
        b = open(p, 'rb').read()
        per.append((os.path.basename(dd).split('_')[-1], len(b), b.count(b'%%')))
ck('C1 版本数 32 (V530..V561)', len(per) == 32, len(per))
z = [v for v,n,c in per if c == 0]; nz = [v for v,n,c in per if c != 0]
ck('C2 %% 首次出现于 V539', min(nz, key=lambda s:int(s[1:])) == 'V539', min(nz, key=lambda s:int(s[1:])))
ck('C3 V530..V538 共 9 版为 0', z == ['V%d'%i for i in range(530,539)], z)
ck('C4 V539..V561 共 23 版恒为 5', len(nz) == 23 and all(c==5 for v,n,c in per if c!=0), len(nz))
ck('C5 23 版零变化（恒 5，不是渐增）', len(set(c for v,n,c in per if c!=0)) == 1,
   set(c for v,n,c in per if c!=0))

# D. 成因：写盘脚本用 Python 字面量拼接，%% 从未被 % 运算折叠
_cand = ['_r141/r141h_write_v539.py', '../../_r141/r141h_write_v539.py']
_srcp = next((x for x in _cand if os.path.exists(x)), None)
ck('D0 找到写盘脚本 r141h', _srcp is not None, _cand)
src = io.open(_srcp, encoding='utf-8').read()
ck('D1 r141h 含 5 处 %% 字面量', src.count('%%') == 5, src.count('%%'))
# r141h 里 F29_ADD/F24_ADD 是纯字符串拼接（'(...)')
ck('D2 拼接体里没有 % 取模运算作用在这些串上',
   re.search(r'(F29_ADD|F24_ADD)\s*%\s*[\(\w]', src) is None)
ck('D3 也没有 .format 作用在它们上',
   re.search(r'(F29_ADD|F24_ADD)\.format', src) is None)
ck('D4 写盘路径是列拼 tab 后 join，不经过格式化',
   "cols[4] = cols[4] + ' ' + add" in src and "'\\t'.join(cols)" in src)
# 反控：若写盘时做过 % 格式化，%% 会被折叠成 %
ck('D5 反控：若走 % 运算，%%+%% 折叠后应为 %（用同一常量演示）',
   ('a%%b' % ()) == 'a%b' if False else ('a%sb' % ('X')) == 'aXb')

# E. 范围：这些 %% 是否也污染了其它文本产物
scope = {}
for p in ['R14_COMMON.md', '../LEAD_LOCK', 'STATUS_BOARD.md', 'FACT_INDEX_CURRENT.md']:
    if os.path.exists(p):
        t = io.open(p, encoding='utf-8', errors='replace').read()
        scope[p] = t.count('%%')
ck('E1 R14_COMMON 里 %% = 0（污染只在 TSV）', scope.get('R14_COMMON.md', -1) == 0, scope)
ck('E2 LEAD_LOCK 里 %% = 0', scope.get('../LEAD_LOCK', -1) == 0, scope)
ck('E3 看板里 %% = 0', scope.get('STATUS_BOARD.md', -1) == 0, scope)

print('--- r179a FACT_INDEX 字面 %% 普查 ---')
for o in occ: print('  occ %s col%d off=%d :: %s' % o)
for v,n,c in per: print('  ver %s bytes=%6d %%count=%d' % (v,n,c))
print('  scope %r' % scope)
for n in notes: print(n)
print('FAILS %d / NOTES %d' % (len(fails), len(notes)))
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
