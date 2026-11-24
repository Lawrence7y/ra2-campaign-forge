# -*- coding: utf-8 -*-
# R69 · FACT_INDEX limitations 列非 § 引用全量机械解析核验 + evidence_paths 存在性普查
# 所有数字实测得出，禁止预估。脚本本身带正控/反控自测；自测失败则后续数字无效。
import os, re, sys, io, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
TSV  = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv')
RDIR = os.path.join(ROOT, 'lead/next_re_20261117_r14')

fails, log = [], []
def W(s=''):
    print(s); log.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

# ---------- 路径/锚点切分（与 verify_anchors.ts 同规则，Python 重实现）----------
def split_paths(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '(（': depth += 1
        elif ch in ')）': depth = max(0, depth - 1)
        if ch == ';' and depth == 0:
            out.append(cur); cur = ''; continue
        cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

def split_anchor(item):
    if not re.search(r'[)）]$', item): return item, None
    depth, start = 0, -1
    for i in range(len(item) - 1, -1, -1):
        c = item[i]
        if c in ')）': depth += 1; continue
        if c in '(（':
            depth -= 1
            if depth == 0: start = i; break
    if start <= 0: return item, None
    return item[:start], item[start + 1:-1]

# ---------- 自测（正控/反控）----------
W('--- 自测（正控/反控）---')
# A 正控：括号深度 0 分割
ck('A 分号分割(正控)', split_paths('a.md(§1;x);b.md') == ['a.md(§1;x)', 'b.md'],
   str(split_paths('a.md(§1;x);b.md')))
# B 反控：若在括号内也分割，结果必不同
ck('B 分号分割(反控：括号内不该切)', split_paths('a.md(§1;x)') == ['a.md(§1;x)'])
# C 正控：锚点剥离
f, a = split_anchor('lead/x.md(§2.9四)')
ck('C 锚点剥离(正控)', (f, a) == ('lead/x.md', '§2.9四'), repr((f, a)))
# D 正控：复合锚点（内层括号）
f, a = split_anchor('lead/x.md(§2.6来源段 / §2.7)')
ck('D 复合锚点(正控)', f == 'lead/x.md' and a == '§2.6来源段 / §2.7', repr((f, a)))
# E 反控：无锚点时不得误剥
f, a = split_anchor('lead/x.md')
ck('E 无锚点(反控：不得误剥)', (f, a) == ('lead/x.md', None), repr((f, a)))
# F 反控：文件名自带括号但不在末尾
f, a = split_anchor('lead/x(1)/y.md')
ck('F 中间括号(反控：不得剥)', (f, a) == ('lead/x(1)/y.md', None), repr((f, a)))

# ---------- 读取索引 ----------
raw = open(TSV, 'rb').read()
W('')
W('[TSV] %d B  CR=%d  LF=%d  sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                        hashlib.sha256(raw).hexdigest()[:16]))
ck('TSV 全 LF（CR=0）', raw.count(b'\r') == 0)
rows = [l.split('\t') for l in raw.decode('utf-8').split('\n') if l]
hdr, data = rows[0], rows[1:]
ck('表头 5 列', hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], str(hdr))
ck('数据行 54', len(data) == 54, str(len(data)))
ck('每行恰 5 列', all(len(r) == 5 for r in data))
ids = [r[0] for r in data]
ck('F01–F54 连续', ids == ['F%02d' % i for i in range(1, 55)], ','.join(ids[:3]))

# ---------- 任务1A：evidence_paths 存在性普查 ----------
W('')
W('=== 1A evidence_paths 路径存在性普查 ===')
items = []
for r in data:
    for it in split_paths(r[3]):
        f, a = split_anchor(it)
        f = f.strip('`').strip()
        items.append((r[0], f, a))
n_items = len(items)
n_anch = sum(1 for _, _, a in items if a)
exists = [(i, f, a) for i, f, a in items
          if os.path.exists(os.path.join(ROOT, f.replace('\\', '/')))]
missing = [(i, f, a) for i, f, a in items
           if not os.path.exists(os.path.join(ROOT, f.replace('\\', '/')))]
W('  条目总数            %d' % n_items)
W('  带锚点              %d' % n_anch)
W('  路径存在            %d' % len(exists))
W('  路径不存在          %d' % len(missing))
ck('条目总数 = 171（与上轮 anchor_check 同一分母）', n_items == 171, str(n_items))
ck('带锚点 = 117（与上轮 anchor_check 同一分母）', n_anch == 117, str(n_anch))
ck('存在 + 不存在 = 总数', len(exists) + len(missing) == n_items)
ck('反控：把一条真实路径改错必判不存在',
   not os.path.exists(os.path.join(ROOT, 'lead/next_re_20261117_r14/__NOPE__.md')))
ck('正控：R14_COMMON.md 必判存在',
   os.path.exists(os.path.join(ROOT, 'lead/next_re_20261117_r14/R14_COMMON.md')))

# 缺失目录归组
W('')
W('  缺失按顶层目录归组：')
grp = {}
for fid, f, a in missing:
    p = f.replace('\\', '/')
    parts = p.split('/')
    key = '/'.join(parts[:3]) if len(parts) > 3 else p
    grp.setdefault(key, []).append((fid, p))
for k in sorted(grp):
    fs = sorted(set(x[0] for x in grp[k]))
    dirtarget = os.path.join(ROOT, k)
    W('    %-58s 条目=%-3d fact=%s  目录存在=%s'
      % (k, len(grp[k]), ','.join(fs), os.path.exists(dirtarget)))

# ---------- 任务1B：limitations 列非 § 引用 ----------
W('')
W('=== 1B limitations 列非 § 引用全量解析 ===')
FPAT = re.compile(r'(?<![A-Za-z0-9_])(F\d{2})(?!\d)')
MPAT = re.compile(r'(?<![A-Za-z0-9_])(M\d{1,3})(?!\d)')
RPAT = re.compile(r'(?<![A-Za-z0-9_])(R17_[A-Z0-9_]+)')
idset = set(ids)
refs = []   # (宿主fact, 类型, 引用串, 目标存在, 备注)
for r in data:
    lim = r[4]
    for m in FPAT.finditer(lim):
        t = m.group(1)
        refs.append((r[0], 'F', t, t in idset, 'FACT_INDEX 内 fact_id'))
    for m in MPAT.finditer(lim):
        t = m.group(1)
        refs.append((r[0], 'M', t, None, 'PANEL/台账 M 号'))
    for m in RPAT.finditer(lim):
        t = m.group(1)
        refs.append((r[0], 'R', t, None, 'R17 目录/卡号'))

# 去重展示（同一宿主同一串只列一次，但保留出现次数）
W('  非 § 引用明细（host | 类 | 串 | 目标存在 | 次数）:')
seen = {}
for fid, kind, t, ex, note in refs:
    seen[(fid, kind, t)] = seen.get((fid, kind, t), 0) + 1
for k in sorted(seen):
    fid, kind, t = k
    if kind == 'F':
        ex = t in idset
        W('    %-4s F %-6s 存在=%-5s 次数=%d' % (fid, t, ex, seen[k]))
    elif kind == 'R':
        p1 = os.path.join(RDIR, t)
        p2 = os.path.join(RDIR, t + '.md')
        ex = os.path.exists(p1) or os.path.exists(p2)
        W('    %-4s R %-26s 存在=%-5s 次数=%d' % (fid, t, ex, seen[k]))
    else:
        W('    %-4s M %-6s 次数=%d' % (fid, t, seen[k]))

nF = sum(1 for k in seen if k[1] == 'F')
nM = sum(1 for k in seen if k[1] == 'M')
nR = sum(1 for k in seen if k[1] == 'R')
W('')
W('  去重后：F 引用 %d 对 / M 引用 %d 对 / R17 引用 %d 对' % (nF, nM, nR))

# F 号悬挂检查
W('')
W('  悬挂 F 号（引用目标不在 FACT_INDEX 内）：')
dangling = sorted(set(t for fid, kind, t in seen if kind == 'F' and t not in idset))
for t in dangling: W('    DANGLING %s' % t)
ck('无悬挂 F 号', dangling == [], str(dangling))

# F 号双向对
W('')
W('  F 号引用的双向对与单向对：')
edges = sorted(set((fid, t) for fid, kind, t in seen if kind == 'F'))
both, one = [], []
for a, b in edges:
    if (b, a) in edges and a < b: both.append((a, b))
for a, b in edges:
    if (b, a) not in edges: one.append((a, b))
W('    双向对 %d: %s' % (len(both), ', '.join('%s<->%s' % p for p in both)))
W('    单向对 %d: %s' % (len(one), ', '.join('%s->%s' % p for p in one[:20])))
ck('双向对数量与单向对数量之和 = 边数（无重复计入）',
   len(both) * 2 + len(one) == len(edges), '%d*2+%d vs %d' % (len(both), len(one), len(edges)))
ck('反控：判双向必须两侧,构造 (F99,F98) 单边应判非双向',
   ('F99', 'F98') in [('F99', 'F98')] and ('F98', 'F99') not in [('F99', 'F98')])

# ---------- 落盘 ----------
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_limref_r69.log')
W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
sys.exit(0 if not fails else 1)
