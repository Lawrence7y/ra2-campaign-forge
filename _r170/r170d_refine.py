#!/usr/bin/env python3
"""R170 D：订正 r170b/r170c 两处判据缺陷（S-566 / S-567）并重跑。
S-566：F35 的撤回语在引号**之后**（「缺一手权威」已撤回），我只查前 40 字符 ⇒ 假 FAIL。
S-567：反控查「全镜像只有两份」，但该串正被否定句引用 ⇒ 反控判据必须排除引用形态。
另：grade 轴 17 行里 1 行是 R150 自指行（含「16 处」），必须剔除后再数。
"""
import json, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
L = ROOT + '/lead/next_re_20261117_r14'
V = L + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
A = []
def ck(i, cond, d):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(d)})
    print(('PASS ' if cond else 'FAIL ') + i + ' :: ' + str(d)[:230])

rows = {}
for p in open(V, encoding='utf-8', newline='').read().split('\n')[1:]:
    if not p.strip(): continue
    f = p.split('\t'); rows[f[0]] = f

# ---- S-566 修正：撤回标记须在引号前或后 40 字符内（双向窗）----
s35 = rows['F35'][1]
i = s35.index('缺一手权威')
win = s35[max(0, i - 40):i + 40]
ck('F1 F35「缺一手权威」双向窗含撤回标记', ('已撤回' in win) or ('不得再写' in win), repr(win))
ck('F2 该处是被「」引用的旧措辞（不是本轮主张）', s35[i - 1:i] == '「' or '「' in s35[max(0, i - 2):i], repr(s35[max(0, i - 2):i + 8]))
ck('F3 反控：F35 statement 里「缺一手权威」恰 1 次（不重复主张）', s35.count('缺一手权威') == 1, s35.count('缺一手权威'))

# ---- S-567 修正：反控必须排除「被否定的引用」形态 ----
s29 = rows['F29'][1]
bad = [m.start() for m in re.finditer('全镜像只有两份', s29)]
ctx = [s29[max(0, b - 12):b] for b in bad]
ck('G1 错句「全镜像只有两份」只以被否定引用形态出现', all('不可读成「' in s29[max(0, b - 12):b] or '不可读成' in s29[max(0, b - 20):b] for b in bad) if bad else True,
   {'hits': len(bad), 'pre': ctx})
# 真正的反控：该错句不得作为肯定断言出现（前置 20 字符内无否定词）
assertive = [b for b in bad if not any(k in s29[max(0, b - 20):b] for k in ('不可读成', '不是', '不得', '误'))]
ck('G2 无反控项作为肯定断言', len(assertive) == 0, assertive)

# ---- F24 limitations 里 86.19 的 5 处逐处定性 ----
l24 = rows['F24'][4]
occ = [m.start() for m in re.finditer(re.escape('86.19'), l24)]
det = []
for o in occ:
    w = l24[max(0, o - 120):o + 120]
    kind = 'retract' if any(k in w for k in ('撤销', '撤下', '不是', '错', '不得', '滑移')) else 'quote'
    det.append((o, kind))
ck('H1 F24.lim 5 处 86.19 全部带定性标记', len(occ) == 5 and all(k in ('retract', 'quote') for _, k in det), det)

# ---- grade 轴：17 行中剔除自指行 ----
G = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
lines = open(G, encoding='utf-8').read().split('\n')
idx = [n for n, s in enumerate(lines) if '分级口径：' in s]
selfref = [n for n in idx if '16 处' in lines[n] and '定义' in lines[n]]
ck('I1 自指行恰 1 处（含「16 处」）', len(selfref) == 1, selfref)
real = [n for n in idx if n not in selfref]
ck('I2 真定义行 = 16', len(real) == 16, len(real))
form = [n for n in real if any(k in lines[n] for k in ('实测', '独立复算', '字节', '签发件', '真机'))]
disk = [n for n in real if ('原件' in lines[n]) or ('在盘' in lines[n]) or ('失联' in lines[n])]
ck('I3 指证据形态的 = 16/16', len(form) == 16 and len(disk) == 0, {'form': len(form), 'disk': len(disk), 'disk_rows': disk})
# 反控：自指行自己提到「在盘」⇒ 若把它算进来会得 disk=1（说明剔除是必要的）
disk_all = [n for n in idx if ('原件' in lines[n]) or ('在盘' in lines[n])]
ck('I4 反控：不剔除自指行会误得 disk=1', len(disk_all) == 1 and disk_all == selfref, disk_all)

json.dump({'assertions': A, 'fail': sum(1 for a in A if not a['ok']),
           'grade': {'all': idx, 'selfref': selfref, 'real': real, 'disk': disk, 'disk_all': disk_all},
           'f24_lim_occ': det},
          open(ROOT + '/_r170/r170d_refine.json', 'w'), ensure_ascii=False, indent=1)
print('FAIL =', sum(1 for a in A if not a['ok']), '/', len(A))
