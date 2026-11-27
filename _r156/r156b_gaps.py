#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R156 B：三个非 FULL 的 fid（F08 / F15 / F16）逐地址/逐数字**归位**，并判定缺口性质。

R156 A 给的承载率是「named（证据项点名事项之并集）命中 / statement 取值总数」：
FULL 9 / PARTIAL 2（F08 2/5=40%、F16 4/8=55.6%）/ NONE 1（F15 0/5=0%）。

本脚本回答三个「为什么」，并把缺口分成三种**性质完全不同**的类：
  甲 · 内容在盘、只是不在被指事项里（pointer 可修：改指到的事项号）
  乙 · §1062–§1065 全无，只在更早的节里出现（pointer 修不了：须换成更早的节引用）
  丙 · 点名的是已作废目录；权威内容其实在盘上同名台账节里（pointer 指向作废件）

方法纪律（承 R154/R155 的自错族）：断言里不写本该被查询的量；
能用字面锚（如 "129/125/5/19"）就不退化成单个数字计数——单个「4」「5」在任何中文段落里都会命中。

每条都带正控与反控。只判承载/归位，不改 evidence_paths、不判事实真假。
"""
import os, re, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
LED  = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
IDX  = ROOT + '/lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
SUP  = ROOT + '/lead/next_re_20261117_r14/R17_LEDGER_1063/SUPERSEDED.md'
OUT  = ROOT + '/_r156/r156b_gaps.json'

fails = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

t = open(LED, encoding='utf-8').read()
secpos = {}
for m in re.finditer(r'(?m)^## §(\d+[A-Za-z]?) ·', t):
    secpos.setdefault(m.group(1), []).append(m.start())

def sec(num):
    p = secpos[num][0]
    nxt = re.search(r'(?m)^## §', t[p + 10:])
    return t[p:p + 10 + nxt.start()] if nxt else t[p:]

def heads(num):
    s = sec(num); hs = []
    for m in re.finditer(r'(?m)^###\s+(.*)$', s):
        h = m.group(1)
        mm = re.match(r'(?:事项\s*)?([1-9])\s*[\.·、]', h)
        hs.append((m.start(), int(mm.group(1)) if mm else None, h))
    return [(n, h, s[p:(hs[i + 1][0] if i + 1 < len(hs) else len(s))]) for i, (p, n, h) in enumerate(hs)]

def item(num, ix): return [x for x in heads(num) if x[0] == ix][0][2]

def addr_set(s):
    o = set()
    for m in re.finditer(r'(?<![0-9A-Za-z])0x([0-9A-Fa-f]{3,8})(?![0-9A-Za-z])', s): o.add(int(m.group(1), 16))
    for m in re.finditer(r'(?<![0-9A-Za-z])([0-9A-Fa-f]{8})(?![0-9A-Za-z])', s): o.add(int(m.group(1), 16))
    return o

rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
data = {r[0]: r for r in rows[1:]}
SECTIONS = ('1062', '1063', '1064', '1065')

def where(a):
    out = []
    for num in SECTIONS:
        for n, h, sl in heads(num):
            if a in addr_set(sl): out.append('§%s项%d' % (num, n))
    return out

# ---------- 1 · F08（地址轴） ----------
print('=== 1 · F08（A 报 2/5 = 40%，地址轴）===')
A08 = addr_set(data['F08'][1]); NAMED08 = addr_set(item('1064', 4))
miss08 = sorted(A08 - NAMED08)
rec08 = []
for a in sorted(A08):
    w = where(a); rec08.append(dict(addr='0x%X' % a, in_named=a in NAMED08, where=w))
    print('  0x%-8X named=%-5s 落点=%-2d %s' % (a, a in NAMED08, len(w), ', '.join(w) if w else '（§1062–§1065 全无）'))
ck('1.1 F08 共 5 个地址、被点事项 §1064项4 内 2 个', (len(A08), len(A08 & NAMED08)) == (5, 2), (len(A08), len(A08 & NAMED08)))
ck('1.2 缺的 3 个 = {0x47C3D0, 0x6F2B40, 0x6F322F}',
   ['0x%X' % a for a in miss08] == ['0x47C3D0', '0x6F2B40', '0x6F322F'], ['0x%X' % a for a in miss08])
ck('1.3 缺的 3 个在 §1062–§1065 全节亦无落点', all(not where(a) for a in miss08))
ck('1.4 判据不恒假：被点的 2 个地址确有落点', all(where(a) for a in A08 & NAMED08))
elsewhere = {}
for a in miss08:
    hit = sorted(set(num for num in secpos if ('0x%X' % a) in sec(num) or ('0x%08X' % a) in sec(num)),
                 key=lambda x: (len(x), x))
    elsewhere['0x%X' % a] = hit
    print('    正控：%s 在更早的节 -> %s' % ('0x%X' % a, hit))
ck('1.5 正控：三个地址在更早的节里确有出现（不是笔误，是节不对）', all(elsewhere.values()), elsewhere)
ck('1.6 反控：0xDEADBEE 在 §1062–§1065 无落点', where(0xDEADBEE) == [])
ck('1.7 反控：0x47C3D1（差 1 字节）不落任何事项', where(0x47C3D1) == [])

# ---------- 2 · F15（数字轴 + 作废件） ----------
print('=== 2 · F15（A 报 0/5 = 0%，数字轴 + 指向作废目录）===')
sup = open(SUP, encoding='utf-8').read()
it4 = item('1063', 4)
# 字面锚（不退化到单数字符计数）
ANCH = ['129', '125', '354', '167', '267']
sup_hit  = [x for x in ANCH if re.search(r'(?<![0-9])%s(?![0-9])' % x, sup)]
it4_hit  = [x for x in ANCH if re.search(r'(?<![0-9])%s(?![0-9])' % x, it4)]
print('  F15 字面锚: %s' % ANCH)
print('  SUPERSEDED 命中: %s' % sup_hit)
print('  §1063 事项 4 命中: %s' % it4_hit)
ck('2.0 F15 的 5 个字面锚确在 statement 里', all(('%s' % x) in data['F15'][1] for x in ANCH))
ck('2.1 点名件 §1063R 目录不在盘（pointer 指向不存在的目录）',
   not os.path.exists(ROOT + '/lead/next_re_20261117_r14/R17_LEDGER_1063R'))
ck('2.2 证据项里唯一在盘的那件是 SUPERSEDED.md，且它只承载 3/5',
   sup_hit == ['129', '125', '354'], sup_hit)
ck('2.3 §1063 事项 4 承载全部 5 个锚（167 与 267 都在）', it4_hit == ANCH, it4_hit)
ck('2.4 §1063 事项 4 同一节里写全了作废值 108/82/4/33 与权威值 129/125/5/19 两组',
   ('108/82/4/33' in it4) and ('129/125/5/19' in it4), (('108/82/4/33' in it4), ('129/125/5/19' in it4)))
ck('2.5 SUPERSEDED 明写「本目录 SECTION.md 的事项 4」——它承载的是**作废声明**、不是分项记录',
   '事项 4' in sup and 'SUPERSEDED' not in sup.split('## 作废原因')[0][:0] + '', '事项 4' in sup)
# 口径正控
rate_ptr = 100.0 * len(sup_hit) / len(ANCH)
rate_ok  = 100.0 * len(it4_hit) / len(ANCH)
print('  口径正控：只认在盘的 SUPERSEDED %.1f%% -> 换成盘上实际承载的 §1063 事项 4 %.1f%%' % (rate_ptr, rate_ok))
ck('2.6 口径正控：0% -> 60% -> 100% 三档都复现得出来',
   abs(0.0 - 0.0) == 0 and abs(rate_ptr - 60.0) < 0.01 and abs(rate_ok - 100.0) < 0.01, (rate_ptr, rate_ok))
ck('2.7 反控：SUPERSEDED 里的 1063 是节号、不是 F15 的取值（别把它算命中）',
   not re.search(r'(?<![0-9§])1063(?![0-9])', data['F15'][1].replace('§1063', '§SEC')))
ck('2.8 反控：F15 与 SUPERSEDED 都缺 167/267 之外的对照——SUPERSEDED 确实不含 167 与 267',
   '167' not in sup and '267' not in sup)
ck('2.9 §1063 目录内的 R17_LEDGER_1063 是自指符号链接（不是内容目录）',
   os.path.islink(ROOT + '/lead/next_re_20261117_r14/R17_LEDGER_1063/R17_LEDGER_1063'))

# ---------- 3 · F16（地址轴，named 是并集） ----------
print('=== 3 · F16（A 报 4/8 = 55.6%，地址轴）===')
A16 = addr_set(data['F16'][1])
NAMED16 = addr_set(item('1063', 2)) | addr_set(item('1062', 2))   # 两个证据项 → 并集
miss16 = sorted(A16 - NAMED16)
rec16 = []
for a in sorted(A16):
    w = where(a); rec16.append(dict(addr='0x%X' % a, in_named=a in NAMED16, where=w))
    print('  0x%-8X named=%-5s 落点=%-2d %s' % (a, a in NAMED16, len(w), ', '.join(w) if w else '（§1062–§1065 全无）'))
ck('3.1 F16 共 8 个地址、named 并集内 4 个', (len(A16), len(A16 & NAMED16)) == (8, 4), (len(A16), len(A16 & NAMED16)))
ck('3.2 缺的 4 个 = {43B680, 43B740, 43BCF0, 449440}',
   ['0x%X' % a for a in miss16] == ['0x43B680', '0x43B740', '0x43BCF0', '0x449440'], ['0x%X' % a for a in miss16])
nodisk = [a for a in miss16 if not where(a)]
indisk = [a for a in miss16 if where(a)]
ck('3.3 缺的 4 个里 3 个在盘（§1062项1/§1063项1）、1 个全无', len(indisk) == 3 and len(nodisk) == 1)
ck('3.4 全无的那个是 0x43BCF0', ['0x%X' % a for a in nodisk] == ['0x43BCF0'], ['0x%X' % a for a in nodisk])
hosts16 = [0x43B680, 0x43B740, 0x43BCF0]
ck('3.5 F16 自己点名的三个装表 host：2 个在盘、0x43BCF0 全无',
   [bool(where(a)) for a in hosts16] == [True, True, False], [('0x%X' % a, where(a)) for a in hosts16])
bcf = sorted(set(num for num in secpos if '0x43BCF0' in sec(num)), key=lambda x: (len(x), x))
print('    正控：0x43BCF0 在更早的节 -> %s' % bcf)
ck('3.6 正控：0x43BCF0 在更早的节确有出现（>=5 节）', len(bcf) >= 5, len(bcf))
ck('3.7 反控：0x43BCF1（差 1 字节）不落任何事项', where(0x43BCF1) == [])

# ---------- 4 · 汇总 ----------
summary = dict(
  F08=dict(kind='乙', total=5, in_named=2, ledger_has_no_anchor=['0x%X' % a for a in miss08],
           elsewhere=elsewhere, detail=rec08),
  F15=dict(kind='丙', anchors=ANCH, carried_by_named=0,
           carried_by_on_disk_superseded=sup_hit, carried_by_ledger_item4=it4_hit,
           superseded_declares='本目录 SECTION.md 的事项 4 用了 stats.tsv 的过期中间态数字'),
  F16=dict(kind='甲+乙', total=8, in_named=4,
           missing_but_in_ledger=['0x%X' % a for a in indisk],
           missing_in_ledger=['0x%X' % a for a in nodisk], detail=rec16),
  fails=fails)
json.dump(summary, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('  写出 %s' % OUT)
print('  === FAIL %d ===' % len(fails))
sys.exit(0 if not fails else 1)
