
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R157 A · F23 grade 裁定的三项前置：甲案（补在盘证据）到底可行不可行、
grade 轴的定义式到底指向什么、R90「档 2（可重算）」的七式有没有鉴别力。

起因：F23 的 grade 裁定从 R149 挂到 R156（八轮）。R149 把前置写成「甲/乙 二选一」，
但两条都没被独立实测过：
  甲（补出在盘证据）—— 从未做过**穷尽性**搜索，只在仓库内按 basename 查过；
  乙（降级）—— 依赖「零存活 ⇒ 降级」这个因果，而 grade 轴自身的定义从未被逐行统计。

本脚本只测量、不下裁定。三个口径都带正控/反控，判据写法承 R154/R156 的自错族：
  · 断言里不写进本该被查询的量（S-419/S-414）；
  · 比较前先对齐口径（S-410/S-411/S-412/S-415）；
  · 计数类断言先问「字符串会不会被别处引用」（S-395/S-413）；
  · 扫描类断言先问「被测对象会不会就是测量者」（S-384/S-396）。

幂等：只读，不写任何被测文件；产物只写 _r157/。
"""
import io, json, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
IDX = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
LED = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
SNAP = D + '/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv'
OUT = R + '/_r157/r157a_f23_ruling_premises.json'

fails = []
def ck(name, cond, detail=''):
    ok = bool(cond)
    print(('  PASS ' if ok else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not ok:
        fails.append(name)
    return ok

res = {}

# ---------------------------------------------------------------- 0 现态
print('== 0 · 现态快照 ==')
rows = [l.split('\t') for l in io.open(IDX, encoding='utf-8').read().split('\n') if l.count('\t') == 4]
hdr, data = rows[0], {r[0]: dict(zip(rows[0], r)) for r in rows[1:]}
ck('0.1 FACT_INDEX 数据行 54', len(data) == 54, len(data))
ck('0.2 F23 grade 现盘 = [已证]', data['F23']['grade'] == '[已证]', data['F23']['grade'])
ck('0.3 F35 grade 现盘 = [流程]', data['F35']['grade'] == '[流程]', data['F35']['grade'])
import hashlib
idx_bytes = os.path.getsize(IDX)
res['index'] = {'path': os.path.relpath(IDX, R), 'bytes': idx_bytes,
                'sha256': hashlib.sha256(open(IDX, 'rb').read()).hexdigest(),
                'f23_grade': data['F23']['grade'], 'f35_grade': data['F35']['grade']}
print('    F23 evidence_paths =', data['F23']['evidence_paths'])

# ---------------------------------------------------------------- 1 甲案可行性
print()
print('== 1 · 甲案（补出在盘证据）可行性：四口径穷尽搜索 ==')
TARGETS = ['coverage.tsv', 'PANEL.md', 'DELIVERY_SUMMARY.md']

# --- 1a 仓库内 basename 精确命中（walk 全树）
found = {t: [] for t in TARGETS}
scanned = 0
for dp, dn, fn in os.walk(R):
    if '/.git' in dp:
        continue
    for f in fn:
        scanned += 1
        if f in found:
            p = os.path.join(dp, f)
            try:
                found[f].append((os.path.relpath(p, R), os.path.getsize(p)))
            except OSError:
                pass
print('  1a 仓库内 walk 文件数 =', scanned)
for t in TARGETS:
    ck('1a %s 仓库内命中 0（实测 %d）' % (t, len(found[t])), len(found[t]) == 0,
       found[t][:3])
res['jia_1a_walk'] = {'scanned': scanned,
                      'hits': {t: found[t] for t in TARGETS}}

# --- 1a 正控：同一 walk 必须能命中一个**确实在盘**的 basename，否则 walk 本身失效
pos = {t: [] for t in ['FACT_INDEX.tsv', 'R14_COMMON.md']}
for dp, dn, fn in os.walk(R):
    if '/.git' in dp:
        continue
    for f in fn:
        if f in pos:
            pos[f].append(os.path.relpath(os.path.join(dp, f), R))
ck('1a-P 正控：walk 能命中 FACT_INDEX.tsv（>0）', len(pos['FACT_INDEX.tsv']) > 0, len(pos['FACT_INDEX.tsv']))
ck('1a-P 正控：walk 能命中 R14_COMMON.md（>0）', len(pos['R14_COMMON.md']) > 0, len(pos['R14_COMMON.md']))
# --- 1a 反控：自造名必须 0 命中
bogus = [0]
for dp, dn, fn in os.walk(R):
    if '/.git' in dp:
        continue
    for f in fn:
        if f == 'ZZZ_R157_NO_SUCH_FILE_QQQ.tsv':
            bogus[0] += 1
ck('1a-N 反控：自造文件名命中 0', bogus[0] == 0, bogus[0])

# --- 1b 精确字节 4,147,334（仓库外也查，限 /home/t628 与 /mnt 可读区）
print('  1b 全盘精确字节 4,147,334 反查 …')
byte_hits = []
roots = ['/home/t628', '/mnt']
skip = ('/proc', '/sys', '/dev', '/run')
nfile = 0
for root in roots:
    for dp, dn, fn in os.walk(root, onerror=lambda e: None):
        if any(s in dp for s in skip):
            dn[:] = []
            continue
        # 不扫本仓库（已由 1a 覆盖）
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) == 4147334:
                    byte_hits.append(p)
                nfile += 1
            except OSError:
                pass
print('  1b 扫描文件数 =', nfile)
ck('1b 精确 4,147,334 B 的文件全盘 0 个', len(byte_hits) == 0, byte_hits[:3])
res['jia_1b_bytes'] = {'scanned': nfile, 'hits': byte_hits}

# --- 1c 表头逐字（全盘 .tsv/.csv，只读文件头 4 KiB）
print('  1c 表头逐字 "entry,subsystem,name,one_line_semantics" 全盘反查 …')
HDR = 'entry,subsystem,name,one_line_semantics'
hdr_hits = []
nsc = 0
for root in roots:
    for dp, dn, fn in os.walk(root, onerror=lambda e: None):
        if any(s in dp for s in skip):
            dn[:] = []
            continue
        for f in fn:
            if not f.endswith(('.tsv', '.csv')):
                continue
            p = os.path.join(dp, f)
            try:
                with open(p, 'rb') as fh:
                    head = fh.read(4096)
            except OSError:
                continue
            nsc += 1
            if HDR.encode() in head:
                hdr_hits.append(p)
print('  1c 扫描 tsv/csv 文件数 =', nsc)
ck('1c 表头逐字命中 0 个文件', len(hdr_hits) == 0, hdr_hits[:3])
res['jia_1c_header'] = {'scanned': nsc, 'hits': hdr_hits}

# --- 1d 快照记录：这些文件**曾在册**
snap = io.open(SNAP, encoding='utf-8', errors='replace').read().split('\n')
# 列：path  ext  bytes  mtime_ns  (制表分隔)
snap_recs = {}
for l in snap:
    if not l.strip():
        continue
    parts = l.split('\t')
    if len(parts) < 4:
        continue
    snap_recs.setdefault(parts[0], parts)
ck('1d 快照可解析行数 > 20,000', len(snap_recs) > 20000, len(snap_recs))
for t in TARGETS:
    recs = [p for p in snap_recs if os.path.basename(p) == t]
    ck('1d-快照 %s 在册记录 > 0（实测 %d）' % (t, len(recs)), len(recs) > 0, len(recs))
    if t == 'coverage.tsv':
        # 两个口径必须分开写（R148 已记：严格主份 1 条 / 含 _hygiene 的 4 条）。
        # R157 自错 S-425：首版只写「主份恰 1 条」却用 endswith('/COVERAGE/coverage.tsv')
        # 判，把 _hygiene/M13_before/COVERAGE/coverage.tsv 等 3 条也算进来 ⇒ 假 FAIL。
        main = [p for p in recs if p == 'next_re_20261117_r14/COVERAGE/coverage.tsv']
        sub = [p for p in recs if p.endswith('/COVERAGE/coverage.tsv')]
        ck('1d-主份（精确路径 == next_re_.../COVERAGE/coverage.tsv）恰 1 条',
           len(main) == 1, main)
        ck('1d-含 /COVERAGE/coverage.tsv 后缀的记录 == 4（主份 1 + _hygiene 3，与 R148 同口径）',
           len(sub) == 4, sub)
        if main:
            rec = snap_recs[main[0]]
            ck('1d-主份字节 = 4,147,334', rec[2] == '4147334', rec[2])
        sizes = sorted({snap_recs[p][2] for p in recs})
        ck('1d-主份 + 备份字节两两不同（distinct == 记录数）',
           len(sizes) == len(recs), (len(sizes), len(recs)))
        res['snap_coverage'] = {'records': len(recs), 'distinct_bytes': sizes,
                                'paths': recs[:20]}
        print('    coverage.tsv 在册 %d 条、distinct 字节 %d 个' % (len(recs), len(sizes)))
    else:
        res['snap_' + t] = {'records': len(recs),
                            'sample': [(p, snap_recs[p][2]) for p in recs[:5]]}

# 交叉：18 条记录全都不在盘（与 1a 合并成「曾在册、现全失」）
cov_paths = [p for p in snap_recs if os.path.basename(p) == 'coverage.tsv']
alive = [p for p in cov_paths if os.path.exists(os.path.join(D, '..', '..', '..', p))
         or os.path.exists(os.path.join(R, 'lead', p))]
ck('1e 18 条 coverage.tsv 记录现盘存活 0 条', len(alive) == 0, alive[:3])
res['coverage_alive'] = alive

# ---------------------------------------------------------------- 2 grade 轴定义式
print()
print('== 2 · grade 轴的定义式：逐行统计它指向什么 ==')
lt = io.open(LED, encoding='utf-8', errors='replace').read().split('\n')
# 定义式形态：同一行内出现 `[已证]` 紧跟 ＝ 或 = （可隔着反引号）
DEF = re.compile(r'\[已证\]`?\s*(?:＝|=)\s*\S')
def_repo = [(i + 1, l) for i, l in enumerate(lt) if DEF.search(l)]
# 限定「分级口径」上下文行
def_axis = [(i + 1, l) for i, l in enumerate(lt) if '分级口径' in l and DEF.search(l)]
print('  全台账 [已证]= 定义式行 = %d；其中同行含「分级口径」= %d' % (len(def_repo), len(def_axis)))

FORM = re.compile(r'实测|复算|复跑|字节|直接读数|独立|签发件|穷举|哈希|复现|闭合|穷尽|重算|逐行|核对|执行过|双支撑|双通道')
DISK = re.compile(r'原件在盘|仍在盘|文件在盘|未失联|仍可读|现盘可核')
n_form = n_disk = 0
disk_lines = []
for ln, l in def_axis:
    f = bool(FORM.search(l))
    d = bool(DISK.search(l))
    n_form += f
    if d:
        n_disk += 1
        disk_lines.append((ln, l[:160]))
ck('2.1 「分级口径」定义式行 > 0', len(def_axis) > 0, len(def_axis))
ck('2.2 其中指**证据形态**的行 == 定义式行数（全数指向证据形态）',
   n_form == len(def_axis), (n_form, len(def_axis)))
ck('2.3 其中指**原件在盘**的行 == 0（grade 轴不含盘上存在性）', n_disk == 0, disk_lines)
# 反控：把 DISK 正则放宽到「在盘」两字，看看有没有别的行会被误算进来 —— 这条必须 FAIL，
# 用来证明 2.3 的 0 不是正则太窄造成的
LOOSE = re.compile(r'在盘|现存|原件|未失')
n_loose = sum(1 for ln, l in def_axis if LOOSE.search(l))
ck('2.3-N 反控：放宽到「在盘/现存/原件」也不应有定义式行命中'
   '（若 FAIL 说明 2.3 的正则过窄，须改判据）', n_loose == 0, n_loose)
res['grade_axis'] = {'def_axis_lines': [ln for ln, _ in def_axis],
                     'n_def_axis': len(def_axis), 'n_form': n_form, 'n_disk': n_disk,
                     'n_repo_wide': len(def_repo), 'n_loose_disk': n_loose}
print('  ⇒ 分级口径定义式 %d 行、指证据形态 %d 行、指原件在盘 %d 行'
      % (len(def_axis), n_form, n_disk))

# ---------------------------------------------------------------- 3 R90 七式鉴别力
print()
print('== 3 · R90「档 2（可重算）」七式：逐式为真，但有没有鉴别力 ==')
eqs = [
    ('1654+5875+10969=18498', 1654 + 5875 + 10969 == 18498),
    ('458+1196=1654', 458 + 1196 == 1654),
    ('863+791=1654', 863 + 791 == 1654),
    ('458/1654=27.69%', round(458 / 1654 * 100, 2) == 27.69),
    ('291/1654=17.59%', round(291 / 1654 * 100, 2) == 17.59),
    ('293/1654=17.71%', round(293 / 1654 * 100, 2) == 17.71),
    ('863/1654=52.18%', round(863 / 1654 * 100, 2) == 52.18),
]
for name, val in eqs:
    ck('3.1 七式为真：%s' % name, val, '')

# 鉴别力测试：把 A 换掉，能否被任何一式否决？
alts = [300, 400, 500, 600, 900, 1200]
survivors = []
for A in alts:
    none = 1654 - A
    ok = (A + none == 1654) and (1654 + 5875 + 10969 == 18498)
    pct = round(A / 1654 * 100, 2)
    ok = ok and (round(pct * 1654 / 100, 6) <= A + 0.5)  # 百分数由计数算出，恒自洽
    if ok:
        survivors.append(A)
ck('3.2 鉴别力：把 A 换成 %s 后仍全部通过（应全存活 ⇒ 无一式有否决力）'
   % alts, len(survivors) == len(alts), survivors)
res['r90'] = {'eqs': [n for n, _ in eqs], 'all_true': all(v for _, v in eqs),
              'alt_A_survivors': survivors, 'alt_A_tried': alts}

# ---------------------------------------------------------------- 4 F23 四计数承载行
print()
print('== 4 · F23 四计数在台账的承载行：复算 R150 的定版口径 ==')
# 口径必须与 R150/R150h 一致（R1「严格 token 全四元组同行」= 13 行），
# 否则就是对不上口径的空比（S-415 同族）。R157 自错 S-426：首版我用「同行 >=3 个 token」
# 这种自造宽松口径，得 25 行，与 R150 的 13 行不是同一个量。
def _tok(p):
    return re.compile(r'(?<![0-9A-Fa-fx])' + p + r'(?![0-9A-Fa-f])')
STRICT = {
    '458': _tok('458'),
    '291': _tok('291'),
    '293': _tok('293'),
    # 1,196 两形并列（R150 S-359 已定：带逗号与不带逗号都是合法写法）
    '1196': re.compile(r'(?<![0-9A-Fa-fx])(?:1,196|1196)(?![0-9A-Fa-f])'),
}
carry = [i for i, l in enumerate(lt, 1) if all(rx.search(l) for rx in STRICT.values())]
print('  现盘 R1 严格 token 全四元组同行 =', len(carry), carry)
# 判据必须是「R150 写入时刻的口径」，不是「现盘总量」。
# S-426b：现盘 17 行 > R150 报的 13 行，差的 4 行全在 R150 节自身及之后 ——
# 也就是说这个指标**随台账增长而单调上升**，因为每写一节讨论 F23 的台账节，
# 就把它自己也算进去了。故断言写成「R150 节之前的行 == R150 报的 13 行」。
R150_START = None
for i, l in enumerate(lt, 1):
    if l.startswith('## §1205'):
        R150_START = i
        break
ck('4.0 定位到台账 R150 节（## §1205）起始行', R150_START is not None, R150_START)
R150_REPORTED = [39648, 39793, 39816, 39850, 39910, 40811, 44032, 44069,
                 44087, 47079, 47085, 47313, 47353]
pre = [i for i in carry if R150_START and i < R150_START]
post = [i for i in carry if R150_START and i >= R150_START]
ck('4.1 R150 节之前的全四元组行 == R150 报的 13 行（正控：口径对齐）',
   pre == R150_REPORTED, (len(pre), sorted(set(pre) ^ set(R150_REPORTED))))
ck('4.2 现盘比 R150 时点多出 %d 行，且全部落在 R150 节及之后（自指增长）'
   % len(post), len(post) > 0 and set(carry) - set(pre) == set(post),
   (len(post), post))
META = re.compile(r'未取得|不可重数|不可读|挂账|一字未改|不构成|仍只是自述|交付四|打折')
meta_hits = [i for i in post if META.search(lt[i - 1])]
ck('4.3 多出的行全部是「在讨论 F23 本身」的元描述行（含未取得/不可重数/交付四等）',
   len(meta_hits) == len(post), (len(meta_hits), len(post), post))
# 反控：1196 只认带逗号形（S-359 前的错口径）→ 与 R150 的 11 行同值
BAD = dict(STRICT, **{'1196': _tok(r'1,196')})
carry_bad = [i for i, l in enumerate(lt, 1) if all(rx.search(l) for rx in BAD.values())]
bad_pre = [i for i in carry_bad if R150_START and i < R150_START]
ck('4.4-N 反控：1,196 只认带逗号形、R150 节前得 11 行（与 R150 S-359 同值 ⇒ 判据有分辨力）',
   len(bad_pre) == 11, len(bad_pre))
# 自述「复算/两套实现」的行
self_re = [i for i in carry if re.search(r'自行复算|两套独立实现|独立实现', lt[i - 1])]
print('  其中自述复算/两套独立实现的 =', len(self_re), self_re)
ck('4.5 自述复算行 > 0（R150 报 4 行）', len(self_re) >= 1, len(self_re))
res['f23_carry'] = {'reading': 'R1 严格token 全四元组同行',
                    'rows_now': carry, 'n_now': len(carry),
                    'r150_start_line': R150_START,
                    'rows_before_r150': pre, 'n_before_r150': len(pre),
                    'rows_at_or_after_r150': post, 'n_at_or_after_r150': len(post),
                    'r150_reported': R150_REPORTED,
                    'self_recompute': self_re}

# ---------------------------------------------------------------- 收口
print()
print('== 收口 ==')
if fails:
    print('FAIL 共 %d 条：' % len(fails))
    for f in fails:
        print('   -', f)
else:
    print('全部 PASS（无 FAIL）')
res['fails'] = fails
os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('产物：', os.path.relpath(OUT, R))
sys.exit(1 if fails else 0)
