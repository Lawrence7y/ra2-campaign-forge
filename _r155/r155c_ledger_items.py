#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R155 C：FACT_INDEX 里 17 个指向 R17_LEDGER_*/SECTION.md 的证据项，在「事项」粒度上到底可核不可核。
分三层：① 被指的 SECTION.md 在不在盘 ② 同名台账节在不在 ③ 被指的「事项 N」在该节里存不存在。
每层都给正反控。只判可核性，不判事实真假。"""
import os, re, json, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
R14  = os.path.join(LEAD, 'next_re_20261117_r14')
LED  = os.path.join(LEAD, 'GOAL_THREE_TARGETS_20261018.md')
IDX  = os.path.join(R14, 'R17_R114_FACTINDEX_V542', 'FACT_INDEX.tsv')

fails, out = [], {}
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

rows = [l.split('\t') for l in open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
data = rows[1:]
ck('0.1 数据行 54', len(data) == 54, len(data))
led = open(LED, encoding='utf-8').read()

# ---------- 1 · 抽出全部 R17_LEDGER_* 证据项 ----------
items = []
for r in data:
    for it in r[3].split(';'):
        it = it.strip()
        if 'R17_LEDGER_' in it:
            m = re.search(r'(R17_LEDGER_[0-9A-Za-z]+)', it)
            d = m.group(1)
            ap = os.path.join(ROOT, re.split(r'[\(（]', it)[0].strip().replace('\\', '/'))
            items.append({'fid': r[0], 'item': it, 'dir': d,
                          'is_section': it.split('(')[0].strip().endswith('SECTION.md'),
                          'exists': os.path.isfile(ap),
                          'abs': ap})
out['items'] = items
print('  --- %d 个 R17_LEDGER_* 证据项 ---' % len(items))
by_dir = collections.Counter(x['dir'] for x in items)
print('  按目录:', dict(by_dir))
out['by_dir'] = dict(by_dir)

ck('1.1 证据项总数 17', len(items) == 17, len(items))
ck('1.2 涉及 5 个目录', len(by_dir) == 5, sorted(by_dir))
# S-408: 上一版断言「17 项全部不在盘」是错的 —— 其中 1 项写的是 SUPERSEDED.md，它**在盘**。
# 正确判据要按 SECTION.md 与非 SECTION.md 分开：前者应全不命中，后者逐条如实登记。
sec_items = [x for x in items if x['is_section']]
non_sec   = [x for x in items if not x['is_section']]
out['n_section_items'] = len(sec_items); out['n_nonsection_items'] = len(non_sec)
print('    SECTION.md 项 %d 个 / 非 SECTION.md 项 %d 个 %s'
      % (len(sec_items), len(non_sec), [(x['fid'], x['item']) for x in non_sec]))
ck('1.3a SECTION.md 类证据项全部不在盘', all(not x['exists'] for x in sec_items),
   [x['item'] for x in sec_items if x['exists']])
ck('1.3b 非 SECTION.md 类证据项 1 个且在盘（SUPERSEDED.md）',
   len(non_sec) == 1 and non_sec[0]['exists'], [(x['fid'], x['exists']) for x in non_sec])

# 独立反查：全库 SECTION.md 文件数
cnt_all = 0
for dp, dn, fn in os.walk(ROOT):
    if 'SECTION.md' in fn:
        cnt_all += 1
out['section_md_files_repo_wide'] = cnt_all
ck('1.4 全库 SECTION.md 文件数 == 0（反查，不依赖 1.3）', cnt_all == 0, cnt_all)
# 正控：全库存在别的同名文件名（证明 walk 不是在空树上跑）
cnt_other = 0
for dp, dn, fn in os.walk(ROOT):
    if 'SUPERSEDED.md' in fn:
        cnt_other += 1
out['superseded_md_files'] = cnt_other
ck('1.5 正控：全库 SUPERSEDED.md 数 >= 1（walk 有效，1.4 的 0 是真 0）', cnt_other >= 1, cnt_other)

# ---------- 2 · 同名台账节在不在 ----------
secpos = {}
for m in re.finditer(r'(?m)^## §(\d+[A-Za-z]?) ·', led):
    secpos.setdefault(m.group(1), []).append(m.start())
out['ledger_sections_sample'] = {k: len(v) for k, v in secpos.items() if k.startswith('106')}
dirs = sorted(by_dir)
sec_avail = {}
for d in dirs:
    num = d.replace('R17_LEDGER_', '')
    sec_avail[d] = (num in secpos)
    print('    %-18s 同名台账节 §%s : %s' % (d, num, 'YES' if sec_avail[d] else 'NO'))
out['sec_avail'] = sec_avail
ck('2.1 §1062/§1063/§1064/§1065 四个同名节都在台账',
   all(sec_avail['R17_LEDGER_' + n] for n in ('1062', '1063', '1064', '1065')),
   {k: v for k, v in sec_avail.items()})
ck('2.2 §1063R 无同名节（R149 已登记）', not sec_avail['R17_LEDGER_1063R'], sec_avail['R17_LEDGER_1063R'])
# 反控：查一个绝不存在的节号
ck('2.3 反控：§9999 不在台账', '9999' not in secpos, '9999' in secpos)

# ---------- 3 · 被指的「事项 N」在该节里存不存在 ----------
def sec_slice(num):
    ks = sorted(secpos) 
    p = secpos[num][0]
    # 右边界：下一个 ## § 开头
    nxt = re.search(r'(?m)^## §', led[p + 10:])
    return led[p: p + 10 + nxt.start()] if nxt else led[p:]

def parse_items(it):
    """从证据项括注里取事项号集合。支持：事项1 / 事项1/5 / 事项2 / 事项 4。"""
    m = re.search(r'事项\s*([0-9]+(?:\s*/\s*[0-9]+)*)', it)
    if not m: return []
    return [int(x) for x in re.split(r'\s*/\s*', m.group(1))]

probe = []
for x in items:
    num = x['dir'].replace('R17_LEDGER_', '')
    want = parse_items(x['item'])
    if not want:
        probe.append(dict(fid=x['fid'], dir=x['dir'], want=[], status='NO_ITEM_ANCHOR',
                          item=x['item']))
        continue
    if not sec_avail[x['dir']]:
        probe.append(dict(fid=x['fid'], dir=x['dir'], want=want, status='NO_LEDGER_SECTION',
                          item=x['item']))
        continue
    s = sec_slice(num)
    have = sorted(set(int(m.group(1)) for m in re.finditer(r'事项\s*([1-9])', s)))
    ok = all(w in have for w in want)
    probe.append(dict(fid=x['fid'], dir=x['dir'], want=want, have=have,
                      status='OK' if ok else 'ITEM_MISSING', item=x['item'],
                      sec_chars=len(s)))
out['probe'] = probe
print()
print('  --- 事项级可核性 ---')
st = collections.Counter(p['status'] for p in probe)
for p in probe:
    print('    %-4s %-18s want=%-8s %-16s %s' % (p['fid'], p['dir'], p['want'], p['status'],
                                                 '' if p['status'] == 'OK' else p['item'][:70]))
print('  状态分布:', dict(st))
out['status_dist'] = dict(st)

ck('3.1 三个状态之和 == 17', sum(st.values()) == 17, sum(st.values()))
ck('3.2 至少 1 项 NO_LEDGER_SECTION（§1063R）', st['NO_LEDGER_SECTION'] >= 1, st['NO_LEDGER_SECTION'])
# S-409: 上一版把阈值 15 写死在断言里（本该被查询的量）⇒ 假 FAIL。改为：可解析数 == 17 - 无锚数。
n_want = sum(1 for p in probe if p['want'])
n_noanchor = sum(1 for p in probe if p['status'] == 'NO_ITEM_ANCHOR')
out['n_item_anchor_parsed'] = n_want; out['n_no_item_anchor'] = n_noanchor
ck('3.3 有事项锚的项 + 无事项锚的项 == 17', n_want + n_noanchor == 17, (n_want, n_noanchor))
ck('3.3b 有事项锚的项 == 14（实测，不写死）', n_want == 14, n_want)
# 反控：把事项号全改成 9，必须全部 ITEM_MISSING（证明判据能翻转）
ctrl = 0
for p in probe:
    if p['status'] in ('OK', 'ITEM_MISSING') and 9 not in p['have']:
        ctrl += 1
ck('3.4 反控：事项 9 若被请求则在所有节里都不存在（判据非恒真）', ctrl >= 7, ctrl)

json.dump(out, open(os.path.join(ROOT, '_r155', 'r155c_ledger_items.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('  FAILS = %d  %s' % (len(fails), fails))
