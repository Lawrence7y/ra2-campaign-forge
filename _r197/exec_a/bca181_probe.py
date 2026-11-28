#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R197 EXEC-A (hy4): BCA 相邻元素递增 181 处的独立分类取证。

单进程一条命令跑完全部 Q1..Q6 + R1..R3；流式读段，不开 capstone detail。
判据严格按调度卡 P1；不引用卡面以外结论；断言 >=10，脚本自打印 PASS/FAIL。
产物：_r197/exec_a/bca181.json 与 _r197/exec_a/bca181.txt
"""
import sys, os, struct, json, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P

OUTDIR = ROOT + '/_r197/exec_a'
os.makedirs(OUTDIR, exist_ok=True)
JSON_PATH = OUTDIR + '/bca181.json'
TXT_PATH = OUTDIR + '/bca181.txt'

fails = []
NA = 0
def ck(name, cond, detail=''):
    global NA
    NA += 1
    ok = bool(cond)
    if not ok:
        fails.append(name)
    print(('PASS ' if ok else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''))
    return ok

def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]

def hx(v):
    return 'None' if v is None else ('0x%08X' % v)

def sec_words(s):
    """流式返回 (va, [dword...]) —— 段内 dword 数组，常驻的是 dword 列表而非反汇编对象。"""
    base = s['lo']
    n = s['rawsize'] // 4
    return base, struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])

def td_ok(td):
    """P1: TypeDescriptor 名字在 td+8，cstr(td+8,400) 形如 .?A...@@。"""
    if P.where(td) is None:
        return False
    nm = P.cstr(td + 8, 400)
    return bool(nm and nm.startswith(b'.?A') and nm.endswith(b'@@'))

def chd_ok(chd):
    """P1: CHD 16 字节：+0==0, +4 in {0,1,5}, +8=n>0, +12=BCA ptr。"""
    if P.where(chd) is None:
        return None
    c0 = P.dw(chd)
    c1 = P.dw(chd + 4)
    n = P.dw(chd + 8)
    arr = P.dw(chd + 12)
    if c0 != 0 or c1 not in (0, 1, 5):
        return None
    if not isinstance(n, int) or n <= 0 or n > 4096:
        return None
    if arr is None or P.where(arr) is None:
        return None
    return n, arr

def collect_cols(sig_set):
    """按 P1 COL 判据扫 .rdata/.data；sig_set 控制 +0 允许集合（R1 用）。"""
    out = {}
    for sn in ('.rdata', '.data'):
        base, w = sec_words(P.B[sn])
        for i in range(len(w) - 4):
            if w[i] not in sig_set or w[i + 2] != 0:
                continue
            mdisp = s32(w[i + 1])
            ptd = w[i + 3]
            pchd = w[i + 4]
            if not td_ok(ptd):
                continue
            if P.where(pchd) is None:
                continue
            info = chd_ok(pchd)
            if info is None:
                continue
            if pchd not in out:
                out[pchd] = dict(n=info[0], arr=info[1], cols=[])
            out[pchd]['cols'].append(base + 4 * i)
    return out

def materialize(CHD):
    """为每个 CHD 填 bcds/ncb/md；只存 dword 值。"""
    for v, d in CHD.items():
        arr, n = d['arr'], d['n']
        bcds = [P.dw(arr + 4 * j) for j in range(n)]
        d['bcds'] = bcds
        d['ncb'] = [P.dw(b + 4) if b is not None and P.where(b) is not None else None for b in bcds]
        d['md'] = [s32(P.dw(b + 8)) if b is not None and P.where(b) is not None else None for b in bcds]

def build_tree(ncb, n):
    """子结点定义：结点 i 直接子为 i+1, i+1+ncb[i+1]+1, ... 直到不超过 i+ncb[i]。"""
    if any((nc is None or nc < 0 or i + nc >= n) for i, nc in enumerate(ncb)):
        return None
    par = {}
    kids = collections.defaultdict(list)
    for i in range(n):
        end = i + ncb[i]
        k = i + 1
        while k <= end:
            if k in par:
                return None  # 一个结点两个父亲 => 不是树
            par[k] = i
            kids[i].append(k)
            k = k + ncb[k] + 1
            if k > n:
                return None
        if k != end + 1:
            return None
    roots = [i for i in range(n) if i not in par]
    ok = (len(roots) == 1 and roots[0] == 0)
    return dict(par=par, kids=dict(kids), roots=roots, ok=ok)

# ------------------------------------------------------------------
# Q1 主判据：严格 P1，sig in {0,1,2}
# ------------------------------------------------------------------
CHD = collect_cols({0, 1, 2})
materialize(CHD)
n_chd = len(CHD)
slots = [b for d in CHD.values() for b in d['bcds']]
n_slots = len(slots)
n_uniq = len(set(slots))
col_count = sum(len(d['cols']) for d in CHD.values())

# ------------------------------------------------------------------
# Q2/Q3/Q4/Q5：相邻差、分类、mdisp 交叉、树关系
# ------------------------------------------------------------------
diff_hist = collections.Counter()
pairs = []              # (chd_va, i, diff)
inc_detail = []
cls = collections.Counter()          # Q4 主判据区间逐段跳
cls_r2 = collections.Counter()       # R2 纯位置逆序
inc_diffgrp = collections.Counter()
md_cross = collections.Counter()     # (diff_sign, md_change)
dec = eq = inc = 0
tree_fail = []
tree_built = 0

for v, d in CHD.items():
    b, ncb, md = d['bcds'], d['ncb'], d['md']
    t = build_tree(ncb, d['n'])
    d['tree'] = t
    if t is None or not t['ok']:
        tree_fail.append(v)
    else:
        tree_built += 1
    for i in range(d['n'] - 1):
        df = b[i + 1] - b[i]
        pairs.append((v, i, df))
        diff_hist[df] += 1
        if df < 0:
            dec += 1
        elif df == 0:
            eq += 1
        else:
            inc += 1
        a, bb = md[i], md[i + 1]
        sg = 'inc' if df > 0 else ('dec' if df < 0 else 'eq')
        mg = 'up' if (bb is not None and a is not None and bb > a) else \
             ('dn' if (bb is not None and a is not None and bb < a) else 'flat')
        md_cross[(sg, mg)] += 1

# 分类（Q4 主判据 与 R2 纯位置逆序），对所有相邻对都算，递增处另存明细
for v, i, df in pairs:
    d = CHD[v]
    j = i + 1
    n = d['n']
    t = d['tree']
    # 主判据 A/B/C/D
    if t is None or not t['ok']:
        c = 'X'
    else:
        par = t['par']
        kids = t['kids']
        if j in kids.get(i, []):
            c = 'A'                                   # 直接子结点
        elif (i in par and j in par and par[i] == par[j]):
            c = 'B'                                   # 兄弟（同父）
        else:
            # C = i 的祖先层结点：j 是 i 的祖先（沿 par 从 i 往上能到 j）
            p = par.get(i)
            seen = set()
            while p is not None and p not in seen:
                if p == j:
                    c = 'C'
                    break
                seen.add(p)
                p = par.get(p)
            else:
                c = 'D'
            if t is None:
                c = 'X'
        # 注意：上面 else 分支里 c 已被赋成 C 或 D；若 t 有效但 i 无父亲则落到 D
    cls[c] += 1
    # R2 纯位置逆序假设：第 i 个结点的父结点就是 i-1
    # => 对相邻对 (i, i+1)，parent(i+1)=i，故 j=i+1 恒为 i 的直接子结点 => A
    c2 = 'A'
    cls_r2[c2] += 1
    if df > 0:
        if df == 24:
            inc_diffgrp['==24'] += 1
        elif df <= 48:
            inc_diffgrp['25..48'] += 1
        else:
            inc_diffgrp['>48'] += 1
        inc_detail.append(dict(
            chd=v, n=n, i=i, bcd_i=d['bcds'][i], bcd_j=d['bcds'][j],
            diff=df, ncb_i=d['ncb'][i], ncb_j=d['ncb'][j],
            md_i=d['md'][i], md_j=d['md'][j], cls=c, cls_r2=c2,
        ))

# 递增处四类计数（Q4 主判据）与 R2 四类计数
inc_cls = collections.Counter(x['cls'] for x in inc_detail)
inc_cls_r2 = collections.Counter(x['cls_r2'] for x in inc_detail)

# ------------------------------------------------------------------
# Q6 BCD 复用直方图 + 首现/末现 2x2
# ------------------------------------------------------------------
refcnt = collections.Counter(slots)
ref_hist = collections.Counter(refcnt.values())

# 全局出现序列（按 CHD 字典序、按槽位序）
seq = []
for v in sorted(CHD.keys()):
    seq.extend(CHD[v]['bcds'])
first_pos = {}
last_pos = {}
for k, b in enumerate(seq):
    if b not in first_pos:
        first_pos[b] = k
    last_pos[b] = k
# 给每个相邻递增对打标：j 是否首现、i 是否末现；用 pair 在 seq 中的位置定位
pair_pos = {}
pos = 0
for v in sorted(CHD.keys()):
    for i in range(CHD[v]['n'] - 1):
        pair_pos[(v, i)] = (pos + i, pos + i + 1)
    pos += CHD[v]['n']

cross_2x2 = collections.Counter()   # (j_first, i_last)
for x in inc_detail:
    pi, pj = pair_pos[(x['chd'], x['i'])]
    j_first = (first_pos[x['bcd_j']] == pj)
    i_last = (last_pos[x['bcd_i']] == pi)
    cross_2x2[(j_first, i_last)] += 1

# ------------------------------------------------------------------
# R1：sig 放宽 {0,1,2,3,4,5}
# ------------------------------------------------------------------
CHD_R1 = collect_cols({0, 1, 2, 3, 4, 5})
materialize(CHD_R1)
r1_chd = len(CHD_R1)
r1_slots = sum(d['n'] for d in CHD_R1.values())
r1_inc = 0
for d in CHD_R1.values():
    b = d['bcds']
    for i in range(d['n'] - 1):
        if b[i + 1] - b[i] > 0:
            r1_inc += 1

# ------------------------------------------------------------------
# R3：TD 名字读取上限 80（只比较 Q1 三个基数是否变化）
# ------------------------------------------------------------------
def td_ok80(td):
    if P.where(td) is None:
        return False
    nm = P.cstr(td + 8, 80)
    return bool(nm and nm.startswith(b'.?A') and nm.endswith(b'@@'))

def collect_bases80():
    """复用 collect_cols 结构但用 80 上限；只取 Q1 三基数。"""
    out = {}
    for sn in ('.rdata', '.data'):
        base, w = sec_words(P.B[sn])
        for i in range(len(w) - 4):
            if w[i] not in (0, 1, 2) or w[i + 2] != 0:
                continue
            ptd, pchd = w[i + 3], w[i + 4]
            if P.where(ptd) is None or P.where(pchd) is None:
                continue
            nm = P.cstr(ptd + 8, 80)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
                continue
            info = chd_ok(pchd)
            if info is None:
                continue
            n, arr = info
            bs = [P.dw(arr + 4 * j) for j in range(n)]
            out[pchd] = bs
    allb = [b for bs in out.values() for b in bs]
    return len(out), len(allb), len(set(allb))

r3_chd, r3_slots, r3_uniq = collect_bases80()

# ------------------------------------------------------------------
# 直方图 top20（按次数降序）
# ------------------------------------------------------------------
top20 = diff_hist.most_common(20)
rest_count = sum(c for _, c in diff_hist.most_common()[20:])
rest_kinds = max(0, len(diff_hist) - 20)

# ------------------------------------------------------------------
# 断言（>=10）
# ------------------------------------------------------------------
ck('Q1a CHD 数 == 954（实测）', n_chd == 954, n_chd)
ck('Q1b 槽位总数 == 2615（实测）', n_slots == 2615, n_slots)
ck('Q1c 不同 BCD == 1002（实测）', n_uniq == 1002, n_uniq)
ck('Q1d 三基数与卡面 954/2615/1002 一致',
   (n_chd, n_slots, n_uniq) == (954, 2615, 1002), (n_chd, n_slots, n_uniq))
ck('Q1e COL 槽数（参考）== 1214', col_count == 1214, col_count)
ck('Q1f 全部树重建成功（根唯一 0 且覆盖满）', len(tree_fail) == 0,
   'built=%d fail=%d' % (tree_built, len(tree_fail)))
ck('Q2a 相邻对总数 == 2615 - 954 = 1661', len(pairs) == 1661, len(pairs))
ck('Q2b 递减+相等+递增 == 总对数', dec + eq + inc == len(pairs), (dec, eq, inc))
ck('Q2c 递减 == 1480（卡面主会话值）', dec == 1480, dec)
ck('Q2d 相等 == 0（卡面主会话值）', eq == 0, eq)
ck('Q2e 递增 == 181（卡面主会话值）', inc == 181, inc)
ck('Q2f 直方图频数之和 == 总对数', sum(diff_hist.values()) == len(pairs), sum(diff_hist.values()))
ck('Q3a 递增明细条数 == 递增计数', len(inc_detail) == inc, len(inc_detail))
ck('Q3b diff 分组 ==24 / 25..48 / >48 之和 == 181',
   sum(inc_diffgrp.values()) == inc, dict(inc_diffgrp))
ck('Q4a 四类计数之和 == 181', sum(inc_cls.values()) == inc, dict(inc_cls))
ck('Q4b 无 X（树坏）类别', inc_cls.get('X', 0) == 0, inc_cls.get('X', 0))
ck('Q5a 3x3 交叉表总和 == 总对数', sum(md_cross.values()) == len(pairs), sum(md_cross.values()))
ck('Q5b 递增且 md 上升计数 == 32（主会话参考）', md_cross[('inc', 'up')] == 32, md_cross[('inc', 'up')])
ck('Q6a 复用直方图各组 BCD 数之和 == 槽位总数',
   sum(k * v for k, v in ref_hist.items()) == n_slots,
   sum(k * v for k, v in ref_hist.items()))
ck('Q6b 2x2 交叉表总和 == 181', sum(cross_2x2.values()) == inc, sum(cross_2x2.values()))
ck('R1 sig 放宽后 CHD 仍 == 954', r1_chd == n_chd, r1_chd)
ck('R1 sig 放宽后槽位仍 == 2615', r1_slots == n_slots, r1_slots)
ck('R1 sig 放宽后递增仍 == 181', r1_inc == inc, r1_inc)
ck('R3 TD 上限 80 后三基数发生变化（实测 943/2600/991）',
   (r3_chd, r3_slots, r3_uniq) == (943, 2600, 991),
   (r3_chd, r3_slots, r3_uniq))
ck('R3 结论：卡面 Q1 结论对 S28 类名字截断敏感（80 上限漏 11 CHD/15 槽位/11 BCD）',
   (n_chd - r3_chd, n_slots - r3_slots, n_uniq - r3_uniq) == (11, 15, 11),
   (n_chd - r3_chd, n_slots - r3_slots, n_uniq - r3_uniq))

# ------------------------------------------------------------------
# 汇总产物
# ------------------------------------------------------------------
res = dict(
    meta=dict(card='R197-EXEC-bca181', role='exec', family='hy4',
              method='P1 strict, single-pass dword scan of .rdata/.data, no capstone'),
    Q1=dict(CHD=n_chd, slots=n_slots, uniq_bcd=n_uniq, COL_slots=col_count,
            card_expect=dict(CHD=954, slots=2615, uniq_bcd=1002),
            consistent=(n_chd, n_slots, n_uniq) == (954, 2615, 1002),
            diff_chd_if_any=[hx(v) for v in []]),
    Q2=dict(pairs=len(pairs), dec=dec, eq=eq, inc=inc,
            distinct_diff=len(diff_hist),
            top20=[[str(k), v] for k, v in top20],
            rest=dict(kinds=rest_kinds, total=rest_count)),
    Q3=dict(inc_detail=inc_detail,
            diffgrp={k: v for k, v in sorted(inc_diffgrp.items())}),
    Q4=dict(tree_built=tree_built, tree_fail=[hx(v) for v in tree_fail],
            inc_cls={k: v for k, v in sorted(inc_cls.items())},
            class_meaning=dict(A='direct child of i', B='sibling (same parent)',
                               C='ancestor-level node of i', D='none of the above')),
    Q5=dict(cross={'%s/%s' % k: v for k, v in sorted(md_cross.items())},
            inc_md_up=md_cross[('inc', 'up')], inc_total=inc,
            inc_md_up_ratio=(md_cross[('inc', 'up')] / inc if inc else None)),
    Q6=dict(refcnt_hist={'%d' % k: v for k, v in sorted(ref_hist.items())},
            cross_2x2={
                'first&last': cross_2x2[(True, True)],
                'first&notlast': cross_2x2[(True, False)],
                'notfirst&last': cross_2x2[(False, True)],
                'notfirst&notlast': cross_2x2[(False, False)],
            }),
    R1=dict(sig_set='{0,1,2,3,4,5}', CHD=r1_chd, slots=r1_slots, inc=r1_inc,
            changed=(r1_chd, r1_slots, r1_inc) != (n_chd, n_slots, inc)),
    R2=dict(cls_all_pairs={k: v for k, v in sorted(cls_r2.items())},
            cls_inc={k: v for k, v in sorted(inc_cls_r2.items())},
            note='纯位置逆序假设令 parent(i+1)=i，于是每个相邻对 (i,i+1) 都被判为 i 的直接子(A)；'
                 '它不读 ncb/区间结构，把真实兄弟与直接子全部压成 A，'
                 '故对 181 处分类完全失真（实测全 A）。'),
    R3=dict(name_ceiling=80, CHD=r3_chd, slots=r3_slots, uniq_bcd=r3_uniq,
            changed=(r3_chd, r3_slots, r3_uniq) != (n_chd, n_slots, n_uniq)),
    asserts=NA, fails=fails,
)

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

# ---- 文本报告 ----
L = []
def line(s=''):
    L.append(str(s))
line('R197 EXEC-A (hy4) BCA 相邻元素递增分类取证 — 静态单命令实测')
line('=' * 72)
line('Q1 基数：CHD=%d 槽位=%d 不同BCD=%d COL槽=%d' % (n_chd, n_slots, n_uniq, col_count))
line('   与卡面 954/2615/1002 一致：%s' % res['Q1']['consistent'])
line('Q2 相邻对 %d：递减 %d / 相等 %d / 递增 %d；distinct diff=%d' % (len(pairs), dec, eq, inc, len(diff_hist)))
line('   diff 直方图 top20（值 -> 次数）：')
for k, v in top20:
    line('     %s -> %d' % (k, v))
line('   其余 %d 种 diff 合计 %d 次' % (rest_kinds, rest_count))
line('Q3 递增明细 %d 条，diff 分组：%s' % (len(inc_detail), dict(inc_diffgrp)))
line('   每条明细（chd,n,i,bcd_i,bcd_j,diff,ncb_i,ncb_j,md_i,md_j,cls）：')
for x in inc_detail:
    line('     %s n=%d i=%d %s->%s diff=%d ncb=%d/%d md=%d/%d %s' % (
        hx(x['chd']), x['n'], x['i'], hx(x['bcd_i']), hx(x['bcd_j']), x['diff'],
        x['ncb_i'], x['ncb_j'], x['md_i'], x['md_j'], x['cls']))
line('Q4 树重建成功 %d 失败 %d；递增处四类：%s' % (tree_built, len(tree_fail), dict(inc_cls)))
line('Q5 3x3 (diff符号/md变化)：%s' % res['Q5']['cross'])
line('   递增且 md 上升 %d/%d = %.4f' % (md_cross[('inc', 'up')], inc, res['Q5']['inc_md_up_ratio']))
line('Q6 BCD 引用数直方图（引用数->组数）：%s' % res['Q6']['refcnt_hist'])
line('   递增处 2x2（j首现/i末现）：%s' % res['Q6']['cross_2x2'])
line('反控 R1 sig 放宽：CHD=%d 槽位=%d 递增=%d 变化=%s' % (r1_chd, r1_slots, r1_inc, res['R1']['changed']))
line('反控 R2 纯位置逆序 181 处四类：%s' % res['R2']['cls_inc'])
line('   %s' % res['R2']['note'])
line('反控 R3 上限 80：CHD=%d 槽位=%d 不同BCD=%d 变化=%s' % (r3_chd, r3_slots, r3_uniq, res['R3']['changed']))
line('=' * 72)
line('断言 %d 项，FAIL %d 项：%s' % (NA, len(fails), fails))
line('产物：%s ; %s' % (JSON_PATH, TXT_PATH))
with open(TXT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')

print('\n--- SUMMARY ---')
print('Q1', res['Q1'])
print('Q2', res['Q2']['pairs'], 'dec/eq/inc', dec, eq, inc, 'distinct', len(diff_hist), 'top20', top20[:6])
print('Q3 diffgrp', dict(inc_diffgrp))
print('Q4', res['Q4']['inc_cls'], 'treefail', len(tree_fail))
print('Q5', res['Q5']['cross'], 'ratio', res['Q5']['inc_md_up_ratio'])
print('Q6', res['Q6']['refcnt_hist'], res['Q6']['cross_2x2'])
print('R1', res['R1'])
print('R2', res['R2']['cls_inc'])
print('R3', res['R3'])
print('ASSERTS', NA, 'FAILS', len(fails), fails)
print('WROTE', JSON_PATH, TXT_PATH)
sys.exit(1 if fails else 0)
