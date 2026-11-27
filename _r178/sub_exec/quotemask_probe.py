#!/usr/bin/env python3
# R178-EXEC-F35-QUOTEMASK: 一次跑完全部取证，写 REPORT.md 并打印完整摘要
import os, glob, hashlib, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r178/sub_exec')
os.makedirs(OUT, exist_ok=True)

A = '同血缘克隆'
B = '不是独立实现'
VERS = list(range(530, 561))
PAT = re.compile(r'^R17_R\d+_FACTINDEX_V(\d+)$')

def depth_arr(s):
    """左引号「先+1再记深度；右引号」先记当前深度再-1(最小0)。"""
    d = 0
    out = []
    for ch in s:
        if ch == '「':
            d += 1
            out.append(d)
        elif ch == '」':
            out.append(d)
            d = max(0, d - 1)
        else:
            out.append(d)
    return out

def count_sub(s, sub):
    """返回 (总次数, 裸次数, 引号内次数)，出现位置按首字符深度判定。"""
    dep = depth_arr(s)
    total = s.count(sub)
    bare = 0
    start = 0
    while True:
        i = s.find(sub, start)
        if i < 0:
            break
        if dep[i] == 0:
            bare += 1
        start = i + 1
    return total, bare, total - bare

def strip_quotes(s):
    return s.replace('「', '').replace('」', '')

def segs(seq):
    """seq: list of (version_str, value)；返回连续恒定区间与变化点。"""
    out = []
    if not seq:
        return out
    cur_v, cur = seq[0]
    start = cur_v
    for v, x in seq[1:]:
        if x != cur:
            out.append((start, cur_v, cur, v))
            start, cur = v, x
        cur_v = v
    out.append((start, cur_v, cur, None))
    return out

dirs = {}
for d in glob.glob(os.path.join(BASE, 'R17_R*_FACTINDEX_V*')):
    m = PAT.match(os.path.basename(d))
    if not m:
        continue
    v = int(m.group(1))
    if v in VERS:
        dirs[v] = d

rows = []
missing = []
for v in VERS:
    d = dirs.get(v)
    if not d or not os.path.isfile(os.path.join(d, 'FACT_INDEX.tsv')):
        missing.append('V%d 缺目录或 FACT_INDEX.tsv' % v)
        rows.append(dict(v=v, err='未取得'))
        continue
    with open(os.path.join(d, 'FACT_INDEX.tsv'), encoding='utf-8', newline='') as fh:
        lines = fh.read().split('\n')
    cols = None
    for ln in lines:
        if not ln.strip():
            continue
        c = ln.split('\t')
        if len(c) == 5 and c[0].strip() == 'F35':
            cols = c
            break
    if cols is None:
        missing.append('V%d 无 F35 五行' % v)
        rows.append(dict(v=v, err='未取得'))
        continue
    sha = hashlib.sha256('\t'.join(cols).encode('utf-8')).hexdigest()[:12]
    stmt, lim = cols[1], cols[4]
    r = dict(v=v, sha=sha,
             st_len=len(stmt), st_a=count_sub(stmt, A), st_b=count_sub(stmt, B),
             li_len=len(lim), li_a=count_sub(lim, A), li_b=count_sub(lim, B),
             st_q=(stmt.count('「'), stmt.count('」')),
             li_q=(lim.count('「'), lim.count('」')),
             st_a2=count_sub(strip_quotes(stmt), A), st_b2=count_sub(strip_quotes(stmt), B),
             li_a2=count_sub(strip_quotes(lim), A), li_b2=count_sub(strip_quotes(lim), B))
    rows.append(r)

# 结论：四个裸序列的恒定区间 / 变化点
bare_seq = {
    'stmt甲': [(r['v'], r['st_a'][1]) for r in rows if 'err' not in r],
    'stmt乙': [(r['v'], r['st_b'][1]) for r in rows if 'err' not in r],
    'lim甲':  [(r['v'], r['li_a'][1]) for r in rows if 'err' not in r],
    'lim乙':  [(r['v'], r['li_b'][1]) for r in rows if 'err' not in r],
}
concl = []
for k, seq in bare_seq.items():
    for s, e, val, chg in segs(seq):
        concl.append((k, s, e, val, chg))

# 反控1：删引号后裸计数变化
ctl1 = []
for r in rows:
    if 'err' in r:
        continue
    for col, orig, after in [
        ('stmt甲', r['st_a'][1], r['st_a2'][1]),
        ('stmt乙', r['st_b'][1], r['st_b2'][1]),
        ('lim甲',  r['li_a'][1],  r['li_a2'][1]),
        ('lim乙',  r['li_b'][1],  r['li_b2'][1]),
    ]:
        if after != orig:
            ctl1.append((r['v'], col, orig, after, after - orig))
# 反控2：不区分引号，总计数序列（甲乙，stmt/lim）
ctl2 = {}
for key, idx in [('stmt', 'st'), ('lim', 'li')]:
    for tag, j in [('甲', 'a'), ('乙', 'b')]:
        ctl2[key + tag] = [(r['v'], r[idx + '_' + j][0]) for r in rows if 'err' not in r]
# 反控3：引号数量是否相等
ctl3 = []
for r in rows:
    if 'err' in r:
        continue
    for col, (lq, rq) in [('stmt', r['st_q']), ('lim', r['li_q'])]:
        if lq != rq:
            ctl3.append((r['v'], col, lq, rq))

lines = []
lines.append('# R178-EXEC-F35-QUOTEMASK 取证报告（裸出现 / 引号内出现，逐版）')
lines.append('')
lines.append('脚本：`_r178/sub_exec/quotemask_probe.py`（本报告由该脚本一次运行生成）。')
lines.append('字符串甲=`同血缘克隆`；乙=`不是独立实现`；深度规则：「 +1 后记深度，」先记深度再 -1(最小0)；出现位置取首字符深度，0 为裸。')
lines.append('sha12 = `sha256("\\t".join(F35 行 5 列))[:12]`（UTF-8）。')
lines.append('')
lines.append('| 版本 | 行sha12 | stmt长度 | stmt甲总/裸 | stmt乙总/裸 | lim长度 | lim甲总/裸 | lim乙总/裸 |')
lines.append('|---|---|---:|---:|---:|---:|---:|---:|')
for r in rows:
    if 'err' in r:
        lines.append('| V%d | 未取得 | 未取得 | 未取得 | 未取得 | 未取得 | 未取得 | 未取得 |' % r['v'])
    else:
        lines.append('| V%d | %s | %d | %d/%d | %d/%d | %d | %d/%d | %d/%d |' % (
            r['v'], r['sha'], r['st_len'], *r['st_a'][:2], *r['st_b'][:2],
            r['li_len'], *r['li_a'][:2], *r['li_b'][:2]))
lines.append('')
lines.append('## 结论：裸计数恒定区间与变化点')
for k, s, e, val, chg in concl:
    rng = 'V%d..V%d = %d' % (s, e, val)
    lines.append('- %s：%s%s' % (k, rng, ('；变化点 V%d' % chg) if chg else ''))
lines.append('')
lines.append('## 反控')
lines.append('1. 删除「」后重数：发生变化的 (版本,列串,原裸,删后裸,差值) 共 %d 项：%s。' % (
    len(ctl1), '; '.join('V%d %s %d->%d (+%d)' % x for x in ctl1) if ctl1 else '无'))
lines.append('2. 不区分引号（等于总计数）序列（V530..V560）：')
for k, seq in ctl2.items():
    lines.append('   - %s: %s' % (k, ' '.join('%d:%d' % (v, n) for v, n in seq)))
lines.append('3. 「与」数量不等的 (版本,列,左,右) 共 %d 项：%s。' % (
    len(ctl3), '; '.join('V%d %s 「%d 」%d' % x for x in ctl3) if ctl3 else '全部相等'))
if missing:
    lines.append('')
    lines.append('未取得项：' + '; '.join(missing))
lines.append('')
report = '\n'.join(lines)
with open(os.path.join(OUT, 'REPORT.md'), 'w', encoding='utf-8') as fh:
    fh.write(report)

print('匹配版本目录数=%d，缺数据=%d' % (len(dirs), len(missing)))
print(report)
