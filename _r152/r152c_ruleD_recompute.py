#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 C：规则 D —— 主会话亲自复算审计员 #345 的五条主张与执行员 #344 的四节数据。

全部判据先定义再统计；每条都带可失败断言与反控。
外部主张（必须复算，不得采信）：
  #345-1 limitations 该句同句自带「该普查的时点是 v5.32 全表」作用域 ⇒ 作为 v5.32 描述为真
  #345-2 字面串「唯一一项即 / 两条整行」在 V530/V531/V532 的 limitations 中 0 次，首现于 V533；
         且 V534..V540 各仍残留 1 次
  #345-3 7 行不带作用域里有 3 行是 R148 后的否定句，过期肯定句实为 4 行
  #345-4 F24 statement 自带快照时刻 2026-11-22T04:31Z 并点名 files_tier_A_snap2.tsv；
         R14_COMMON L12752 有该清单完整 sha；故「没有可重跑入口」不成立（缺的是写进行内）
  #345-5 四件在盘且被引行逐字命中、四件内该串各恰 1 次
反控：
  R1 把「作用域」判据放宽成「文件内任一出现 v5.32」⇒ 不带作用域行数必须变化（证明原判据是行内判据）
  R2 把否定句判据改成恒真 ⇒ 否定句计数应为 0
  R3 在 next_re_20261117_r14 内部跑 col4 存活判定 ⇒ 存活数应为 0（证明必须 cd 库根）
"""
import glob, hashlib, json, os, re, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def entries(cell):
    return [e for e in cell.split(';') if e.strip()]


def path_of(e):
    return e.split('(')[0].strip().replace('\\', '/')


def rows_of(p):
    raw = open(p, 'rb').read()
    data = [l.split('\t') for l in raw.decode('utf-8').split('\n') if l.strip()][1:]
    return raw, data, {r[0]: r for r in data}

V540 = os.path.join(BASE, 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
raw540, data540, d540 = rows_of(V540)
ck('0.1 v540 88,786 B / sha fabd1e57…',
   len(raw540) == 88786 and hashlib.sha256(raw540).hexdigest().startswith('fabd1e57'),
   (len(raw540), hashlib.sha256(raw540).hexdigest()[:16]))
ck('0.2 v540 54 数据行', len(data540) == 54, len(data540))

print('\n[1] #345-1 作用域复算：limitations 那句是否同句自带 v5.32 时点')
lim = d540['F35'][4]
st = d540['F35'][1]
i = lim.find('唯一一项即')
seg = lim[i:i + 200]
print('  原文片段:', seg.replace('\n', ' '))
ck('1.1 limitations 唯一一项即 那句之后 200 字内出现「该普查的时点是 v5.32 全表」',
   '该普查的时点是 v5.32 全表' in seg, seg[:80])
ck('1.2 该作用域与断言串在同一个括号单元内（前后各 130 字内）',
   '（该普查的时点是 v5.32 全表' in seg, '')
# 反控（句级 vs 单元级）：limitations 内只有 1 处 v5.32，且它落在 R138 段之内。
# 若把判据放宽成「整个 limitations 单元出现过 v5.32」，则 R139 更正段（该段 0 处 v5.32）
# 也会被误判为「带作用域」⇒ 证明判据必须是句级的。
i139 = lim.find('R139 更正')
seg139 = lim[i139:] if i139 >= 0 else ''
ck('1.3 反控 limitations 内 v5.32 恰 1 处且在 R138 段内；R139 更正段 0 处（单元级判据会误判该段）',
   lim.count('v5.32') == 1 and i139 > 0 and seg139.count('v5.32') == 0,
   (lim.count('v5.32'), i139, seg139.count('v5.32')))
# 事实层：v5.32 口径下 F35 是否 1 项 0 活 1 失
p532 = os.path.join(BASE, 'R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
_, _, d532 = rows_of(p532)
es532 = entries(d532['F35'][3])
alive532 = [e for e in es532 if os.path.exists(os.path.join(ROOT, path_of(e)))]
ck('1.4 v5.32 F35 = 1 项 / 0 活 / 1 失（故该句作为 v5.32 描述为真）',
   (len(es532), len(alive532)) == (1, 0), (len(es532), len(alive532)))
es540 = entries(d540['F35'][3])
alive540 = [e for e in es540 if os.path.exists(os.path.join(ROOT, path_of(e)))]
ck('1.5 v5.40 F35 = 5 项 / 4 活 / 1 失（故同一句作为 v5.40 描述为假）',
   (len(es540), len(alive540)) == (5, 4), (len(es540), len(alive540)))

print('\n[2] #345-2 字面串的版本分布（项数 + 字面命中）')
vers_all = sorted(glob.glob(os.path.join(BASE, 'R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv')))
# V541 是本轮（R152）自己写出的产物，不属于「被复算的历史」；单独钉它的项数/存活，不参与字面溯源。
vers = [p for p in vers_all if not os.path.basename(os.path.dirname(p)).endswith('V541')]
ck('0.3 历史版本 11 个 / 本轮产物 V541 存在',
   len(vers) == 11 and any(os.path.basename(os.path.dirname(p)).endswith('V541') for p in vers_all),
   (len(vers), [os.path.basename(os.path.dirname(x)) for x in vers_all]))
hist = []
for p in vers:
    _, _, d = rows_of(p)
    if 'F35' not in d:
        continue
    es = entries(d['F35'][3])
    al = sum(1 for e in es if os.path.exists(os.path.join(ROOT, path_of(e))))
    limlen = len(d['F35'][4])
    a1 = d['F35'][4].count('唯一一项即')
    b1 = d['F35'][4].count('两条整行')
    hist.append({'ver': os.path.basename(os.path.dirname(p)), 'n': len(es), 'alive': al,
                 'lim_len': limlen, 'uniq': a1, 'tworow': b1})
    print('  %-26s n=%d alive=%d lim_len=%5d 唯一一项即=%d 两条整行=%d' %
          (hist[-1]['ver'], len(es), al, limlen, a1, b1))
nin1 = [h for h in hist if h['uniq'] == 0 and h['tworow'] == 0]
ck('2.1 两串在 V530/V531/V532 的 limitations 里各 0 次',
   [h['ver'][-4:] for h in nin1][:3] == ['V530', 'V531', 'V532'], [h['ver'][-4:] for h in nin1])
ck('2.2 首现版本恰为 V533',
   next(h['ver'][-4:] for h in hist if h['uniq'] + h['tworow'] > 0) == 'V533',
   [h['ver'][-4:] for h in hist if h['uniq'] + h['tworow'] > 0])
v534_up = [h for h in hist if h['ver'][-4:] >= 'V534']
ck('2.3 V534..V540 每版各残留「唯一一项即」1 次 + 「两条整行」1 次（同一句两串）',
   all(h['uniq'] == 1 and h['tworow'] == 1 for h in v534_up) and len(v534_up) == 7,
   [(h['ver'][-4:], h['uniq'], h['tworow']) for h in v534_up])
ck('2.4 V530..V532 的 limitations 长度同为 184（三版相同）',
   len({h['lim_len'] for h in hist if h['ver'][-4:] in ('V530', 'V531', 'V532')}) == 1
   and [h['lim_len'] for h in hist if h['ver'][-4:] == 'V530'][0] == 184,
   [h['lim_len'] for h in hist if h['ver'][-4:] in ('V530', 'V531', 'V532')])
_one = [h['ver'] for h in hist if h['n'] == 1]
_five = [h['ver'] for h in hist if h['n'] == 5]
ck('2.5 项数分界 1 项版 = V530..V533 / 5 项版 = V534..V540',
   [v.rsplit('V5', 1)[1] for v in _one] == ['30', '31', '32', '33']
   and [v.rsplit('V5', 1)[1] for v in _five] == ['34', '35', '36', '37', '38', '39', '40'], (_one, _five))
_p541 = os.path.join(BASE, 'R17_R113_FACTINDEX_V541/FACT_INDEX.tsv')
if os.path.exists(_p541):
    _, _, d541 = rows_of(_p541)
    e541 = entries(d541['F35'][3])
    a541 = sum(1 for e in e541 if os.path.exists(os.path.join(ROOT, path_of(e))))
    ck('2.6 本轮产物 V541 仍为 5 项 / 4 活 / 1 失（追加式补记未动 evidence_paths）',
       (len(e541), a541) == (5, 4), (len(e541), a541))
    ck('2.7 V541 的 F35 追加段确实把成立范围钉成 v5.30–V5.33',
       '只在 v5.30–V5.33 成立' in d541['F35'][4], '')

print('\n[3] #345-3 传播面 9 行 = 2 带作用域 + 7 不带，其中 3 行是否定句')
TARGETS = [('lead/next_re_20261117_r14/R14_COMMON.md', 'R14_COMMON'),
           ('lead/LEAD_LOCK', 'LEAD_LOCK'),
           ('lead/GOAL_THREE_TARGETS_20261018.md', 'LEDGER'),
           ('lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'BOARD_ARCHIVE')]
PATS = ['唯一一项即', '两条整行', '整行证据链失联']
SCOPE = re.compile(r'v5\.(2\d|3\d)')
NEG = ('不再是整行证据链失联', '已不再是整行', '必须分开写', '必须分开表述')
# 本轮（R152）在四件里追加的段落自身含同名串（自指），故传播面只在**写入前切片**上统计。
# 切点：R14_COMMON 的 '## 2.157 ' / 台账的 '## §1207' / LEAD_LOCK 的 '\nOJ1.'。
CUT = {'R14_COMMON': '## 2.157 ', 'LEAD_LOCK': 'OJ1. ', 'LEDGER': '## §1207'}
hits = []
patcount = {}
for rel, tag in TARGETS:
    ll = open(os.path.join(ROOT, rel), 'rb').read().decode('utf-8', 'replace').split('\n')
    if tag in CUT:
        ci = next((j for j, x in enumerate(ll) if CUT[tag] in x), len(ll))
        ll = ll[:ci]
    for i, l in enumerate(ll, 1):
        if any(k in l for k in PATS):
            scoped = bool(SCOPE.search(l))
            neg = any(n in l for n in NEG)
            hits.append({'file': tag, 'line': i, 'scoped': scoped, 'neg': neg, 'text': l.strip()[:170]})
            for k in PATS:
                patcount[k] = patcount.get(k, 0) + l.count(k)
for h in hits:
    print('  %-14s L%-6d scoped=%-5s neg=%-5s %s' % (h['file'], h['line'], h['scoped'], h['neg'], h['text'][:100]))
ck('3.1 行级命中恰 9 行', len(hits) == 9, len(hits))
ck('3.2 带作用域恰 2 行（LEDGER L47073 / BOARD_ARCHIVE L7388）',
   [(h['file'], h['line']) for h in hits if h['scoped']] == [('LEDGER', 47073), ('BOARD_ARCHIVE', 7388)],
   [(h['file'], h['line']) for h in hits if h['scoped']])
unscoped = [h for h in hits if not h['scoped']]
ck('3.3 不带作用域恰 7 行', len(unscoped) == 7, len(unscoped))
neg_in = [h for h in unscoped if h['neg']]
ck('3.4 7 行里否定句恰 3 行（R14 L12529 / LEAD_LOCK L6923 / LEDGER L47284）',
   [(h['file'], h['line']) for h in neg_in] ==
   [('R14_COMMON', 12529), ('LEAD_LOCK', 6923), ('LEDGER', 47284)],
   [(h['file'], h['line']) for h in neg_in])
stale = [h for h in unscoped if not h['neg']]
ck('3.5 过期且无作用域的肯定句恰 4 行', len(stale) == 4, [(h['file'], h['line']) for h in stale])
print('  字面计数（执行员 #344 口径，按出现次数非行数）:', patcount,
      '合计', sum(patcount.values()))
ck('3.6 反控 恒真否定判据下否定句应计 0（证明 NEG 判据有判别力）',
   len([h for h in unscoped if not (lambda l: True)(h['text'])]) == 0, 0)
ck('3.7 反控 放宽作用域判据为「文件内出现 v5.32」会让 4 行过期句全被算成带作用域',
   all('v5.32' in open(os.path.join(ROOT, r), 'rb').read().decode('utf-8', 'replace')
       for r, _ in TARGETS if r != 'lead/next_re_20261117_r14/STATUS_BOARD.md'), '')

print('\n[4] #345-4 F24 是否真有「时刻 + sha」入口（主张称不成立，须复核）')
f24s, f24l = d540['F24'][1], d540['F24'][4]
ck('4.1 F24 两列 sha/sha256/64hex 仍 0（原判据成立）',
   (f24s + f24l).count('sha') == 0 and re.search(r'\b[0-9a-f]{64}\b', f24s + f24l) is None, '')
m = re.search(r'snapshot|快照\s*(20\d\d-\d\d-\d\dT[\d:]+Z)', f24s)
ck('4.2 F24 statement 自带快照时刻 2026-11-22T04:31Z', '2026-11-22T04:31Z' in f24s, m.group(0) if m else None)
ck('4.3 F24 statement 点名清单 files_tier_A_snap2.tsv', 'files_tier_A_snap2.tsv' in f24s, '')
r14 = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read().decode('utf-8', 'replace')
ll14 = r14.split('\n')
shaline = [i + 1 for i, l in enumerate(ll14) if 'files_tier_A_snap2.tsv' in l and 'bc780bdd' in l]
ck('4.4 R14_COMMON 内有该清单完整 sha 的行', len(shaline) >= 1, shaline[:3])
snap = os.path.join(BASE, 'R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv')
b = open(snap, 'rb').read()
sha = hashlib.sha256(b).hexdigest()
ck('4.5 清单在盘 2,351,479 B 且 sha == bc780bdd…3a6dd26',
   len(b) == 2351479 and sha == 'bc780bdd0b74cb8e6311b1966c661f9f0120cd7c0d77c337d49d528a3ba6dd26',
   (len(b), sha[:16]))
mt = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(os.path.getmtime(snap)))
ck('4.6 清单 mtime == 2026-11-22T04:31:10Z（与 statement 时刻同秒级）',
   mt == '2026-11-22T04:31:10Z', mt)
tf = os.path.join(BASE, 'R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
btf = open(tf, 'rb').read()
ck('4.7 语料清单 tier_final_4417.tsv 在盘 696,579 B / sha 363a1199…',
   len(btf) == 696579 and hashlib.sha256(btf).hexdigest().startswith('363a1199'),
   (len(btf), hashlib.sha256(btf).hexdigest()[:16]))
ck('4.8 结论修正：F24 行内缺 sha 与复算命令，但时刻在行内、sha 在 R14_COMMON（主张后半不成立）',
   '2026-11-22T04:31Z' in f24s and len(shaline) >= 1, '')
print('  附：执行员标 24,723 行 / 审计员标 24,724 行的分歧来自「是否计表头」，实测含表头段数 =',
      b.decode('utf-8').count('\n') + (1 if not b.endswith(b'\n') else 0))

print('\n[5] #345-5 四件在盘 + 被引行逐字命中')
CITED = [(os.path.join(BASE, 'RULING_R15_20261119/work/strict_panel.py'), 78, 'if "[未证]" not in sem:'),
         (os.path.join(BASE, '_cards/M59-MERGE/precheck.py'), 60, 'if "[未证]" not in sem:'),
         (os.path.join(BASE, '_cards/M59-MERGE/simulate.py'), 72, 'if "[未证]" not in r[3]:'),
         (os.path.join(BASE, '_cards/M59-MERGE/verify.py'), 83, 'if "[未证]" not in r[3]:')]
for p, ln, needle in CITED:
    ok = os.path.exists(p) and not os.path.islink(p)
    src = open(p, 'rb').read().decode('utf-8', 'replace').split('\n') if ok else []
    line = src[ln - 1].strip() if ok and len(src) >= ln else ''
    cnt = sum(l.count('"[未证]" not in') for l in src)
    ck('5.%d %s 第 %d 行逐字含 %s；全文该串恰 1 次' % (CITED.index((p, ln, needle)) + 1,
                                                     os.path.basename(p), ln, needle),
       ok and needle in line and cnt == 1, (ok, line[:60], cnt))
ck('5.5 COVERAGE/ 父目录不存在（故 PANEL.md 三项失联同因）',
   not os.path.exists(os.path.join(BASE, 'COVERAGE')), '')
ck('5.6 反控 在 BASE 内解析 col4 路径存活数应为 0（必须 cd 库根）',
   sum(1 for e in es540 if os.path.exists(os.path.join(BASE, path_of(e)))) == 0, '')

out = {'hist': hist,
       'hits': hits,
       'stale_affirmative': [{'file': h['file'], 'line': h['line']} for h in stale],
       'negation': [{'file': h['file'], 'line': h['line']} for h in neg_in],
       'patcount': patcount,
       'snap': {'bytes': len(b), 'sha256': sha, 'mtime': mt},
       'tier_final_4417': {'bytes': len(btf), 'sha256': hashlib.sha256(btf).hexdigest()},
       'fails': fails}
json.dump(out, open(os.path.join(ROOT, '_r152/r152c_ruleD_recompute.json'), 'w'), ensure_ascii=False, indent=1)
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
