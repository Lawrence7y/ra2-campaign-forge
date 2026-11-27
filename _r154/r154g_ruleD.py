# -*- coding: utf-8 -*-
"""R154 · 规则 D：把 hy4 执行员 #352 的独立结果与主会话 r154c/r154d 逐项对齐（不是复述，是复算）。

对齐口径必须先声明，因为两家的「观测次数」定义不同：
  * 主会话 r154d：obs = 当前文件 ∪ 同目录 <name>.bak/<name>.before_* ∪ 全仓 *.bak 名中含 <name>
  * 执行员 #352：obs = 当前文件 ∪ 全仓 *.bak 名中含 <name>（排除同目录同 basename 副本，理由是同轮
    兄弟目录的副本不是历史版本）
⇒ 两家对 31 行的档位与观测次数**应当完全相同**（本仓同目录没有 <name>.bak 形态），这一条本身就是要核的。
"""
import io, json, sys, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
mine = json.load(io.open(ROOT + '/_r154/r154d_c7_candidates.json', encoding='utf-8'))
sub = json.load(io.open(ROOT + '/_r154/sub_c7/hy4_c7_natural.json', encoding='utf-8'))

FAILS, NOTES = [], []
def chk(c, m): (NOTES if c else FAILS).append(('PASS ' if c else 'FAIL ') + m)

print('exec json top-level keys:', sorted(sub.keys())[:12])
rows = sub.get('rows') or sub.get('table') or []
if not rows:
    # 尝试常见容器
    for k in sub:
        if isinstance(sub[k], list) and sub[k] and isinstance(sub[k][0], dict) and 'id' in sub[k][0]:
            rows = sub[k]; print('using key', k); break
print('sub rows', len(rows))
if rows: print('sample row keys', sorted(rows[0].keys()))

mine_by = {}
for tier in ('A', 'B', 'C'):
    for d in mine[tier]:
        mine_by[str(d['id'])] = {'tier': tier, 'obs': d['obs'],
                                 'bytes': d.get('bytes') or d.get('max')}

def norm(r):
    return str(r.get('id') or r.get('discipline_id') or r.get('disc_id'))

sub_by = {}
for r in rows:
    sub_by[norm(r)] = r

chk(len(sub_by) == 31, 'subagent reported 31 rows (%d)' % len(sub_by))
chk(set(sub_by) == set(mine_by), 'same id set ; diff=%r' % sorted(set(sub_by) ^ set(mine_by)))

tier_mismatch, obs_mismatch = [], []
for i in sorted(mine_by, key=int):
    a, b = mine_by[i], sub_by[i]
    btier = b.get('tier') or b.get('grade') or b.get('bucket')
    bobs = b.get('observations') or b.get('obs') or b.get('obs_count')
    if btier != a['tier']: tier_mismatch.append((i, a['tier'], btier))
    if bobs is not None and int(bobs) != a['obs']: obs_mismatch.append((i, a['obs'], bobs))
chk(not tier_mismatch, 'tier assignment identical for all 31 rows ; mismatches=%r' % tier_mismatch[:6])
chk(not obs_mismatch, 'observation counts identical ; mismatches=%r' % obs_mismatch[:6])

# C 档 id 集与行集
mineC = sorted([i for i, v in mine_by.items() if v['tier'] == 'C'], key=int)
subC = sorted([i for i, r in sub_by.items() if (r.get('tier') or '') == 'C'], key=int)
chk(mineC == subC, 'C-tier ids identical: mine=%r sub=%r' % (mineC, subC))
chk(mineC == ['1', '2', '9', '20'], 'C-tier is exactly ids 1,2,9,20 (R14_COMMON x3 + check_disc.py)')

# A 档为空 —— 两家必须同判
mineA = mine['A']; subA = [r for r in rows if (r.get('tier') or '') == 'A']
chk(mineA == [] and subA == [], 'A-tier empty in BOTH reports (mine=%d sub=%d)' % (len(mineA), len(subA)))

# grep 历史命中率：主会话 r154d 的 hist_grep 与子代理的文本描述对齐
hg = mine['hist_grep']
chk(hg.get('1') == [109, 109] and hg.get('2') == [109, 109] and hg.get('9') == [109, 109],
    'lead hist_grep for ids 1/2/9 = 109/109 each ; got %r' % {k: hg.get(k) for k in ('1', '2', '9')})
chk(hg.get('20', [0, 0])[0] == 1, 'lead hist_grep for id 20 = 1/51 ; got %r' % (hg.get('20'),))

# 子代理文本里的 109/109 与 1/51 必须出现
mdpath = ROOT + '/_r154/sub_c7/hy4_c7_natural.md'
txt = io.open(mdpath, encoding='utf-8', errors='replace').read()
chk(txt.count('(109/109)') == 3, 'subagent md states 109/109 exactly 3 times (got %d)' % txt.count('(109/109)'))
chk('(1/51)' in txt, 'subagent md states 1/51 for id 20')

# 反控：把 A 档人为注入一行，档位比较必须能发现
fake = dict(mine_by); fake['3'] = {'tier': 'A', 'obs': 1, 'bytes': 911}
mism = [i for i in fake if fake[i]['tier'] != (sub_by[i].get('tier') or '')]
chk(mism == ['3'], 'NEGCTRL injected A-tier row is detected as mismatch (%r)' % mism)

out = {'mine_rows': len(mine_by), 'sub_rows': len(sub_by),
       'tier_mismatch': tier_mismatch, 'obs_mismatch': obs_mismatch,
       'C_ids': mineC, 'A_empty_both': (mineA == [] and subA == []),
       'pass': len(NOTES), 'fail': len(FAILS), 'fails': FAILS, 'notes': NOTES}
io.open(ROOT + '/_r154/r154g_ruleD.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
for m in NOTES + FAILS: print(m)
print('RESULT pass=%d fail=%d' % (len(NOTES), len(FAILS)))
sys.exit(1 if FAILS else 0)
