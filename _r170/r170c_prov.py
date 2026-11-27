#!/usr/bin/env python3
"""R170 C：R137 九节①–④ 的逐版溯源（V530..V549）+ grade 轴复算。"""
import glob, json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
L = ROOT + '/lead/next_re_20261117_r14'
A = []
def ck(i, cond, d):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(d)})
    print(('PASS ' if cond else 'FAIL ') + i + ' :: ' + str(d)[:220])

def rows_of(p):
    out = {}
    for ln in open(p, encoding='utf-8', newline='').read().split('\n')[1:]:
        if not ln.strip(): continue
        f = ln.split('\t'); out[f[0]] = f
    return out

vers = sorted(glob.glob(L + '/R17_R1*_FACTINDEX_V5*/FACT_INDEX.tsv'))
ck('C0 版本数 20', len(vers) == 20, len(vers))
seq = []
for p in vers:
    v = os.path.basename(os.path.dirname(p)).split('_')[-1]
    seq.append((v, rows_of(p)))
ck('C1 版本号 V530..V549 连续', [v for v, _ in seq] == ['V%d' % n for n in range(530, 550)], [v for v, _ in seq][:3])

PROBE = {
    'F23': ['差 **1 行无归属**', '4,147,334', 'coverage.tsv', '没有归属'],
    'F35': ['缺一手权威', '已撤回', '无外部规范权威', '定义有代码权威'],
}
tab = {}
for fid, pats in PROBE.items():
    print('---- %s ----' % fid)
    for v, r in seq:
        f = r[fid]
        got = ['%s=%d/%d' % (p, f[1].count(p), f[4].count(p)) for p in pats]
        tab.setdefault(fid, []).append([v] + [x for p in pats for x in (f[1].count(p), f[4].count(p))])
        print('%-5s %s  stmt=%d lim=%d' % (v, ' '.join(got), len(f[1]), len(f[4])))

first = next((row[0] for row in tab['F23'] if row[1] >= 1), None)
ck('C2 F23「差 **1 行无归属**」statement 首现版本', first is not None, first)
ck('C3 V549 F23 statement 含该串（R169 待办①「仍有差」判据落空）',
   tab['F23'][-1][1] == 1, tab['F23'][-1][:3])
first414 = next((row[0] for row in tab['F23'] if row[3] >= 1), None)
ck('C4 F23 statement 4,147,334 首现版本', first414 is not None, first414)

r35 = rows_of(L + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv')['F35'][1]
i = r35.index('缺一手权威')
ck('C5 F35 statement 该处前 40 字符含「已撤回」', '已撤回' in r35[max(0, i - 40):i], repr(r35[max(0, i - 40):i]))

G = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
lines = open(G, encoding='utf-8').read().split('\n')
idx = [n for n, s in enumerate(lines) if '分级口径：' in s]
selfref = [n for n in idx if '处「分级口径：」定义' in lines[n]]
ck('C6 自指行恰 1 处', len(selfref) == 1, selfref)
real = [n for n in idx if n not in selfref]
ck('C7 真定义处 = 16', len(real) == 16, len(real))
form = [n for n in real if any(k in lines[n] for k in ('实测', '独立复算', '字节', '签发件'))]
disk = [n for n in real if ('原件' in lines[n]) or ('在盘' in lines[n])]
ck('C8 指证据形态处数 >= 15', len(form) >= 15, 'form=%d disk=%d' % (len(form), len(disk)))
ck('C9 指「原件是否在盘」处数 = 0', len(disk) == 0, len(disk))

json.dump({'assertions': A, 'fail': sum(1 for a in A if not a['ok']), 'tab': tab,
           'graderows': {'all': idx, 'selfref': selfref, 'real': real, 'form': form, 'disk': disk}},
          open(ROOT + '/_r170/r170c_prov.json', 'w'), ensure_ascii=False, indent=1)
print('FAIL =', sum(1 for a in A if not a['ok']), '/', len(A))
