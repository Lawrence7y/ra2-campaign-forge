#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 A：FACT_INDEX v5.40 全 54 行的证据路径存活度普查（逐行 live/dead 计数）。
正控：已知在盘件必须判活；负控：自造路径必须判死；另设「同集合不同口径」反控。
不改任何文件，只读。
"""
import hashlib, json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
D14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FIX = os.path.join(D14, 'R17_R112_FACTINDEX_V540', 'FACT_INDEX.tsv')
fails = []
def ck(n, c, d=''):
    ok = bool(c); print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

raw = open(FIX, 'rb').read()
ck('0.1 54 数据行 + 表头 = 55 行', raw.count(b'\n') == 55, raw.count(b'\n'))
ck('0.2 全 LF', b'\r' not in raw, raw.count(b'\r'))
lines = raw.decode('utf-8').split('\n')
ck('0.3 表头五列', lines[0].split('\t') == ['fact_id','statement','grade','evidence_paths','limitations'])
rows = []
for ln in lines[1:]:
    if not ln.strip(): continue
    p = ln.split('\t')
    assert len(p) == 5, p[0]
    rows.append(p)
ck('0.4 数据行 54', len(rows) == 54, len(rows))

def items(col):
    out = []
    for seg in col.split(';'):
        s = seg.strip()
        if not s: continue
        s = s.split('(')[0].split('\uff08')[0].strip()
        out.append(s)
    return out

def resolve(p):
    q = p.replace('\\', '/')
    cands = [os.path.join(ROOT, q), os.path.join(ROOT, 'lead', q)]
    return any(os.path.exists(c) for c in cands), [c for c in cands if os.path.exists(c)]

census = {}
for r in rows:
    fid = r[0]
    its = items(r[3])
    live = [p for p in its if resolve(p)[0]]
    dead = [p for p in its if not resolve(p)[0]]
    census[fid] = {'n': len(its), 'live': len(live), 'dead': len(dead),
                   'grade': r[2], 'live_paths': live, 'dead_paths': dead}

tot_items = sum(v['n'] for v in census.values())
tot_live = sum(v['live'] for v in census.values())
tot_dead = sum(v['dead'] for v in census.values())
print('  总证据项 %d / 存活 %d / 失联 %d' % (tot_items, tot_live, tot_dead))
ck('1.1 项数与 deadd 之和闭合', tot_live + tot_dead == tot_items)
ck('1.2 总项数 178（与 R149 同口径）', tot_items == 178, tot_items)
ck('1.3 失联项 43（与 R149 同口径）', tot_dead == 43, tot_dead)

zero = [f for f, v in census.items() if v['n'] > 0 and v['live'] == 0]
print('  零存活行:', zero)
ck('2.1 零存活恰 1 行且为 F23', zero == ['F23'], zero)
ck('2.2 F23 grade 仍 [已证]', census['F23']['grade'] == '[已证]', census['F23']['grade'])
ck('2.3 F23 两项全失', census['F23']['n'] == 2 and census['F23']['dead'] == 2, census['F23'])

# 唯一失联路径
all_dead = []
for v in census.values(): all_dead += v['dead_paths']
uniq = sorted(set(p.replace('\\','/') for p in all_dead))
print('  唯一失联路径 %d 条' % len(uniq))
ck('3.1 唯一失联路径 16 条（与 R149 同口径）', len(uniq) == 16, len(uniq))
LEDGER = [p for p in uniq if re.search(r'R17_LEDGER_\d+R?/SECTION\.md$', p)]
ck('3.2 LEDGER 型 5 条', len(LEDGER) == 5, LEDGER)

# 正控 / 负控
ck('4.1 正控 在盘件 R14_COMMON.md 判活',
   resolve('lead/next_re_20261117_r14/R14_COMMON.md')[0])
ck('4.2 正控 以仓库根解析出的 lead/... 路径判活',
   resolve(r'lead\next_re_20261117_r14\R14_COMMON.md')[0])
ck('4.3 负控 自造路径判死',
   not resolve('lead/next_re_20261117_r14/ZZZ_NOT_ON_DISK_QQQ.md')[0])
ck('4.4 负控 已失件 COVERAGE/PANEL.md 判死',
   not resolve(r'lead\next_re_20261117_r14\COVERAGE\PANEL.md')[0])
# 反控：若只用仓库根（不补 lead/）解析，则 lead/ 相对项会全部误判为死
q = r'lead\next_re_20261117_r14\R14_COMMON.md'.replace('\\','/')
ck('4.5 反控 只拼仓库根可得同一条命中（口径不分叉）', os.path.exists(os.path.join(ROOT, q)))

out = {'total_items': tot_items, 'live': tot_live, 'dead': tot_dead,
       'zero_live': zero, 'unique_missing': uniq, 'ledger_type': LEDGER,
       'census': {k: {'n': v['n'], 'live': v['live'], 'dead': v['dead'], 'grade': v['grade']}
                  for k, v in sorted(census.items())},
       'src_sha256': hashlib.sha256(raw).hexdigest(), 'src_bytes': len(raw)}
json.dump(out, open(os.path.join(ROOT,'_r150/r150a_evidcensus.json'),'w'),
          ensure_ascii=False, indent=1)
print('\n  sha256(v5.40) =', out['src_sha256'])
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ', f)
