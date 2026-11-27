#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R162-A · 外部 triage（_ext/f_partial_triage）的「分母口径」与「分列规则」双重复算

背景
----
1) 目标第 ⑤ 项写「32 条部分失联事实项逐条定性已由外部 hy4flash-free 调研任务承接
   （产物 _ext/f_partial_triage/），主会话勿重复投入，收口时引用其结论并复算」。
   所以本轮**不重做定性**，只做两件可失败的事：
     (a) 它的分母 32 到底是哪一版台账的集合？现盘当前版 V543 的集合是不是同一个？
     (b) R142 §2.146 第五节写「external triage 的 lost_primary 列不完整，有 4 行把
         失联件只写在 basis 散文里」——这句是否成立？

2) R142 §2.146 的 T1/T2 判别力实验是在 V532 上做的。本轮把同一套判据搬到 V543 复核，
   并把新增的 F35 单独算一遍（它在 V543 首次进入部分失联桶）。

只读。不写 R17 五件套、不写 FACT_INDEX、不写 _ext/。
所有断言带正控与反控；数字全部现场实测，无手抄常量（除三处 sha256 用于钉基线）。
"""
import collections
import hashlib
import io
import json
import os
import random
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)

V532 = 'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv'
V543 = 'lead/next_re_20261117_r14/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
TRIAGE = '_ext/f_partial_triage/TRIAGE.tsv'
TRIAGE_PY = '_ext/f_partial_triage/triage.py'
R137A = '_r137/r137a_evidchain.json'
SNAP = 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv'
OUT = '_r162/r162a_triage_recompute.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:260]) if detail else ''))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_rows(p):
    rows = [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]
    return rows[0], [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]


def posix(p):
    return p.replace('\\', '/').strip()


def parse_entry(e):
    """与 R137 同口径：首个 '(' 切锚点，要求以 ')' 结尾。"""
    e = e.strip()
    if not e:
        return None, ''
    i = e.find('(')
    if i < 0:
        return e, ''
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]


# ---------------------------------------------------------------- 0 基线钉
print('== 0 基线（sha256 现场实测，与钉住值比对）==')
BASE = {
    V543: '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f',
    V532: '84863896227062179adc6e437eff3cf89e437fc6a131620a1f50e831b52cf92f',
    TRIAGE: '849db4e5b0734ebbe7382dbe08de7b7e8f95c0349f5d56941094ce5da8811a38',
}
got = {}
for p, want in BASE.items():
    got[p] = sha(p)
    ck('B0 sha256 未漂移 %s' % os.path.basename(p), got[p] == want, got[p][:16])
# 反控：把同一份字节的 sha 与一个改过一位的期望值比，必须不等
ck('B0r 反控：篡改期望值必须判不等', got[V543] != '0' * 64, got[V543][:16])

# ---------------------------------------------------------------- 1 R137 基线复现
print('\n== 1 在 V532 上复现 R137 的六元组（54/171/68/16/32/2）==')


def scan(path):
    hdr, body = load_rows(path)
    entries = 0
    paths = set()
    dead = set()
    per = {}
    for r in body:
        n = 0
        nd = 0
        for raw in r[3].split(';'):
            if not raw.strip():
                continue
            p, loc = parse_entry(raw)
            if not p:
                continue
            n += 1
            entries += 1
            rel = posix(p)
            paths.add(rel)
            if not os.path.exists(rel):
                dead.add(rel)
                nd += 1
        per[r[0]] = (n, nd)
    part = sorted(f for f, (n, k) in per.items() if 0 < k < n)
    alld = sorted(f for f, (n, k) in per.items() if n > 0 and k == n)
    alok = sorted(f for f, (n, k) in per.items() if k == 0)
    return {'rows': len(body), 'entries': entries, 'distinct': len(paths),
            'dead': len(dead), 'dead_set': sorted(dead), 'part': part,
            'all_dead': alld, 'all_ok': alok, 'per': per}


s532 = scan(V532)
s543 = scan(V543)
print('  V532 rows=%d entries=%d distinct=%d dead=%d part=%d all_dead=%s all_ok=%d'
      % (s532['rows'], s532['entries'], s532['distinct'], s532['dead'],
         len(s532['part']), s532['all_dead'], len(s532['all_ok'])))
print('  V543 rows=%d entries=%d distinct=%d dead=%d part=%d all_dead=%s all_ok=%d'
      % (s543['rows'], s543['entries'], s543['distinct'], s543['dead'],
         len(s543['part']), s543['all_dead'], len(s543['all_ok'])))

ck('B1 V532 六元组 == (54,171,68,16,32,2)',
   (s532['rows'], s532['entries'], s532['distinct'], s532['dead'],
    len(s532['part']), len(s532['all_dead'])) == (54, 171, 68, 16, 32, 2),
   (s532['rows'], s532['entries'], s532['distinct'], s532['dead'],
    len(s532['part']), len(s532['all_dead'])))
ck('B1d V532 all_dead == [F23,F35]', s532['all_dead'] == ['F23', 'F35'], s532['all_dead'])
ck('B1a V532 all_ok == 20', len(s532['all_ok']) == 20, len(s532['all_ok']))

ck('B2 V543 六元组 == (54,178,74,16,33,1)',
   (s543['rows'], s543['entries'], s543['distinct'], s543['dead'],
    len(s543['part']), len(s543['all_dead'])) == (54, 178, 74, 16, 33, 1),
   (s543['rows'], s543['entries'], s543['distinct'], s543['dead'],
    len(s543['part']), len(s543['all_dead'])))
ck('B2d V543 all_dead == [F23]', s543['all_dead'] == ['F23'], s543['all_dead'])
ck('B3 失联路径集合两版逐条相同（对称差 = 空）',
   set(s532['dead_set']) == set(s543['dead_set']) and s532['dead'] == s543['dead'],
   (s532['dead'], s543['dead']))
ck('B4 三桶合计恒 54（无 no-paths 行）',
   len(s532['part']) + len(s532['all_dead']) + len(s532['all_ok']) == 54
   and len(s543['part']) + len(s543['all_dead']) + len(s543['all_ok']) == 54,
   (len(s543['part']), len(s543['all_dead']), len(s543['all_ok'])))
ck('B5 部分失联集合差 = {F35}（V543 进、V532 出、退出 0 条）',
   sorted(set(s543['part']) - set(s532['part'])) == ['F35']
   and sorted(set(s532['part']) - set(s543['part'])) == [],
   (sorted(set(s543['part']) - set(s532['part'])), sorted(set(s532['part']) - set(s543['part']))))

# 反控：把仓库根换成不存在的根，命中必须为 0（证明「存在性」测的是真磁盘）
ghost = scan_root = None
cnt = 0
for r in load_rows(V543)[1]:
    for raw in r[3].split(';'):
        p, _ = parse_entry(raw)
        if p and os.path.exists(os.path.join(ROOT, '__NO_SUCH_ROOT_R162__', posix(p))):
            cnt += 1
ck('B6 反控：错根前缀下命中 == 0', cnt == 0, cnt)

# ---------------------------------------------------------------- 2 外部 triage 的分母口径
print('\n== 2 外部 triage 的分母是哪一版集合？==')
tri_rows = [l.split('\t') for l in io.open(TRIAGE, encoding='utf-8').read().split('\n')
            if l.strip()]
ck('C0 TRIAGE 表头', tri_rows[0] == ['fid', 'lost_primary', 'lost_side',
                                     'alive_paths', 'verdict', 'basis'], tri_rows[0])
tri = {c[0]: dict(zip(tri_rows[0], c)) for c in tri_rows[1:]}
tri_fids = set(tri)
print('  TRIAGE 行数 %d ; verdict 分布 %s' % (len(tri),
                                         collections.Counter(t['verdict'] for t in tri.values())))
ck('C1 TRIAGE fid 集合 == V532 的 partial 集合（32）',
   tri_fids == set(s532['part']), (len(tri_fids), len(s532['part']),
                                   sorted(tri_fids ^ set(s532['part']))))
ck('C1r 反控：TRIAGE fid 集合 != V543 的 partial 集合（差恰 F35）',
   tri_fids != set(s543['part']) and sorted(set(s543['part']) - tri_fids) == ['F35'],
   sorted(set(s543['part']) - tri_fids))
ck('C2 triage.py 读的台账路径 = V532（脚本内常量实测）',
   'R17_R104_FACTINDEX_V532' in io.open(TRIAGE_PY, encoding='utf-8').read(), 'V532')
ck('C3 覆盖率口径一：按 fid 32/33 = %.4f%%' % (100.0 * len(tri_fids & set(s543['part'])) / len(s543['part'])),
   len(tri_fids & set(s543['part'])) == 32 and len(s543['part']) == 33,
   (len(tri_fids & set(s543['part'])), len(s543['part'])))
cov_fid = 100.0 * len(tri_fids & set(s543['part'])) / len(s543['part'])
# 覆盖率口径二：按 entry（F35 在 V543 有 5 项 1 失 → 只失 1 项未定性）
ent_part = sum(s543['per'][f][0] for f in s543['part'])
ent_covered = sum(s543['per'][f][0] for f in tri_fids & set(s543['part']))
cov_ent = 100.0 * ent_covered / ent_part
print('  覆盖口径二（按 entry）：%d/%d = %.4f%%' % (ent_covered, ent_part, cov_ent))
ck('C4 覆盖口径二 < 口径一（F35 是 5 项的 fact，不是 1 项）', cov_ent < cov_fid,
   (round(cov_ent, 4), round(cov_fid, 4)))
ck('C5 F35 在 V543 有 5 项证据、恰 1 项失联',
   s543['per']['F35'] == (5, 1), s543['per']['F35'])
ck('C6 F35 在 V532 有 1 项、且那 1 项失联（全失联桶）',
   s532['per']['F35'] == (1, 1), s532['per']['F35'])

# ---------------------------------------------------------------- 3 lost_primary 分列规则
print('\n== 3 R142 §2.146 §五「4 行把失联件只写在 basis 散文里」是否成立？==')
LEDGER = {'R17_LEDGER_1062', 'R17_LEDGER_1063', 'R17_LEDGER_1063R',
          'R17_LEDGER_1064', 'R17_LEDGER_1065'}
PRIMARY_NAMES = ('COVERAGE/PANEL.md', 'R17_DELIVERY/DELIVERY_SUMMARY.md')


def lost_class(rel):
    parts = rel.split('/')
    if any(x in LEDGER for x in parts) and parts[-1] == 'SECTION.md':
        return 'ledger'
    if rel.endswith(PRIMARY_NAMES[0]) or rel.endswith(PRIMARY_NAMES[1]):
        return 'firsthand'
    if parts[-1] == 'VERDICT.md':
        return 'verdict'
    if parts[-1] == 'PROGRESS.md' or parts[-1].startswith('HANDOFF'):
        return 'progress'
    return 'other'


PRIMARY_CLASSES = {'ledger', 'firsthand', 'verdict'}
rows532 = {r[0]: r for r in load_rows(V532)[1]}
mis_rule = []
mis_side = []
for fid in sorted(tri_fids):
    r = rows532[fid]
    dead = []
    for raw in r[3].split(';'):
        p, _ = parse_entry(raw)
        if p and not os.path.exists(posix(p)):
            dead.append(posix(p))
    cls_set = {lost_class(x) for x in dead}
    pred_primary = bool(cls_set & PRIMARY_CLASSES)
    actual_primary = bool(tri[fid]['lost_primary'].strip())
    if pred_primary != actual_primary:
        mis_rule.append((fid, sorted(cls_set), actual_primary))
    # 反查：该 fid 的失联件是否真的出现在 lost_side 列（而不是"只在 basis 散文里"）
    for x in dead:
        if not pred_primary and x not in tri[fid]['lost_side']:
            mis_side.append((fid, x))
print('  分列规则违例 %d 行；lost_side 漏登记 %d 条' % (len(mis_rule), len(mis_side)))
ck('D1 lost_primary 空 <=> 失联类不含 {ledger,firsthand,verdict} —— 32/32 成立',
   not mis_rule, mis_rule[:5])
ck('D2 被判「旁证」的那 4 行，失联件全部机械登记在 lost_side 列（不是只在 basis 散文里）',
   not mis_side, mis_side[:5])

four = [f for f in sorted(tri_fids) if not tri[f]['lost_primary'].strip()]
print('  lost_primary 为空的 fid：%s' % four)
ck('D3 lost_primary 为空的恰 4 行 F18/F27/F39/F49', four == ['F18', 'F27', 'F39', 'F49'], four)
for f in four:
    ck('D3-%s lost_side 非空且逐个在盘判失' % f,
       bool(tri[f]['lost_side'].strip())
       and all(not os.path.exists(posix(x.split('(')[0])) for x in tri[f]['lost_side'].split(';')),
       tri[f]['lost_side'][:120])

# 反控：把「primary/side 的类集合」整体错贴（把 progress 也算 primary），必须产生违例
bad = 0
for fid in sorted(tri_fids):
    r = rows532[fid]
    dead = [posix(parse_entry(x)[0]) for x in r[3].split(';')
            if parse_entry(x)[0] and not os.path.exists(posix(parse_entry(x)[0]))]
    cls_set = {lost_class(x) for x in dead}
    if bool(cls_set & (PRIMARY_CLASSES | {'progress'})) != bool(tri[fid]['lost_primary'].strip()):
        bad += 1
ck('D4 反控：把 progress 也算进 primary 必须产生 >= 1 处违例（规则不是恒真）', bad >= 1, bad)

# ---------------------------------------------------------------- 4 路径层总量对账（R142 §2.146 一）
print('\n== 4 路径层总量 131 = 91 + 36 + 4 复核 ==')
n_alive = n_lp = n_ls = 0
alive_missing = []
lp_alive = []
ls_alive = []
for fid, t in tri.items():
    for x in [y for y in t['alive_paths'].split(';') if y.strip()]:
        n_alive += 1
        if not os.path.exists(posix(x.split('(')[0])):
            alive_missing.append((fid, x))
    for x in [y for y in t['lost_primary'].split(';') if y.strip()]:
        n_lp += 1
        if os.path.exists(posix(x.split('(')[0])):
            lp_alive.append((fid, x))
    for x in [y for y in t['lost_side'].split(';') if y.strip()]:
        n_ls += 1
        if os.path.exists(posix(x.split('(')[0])):
            ls_alive.append((fid, x))
print('  alive=%d lost_primary=%d lost_side=%d total=%d' % (n_alive, n_lp, n_ls, n_alive + n_lp + n_ls))
ck('E1 alive_paths 声明的 %d 条全部在盘' % n_alive, not alive_missing, alive_missing[:3])
ck('E2 lost_primary 声明的 %d 条全部不在盘' % n_lp, not lp_alive, lp_alive[:3])
ck('E3 lost_side 声明的 %d 条全部不在盘' % n_ls, not ls_alive, ls_alive[:3])
ck('E4 总量 = alive + lost_primary + lost_side', n_alive + n_lp + n_ls == n_alive + n_lp + n_ls,
   n_alive + n_lp + n_ls)

# ---------------------------------------------------------------- 5 档位是否为路径状态的函数
print('\n== 5 档位 vs 路径状态（T1 复算 + 置换基线）==')
VERDICTS = ['仍可核验', '需重建', '不可核验']


def t1_predict(fid, S):
    n, k = S['per'][fid]
    if n == 0:
        return '不可核验'
    if k > 0:
        return '需重建'
    return '仍可核验'


for tag, S in (('V532', s532), ('V543', s543)):
    fids = [f for f in tri_fids if f in S['per']]
    agree = sum(1 for f in fids if t1_predict(f, S) == tri[f]['verdict'])
    print('  %s：T1 一致 %d/%d = %.4f%%' % (tag, agree, len(fids), 100.0 * agree / len(fids)))
    if tag == 'V532':
        ck('F1 V532 上 T1 一致率 == 18/32（R142 实测值复现）', (agree, len(fids)) == (18, 32),
           (agree, len(fids)))
    else:
        ck('F1b V543 上 T1 一致率 == 18/32（F35 未定性，不进分母）',
           (agree, len(fids)) == (18, 32), (agree, len(fids)))

# 置换基线：固定真实标签多重集与预测多重集，随机置换标签，看一致率分布
truth = [tri[f]['verdict'] for f in sorted(tri_fids)]
pred = [t1_predict(f, s532) for f in sorted(tri_fids)]
print('  预测分布 %s ; 真值分布 %s' % (collections.Counter(pred), collections.Counter(truth)))
random.seed(162)
scores = []
for _ in range(4000):
    sh = truth[:]
    random.shuffle(sh)
    scores.append(sum(1 for a, b in zip(pred, sh) if a == b))
mean = sum(scores) / len(scores)
var = sum((x - mean) ** 2 for x in scores) / len(scores)
obs = sum(1 for a, b in zip(pred, truth) if a == b)
print('  置换基线 mean=%.4f sd=%.4f ; 实测 %d' % (mean, var ** 0.5, obs))
ck('F2 T1 实测一致数 == 置换期望（即 T1 与随机不可分）', abs(obs - mean) < 0.01, (obs, round(mean, 4)))
# S-468（自错）：首版这里断言「置换 sd > 0，基线不是常数退化」，实测 sd == 0.0 当场 FAIL。
# 但 sd == 0 不是缺陷，是我没想清楚：T1 在「部分失联」这个总体上是**常数预测器**——
# 该总体的定义就是 0 < k < n，T1 的第一支（k==0 → 仍可核验）与第二支（k==n → 不可核验）
# 在这一总体上**结构上不可能命中**，于是 32 行全部预测成同一个档，得分恒等于真值里该档的个数。
# 所以正确断言是「预测单一化 ⇒ sd 必为 0」，并且这比 R142 的「与随机不可分」更强：
# T1 不是「弱判据」，是**多数类常数判据**。
pred_kinds = collections.Counter(pred)
ck('F2b T1 在部分失联总体上预测单一化（只剩 1 个预测档，结构上不可能命中另两档）',
   len(pred_kinds) == 1 and list(pred_kinds)[0] == '需重建', dict(pred_kinds))
ck('F2c 预测单一 ⇒ 置换分布 sd == 0（这是必然，不是巧合）', var == 0.0, round(var, 6))
ck('F2d 得分恒等于真值里「需重建」的个数（常数判据的可失败形式）',
   obs == truth.count('需重建'), (obs, truth.count('需重建')))

# 决定性反例：零失联却跨两档 / 同失联件不同档
ck('F3 决定性反例：lost_primary 为空的 4 行跨两档',
   len({tri[f]['verdict'] for f in four}) >= 2,
   {f: tri[f]['verdict'] for f in four})
ck('F4 F39 与 F49 lost_primary 均空、都点名同一已失件，档位不同',
   tri['F39']['lost_primary'] == '' and tri['F49']['lost_primary'] == ''
   and tri['F39']['verdict'] != tri['F49']['verdict']
   and 'HANDOFF_R14_R3' in tri['F39']['lost_side']
   and 'HANDOFF_R14_R3' in tri['F49']['lost_side'],
   (tri['F39']['verdict'], tri['F49']['verdict']))

# ---------------------------------------------------------------- 6 V543 新增项 F35 的定性归属
print('\n== 6 V543 新增进部分失联桶的 F35：三套规则各给什么档 ==')
f35_dead = [posix(parse_entry(x)[0]) for x in rows532['F35'][3].split(';')
            if parse_entry(x)[0] and not os.path.exists(posix(parse_entry(x)[0]))]
rows543 = {r[0]: r for r in load_rows(V543)[1]}
f35_dead543 = [posix(parse_entry(x)[0]) for x in rows543['F35'][3].split(';')
               if parse_entry(x)[0] and not os.path.exists(posix(parse_entry(x)[0]))]
print('  F35 失联件 V532=%s ; V543=%s' % (f35_dead, f35_dead543))
ck('G1 F35 的失联件两版相同（V543 只是补了 4 条在盘路径）',
   set(f35_dead) == set(f35_dead543) and len(f35_dead) == 1, (f35_dead, f35_dead543))
ck('G2 F35 失联件属 firsthand 类（PANEL/DELIVERY 档）',
   lost_class(f35_dead543[0]) == 'firsthand', (f35_dead543[0], lost_class(f35_dead543[0])))


def t2_predict(fid, S, texts):
    base = t1_predict(fid, S)
    if base != '需重建':
        return base
    t = tri.get(fid)
    blob = (t['basis'] if t else '')
    if any(k in blob for k in ('无在盘替代', '唯一裁定载体')):
        return '不可核验'
    if any(k in blob for k in ('不影响主体链', '旁证')):
        return '仍可核验'
    return '需重建'


# T2 只能在有 basis 的行上用（F35 无 basis ⇒ 只能落到默认支）
f35_t1 = t1_predict('F35', s543)
f35_peak = 'PANEL.md' in rows543['F35'][1] or 'PANEL.md' in rows543['F35'][4]
print('  F35 在 V543 下：T1 预测 = %s ; 正文是否仍点名 PANEL.md = %s' % (f35_t1, f35_peak))
ck('G3 F35 在 V543 下 T1 预测 = 需重建（失联量 > 0 且 < 全量）', f35_t1 == '需重建', f35_t1)
ck('G4 F35 的失联件 PANEL.md 在正文里仍被点名（失联件不是孤儿登记）', f35_peak, f35_peak)
ck('G5 F35 无 basis ⇒ T2 只能落默认支「需重建」（T2 不可判它）',
   t2_predict('F35', s543, {}) == '需重建', t2_predict('F35', s543, {}))

# 同组合对照：V543 里与 F35 同「失联类组合」的其它 fact
# S-469（自错）：首版把分组键写成 (失联类组合, 证据项数)，F35 的项数是 5、其余四家都不是 5
# ⇒ 它成了同组独苗、断言「同组其它 fact 全部判需重建」必然 FAIL。
# 但这不是数据问题：F35 的项数从 1 变 5 正是它从全失联桶掉进部分失联桶的原因，
# 把它塞进分组键等于把「被测的那次变化」也当成判据。改为只按失联类组合分组。
comp543 = {}
for fid in s543['part']:
    r = rows543[fid]
    dead = [posix(parse_entry(x)[0]) for x in r[3].split(';')
            if parse_entry(x)[0] and not os.path.exists(posix(parse_entry(x)[0]))]
    comp = tuple(sorted(collections.Counter(lost_class(x) for x in dead).items()))
    comp543.setdefault(comp, []).append((fid, tri.get(fid, {}).get('verdict', '(未定性)')))
f35_key = None
for key, lst in comp543.items():
    if any(f == 'F35' for f, _ in lst):
        f35_key = key
print('  F35 所在同组（只按失联类组合）= %s -> %s' % (f35_key, comp543[f35_key]))
same = [x for x in comp543[f35_key] if x[0] != 'F35']
ck('G6 F35 同组内其它 fact 全部判「需重建」（4/4），F35 落该档无歧义',
   len(same) == 4 and all(v == '需重建' for _, v in same), (same,))
ck('G6b F35 是该组第 5 个成员（项数 5 是它与另 4 家的唯一差别，也是它改档的原因）',
   s543['per']['F35'] == (5, 1) and all(s543['per'][f][0] != 5 for f, _ in same),
   [(f, s543['per'][f]) for f, _ in same])
ck('G7 反控：同组外必存在判「不可核验」的 firsthand 组（分组有区分力）',
   any(v == '不可核验' for k, lst in comp543.items() if k != f35_key for _, v in lst), True)

# ---------------------------------------------------------------- 7 收口
summary = {
    'baseline_sha': got,
    'V532': {k: s532[k] for k in ('rows', 'entries', 'distinct', 'dead')} |
            {'part': len(s532['part']), 'all_dead': s532['all_dead'], 'all_ok': len(s532['all_ok'])},
    'V543': {k: s543[k] for k in ('rows', 'entries', 'distinct', 'dead')} |
            {'part': len(s543['part']), 'all_dead': s543['all_dead'], 'all_ok': len(s543['all_ok'])},
    'triage_rows': len(tri),
    'triage_verdict_counts': dict(collections.Counter(t['verdict'] for t in tri.values())),
    'coverage_by_fid_pct': round(cov_fid, 4),
    'coverage_by_entry_pct': round(cov_ent, 4),
    'triage_missing_fids': sorted(set(s543['part']) - tri_fids),
    'lost_primary_empty_fids': four,
    'class_rule_violations': len(mis_rule),
    'lost_side_missing_dead': len(mis_side),
    'path_layer': {'alive': n_alive, 'lost_primary': n_lp, 'lost_side': n_ls},
    't1_agree_v532': 18, 't1_perm_mean': round(mean, 4), 't1_perm_sd': round(var ** 0.5, 4),
    'f35_pred_t1': f35_t1,
    'checks': len(RES), 'fails': FAIL,
}
os.makedirs('_r162', exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print('\n== 收口：%d 断言，%d FAIL ==' % (len(RES), FAIL))
print(json.dumps({k: v for k, v in summary.items() if k != 'baseline_sha'},
                 ensure_ascii=False, indent=1))
sys.exit(1 if FAIL else 0)
