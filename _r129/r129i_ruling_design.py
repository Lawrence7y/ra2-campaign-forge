# -*- coding: utf-8 -*-
"""R129i：五条不可能行的三选一裁定 —— 本轮只做「设计 + 验算」，不落盘。

三条路各有硬约束，先逐条验算哪条在机制上可行：
  改行 把 round=R55 改成真实轮次（路径轮次），验算：新行能否通过 recheck_verify 的六条？
       关键在 R4 —— at 必须落在**新轮次**的窗口内。五条的 at 都在 R55 窗口
       （17:39:19 / 17:40:02），而 R61/R81/R84/R88 的窗口都在别处 ⇒ 只改 round 必失败。
       若同时改 at，那 at 就是我自己编的时刻，没有外部时钟可依 ⇒ 这是造假，不能做。
  撤回 删掉这五条自述行。验算：C11 对这五行会从 ok 掉成 fail（声称有却没有行）。
       必须同时把第 7 列改成无 —— 而那是改表，会撞 C14 指纹。
  降级 把第 7 列从有改成无（声明不补）。验算：C14 表指纹变 ⇒ 必须显式重钉；
       C11B_PIN_GAP 的 7 个 id 集合也会变 ⇒ 必须显式重钉；C17_PIN 会塌成空集 ⇒ 必须显式重钉。
       三条重钉都是「可见的、要写理由的」动作。

本脚本把三条路的**代价**逐项算出来，并证明只有「降级」这一条不需要编造任何时刻。
"""
import sys, os, json, re, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import ROOT
import io

R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
sys.path.insert(0, R14)
import recheck_verify as v

OUT = os.path.join(ROOT, '_r129', 'r129i_ruling_design.json')
rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n') if l][1:]
IDS = ['3', '4', '22', '27', '28']
byid = {r[0]: r for r in rows if len(r) == 7}
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

LINERE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')

def cur_line(i):
    ap = os.path.join(ROOT, byid[i][4].strip().replace('\\', '/'))
    for l in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
        m = LINERE.match(l)
        if m and int(m.group(1)) == int(i): return l
    return None

# 路一：只改 round
p1 = []
for i in IDS:
    l = cur_line(i)
    prs = sorted(set(int(m.group(1)) for m in PATHR.finditer(byid[i][4].strip().replace('\\', '/'))))
    cand = LINERE.sub(lambda m: 'DISC_RECHECK discipline=%s round=R%d at=%s anchors=%s conclusion=%s'
                      % (m.group(1), min(prs), m.group(3), m.group(4), m.group(5)), l)
    at = LINERE.match(cand).group(3)
    hh = at[11:13] + at[14:16] + at[17:19]
    w = v.ROUND_WINDOWS.get(min(prs))
    inwin = bool(w and w[0] <= v._hhmmss(hh) < w[1])
    p1.append({'id': i, 'new_round': min(prs), 'at': at, 'in_window': inwin,
               'window': (w[0].isoformat(), w[1].isoformat()) if w else None})
add('I1 路一「只改 round 到路径轮次」：五条全部仍不在新轮次窗口内 ⇒ 必然 R4 失败，不可行',
    all(not x['in_window'] for x in p1), p1)
add('I2 路一若还要改 at 才能过 R4，那 at 就是自编时刻（无外部时钟）⇒ 属造假，不做',
    True, '本条是纪律判断而非字节判断，如实标注')

# 路二：撤回（删行但不改表）
p2 = []
for i in IDS:
    p2.append({'id': i, 'later_col': byid[i][6].strip()[:4]})
add('I3 路二「删行、第 7 列不动」：C11 对这五条会从 ok 掉成 fail（声称有却没有有效自述行）',
    all(x['later_col'].startswith('有') for x in p2), p2)

# 路三：降级（第 7 列 有 -> 无）
p3 = []
for i in IDS:
    p3.append({'id': i, 'later': byid[i][6].strip(), 'expr': byid[i][5].strip()[:50]})
add('I4 路三「降级」在机制上可行：降级后 C11 走 claims-none，而 R129 的新判据要求校验式仍成立；'
    '实测这五条的校验式现在全部成立（r129d 已测 14/14）',
    all(x['later'].startswith('有') for x in p3), p3)

# 三条重钉代价
c14 = hashlib.sha256('\n'.join('%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])
                               for r in rows if len(r) == 7).encode('utf-8')).hexdigest()
add('I5 路三的代价一：C14 指纹会变（col2..col4 不变则不变；降级只改 col7 ⇒ C14 实际不变）',
    c14 == 'a740bcc9add4e6073071e5d6b693d213b4711ee2f3df8ab3c1db32e1a153975f', c14[:16])
load_gap = sorted(int(r[0]) for r in rows if len(r) == 7 and r[0].strip().isdigit()
                  and int(r[0]) in {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
                  and not r[6].strip().startswith('有'))
add('I6 路三的代价二：C11B_PIN_GAP 会从 7 个 id 涨到 12 个（3/4/22/27/28 加入），必须显式重钉',
    load_gap == [11, 12, 13, 14, 15, 17, 26], load_gap)
add('I7 路三的代价三：C17_PIN 会从 5 条塌成 0 条（降级后这些行不再「声称有」，C17 扫不到），'
    '必须显式重钉 —— 这是三处里最重要一处，因为它把「已承认的不可能」变成「已撤回的声称」',
    True, '常量须同步改：C17_PIN = set() 与新的 C17_PIN_SHA256')

# 关键核对：降级后 C11 会不会 FAIL
sys.path.insert(0, R14)
for i in IDS:
    ok, det = v.verify_recheck_line(ROOT, byid[i])
    add('I8 id %s 当前自述行能过 recheck_verify（说明它是「自洽但不可能」，不是格式坏行）' % i,
        ok, det)

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck), 'road1': p1, 'road3': p3},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
for x in p1: print('  road1 id=%s new_round=R%d at=%s in_window=%s' % (x['id'], x['new_round'], x['at'], x['in_window']))
