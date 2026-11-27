#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R162-B · 反驳 R142 §2.146 第五节那句「有 4 行把失联件只写在 basis 散文里」

被反驳的原句（R14_COMMON.md §2.146 第五节，逐字）：
  「外部 triage 的 `lost_primary` 列**不完整**，有 4 行把失联件只写在 `basis` 散文里。
    任何下游若只读 `lost_primary` 列，会把这 4 行误当「无失联」。
    这也是 T2 必须读 `basis` 才能到 75% 的原因。」

本轮实测要判三件事：
  (a) 那 4 行的失联件，到底有没有被机械登记在某一列（`lost_primary` 或 `lost_side`）？
  (b) 这份外部 triage 的两列合起来，与「按 V532 台账逐 entry 实测的失联集合」是否**双向相等**？
      （相等 ⇒ 列是**分类**，不是**遗漏**；「不完整」这个词用错了对象）
  (c) T2 读 `basis` 的真实理由是「取档位关键词」，与「失联件登记在不在 basis」无关 ⇒ 因果归错。

只读。不写 R17 五件套、不写 FACT_INDEX、不写 _ext/。
"""
import collections
import hashlib
import io
import json
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)

V532 = 'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv'
TRIAGE = '_ext/f_partial_triage/TRIAGE.tsv'
R14C = 'lead/next_re_20261117_r14/R14_COMMON.md'
OUT = '_r162/r162b_column_vs_omission.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:300]) if detail else ''))


def load_rows(p):
    rows = [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]
    return rows[0], [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]


def posix(p):
    return p.replace('\\', '/').strip()


def parse_entry(e):
    e = e.strip()
    if not e:
        return None, ''
    i = e.find('(')
    if i < 0:
        return e, ''
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]


def split_decl(col):
    """把 triage 的一列拆成 posix 路径列表（丢掉括号内定位符）。"""
    out = []
    for x in col.split(';'):
        x = x.strip()
        if not x:
            continue
        out.append(posix(x.split('(')[0]))
    return out


# ---------------------------------------------------------------- 0 基线
print('== 0 基线 ==')
h_src = hashlib.sha256(io.open(R14C, 'rb').read()).hexdigest()
print('  R14_COMMON.md sha256 = %s (bytes=%d)' % (h_src[:16], os.path.getsize(R14C)))
with open(R14C, 'rb') as f:
    blob = f.read()
# S-470（自错）：首版在这里断言「R14_COMMON 是纯 LF（CR == 0）」，实测 CR = 1081 当场 FAIL。
# 这是我把「STATUS_BOARD 的 CR=0 纪律」错贴到 R14_COMMON 上：五件套里只有看板要求 CR=0，
# R14_COMMON 的不变量恰恰是 **CR 保持 1081**（1081 = CRLF 行数，文件并非全 LF）。
# 正确做法是断言 CR == 1081 且 LF == 13406，与 re-tool get_goal 报的 lf/bytes 三项一致。
ck('B0 R14_COMMON 的 CR 不变量 == 1081（不是 LF-only 文件）',
   blob.count(b'\r') == 1081, blob.count(b'\r'))
ck('B0b LF == 13406 且 bytes == 1396538（与 get_goal 三项逐项相同）',
   blob.count(b'\n') == 13406 and len(blob) == 1396538,
   (blob.count(b'\n'), len(blob)))
ck('B0c CRLF 配对数 == CR 计数（1081 行是 CRLF，其余纯 LF —— 混合形态，不是单一形态）',
   blob.count(b'\r\n') == 1081, blob.count(b'\r\n'))

# ---------------------------------------------------------------- 1 原句是否真的在盘上
print('\n== 1 被反驳的原句逐字在盘（防止我打稻草人）==')
txt = blob.decode('utf-8', errors='replace')
needles = [
    '`lost_primary` 列**不完整**，有 4 行把失联件只写在 `basis` 散文里',
    '会把这 4 行误当「无失联」',
    '这也是 T2 必须读 `basis` 才能到 75% 的原因',
]
for i, n in enumerate(needles):
    ck('A%d 原句片段在场：%s' % (i + 1, n[:34] + '…'), n in txt, txt.count(n))

# ---------------------------------------------------------------- 2 实测失联集合 vs 两列声明
print('\n== 2 逐 fid 双向集合相等：实测失联集 vs (lost_primary ∪ lost_side) ==')
hdr, body = load_rows(V532)
rows = {r[0]: r for r in body}
tri_raw = [l.split('\t') for l in io.open(TRIAGE, encoding='utf-8').read().split('\n') if l.strip()]
assert tri_raw[0] == ['fid', 'lost_primary', 'lost_side', 'alive_paths', 'verdict', 'basis'], tri_raw[0]
tri = {c[0]: dict(zip(tri_raw[0], c)) for c in tri_raw[1:]}

measured = {}
declared = {}
for fid in tri:
    r = rows[fid]
    m = set()
    for raw in r[3].split(';'):
        p, _ = parse_entry(raw)
        if p and not os.path.exists(posix(p)):
            m.add(posix(p))
    measured[fid] = m
    declared[fid] = set(split_decl(tri[fid]['lost_primary'])) | set(split_decl(tri[fid]['lost_side']))

extra = {f: sorted(declared[f] - measured[f]) for f in tri if declared[f] - measured[f]}
short = {f: sorted(measured[f] - declared[f]) for f in tri if measured[f] - declared[f]}
print('  声明多出（声明了但实际在盘/不在台账）: %d 个 fid' % len(extra))
print('  声明漏登记（在台账里失联但两列都没写）: %d 个 fid' % len(short))
for f in sorted(short):
    print('    %s 漏: %s' % (f, short[f]))
ck('C1 两列并集 与 实测失联集合 逐 fid 相等（无多、无漏，32/32）',
   not extra and not short, {'extra': extra, 'short': short})

# 分量：lost_primary 精确等于实测失联集里 primary 类的那部分
LEDGER = {'R17_LEDGER_1062', 'R17_LEDGER_1063', 'R17_LEDGER_1063R',
          'R17_LEDGER_1064', 'R17_LEDGER_1065'}
PRIM = ('COVERAGE/PANEL.md', 'R17_DELIVERY/DELIVERY_SUMMARY.md')


def is_primary(rel):
    parts = rel.split('/')
    if any(x in LEDGER for x in parts) and parts[-1] == 'SECTION.md':
        return True
    if rel.endswith(PRIM[0]) or rel.endswith(PRIM[1]):
        return True
    if parts[-1] == 'VERDICT.md':
        return True
    return False


lp_mis = []
ls_mis = []
for fid in tri:
    exp_p = {x for x in measured[fid] if is_primary(x)}
    exp_s = {x for x in measured[fid] if not is_primary(x)}
    if set(split_decl(tri[fid]['lost_primary'])) != exp_p:
        lp_mis.append((fid, sorted(exp_p), sorted(split_decl(tri[fid]['lost_primary']))))
    if set(split_decl(tri[fid]['lost_side'])) != exp_s:
        ls_mis.append((fid, sorted(exp_s), sorted(split_decl(tri[fid]['lost_side']))))
ck('C2 lost_primary 精确 == 实测失联集里的 {ledger|firsthand|verdict} 部分（32/32）',
   not lp_mis, lp_mis[:3])
ck('C3 lost_side 精确 == 实测失联集里的剩余部分（32/32）', not ls_mis, ls_mis[:3])

# ---------------------------------------------------------------- 3 那 4 行的原件
print('\n== 3 那 4 行（lost_primary 空）的失联件到底登记在哪 ==')
four = sorted(f for f in tri if not tri[f]['lost_primary'].strip())
ck('D0 lost_primary 为空的恰 4 行 F18/F27/F39/F49', four == ['F18', 'F27', 'F39', 'F49'], four)
for f in four:
    ls = split_decl(tri[f]['lost_side'])
    basis = tri[f]['basis']
    in_ls = [x for x in measured[f] if any(x.endswith(y.split('/')[-1]) or y.endswith(x.split('/')[-1]) for y in ls)]
    ck('D1-%s 失联件 %d 条全部出现在 lost_side 列（不是"只在 basis 散文里"）' % (f, len(measured[f])),
       len(in_ls) == len(measured[f]) and len(measured[f]) > 0, (sorted(measured[f]), ls))
    # S-471（自错）：首版用 basename 带 .md 去比 basis，F39/F49 当场 FAIL ——
    # 因为 basis 写的是「HANDOFF_R14_R3 五 已失」／「失 HANDOFF_R14_R3 九为旁证」，
    # 省略了 .md 后缀。事实是两处**都**提到了，只是散文里的文件名不带扩展名。
    # 改用 stem（去扩展名）比对，并保留带后缀的情况作并集。
    stems = [os.path.splitext(os.path.basename(x))[0] for x in measured[f]]
    hit = any(s in basis or os.path.basename(x) in basis
              for s, x in zip(stems, measured[f]))
    ck('D2-%s basis 散文同样提到该件（去扩展名比对；两处都写了，不是只写一处）' % f,
       hit, (stems, basis[:90]))

# 反控：随机挑一个「lost_primary 非空」的行，其 lost_side 也应有登记吗？不必然——
# 反控改用：把 LOST 两列整体置空，C1 必须 FAIL 式地出现 32 条漏登记（证明判据不是恒真）
short_ct = 0
for fid in tri:
    if not (set(split_decl('')) | set(split_decl(''))) == measured[fid]:
        short_ct += 1
ck('D3 反控：两列全置空 ⇒ 32 条全部成为漏登记（判据有区分力）', short_ct == 32, short_ct)

# ---------------------------------------------------------------- 4 T2 读 basis 的真实作用
print('\n== 4 T2 读 basis 是取「档位关键词」，与失联件登记无关 ==')
T2_KW_UNVER = ('无在盘替代', '唯一裁定载体')
T2_KW_VER = ('不影响主体链', '旁证')
# 4 行里，basis 是否含 T2 关键词？含关键词的又是哪几行？
kw_hit = {}
for fid in tri:
    b = tri[fid]['basis']
    k = []
    if any(x in b for x in T2_KW_UNVER):
        k.append('->不可核验')
    if any(x in b for x in T2_KW_VER):
        k.append('->仍可核验')
    if k:
        kw_hit[fid] = (k, tri[fid]['verdict'])
for f in sorted(kw_hit):
    print('  %s %s 实测档=%s' % (f, kw_hit[f][0], kw_hit[f][1]))
print('  含 T2 关键词的行数 = %d' % len(kw_hit))
ck('E1 那 4 行里有 basis 关键词的行数 < 4（即 T2 读 basis 不是为了找回那 4 行的失联件）',
   len([f for f in four if f in kw_hit]) < 4,
   ([f for f in four if f in kw_hit], four))
ck('E2 T2 关键词与失联件登记是两件事：关键词行里也存在 lost_primary 非空的行',
   any(tri[f]['lost_primary'].strip() for f in kw_hit), [f for f in kw_hit if tri[f]['lost_primary'].strip()])
# T2 的 75% 复核：T1 + 关键词
def t1(fid):
    n = len([1 for raw in rows[fid][3].split(';') if parse_entry(raw)[0]])
    k = len(measured[fid])
    if n == 0:
        return '不可核验'
    if k > 0:
        return '需重建'
    return '仍可核验'


def t2(fid):
    b = t1(fid)
    if b != '需重建':
        return b
    bb = tri[fid]['basis']
    if any(x in bb for x in T2_KW_UNVER):
        return '不可核验'
    if any(x in bb for x in T2_KW_VER):
        return '仍可核验'
    return '需重建'


a1 = sum(1 for f in tri if t1(f) == tri[f]['verdict'])
a2 = sum(1 for f in tri if t2(f) == tri[f]['verdict'])
print('  T1 %d/32 = %.4f%% ; T2 %d/32 = %.4f%%' % (a1, 100.0 * a1 / 32, a2, 100.0 * a2 / 32))
ck('E3 T1 == 18/32（复现 R142）', a1 == 18, a1)
ck('E4 T2 == 24/32（复现 R142），残余 8 条', a2 == 24, a2)
resid = sorted(f for f in tri if t2(f) != tri[f]['verdict'])
ck('E5 T2 残余 8 条 == F09/F10/F19/F22/F25/F28/F46/F52',
   resid == ['F09', 'F10', 'F19', 'F22', 'F25', 'F28', 'F46', 'F52'], resid)
ck('E6 残余 8 条与那 4 行（lost_primary 空）交集为空 ⇒ 75% 的天花板与「列不完整」无关',
   not (set(resid) & set(four)), (resid, four))

# ---------------------------------------------------------------- 5 收口
summary = {
    'r14common_sha256': h_src,
    'refuted_sentence_present': all(n in txt for n in needles),
    'declared_vs_measured': {
        'fids_extra': sorted(extra), 'fids_short': sorted(short),
        'bidirectional_equal': (not extra and not short),
    },
    'lost_primary_exact_class_rule': {'mismatches': len(lp_mis)},
    'lost_side_exact_remainder': {'mismatches': len(ls_mis)},
    'four_rows_with_empty_lost_primary': four,
    'four_rows_dead_in_lost_side': {f: sorted(measured[f]) for f in four},
    't2_keyword_rows': {f: kw_hit[f][0] for f in sorted(kw_hit)},
    't1_agree': a1, 't2_agree': a2, 't2_residual': resid,
    'checks': len(RES), 'fails': FAIL,
}
os.makedirs('_r162', exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print('\n== 收口：%d 断言，%d FAIL ==' % (len(RES), FAIL))
print(json.dumps(summary, ensure_ascii=False, indent=1))
sys.exit(1 if FAIL else 0)
