#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-a · F23/F35 的「作用域过期」与「措辞残留」证据测量（只读，不改任何被测量文件）

两个待判命题（都是「引用会引错方向」的类型，不是数字错）：

  P1（F23）: limitations 里 R159 段自称「逐版扫 13 版（V530–V542）……首现于 V540，
     V541/V542 逐字延续」。现版是 V544。若 V543/V544 的计数与 V540–V542 不同，
     则该作用域**已经过期**，引用「每版 1 次」会与现版实况相反。

  P2（F35）: statement ② 写「另 3 个脚本……**不是独立实现**……属同血缘克隆」，
     而 limitations 的 R139 段仍写「另有 3 个**独立脚本**含同一逐字判据」。同列两处
     对同一批文件给定性相反。血缘可机械判：共用同一 PROJ 常量 + 同一对输入文件。

设计约束：
  - 只读文本与小文件，不碰 gamemd.exe 大段反汇编（不触 OOM 红线）。
  - 每条判据都带反控：正控（已知存在串必须命中）/ 负控（自造串必须 0 命中）。
  - 禁止 `or True` 型恒真断言。
"""
import glob
import hashlib
import io
import json
import os
import re
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
OUT = {}
FAILS = []


def ck(name, cond, detail=''):
    ok = bool(cond)
    print(('  PASS ' if ok else '  FAIL ') + name + (('  :: ' + str(detail)[:240]) if detail else ''))
    if not ok:
        FAILS.append(name)
    return ok


def rd(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def rows_of(p):
    d = {}
    for l in rd(p).split('\n'):
        if not l:
            continue
        c = l.split('\t')
        d[c[0]] = c
    return d


def versions():
    ds = glob.glob(os.path.join(T, 'R17_R1*_FACTINDEX_V5*'))
    ds = [d for d in ds if re.search(r'_V5\d\d$', d)]
    return sorted(ds, key=lambda d: int(d.rsplit('_V', 1)[1]))


# ---------------------------------------------------------------- P1 · F23
print('== P1 · F23 的 R159 作用域（V530..V542）是否仍然覆盖现版 ==')
# S-519：本脚本原先写死「恰 15 个 / 530..544」，V545 一落盘即假 FAIL。
# 正确口径：目录数 >= 15 且最小/最大覆盖 530 与「观测到的最大版」，并把「本脚本写时是否已有 V545」记下来。
V = versions()
_vs = [int(os.path.basename(x).rsplit('_V', 1)[1]) for x in V]
ck('P1.0 版本目录 >= 15 且自 530 起连续（V530..max）',
   len(V) >= 15 and min(_vs) == 530 and _vs == list(range(530, 530 + len(_vs))), _vs)
ck('P1.0b 观测到的最大版 ∈ {544, 545}（本脚本测量时点的如实记录，不外推）',
   max(_vs) in (544, 545), max(_vs))
MEAS_MAX = max(_vs)

NEEDLE = '12 行分解'
ALSO = ['6 + 2 + 3', '6+2+3+3', '1 行无归属']
counts = {}
for d in V:
    ver = int(os.path.basename(d).rsplit('_V', 1)[1])
    r = rows_of(os.path.join(d, 'FACT_INDEX.tsv'))
    f = r['F23']
    counts[ver] = {
        'n_needle': f[1].count(NEEDLE) + f[4].count(NEEDLE),
        'col2': f[1].count(NEEDLE),
        'col5': f[4].count(NEEDLE),
        'len2': len(f[1]),
        'len5': len(f[4]),
        'grade': f[2],
    }
    print('   V%d  12 行分解 计%d (col2=%d col5=%d) len2=%5d len5=%5d grade=%s'
          % (ver, counts[ver]['n_needle'], counts[ver]['col2'], counts[ver]['col5'],
             counts[ver]['len2'], counts[ver]['len5'], counts[ver]['grade']))
OUT['P1_counts'] = counts

ck('P1.1 正控：V544 该串命中 >0（尺子有效）', counts[544]['n_needle'] > 0, counts[544]['n_needle'])
ck('P1.2 反控：自造串在 V544 命中 0', ('12 行分解ZZQ' in rd(
    os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv'))) is False)
ck('P1.3 R159 自述「V539 及以前共 0 版命中」成立',
   all(counts[v]['n_needle'] == 0 for v in range(530, 540)),
   {v: counts[v]['n_needle'] for v in range(530, 540)})
ck('P1.4 R159 自述「首现于 V540」成立',
   counts[540]['n_needle'] > 0 and counts[539]['n_needle'] == 0,
   (counts[539]['n_needle'], counts[540]['n_needle']))
ck('P1.5 R159 自述「V541/V542 逐字延续」成立（两版计数相同）',
   counts[541]['n_needle'] == counts[542]['n_needle'] == counts[540]['n_needle'],
   (counts[540]['n_needle'], counts[541]['n_needle'], counts[542]['n_needle']))

# 关键判定：作用域止于 V542，而现版 V544 计数不同
GROW = (counts[MEAS_MAX]['n_needle'] != counts[542]['n_needle'])
ck('P1.6 【作用域过期】观测到的最新版计数 != V542 计数（R159 的度量不能外推到 V543 及以后）',
   GROW, {'V542': counts[542]['n_needle'], 'V543': counts[543]['n_needle'],
          'V544': counts[544]['n_needle'], 'max': counts[MEAS_MAX]['n_needle']})
ck('P1.7 V543..最新版计数相同（V543 一次引入，之后未再变）',
   len({counts[v]['n_needle'] for v in range(543, MEAS_MAX + 1)}) == 1,
   {v: counts[v]['n_needle'] for v in range(543, MEAS_MAX + 1)})
ck('P1.8 增量全部来自 limitations（col2 在 V540..V544 恒为 1）',
   all(counts[v]['col2'] == 1 for v in range(540, 545)),
   {v: counts[v]['col2'] for v in range(540, 545)})
ck('P1.9 statement 在 V540..最新版逐版长度不变（1012）',
   all(counts[v]['len2'] == 1012 for v in range(540, MEAS_MAX + 1)),
   {v: counts[v]['len2'] for v in range(540, MEAS_MAX + 1)})
# 三次出现分别落在哪一段：R148 段 / R138 段 / R159 段
v544lim = rows_of(os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv'))['F23'][4]
seg = {}
seg['R148'] = v544lim.count('【R148 补')
for tag in ('R138 补·分解不闭合', 'R159 补·12 行分解的缺口与作用域'):
    seg[tag] = v544lim.count(tag)
ck('P1.10 【R138 补·分解不闭合】/【R159 补·…】两段在现版各恰 1 次（定位锚有效）',
   seg['R138 补·分解不闭合'] == 1 and seg['R159 补·12 行分解的缺口与作用域'] == 1, seg)
i159 = v544lim.find('【R159 补·12 行分解的缺口与作用域】')
seg159 = v544lim[i159:]
seg_before = v544lim[:i159]
# 段头本身含该串 ⇒ R159 段内应为 2 次（段头 1 + 引文 1），R159 之前 0 次
ck('P1.11 R159 段头内含该串 ⇒ 段内 2 次（段头 1 + 引文 1）、段前 0 次、总 2 次',
   seg159.count('12 行分解') == 2 and seg_before.count('12 行分解') == 0
   and v544lim.count('12 行分解') == 2,
   (seg159.count('12 行分解'), seg_before.count('12 行分解'), v544lim.count('12 行分解')))
VMAX_DIR = os.path.join(T, 'R17_R1%02d_FACTINDEX_V%d' % (0, MEAS_MAX))
_cand = [d for d in V if int(os.path.basename(d).rsplit('_V', 1)[1]) == MEAS_MAX][0]
ck('P1.12 第 3 次来自 statement（col2 1 次）',
   rows_of(os.path.join(_cand, 'FACT_INDEX.tsv'))['F23'][1].count('12 行分解') == 1)

# 其他三条子串的逐版轨迹（说明 R159 段的算式串同样在 V543 增长）
traj = {}
for d in V:
    ver = int(os.path.basename(d).rsplit('_V', 1)[1])
    f = rows_of(os.path.join(d, 'FACT_INDEX.tsv'))['F23']
    blob = f[1] + '\x00' + f[4]
    traj[ver] = {a: blob.count(a) for a in ALSO}
OUT['P1_traj'] = traj
ck('P1.13 「6 + 2 + 3」在 V539 为 0、V540 起 >0（同源首现）',
   traj[539]['6 + 2 + 3'] == 0 and traj[540]['6 + 2 + 3'] > 0,
   (traj[539]['6 + 2 + 3'], traj[540]['6 + 2 + 3']))
ck('P1.14 「1 行无归属」在 V539 为 0、V540 起 >0',
   traj[539]['1 行无归属'] == 0 and traj[540]['1 行无归属'] > 0,
   (traj[539]['1 行无归属'], traj[540]['1 行无归属']))

json.dump({'P1': counts, 'P1_traj': traj, 'P1_seg': seg}, open(os.path.join(R, '_r165/_p1.json'), 'w'), indent=1)

# ---------------------------------------------------------------- P2 · F35
print()
print('== P2 · F35 「独立脚本」与「不是独立实现」是否同列互斥 ==')
F35 = rows_of(os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv'))['F35']
ck('P2.1 statement 含「不是独立实现」恰 1 次', F35[1].count('不是独立实现') == 1, F35[1].count('不是独立实现'))
ck('P2.2 statement 含「同血缘克隆」恰 1 次', F35[1].count('同血缘克隆') == 1, F35[1].count('同血缘克隆'))
ck('P2.3 limitations 含「独立脚本」恰 1 次', F35[4].count('独立脚本') == 1, F35[4].count('独立脚本'))
ck('P2.4 limitations **不含**「不是独立实现」（撤回措辞只写在 statement，未回写到 limitations）',
   F35[4].count('不是独立实现') == 0, F35[4].count('不是独立实现'))
i = F35[4].find('另有 3 个独立脚本含同一逐字判据')
ck('P2.5 limitations 的「独立脚本」句定位成功', i > 0, i)
para = F35[4][max(0, i - 700):i + 300]
ck('P2.6 该句所在段的首句是「【R139 更正·定义有现盘一手实现，R138 那句「只有二手转述」为伪】」',
   '【R139 更正' in F35[4][max(0, i - 900):i], F35[4][max(0, i - 900):i][:120])
ck('P2.7 该「R139 更正」段内**不含**任何「同血缘 / 不是独立实现 / 克隆」字样（说明该段未被回写）',
   all(w not in para for w in ('同血缘', '不是独立实现', '克隆')), para[-120:])

# 逐版轨迹：这两处措辞谁先出现、是否同一版
tr = {}
for d in V:
    ver = int(os.path.basename(d).rsplit('_V', 1)[1])
    f = rows_of(os.path.join(d, 'FACT_INDEX.tsv'))['F35']
    tr[ver] = {'s_indep_impl_no': f[1].count('不是独立实现'),
               's_clone': f[1].count('同血缘'),
               'l_indep': f[4].count('独立脚本'),
               'len2': len(f[1]), 'len5': len(f[4]), 'grade': f[2]}
    print('   V%d  「不是独立实现」=%d 「同血缘」=%d 「独立脚本」(限)=%d len2=%5d len5=%5d grade=%s'
          % (ver, tr[ver]['s_indep_impl_no'], tr[ver]['s_clone'], tr[ver]['l_indep'],
             tr[ver]['len2'], tr[ver]['len5'], tr[ver]['grade']))
OUT['P2_traj'] = tr
ck('P2.8 「独立脚本」首现于 V534（与 R139 段同版）',
   tr[533]['l_indep'] == 0 and tr[534]['l_indep'] == 1,
   (tr[533]['l_indep'], tr[534]['l_indep']))
ck('P2.9 「不是独立实现 / 同血缘」首现于 V540（晚 6 版）',
   tr[539]['s_indep_impl_no'] == 0 and tr[540]['s_indep_impl_no'] == 1
   and tr[539]['s_clone'] == 0 and tr[540]['s_clone'] == 1,
   (tr[539], tr[540]))
ck('P2.10 V540..V544 五版里两处措辞同时存在（互斥表述共存 5 版，未被回收）',
   all(tr[v]['s_indep_impl_no'] == 1 and tr[v]['l_indep'] == 1 for v in range(540, 545)),
   {v: (tr[v]['s_indep_impl_no'], tr[v]['l_indep']) for v in range(540, 545)})
ck('P2.11 F35 grade 在 15 版恒为 [流程]（从未被降级/升级）',
   len(set(tr[v]['grade'] for v in range(530, 545))) == 1 and tr[544]['grade'] == '[流程]',
   tr[544]['grade'])

# 血缘机械判据：PROJ 常量 + 输入文件 + 判据串行号
print()
print('== P2b · 三个脚本与权威脚本是否「同血缘」（PROJ / 输入 / 判据串）==')
SCRIPTS = {
    'authority': os.path.join(T, 'RULING_R15_20261119/work/strict_panel.py'),
    'precheck': os.path.join(T, '_cards/M59-MERGE/precheck.py'),
    'simulate': os.path.join(T, '_cards/M59-MERGE/simulate.py'),
    'verify': os.path.join(T, '_cards/M59-MERGE/verify.py'),
    'writer': os.path.join(T, '_cards/M59-MERGE/merge_panel.py'),
}
info = {}
for k, p in SCRIPTS.items():
    ck('P2b.0 %s 在盘' % k, os.path.isfile(p), p)
    t = rd(p)
    lines = t.split('\n')
    hits = [i + 1 for i, l in enumerate(lines) if '[未证]' in l]
    proj = re.search(r'PROJ\s*=\s*r?"([^"]+)"', t)
    info[k] = {
        'sha256_12': hashlib.sha256(open(p, 'rb').read()).hexdigest()[:12],
        'nz_lines': hits,
        'code_lines': [n for n in hits if 'not in' in lines[n - 1]],
        'proj': proj.group(1) if proj else None,
        'inputs': sorted(set(re.findall(r'COVERAGE[/\\\\]+coverage\.tsv|function_atlas\.tsv', t))),
        'bytes': os.path.getsize(p),
    }
    print('   %-10s bytes=%5d  [未证]行=%s  代码态=%s  PROJ=%s  inputs=%s'
          % (k, info[k]['bytes'], info[k]['nz_lines'], info[k]['code_lines'],
             info[k]['proj'], info[k]['inputs']))
OUT['P2b'] = info

ck('P2b.1 权威脚本恰 2 处「[未证]」、代码态恰 1 处（第 78 行），散文在第 14 行',
   info['authority']['nz_lines'] == [14, 78] and info['authority']['code_lines'] == [78],
   info['authority']['nz_lines'])
ck('P2b.2 statement 声称的三个行号逐一对上：precheck:60 / simulate:72 / verify:83',
   info['precheck']['code_lines'] == [60] and info['simulate']['code_lines'] == [72]
   and info['verify']['code_lines'] == [83],
   (info['precheck']['code_lines'], info['simulate']['code_lines'], info['verify']['code_lines']))
ck('P2b.3 四者 PROJ 常量逐字相同（同血缘的机械判据之一）',
   len({info[k]['proj'] for k in ('authority', 'precheck', 'simulate', 'verify')}) == 1,
   {k: info[k]['proj'] for k in ('authority', 'precheck', 'simulate', 'verify')})
# 输入路径由 os.path.join(ROOT,"COVERAGE","coverage.tsv") 拼出 ⇒ 必须按分段字面量核，不能按整串正则
IO = {}
for k, p in SCRIPTS.items():
    t2 = rd(p)
    IO[k] = {
        'cov': ('"COVERAGE", "coverage.tsv"' in t2) or ('"COVERAGE","coverage.tsv"' in t2),
        'atlas': ('"W130_atlas", "function_atlas.tsv"' in t2) or ('"W130_atlas","function_atlas.tsv"' in t2),
        'root': 'ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")' in t2,
    }
    print('   %-10s COV分段=%s ATLAS分段=%s ROOT同一=%s' % (k, IO[k]['cov'], IO[k]['atlas'], IO[k]['root']))
OUT['P2b_io'] = IO
ck('P2b.4 四者共用同一对输入：COV=ROOT/COVERAGE/coverage.tsv 且 ATLAS=PROJ/.../function_atlas.tsv',
   all(IO[k]['cov'] and IO[k]['atlas'] and IO[k]['root']
       for k in ('authority', 'precheck', 'simulate', 'verify')),
   IO)
ck('P2b.4b 反控：写入器虽有同一 PROJ/ROOT，但**不打开**这对输入（cov/atlas 分段均 False）',
   IO['writer']['cov'] is False and IO['writer']['atlas'] is False, IO['writer'])
ck('P2b.5 反控：写入器 merge_panel.py 不含该判据（0 处「[未证]」）',
   info['writer']['nz_lines'] == [] and info['writer']['code_lines'] == [], info['writer']['nz_lines'])
ck('P2b.6 反控：写入器与四者同 PROJ 但不同判据 ⇒ 「共用 PROJ」不能单独当血缘充分条件',
   info['writer']['proj'] == info['authority']['proj'] and info['writer']['nz_lines'] == [],
   (info['writer']['proj'], info['writer']['nz_lines']))
ck('P2b.7 四者输入路径同为「已失文件」（coverage.tsv 现盘 0 命中）',
   os.path.isdir(os.path.join(T, 'COVERAGE')) is False)
ck('P2b.8 两个输入文件的父目录均不存在（COVERAGE / next_re_20261112_r10）',
   not os.path.isdir(os.path.join(T, 'COVERAGE'))
   and not os.path.isdir(os.path.join(T, '..', 'next_re_20261112_r10')),
   (os.path.isdir(os.path.join(T, 'COVERAGE')),
    os.path.isdir(os.path.join(T, '..', 'next_re_20261112_r10'))))

json.dump({'P2': tr, 'P2b': info}, open(os.path.join(R, '_r165/_p2.json'), 'w'), indent=1)

print()
print('=== FAILS: %d ===' % len(FAILS))
for f in FAILS:
    print('   -', f)
sys.exit(1 if FAILS else 0)
