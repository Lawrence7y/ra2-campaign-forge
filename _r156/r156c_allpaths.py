#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R156 C：把承载性口径从「只测 R17_LEDGER_* 子集」改成「测证据项声明的**全部**路径」。

为什么必须改（审计员 #359 的四条批评，主会话已逐条复算，见 §2 各条）：
  A/B 只解析了形如 R17_LEDGER_*/SECTION.md(事项N) 的路径，把同一格里
  R14_COMMON.md(§2.9三)、BOARD_ARCHIVE.md(R17 第 N 轮 段)、GOAL_THREE_TARGETS(...)、以及 .tsv/.md 报告
  这些**同样在盘、同样被声明**的路径整个忽略了。于是 F08 只量第 ② 条得 40%（第 ① 条 5/5 全中）、
  F16 漏掉 R14_COMMON §2.9三（那一句里三个装表 host 逐字同现）。

路径六类，逐类解析成文本切片：
  1) R17_LEDGER_<n>/SECTION.md(事项N)   → 目录基本不在盘；同名台账节在盘（记 DIR_ABSENT_SECTION_PRESENT）
  2) R17_LEDGER_<n>/SUPERSEDED.md        → 在盘
  3) R14_COMMON.md(§a/b/c)               → 按节切（文件含 NUL，须容错读）
  4) BOARD_ARCHIVE.md(R17 第 N 轮 段)     → 按段切
  5) GOAL_THREE_TARGETS_...md(§n/...)    → 台账自身，按节切
  6) 其它 .tsv/.md 文件路径              → 在盘则整文件读入作文本，不在盘记 ABSENT

另设一条**显式重定向**（不当机械事实、单列并给出权威出处）：
  1063R/SECTION.md(事项N) → 台账 §1063 事项N
  依据：R17_LEDGER_1063/SUPERSEDED.md 第 12–13 行明写「台账 §1063 采用的是 R17_LEDGER_1063R 版本」。
  这个映射是**判断**，故矩阵同时给 with-redirect 与 without-redirect 两栏。

不改任何 evidence_paths。带正控与反控。
"""
import os, re, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D    = ROOT + '/lead/next_re_20261117_r14'
LED  = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
IDX  = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
RC   = D + '/R14_COMMON.md'
BA   = D + '/BOARD_ARCHIVE.md'
SUP  = D + '/R17_LEDGER_1063/SUPERSEDED.md'
OUT  = ROOT + '/_r156/r156c_allpaths.json'

fails = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

# ---------- 取值归一 ----------
def addr_set(s):
    o = set()
    for m in re.finditer(r'(?i)(?<![0-9a-z])0x([0-9a-f]{3,8})(?![0-9a-z])', s): o.add(int(m.group(1), 16))
    for m in re.finditer(r'(?i)(?<![0-9a-z])([0-9a-f]{8})(?![0-9a-z])', s): o.add(int(m.group(1), 16))
    return o

def num_set(s):
    s = re.sub(r'(?<![0-9A-Za-z.])(\d{1,3}(?:,\d{3})+)', lambda m: ' %s ' % m.group(1).replace(',', ''), s)
    s = re.sub(r'§\s*\d+', ' §SEC ', s)
    return set(int(x) for x in re.findall(r'(?<![0-9A-Za-z.])(\d{3,7})(?![0-9A-Za-z])', s))

# ---------- 台账节/事项 ----------
t = open(LED, encoding='utf-8').read()
secpos = {}
for m in re.finditer(r'(?m)^## §(\d+[A-Za-z]?) ·', t): secpos.setdefault(m.group(1), []).append(m.start())
def ledger_sec(num):
    p = secpos[num][0]; nx = re.search(r'(?m)^## §', t[p + 10:])
    return t[p:p + 10 + nx.start()] if nx else t[p:]
def ledger_items(num):
    s = ledger_sec(num); hs = []
    for m in re.finditer(r'(?m)^###\s+(.*)$', s):
        h = m.group(1); mm = re.match(r'(?:事项\s*)?([1-9])\s*[\.·、]', h)
        hs.append((m.start(), int(mm.group(1)) if mm else None))
    return [(n, s[p:(hs[i+1][0] if i+1 < len(hs) else len(s))]) for i, (p, n) in enumerate(hs)]
def ledger_item(num, ix):
    for n, tx in ledger_items(num):
        if n == ix: return tx
    return None

# ---------- 其它三个文本源 ----------
rc = open(RC, encoding='utf-8', errors='replace').read()
ba = open(BA, encoding='utf-8', errors='replace').read()
sup = open(SUP, encoding='utf-8').read()
# 注意：字符数 != 字节数（中文 3 B/字）。用字节数做量级断言，别拿字符数比字节阈值（R156 自错 S-417）。
rc_bytes = len(rc.encode('utf-8'))
ck('0.1 R14_COMMON 可读（按**字节** 1,339,419 B ± 读容错损耗）',
   rc_bytes > 1_300_000, '%d chars / %d bytes' % (len(rc), rc_bytes))
ck('0.2 R14_COMMON 确实含 NUL 字节（否则 errors=replace 这个防御是多余的）', '\x00' in rc, rc.count('\x00'))

def rc_section(numstr):
    m = re.search(r'(?m)^## %s\b' % re.escape(numstr), rc)
    if not m: return None
    nx = re.search(r'(?m)^## 2\.\d+\b', rc[m.start() + 5:])
    return rc[m.start(): m.start() + 5 + nx.start()] if nx else rc[m.start():]
for nm in ('2.9', '2.10', '2.8'):
    ck('0.3 §%s 节可解析' % nm, rc_section(nm) is not None)

def ba_round(n):
    m = re.search(r'(?m)^##.*R17 第 %d 轮' % n, ba)
    if not m: return None
    nx = re.search(r'(?m)^##\s', ba[m.start() + 5:])
    return ba[m.start(): m.start() + 5 + nx.start()] if nx else ba[m.start():]

# ---------- 路径解析 ----------
rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
data = {r[0]: r for r in rows[1:]}
ck('0.4 FACT_INDEX 数据行 54', len(data) == 54, len(data))

RE_LEDGER = re.compile(r'R17_LEDGER_([0-9A-Za-z]+)[\\/]+(SECTION\.md|SUPERSEDED\.md)(?:\(([^)]*)\))?')
RE_RC     = re.compile(r'R14_COMMON\.md\(([^)]*)\)')
RE_BA     = re.compile(r'BOARD_ARCHIVE\.md\(([^)]*)\)')
RE_GOAL   = re.compile(r'GOAL_THREE_TARGETS_20261018\.md\(([^)]*)\)')
RE_FILE   = re.compile(r'(lead[\\/][^\s;()]+\.(?:tsv|md|json|py))')

def resolve_paths(fid):
    """→ [(kind, target, text|None, why, redirect_ok)]"""
    out = []
    for it in data[fid][3].split(';'):
        it = it.strip()
        if not it: continue
        m = RE_LEDGER.search(it)
        if m:
            num, fn, topic = m.group(1), m.group(2), m.group(3)
            tp = (topic or '').replace('事项', '').strip()
            if fn == 'SUPERSEDED.md':
                out.append(('SUPERSEDED', num, sup, 'OK', False)); continue
            if num in secpos:
                out.append(('LEDGER_SEC', '%s(事项%s)' % (num, tp), ledger_sec(num),
                            'DIR_ABSENT_SECTION_PRESENT', False)); continue
            # 台账里没有同名节 —— 只有 1063R 这一例，试显式重定向
            if num == '1063R':
                ix = int(re.match(r'\d+', tp).group(0)) if re.match(r'\d+', tp) else None
                tx = ledger_item('1063', ix) if ix else None
                out.append(('REDIRECT', '1063R(事项%s)->§1063(事项%s)' % (tp, tp), tx,
                            'REDIRECT_VIA_SUPERSEDED' if tx else 'REDIRECT_FAIL', True)); continue
            out.append(('LEDGER', '%s(事项%s)' % (num, tp), None, 'NO_SECTION', False)); continue
        m = RE_RC.search(it)
        if m:
            spec = m.group(1); nums = re.findall(r'(2\.\d+)', spec)
            tx = ''.join((rc_section(n) or '') for n in nums)
            out.append(('R14_COMMON', spec, tx or None, 'OK' if tx else 'MISS', False)); continue
        m = RE_BA.search(it)
        if m:
            spec = m.group(1); mm = re.search(r'第\s*(\d+)\s*轮', spec)
            tx = ba_round(int(mm.group(1))) if mm else None
            out.append(('BOARD_ARCHIVE', spec, tx, 'OK' if tx else 'MISS', False)); continue
        m = RE_GOAL.search(it)
        if m:
            spec = m.group(1); nums = re.findall(r'§(\d+[A-Za-z]?)', spec)
            tx = ''.join(ledger_sec(n) for n in nums if n in secpos)
            out.append(('GOAL', spec, tx or None, 'OK' if tx else 'MISS', False)); continue
        m = RE_FILE.search(it)
        if m:
            rel = m.group(1).replace('\\', '/')
            p = os.path.join(ROOT, rel)
            if os.path.isfile(p):
                try: tx = open(p, encoding='utf-8', errors='replace').read()
                except Exception: tx = None
                out.append(('FILE', rel, tx, 'OK' if tx else 'MISS', False))
            else:
                out.append(('FILE', rel, None, 'ABSENT', False))
            continue
        out.append(('UNPARSED', it, None, 'UNPARSED', False))
    return out

FIDS = ['F04', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16']
allres = {}
print('  --- 路径解析总览 ---')
for f in FIDS:
    ps = resolve_paths(f); allres[f] = ps
    print('   %-4s %s' % (f, [(k, w) for k, tg, tx, w, rd in ps]))

ck('1.1 没有 UNPARSED 路径', not any(k == 'UNPARSED' for f in FIDS for k, _, _, _, _ in allres[f]),
   [f for f in FIDS if any(k == 'UNPARSED' for k, _, _, _, _ in allres[f])])
ck('1.2 F16 的 R14_COMMON §2.9三 解析成功',
   any(k == 'R14_COMMON' and tx for k, tg, tx, w, rd in allres['F16']))
ck('1.3 F08 的 R14_COMMON §2.9一/§2.10一/二 解析成功',
   any(k == 'R14_COMMON' and tx for k, tg, tx, w, rd in allres['F08']))
ck('1.4 F14 的 GOAL_THREE_TARGETS(§1060/§1061/§1062) 解析成功',
   any(k == 'GOAL' and tx for k, tg, tx, w, rd in allres['F14']),
   [(k, tg, w) for k, tg, tx, w, rd in allres['F14']])
ck('1.5 重定向（1063R→§1063）成功落地', any(k == 'REDIRECT' and tx for k, tg, tx, w, rd in allres['F15']),
   [(tg, w) for k, tg, tx, w, rd in allres['F15'] if k == 'REDIRECT'])

# ---------- 四档口径 ----------
print('  --- 四档承载率 ---')
print('   %-4s %-12s %-12s %-12s %s' % ('fid', 'ledger-only', 'no-redirect', 'with-redirect', 'miss(with-redirect)'))
res = []
for f in FIDS:
    A, N = addr_set(data[f][1]), num_set(data[f][1])
    led  = ''.join(tx for k, tg, tx, w, rd in allres[f] if k in ('LEDGER_SEC', 'SUPERSEDED') and tx)
    nord = ''.join(tx for k, tg, tx, w, rd in allres[f] if tx and k != 'REDIRECT')
    withr= ''.join(tx for k, tg, tx, w, rd in allres[f] if tx)
    tot = len(A) + len(N)
    def hit(txt): return len(A & addr_set(txt)) + len(N & num_set(txt))
    miss = sorted('0x%X' % v for v in A - addr_set(withr)) + sorted(str(x) for x in N - num_set(withr))
    r = dict(fid=f, addr_total=len(A), num_total=len(N), total=tot,
             ledger_rate=(100.0*hit(led)/tot) if tot else None,
             noredirect_rate=(100.0*hit(nord)/tot) if tot else None,
             rate=(100.0*hit(withr)/tot) if tot else None,
             hit=hit(withr), miss=miss)
    res.append(r)
    print('   %-4s %2d/%-2d %-7s %2d/%-2d %-7s %2d/%-2d %-7s %s'
          % (f, hit(led), tot, ('%.0f%%' % r['ledger_rate']) if tot else '-',
             hit(nord), tot, ('%.0f%%' % r['noredirect_rate']) if tot else '-',
             hit(withr), tot, ('%.0f%%' % r['rate']) if tot else '-',
             ','.join(miss) if miss else 'FULL'))

# ---------- 复算审计员 #359 的四条 ----------
print('  --- 复算审计员 #359 的四条主张 ---')
rc29 = rc_section('2.9')
ck('2.1 主张二成立：三装表 host 在 R14_COMMON §2.9 逐字同现',
   all(('0x%X' % a) in rc29 for a in (0x43B680, 0x43B740, 0x43BCF0)))
f16 = [x for x in res if x['fid'] == 'F16'][0]
ck('2.2 F16 with-redirect 下无地址缺口', f16['miss'] == [], f16['miss'])
ck('2.3 F16 承载率 100%（不是 A 报的 55.6%）', f16['rate'] == 100.0, f16['rate'])
f08 = [x for x in res if x['fid'] == 'F08'][0]
ck('2.4 主张四成立：F08 第 ① 条路径承载 5/5 地址',
   addr_set(data['F08'][1]) <= addr_set(''.join(tx for k, tg, tx, w, rd in allres['F08'] if k == 'R14_COMMON' and tx)))
ck('2.5 F08 ledger-only 40% 与 with-redirect 100% 两个口径都能复现',
   abs(f08['ledger_rate'] - 40.0) < 0.01 and f08['rate'] == 100.0, (f08['ledger_rate'], f08['rate']))
ck('2.6 主张一前提成立：SUPERSEDED 明写台账 §1063 采用 1063R 版本',
   'R17_LEDGER_1063R' in sup and '采用的是' in sup)
ANCH = ['129', '125', '354', '167', '267']
it4 = ledger_item('1063', 4)
ck('2.7 §1063 事项 4 承载 F15 的 5 个字面锚',
   all(re.search(r'(?<![0-9])%s(?![0-9])' % a, it4) for a in ANCH),
   [a for a in ANCH if not re.search(r'(?<![0-9])%s(?![0-9])' % a, it4)])
f15 = [x for x in res if x['fid'] == 'F15'][0]
ck('2.8 F15 由 60%（不含重定向）升到 100%（含重定向）',
   abs(f15['noredirect_rate'] - 60.0) < 0.01 and f15['rate'] == 100.0, (f15['noredirect_rate'], f15['rate']))
ck('2.9 主张三成立：台账里 4,063,232 与 4063232 两种写法并存', ('4,063,232' in t) and ('4063232' in t))
ck('2.10 归一后相等', num_set('4,063,232') == num_set('4063232') == {4063232})
ck('2.11 00449440 与 0x449440 归一到同一 int', addr_set('00449440') == addr_set('0x449440') == {0x449440})

# 反控
ck('2.12 反控：0xDEADBEE 在全部已声明路径里也不命中',
   not any(0xDEADBEE in addr_set(tx) for f in FIDS for k, tg, tx, w, rd in allres[f] if tx))
ck('2.13 反控：0x43BCF0 在 R14_COMMON §2.9 命中、但在 §1062–§1065 任何事项都不命中（两口径确有差异）',
   ('0x43BCF0' in rc29) and all('0x43BCF0' not in tx for num in ('1062','1063','1064','1065') for n, tx in ledger_items(num)))
ck('2.14 反控：把 F15 的重定向去掉必须掉回 60%（证明重定向确实在起作用）',
   f15['noredirect_rate'] < f15['rate'], (f15['noredirect_rate'], f15['rate']))

# ---------- 汇总 ----------
def g(r): return 'FULL' if not r['miss'] else ('PARTIAL' if r['hit'] else 'NONE')
for r in res: r['grade'] = g(r)
from collections import Counter
G = Counter(r['grade'] for r in res)
GL = Counter('FULL' if abs((r['ledger_rate'] or 0) - 100.0) < 1e-9 else ('PARTIAL' if (r['ledger_rate'] or 0) > 0 else 'NONE') for r in res)
print('  with-redirect 档位:', dict(G))
print('  ledger-only  档位:', dict(GL))
ck('2.15 档位闭合 12', sum(G.values()) == 12, sum(G.values()))
ck('2.16 口径差异真实存在：ledger-only 的 FULL 数 < with-redirect 的 FULL 数',
   GL.get('FULL', 0) < G.get('FULL', 0), (GL.get('FULL'), G.get('FULL')))

json.dump(dict(matrix=res, grades=dict(G), grades_ledger_only=dict(GL), fails=fails),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('  写出 %s' % OUT)
print('  === FAIL %d ===' % len(fails))
sys.exit(0 if not fails else 1)
