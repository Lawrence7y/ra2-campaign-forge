#!/usr/bin/env python3
# R142 A: 三分档可复算性审计
#   1) 外部 triage 路径层与磁盘逐条对账（可失败）
#   2) 部分失联集合在 v5.39 上重算
#   3) 证明「档位不是路径状态的函数」（零失联却跨档）
#   4) 表内自洽性：lost_primary 空但 basis 点名已失件
#   5) 两个候选定义 T1/T2 + 确定性随机基线 + 置换对照
#   6) 过拟合对照
# 纪律：只读；一次取证；正控失败计入 cc_fails，反控（设计上必 False）计入 neg_fails。
import csv
import io
import json
import os
import random
import statistics
from collections import Counter, defaultdict

ROOT = '/home/t628/projects/ra2-campaign-forge'
FI = os.path.join(ROOT, 'lead', 'next_re_20261117_r14',
                  'R17_R111_FACTINDEX_V539', 'FACT_INDEX.tsv')
EXT = os.path.join(ROOT, '_ext', 'f_partial_triage', 'TRIAGE.tsv')
OUT = os.path.join(ROOT, '_r142', 'r142a_tier_audit.json')

cc, neg, cc_n, neg_n = [], [], 0, 0


def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        cc.append(name)


def nk(name, cond, detail=''):
    """反向对照：cond 期望为 False 才 PASS。"""
    global neg_n
    neg_n += 1
    ok = not cond
    print(('  PASS ' if ok else '  FAIL ') + '[neg] ' + name +
          (('  ' + str(detail)) if detail else ''))
    if not ok:
        neg.append(name)


def sp(s):
    return [x.strip() for x in (s or '').split(';') if x.strip()]


def norm(p):
    p = p.strip().replace('\\', '/')
    return p.split('(', 1)[0].strip() if '(' in p else p


def base(p):
    return norm(p).split('/')[-1]


def exists(p):
    return os.path.exists(os.path.join(ROOT, norm(p)))


rows = list(csv.DictReader(io.open(FI, encoding='utf-8'), delimiter='\t'))
ext = list(csv.DictReader(io.open(EXT, encoding='utf-8'), delimiter='\t'))

print('=== 0 · 输入校验 ===')
ck('0.1 台账 54 行', len(rows) == 54, len(rows))
ck('0.2 triage 32 行', len(ext) == 32, len(ext))
ck('0.3 列名', list(rows[0].keys()) ==
   ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'],
   list(rows[0].keys()))

# ---------- 1 · 路径层逐条对账 ----------
print('\n=== 1 · 外部 triage 路径层（每条声明 vs 磁盘）===')
alive_tot = alive_bad = lp_tot = ls_tot = lost_bad = 0
alive_bad_l, lost_bad_l = [], []
for e in ext:
    for p in sp(e['alive_paths']):
        alive_tot += 1
        if not exists(p):
            alive_bad += 1
            alive_bad_l.append((e['fid'], norm(p)))
    for p in sp(e['lost_primary']):
        lp_tot += 1
        if exists(p):
            lost_bad += 1
            lost_bad_l.append((e['fid'], norm(p)))
    for p in sp(e['lost_side']):
        ls_tot += 1
        if exists(p):
            lost_bad += 1
            lost_bad_l.append((e['fid'], norm(p)))
ck('1.1 声明的存活路径全部在盘', alive_bad == 0, (alive_bad, alive_tot, alive_bad_l[:3]))
ck('1.2 声明的失联路径全部不在盘', lost_bad == 0, (lost_bad, lp_tot + ls_tot, lost_bad_l[:3]))
ck('1.3 路径层总量 == 91 + 36 + 4 == 131',
   alive_tot + lp_tot + ls_tot == 131 and alive_tot == 91 and lp_tot == 36 and ls_tot == 4,
   (alive_tot, lp_tot, ls_tot))

# ---------- 2 · 部分失联集合 ----------
print('\n=== 2 · 部分失联集合（v5.39 重算）===')
det, partial, fulldead, nalive = {}, [], [], 0
for r in rows:
    ps = [norm(p) for p in sp(r['evidence_paths'])]
    if not ps:
        det[r['fact_id']] = dict(kind='no-paths', n=0, alive=0)
        continue
    a = sum(1 for p in ps if exists(p))
    k = 'alive' if a == len(ps) else ('dead' if a == 0 else 'partial')
    det[r['fact_id']] = dict(kind=k, n=len(ps), alive=a)
    if k == 'dead':
        fulldead.append(r['fact_id'])
    elif k == 'partial':
        partial.append(r['fact_id'])
    else:
        nalive += 1
ck('2.1 部分失联 == 33', len(partial) == 33, len(partial))
ck('2.2 全部失联 == [F23]', fulldead == ['F23'], fulldead)
ck('2.3 有路径项 54 且不重不漏', len(partial) + len(fulldead) + nalive == 54,
   (len(partial), len(fulldead), nalive))
ext_set = set(e['fid'] for e in ext)
ck('2.4 与外部 32 的差集 == {F35}', sorted(set(partial) ^ ext_set) == ['F35'],
   sorted(set(partial) ^ ext_set))
nk('2.5 反控：若按外部数得 32 则与 33 不符', len(partial) == 32, len(partial))

# ---------- 3 · 档位不是路径状态的函数 ----------
print('\n=== 3 · 零失联同状态跨档（决定性反例）===')
zeroloss = [e for e in ext if not sp(e['lost_primary'])]
zt = defaultdict(list)
for e in zeroloss:
    zt[e['verdict']].append(e['fid'])
ck('3.1 lost_primary 为空的项 == 4', len(zeroloss) == 4, len(zeroloss))
ck('3.2 这些项跨 2 档', len(zt) == 2, dict(zt))
ck('3.3 同时含 需重建(F18,F27,F39) 与 仍可核验(F49)',
   sorted(zt.get('需重建', [])) == ['F18', 'F27', 'F39'] and zt.get('仍可核验') == ['F49'],
   dict(zt))
F39 = [e for e in ext if e['fid'] == 'F39'][0]
F49 = [e for e in ext if e['fid'] == 'F49'][0]
ck('3.4 F39/F49 存活路径数同为 2',
   len(sp(F39['alive_paths'])) == len(sp(F49['alive_paths'])) == 2,
   (len(sp(F39['alive_paths'])), len(sp(F49['alive_paths']))))
ck('3.5 F39/F49 档位不同', F39['verdict'] != F49['verdict'],
   (F39['verdict'], F49['verdict']))
ck('3.6 两者 basis 都点名同一个已失件 HANDOFF_R14_R3',
   'HANDOFF_R14_R3' in F39['basis'] and 'HANDOFF_R14_R3' in F49['basis'])
hits = [os.path.join(dp, f) for dp, _, fn in os.walk(ROOT) for f in fn
        if f.startswith('HANDOFF_R14_R3')]
ck('3.7 HANDOFF_R14_R3* 全库 0 个文件（确实失联）', len(hits) == 0, hits[:3])
nk('3.8 反控：若两者同档则无法区分档位来源', F39['verdict'] == F49['verdict'])

# ---------- 4 · 表内自洽性 ----------
print('\n=== 4 · 表内自洽性（lost_primary 空 ∧ basis 点名已失）===')
inc = []
for e in ext:
    if sp(e['lost_primary']):
        continue
    if '已失' in e['basis'] or '失 ' in e['basis']:
        inc.append((e['fid'], e['verdict']))
ck('4.1 存在该形态的不一致行', len(inc) > 0, inc)
ck('4.2 不一致行恰为 F18/F27/F39/F49（首版预估 3 条，实测 4 条）',
   sorted(x[0] for x in inc) == ['F18', 'F27', 'F39', 'F49'],
   sorted(x[0] for x in inc))
ck('4.2b 这 4 行恰等于「lost_primary 为空」的全部 4 行',
   sorted(x[0] for x in inc) == sorted(e['fid'] for e in ext if not sp(e['lost_primary'])),
   sorted(x[0] for x in inc))
ck('4.3 被点名已失的 GATE_BEHAV/PROGRESS.md 确实不在盘',
   not exists('lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md'))
ck('4.4 被点名在盘的 GATE_BEHAV/CASES.tsv 确实在盘（反证 4.3 非误判）',
   exists('lead/next_re_20261117_r14/GATE_BEHAV/CASES.tsv'))
# 我首版正则把「在盘」的 CASES.tsv 误报为已失 —— 自错留痕
ck('4.5 自错留痕：F18 的 CASES.tsv 是「在盘」侧，不是失联侧',
   'CASES.tsv / §2.6四 在盘' in [e for e in ext if e['fid'] == 'F18'][0]['basis'])

# ---------- 5 · 两个候选定义 ----------
print('\n=== 5 · 候选定义 T1（纯路径）/ T2（路径 + basis 关键词）===')


def tier_T1(e):
    a = sp(e['alive_paths'])
    l = sp(e['lost_primary']) + sp(e['lost_side'])
    if not l:
        return '仍可核验'
    if not a:
        return '不可核验'
    return '需重建'


def tier_T2(e):
    a = sp(e['alive_paths'])
    b = e['basis']
    l = sp(e['lost_primary']) + sp(e['lost_side'])
    if not a:
        return '不可核验'
    if '无在盘替代' in b or '唯一裁定载体' in b:
        return '不可核验'
    if not l and '已失' not in b:
        return '仍可核验'
    if '不影响主体链' in b or '旁证' in b:
        return '仍可核验'
    return '需重建'


def agree(fn):
    ok = sum(1 for e in ext if fn(e) == e['verdict'])
    bad = sorted(e['fid'] for e in ext if fn(e) != e['verdict'])
    return ok, sorted(bad)


tiers = [e['verdict'] for e in ext]
n = len(ext)
freq = Counter(tiers)
pred1 = Counter(tier_T1(e) for e in ext)
pred2 = Counter(tier_T2(e) for e in ext)
# 确定性随机基线：标签置换下 E[agree] = sum_class p_class * (#被预测为该类)/n
chance1 = sum(freq[c] * pred1.get(c, 0) for c in freq) / n
chance2 = sum(freq[c] * pred2.get(c, 0) for c in freq) / n

ok1, bad1 = agree(tier_T1)
ok2, bad2 = agree(tier_T2)
print('  T1 一致 %d/%d (%.1f%%)  随机基线 %.1f  不一致=%s'
      % (ok1, n, 100.0 * ok1 / n, chance1, bad1))
print('  T2 一致 %d/%d (%.1f%%)  随机基线 %.1f  不一致=%s'
      % (ok2, n, 100.0 * ok2 / n, chance2, bad2))
ck('5.1 T1 不足（一致率 < 100%）', ok1 < n, ok1)
ck('5.2 T1 不优于确定性随机基线（一致率 <= 基线 + 1 行容差）',
   ok1 <= chance1 + 1.0, (ok1, chance1))
ck('5.3 T2 严格优于 T1', ok2 > ok1, (ok2, ok1))
ck('5.4 T2 严格优于自己的随机基线', ok2 > chance2, (ok2, chance2))
ck('5.5 T2 仍非 100%（仍有 8 条不可机械定）', ok2 < n, (ok2, n))
nk('5.6 反控：若 T2 达 100% 则说明它在拟合人工结论', ok2 == n, (ok2, n))
ck('5.7 T2 的 8 条残余就是纯人工判读项',
   bad2 == ['F09', 'F10', 'F19', 'F22', 'F25', 'F28', 'F46', 'F52'], bad2)

# ---------- 6 · 置换对照 ----------
print('\n=== 6 · 置换对照（4000 次打乱 tier）===')
random.seed(20261127)
for label, fn, obs in (('T1', tier_T1, ok1), ('T2', tier_T2, ok2)):
    ds = []
    for _ in range(4000):
        p = tiers[:]
        random.shuffle(p)
        ds.append(sum(1 for e, t in zip(ext, p) if fn(e) == t))
    pv = sum(1 for d in ds if d >= obs) / len(ds)
    print('  %s obs=%d perm_mean=%.2f perm_sd=%.2f p(>=obs)=%.4f'
          % (label, obs, statistics.mean(ds), statistics.pstdev(ds), pv))
    if label == 'T1':
        ck('6.1 T1 置换 p 值高（与随机不可分）', pv > 0.5, pv)
    else:
        ck('6.2 T2 置换 p 值 < 0.001（显著）', pv < 0.001, pv)

# ---------- 7 · 过拟合对照 ----------
print('\n=== 7 · 过拟合对照 ===')
g = defaultdict(set)
for e in ext:
    g[tuple(sorted(set(norm(x) for x in sp(e['alive_paths']))))].add(e['verdict'])
conf = [k for k, v in g.items() if len(v) > 1]
print('  存活全路径集合分组：组数 %d / 32，冲突组 %d' % (len(g), len(conf)))
ck('7.1 该特征没把每行变成独立组（组数 < 28，未饱和）', len(g) < 28, len(g))
ck('7.2 仍有冲突组（该特征不是判决变量）', len(conf) >= 1, len(conf))
ck('7.3 组数 == 15', len(g) == 15, len(g))

out = dict(
    path_layer=dict(alive=alive_tot, alive_bad=alive_bad,
                    lost_primary=lp_tot, lost_side=ls_tot, lost_bad=lost_bad),
    partial_v539=partial, full_dead=fulldead, ext_diff=sorted(set(partial) ^ ext_set),
    zero_loss_tiers={k: v for k, v in zt.items()},
    tsv_inconsistent=inc,
    T1=dict(match=ok1, n=n, chance=chance1, mismatched=bad1),
    T2=dict(match=ok2, n=n, chance=chance2, mismatched=bad2),
    alive_set_groups=len(g), alive_set_conflicts=len(conf),
    cc_checks=cc_n, cc_fails=cc, neg_checks=neg_n, neg_fails=neg,
)
json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 收口：正控 %d 项 / FAIL %d ；反控 %d 项 / FAIL %d ==='
      % (cc_n, len(cc), neg_n, len(neg)))
print('输出', OUT)
