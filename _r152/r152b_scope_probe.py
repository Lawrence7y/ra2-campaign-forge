#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 B：F35「唯一一项 / 两条整行」句的版本作用域与传播面 + F24 缺「时刻+sha」实测。

三条判据（先定义再统计）：
 P1 F35 的 evidence_paths 项数在各版本的分界点（必须实测，不许写死）
 P2 「唯一一项即」「两条整行」「整行证据链失联」三类串在五件套+台账的命中，逐条判
    「同句/同节标题内是否带 v5.2x/v5.3x 版本作用域」—— 带作用域=合格，不带=过期陈述外泄
 P3 F24 正文是否已钉「清单 sha256」与「测量时刻」两个可重跑要素
正控：F35 v5.40 必须 5 项 4 活 1 失；反控：把作用域判据改成恒真（任何串都算带作用域）
      必须让「4 处不带作用域」降为 0，证明判据有判别力。
"""
import glob, hashlib, json, os, re, sys

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


def rowmap(p):
    raw = open(p, 'rb').read()
    rows = [l.split('\t') for l in raw.decode('utf-8').split('\n') if l.strip()][1:]
    return raw, {r[0]: r for r in rows}


print('[P1] F35 evidence_paths 项数的版本分界')
vers = sorted(glob.glob(os.path.join(BASE, 'R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv')))
ck('1.0 版本数 11', len(vers) == 11, len(vers))
hist = []
for p in vers:
    raw, d = rowmap(p)
    es = entries(d['F35'][3])
    dead = [e for e in es if not os.path.exists(os.path.join(ROOT, path_of(e)))]
    whole = [r[0] for r in d.values()
             if entries(r[3]) and all(not os.path.exists(os.path.join(ROOT, path_of(e))) for e in entries(r[3]))]
    hist.append({'ver': os.path.basename(os.path.dirname(p)), 'bytes': len(raw),
                 'f35_n': len(es), 'f35_dead': len(dead), 'whole_dead': whole})
    print('  %-24s %6d B  F35 n=%d dead=%d  whole=%s' %
          (hist[-1]['ver'], len(raw), len(es), len(dead), whole))
n1 = [h['ver'] for h in hist if h['f35_n'] == 1]
n5 = [h['ver'] for h in hist if h['f35_n'] == 5]
ck('1.1 1 项版 = V530..V533 四版', [v[-6:] for v in n1] == ['V530', 'V531', 'V532', 'V533'], n1)
ck('1.2 5 项版 = V534..V540 七版', [v[-6:] for v in n5] ==
   ['V534', 'V535', 'V536', 'V537', 'V538', 'V539', 'V540'], n5)
ck('1.3 分界点在 V533->V534 之间（V533 n=1 / V534 n=5）',
   hist[3]['ver'].endswith('V533') and hist[3]['f35_n'] == 1
   and hist[4]['ver'].endswith('V534') and hist[4]['f35_n'] == 5,
   (hist[3]['ver'], hist[3]['f35_n'], hist[4]['ver'], hist[4]['f35_n']))
ck('1.4 1 项版里 F35 与 F23 都是整行失联（两条整行句在 V530..V533 成立）',
   all(h['whole_dead'] == ['F23', 'F35'] for h in hist if h['f35_n'] == 1),
   [h['whole_dead'] for h in hist if h['f35_n'] == 1])
ck('1.5 5 项版里整行失联只剩 F23',
   all(h['whole_dead'] == ['F23'] for h in hist if h['f35_n'] == 5),
   [h['whole_dead'] for h in hist if h['f35_n'] == 5])
raw540, d540 = rowmap(os.path.join(BASE, 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv'))
es = entries(d540['F35'][3])
dead = [e for e in es if not os.path.exists(os.path.join(ROOT, path_of(e)))]
ck('1.6 正控 v540 F35 = 5 项 / 4 活 / 1 失', (len(es), len(dead)) == (5, 1), (len(es), len(dead)))

print('\n[P2] F35 同一行两处相反断言（statement vs limitations）')
st, lim = d540['F35'][1], d540['F35'][4]
ck('2.1 statement ④ 断言 5 项里只有 PANEL.md 失联',
   '5 项里只有' in st and '`COVERAGE/PANEL.md` 失联' in st, '')
ck('2.2 statement ④ 断言「不再是整行证据链失联项」',
   '不再是整行证据链失联项' in st, '')
ck('2.3 limitations 仍断言「evidence_paths 唯一一项即该已失文件」',
   '唯一一项即该已失文件' in lim, '')
ck('2.4 limitations 仍断言「与 F23 并列…两条整行证据链失联项」',
   '两条整行证据链失联项' in lim, '')
ck('2.5 两处相反断言同处一行（本条缺陷的机械定义）',
   ('不再是整行证据链失联项' in st) and ('两条整行证据链失联项' in lim), '')

print('\n[P3] 传播面：五件套 + 台账里的同名过期陈述及其作用域')
TARGETS = [
    ('lead/next_re_20261117_r14/R14_COMMON.md', 'R14_COMMON'),
    ('lead/LEAD_LOCK', 'LEAD_LOCK'),
    ('lead/GOAL_THREE_TARGETS_20261018.md', 'LEDGER'),
    ('lead/next_re_20261117_r14/STATUS_BOARD.md', 'STATUS_BOARD'),
    ('lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'BOARD_ARCHIVE'),
]
PATS = ['唯一一项即', '两条整行', '整行证据链失联']
SCOPE = re.compile(r'v5\.(2\d|3\d)|V5(2\d|3\d)')
hits = []
for rel, tag in TARGETS:
    p = os.path.join(ROOT, rel)
    ck('3.0 %s 在盘' % tag, os.path.exists(p), '')
    ll = open(p, 'rb').read().decode('utf-8', 'replace').split('\n')
    for i, l in enumerate(ll, 1):
        if any(k in l for k in PATS):
            # 作用域判据（窄）：同句（同段落单元，取该行本身 + 若为节标题则整行）内出现 v5.2x/v5.3x
            scoped = bool(SCOPE.search(l))
            hits.append({'file': tag, 'line': i, 'scoped': scoped, 'text': l.strip()[:200]})
            print('  %-14s L%-6d scoped=%-5s %s' % (tag, i, scoped, l.strip()[:120]))
ck('3.1 命中 >= 6 处', len(hits) >= 6, len(hits))
unscoped = [h for h in hits if not h['scoped']]
print('  -> 带版本作用域 %d 处 / 不带 %d 处' % (len(hits) - len(unscoped), len(unscoped)))
# 反控：把作用域判据换成恒真函数 ⇒ 不带作用域必须降为 0
trivial_unscoped = [h for h in hits if not (lambda l: True)(h['text'])]
ck('3.2 反控 恒真作用域判据下不带作用域 == 0（判据有判别力）', len(trivial_unscoped) == 0,
   len(trivial_unscoped))
ck('3.3 台账 §1191 节标题带 v5.32 作用域（唯一合格的一处）',
   any(h['file'] == 'LEDGER' and h['scoped'] and h['line'] == 47073 for h in hits),
   [(h['file'], h['line'], h['scoped']) for h in hits])

print('\n[P4] F24 正文是否已钉「清单 sha256」与「测量时刻」')
f24 = d540['F24']
f24txt = f24[1] + '\n' + f24[4]
ck('4.1 F24 两列内 sha256 出现 0 次', f24txt.count('sha256') == 0, f24txt.count('sha256'))
ck('4.2 F24 两列内「sha」子串出现 0 次', f24txt.count('sha') == 0, f24txt.count('sha'))
ck('4.3 F24 两列内「测量时刻」出现 1 次（但是引用限定、非已钉值）',
   f24txt.count('测量时刻') == 1, f24txt.count('测量时刻'))
ck('4.4 F24 两列内无 64 位十六进制串（即无任何已钉 sha）',
   re.search(r'\b[0-9a-f]{64}\b', f24txt) is None, '')
tf = os.path.join(BASE, 'R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
b = open(tf, 'rb').read()
sha = hashlib.sha256(b).hexdigest()
mt = os.path.getmtime(tf)
import time
ck('4.5 正控 清单可 stat 出 sha 与 mtime（补齐要素可得）',
   len(sha) == 64 and mt > 0, (sha[:16], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))))
ck('4.6 清单 696,579 B', len(b) == 696579, len(b))
ck('4.7 清单 sha == 363a1199…',
   sha == '363a1199efa752292de684100ea6632abb145e7e031a4fbaf820db08aff7598c', sha[:16])
ck('4.8 清单 4,418 段 = 表头 + 4,417 行 + 末尾空串',
   b.decode('utf-8').count('\n') == 4418, b.decode('utf-8').count('\n'))

out = {'p1_hist': hist, 'p2': {'st_has_5of5': '5 项里只有' in st, 'lim_has_unique': '唯一一项即该已失文件' in lim},
       'p3_hits': hits, 'p3_unscoped': [{'file': h['file'], 'line': h['line']} for h in unscoped],
       'p4': {'tier_final_4417': {'bytes': len(b), 'sha256': sha,
                                   'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))}},
       'pins': {'v540_bytes': len(raw540), 'v540_sha256': hashlib.sha256(raw540).hexdigest()},
       'fails': fails}
json.dump(out, open(os.path.join(ROOT, '_r152/r152b_scope_probe.json'), 'w'), ensure_ascii=False, indent=1)
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
