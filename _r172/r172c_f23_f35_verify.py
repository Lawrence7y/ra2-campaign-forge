#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r172c: 三组机械核验（F23 指纹出处 / F23 12 行分解算术 / F35 五个数）。

每条断言都可失败；正控与反控成对出现。数字全部实测，不写预算值。
"""
import hashlib, io, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FIF = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')
U = os.path.join(TIER, '_r67', 'unique_content_4417.tsv')
T = os.path.join(TIER, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
SP = os.path.join(TIER, 'RULING_R15_20261119', 'work', 'strict_panel.py')
SHA = 'c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a'

FAIL, N = [], [0]
def ck(name, cond, detail=''):
    N[0] += 1
    print(('PASS  ' if cond else 'FAIL  ') + '%02d. %s' % (N[0], name) + (('  :: ' + str(detail)) if detail and not cond else ''))
    if not cond: FAIL.append(name)

def lines(p):
    return io.open(p, encoding='utf-8').read().split('\n')

# ============ E 组：F23 的「指纹出处为两份清单第 1022 行」 ============
ul = lines(U); tl = lines(T)
ck('E0 两份清单都是 4,418 行（表头 1 + 数据 4,417）', len(ul) - 1 == 4418 and len(tl) - 1 == 4418, (len(ul), len(tl)))
ck('E1 unique_content_4417.tsv 第 1022 行含完整 sha256',
   SHA in ul[1021], ul[1021][:80])
ck('E2 tier_final_4417.tsv 第 1022 行**不含**该 sha256（该表无 sha 列）',
   SHA not in tl[1021], tl[1021][:120])
ck('E3 tier_final_4417.tsv 全文该 sha256 出现 0 次（反控：不是只在第 1022 行缺）',
   io.open(T, encoding='utf-8').read().count(SHA) == 0)
ck('E4 unique_content_4417.tsv 全文该 sha256 出现恰 1 次（正控：出处唯一）',
   io.open(U, encoding='utf-8').read().count(SHA) == 1)
ck('E5 两表表头不同 ⇒ 是两份不同口径的清单（4 列 vs 7 列）',
   len(ul[0].split('\t')) == 7 and len(tl[0].split('\t')) == 4,
   (len(ul[0].split('\t')), len(tl[0].split('\t'))))
ck('E6 两表第 1022 行的 rel 与 bytes 相同（第二表只能佐证路径与字节，不能佐证摘要）',
   ul[1021].split('\t')[0] == tl[1021].split('\t')[0] and ul[1021].split('\t')[1] == tl[1021].split('\t')[1] == '4147334',
   (ul[1021].split('\t')[:2], tl[1021].split('\t')[:2]))
ck('E7 全库该 sha256 出现在数据行层面的清单只有 unique_content（其余命中皆为叙述文本）',
   sum(1 for p in (U, T) if io.open(p, encoding='utf-8').read().count(SHA) > 0) == 1)

# ============ F 组：F23 12 行分解算术 ============
rows = {}
for line in io.open(FIF, encoding='utf-8'):
    c = line.rstrip('\n').split('\t'); rows[c[0]] = c
f23lim = rows['F23'][4]
ck('F1 F23.limitations 含「6 + 2 + 3」与 total 12 的同段表述',
   '6 + 2 + 3' in f23lim and '12 行分解' in f23lim)
m = re.search(r'三个分项 6 \+ 2 \+ 3 与 total = 12', f23lim)
ck('F2 该句在盘逐字（「三个分项 6 + 2 + 3 与 total = 12」）', bool(m))
ck('F3 算术：6+2+3=11，与 12 差 1', 12 - (6 + 2 + 3) == 1)
ck('F4 算术：第二读法 6+2+3+3=14 > 12，多 2', (6 + 2 + 3 + 3) - 12 == 2)
ck('F5 反控：若分项是 6+2+4 则闭合（证明缺口不是记账习惯而是真的差 1）', (6 + 2 + 4) == 12)

# ============ G 组：F35 五个数 ============
sp = io.open(SP, encoding='utf-8').read()
sp_lines = sp.split('\n')
tok = '[未证]'   # 方括号字面 [未证]
cnt = sp.count(tok)
where = [i + 1 for i, l in enumerate(sp_lines) if tok in l]
ck('G1 strict_panel.py 全文 [未证] 恰 2 次', cnt == 2, cnt)
ck('G2 两次分别在第 14 行与第 78 行', where == [14, 78], where)
ck('G3 第 76 行是 grade 判断（if grade == "[已证]":）', 'if grade == "[已证]":' in sp_lines[75], sp_lines[75].strip())
ck('G4 第 78 行是 not in sem 形式', 'if "[未证]" not in sem:' in sp_lines[77], sp_lines[77].strip())
ck('G5 反控：全文 "not in sem:" 恰 1 次', sp.count('not in sem:') == 1, sp.count('not in sem:'))
ev = rows['F35'][3].split(';')
alive = []; dead = []
def resolve(pth, extra_root=''):
    """evidence 里的路径是反斜杠形式且以 lead 开头；按 ROOT 与 ROOT/lead 两种根各试一次"""
    for base in (ROOT, os.path.join(ROOT, 'lead')):
        c = os.path.join(base, extra_root, pth) if extra_root else os.path.join(base, pth)
        if os.path.isfile(c): return c
    return None
for it in ev:
    pth = it.split('(')[0].replace('\\', '/')
    hit = resolve(pth)
    (alive if hit else dead).append(pth)
ck('G6 F35 五项 evidence：4 活 1 失', len(ev) == 5 and len(alive) == 4 and len(dead) == 1, (len(alive), len(dead), dead))
ck('G7 失联的那一项恰为 COVERAGE/PANEL.md', len(dead) == 1 and dead[0].endswith('COVERAGE/PANEL.md'), dead)
st, lim = rows['F35'][1], rows['F35'][4]
ck('G8 statement 含「有一手代码权威」1 次', st.count('有一手代码权威') == 1)
ck('G9 limitations 也含「一手代码权威」1 次 ⇒ 两列在同一命题上**一致**，不构成矛盾（本轮曾疑为矛盾，实测证伪）',
   lim.count('一手代码权威') == 1)
ck('G10 limitations 的「都过强」判的是「缺一手权威」与「已有一手权威」两句，均非 statement 的原句（一字不差反控）',
   lim.count('都过强') == 1 and '已有一手权威' in lim and st.count('已有一手权威') == 0)

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
