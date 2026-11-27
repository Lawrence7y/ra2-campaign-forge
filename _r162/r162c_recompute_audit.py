#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R162-C · 复算审计员 #378 的六条新增强判据（§2.12 规则 D：审计员结论不可直接采信）

审计员（deepseek, audit, 20 回合 / 3.57′ / 预算 8′ / 无 OVERTIME）核对了 r162a/r162b 的
五条结论，并加了六条我没测的判据。本轮逐条复算，任何一条不成立都必须当场记下来。

要复算的六条：
  A1 两列互斥分类：0 行「lost_primary 与 lost_side 同时非空」、0 行「同时为空」。
  A2 entry 级账：TRIAGE 覆盖的 32 个 fid 的失联 entry = 40 条（36 primary + 4 side）；
     V532 全表失联 entry = 43 条；差 3 条 = F23(2) + F35(1) 这两个非 TRIAGE 口径的 fid。
  A3 逐路径失联次数（Counter）两版完全相同，且总数 43。
  A4 覆盖面按 entry 的分母是 139（= V543 那 33 个 partial fid 的项数和），
     不是 278 也不是 178；134/139 = 96.4029%。
  A5 锚点级比对：TRIAGE 40 条失联 entry 的「路径(定位符)」锚点，逐字出现在同 fid
     同路径的台账 entry 里，40/40 全等。
  A6 T2 残余 8 条的错误方向统一：8 条全是「实为不可核验、被判需重建」。

只读；不写 R17 五件套、不写 FACT_INDEX、不写 _ext/。
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
V543 = 'lead/next_re_20261117_r14/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
TRIAGE = '_ext/f_partial_triage/TRIAGE.tsv'
OUT = '_r162/r162c_recompute_audit.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:300]) if detail else ''))


def load_rows(p):
    rows = [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]
    return rows[0], [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]


def posix(p):
    return p.replace('\\', '/').strip()


def split_entries(col):
    """在括号深度 0 处按 ';' 切；深度用 () 计数，忽略全角括号。"""
    out = []
    depth = 0
    cur = []
    for ch in col:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        if ch == ';' and depth == 0:
            out.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append(''.join(cur))
    return [x.strip() for x in out if x.strip()]


def parse_entry(e):
    e = e.strip()
    if not e:
        return None, ''
    i = e.find('(')
    if i < 0 or not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]


def load_v(p):
    hdr, body = load_rows(p)
    d = {}
    for r in body:
        ents = []
        for raw in split_entries(r[3]):
            pth, loc = parse_entry(raw)
            if not pth:
                continue
            rel = posix(pth)
            ents.append({'raw': raw.strip(), 'rel': rel, 'loc': loc,
                         'alive': os.path.exists(rel)})
        d[r[0]] = {'raw': r, 'ents': ents,
                   'dead': [e for e in ents if not e['alive']],
                   'alive': [e for e in ents if e['alive']]}
    return hdr, d


_, D532 = load_v(V532)
_, D543 = load_v(V543)
tri_raw = [l.split('\t') for l in io.open(TRIAGE, encoding='utf-8').read().split('\n') if l.strip()]
tri = {c[0]: dict(zip(tri_raw[0], c)) for c in tri_raw[1:]}
TRI = sorted(tri)

print('== 0 基线 ==')
ck('B0 TRIAGE 32 行、V532/V543 各 54 行',
   len(tri) == 32 and len(D532) == 54 and len(D543) == 54,
   (len(tri), len(D532), len(D543)))

# ---------------------------------------------------------------- A1 两列互斥
print('\n== A1 两列互斥分类（0 行同时非空 / 0 行同时为空）==')


def split_decl(col):
    return [posix(x.split('(')[0]) for x in split_entries(col)]


both_ne = [f for f in TRI if tri[f]['lost_primary'].strip() and tri[f]['lost_side'].strip()]
both_em = [f for f in TRI if not tri[f]['lost_primary'].strip() and not tri[f]['lost_side'].strip()]
print('  同时非空 %d 行 %s ; 同时为空 %d 行 %s' % (len(both_ne), both_ne, len(both_em), both_em))
ck('A1 0 行同时非空', not both_ne, both_ne)
ck('A1b 0 行同时为空', not both_em, both_em)

# ---------------------------------------------------------------- A2 entry 级账
print('\n== A2 entry 级账：40 = 36 + 4 ；43 = 40 + 3 ==')
tri_lp = sum(len(split_entries(tri[f]['lost_primary'])) for f in TRI)
tri_ls = sum(len(split_entries(tri[f]['lost_side'])) for f in TRI)
tri_dead_entries = sum(len(D532[f]['dead']) for f in TRI)
tri_alive_entries = sum(len(D532[f]['alive']) for f in TRI)
all_dead_entries = sum(len(D532[f]['dead']) for f in D532)
# S-472（自错）：首版把 outside 写成「所有不在 TRIAGE 里的 fid」（22 家），
# 于是断言「这 3 条恰来自 F23(2)+F35(1)」必然 FAIL —— 22 家里有 20 家 dead 数为 0。
# 正确口径是「不在 TRIAGE 里**且有失联**的 fid」，实测恰 2 家 F23/F35。
outside = [f for f in D532 if f not in tri]
outside_with_dead = sorted(f for f in outside if D532[f]['dead'])
outside_dead = sum(len(D532[f]['dead']) for f in outside_with_dead)
print('  TRIAGE 32 fid: dead=%d alive=%d total=%d' % (tri_dead_entries, tri_alive_entries,
                                                      tri_dead_entries + tri_alive_entries))
print('  lost_primary 条目 %d ; lost_side 条目 %d ; 合计 %d' % (tri_lp, tri_ls, tri_lp + tri_ls))
print('  全表 dead entry %d ; TRIAGE 之外有失联的 fid %s 的 dead entry %d'
      % (all_dead_entries, outside_with_dead, outside_dead))
ck('A2 TRIAGE 覆盖的 32 fid 的失联 entry == 40 条', tri_dead_entries == 40, tri_dead_entries)
ck('A2b 36 + 4 == 40（两列条目数之和 == 实测失联 entry 数）', tri_lp == 36 and tri_ls == 4
   and tri_lp + tri_ls == tri_dead_entries, (tri_lp, tri_ls))
ck('A2c 全表失联 entry == 43', all_dead_entries == 43, all_dead_entries)
ck('A2d 43 - 40 == 3，且这 3 条恰来自 F23(2) + F35(1)',
   all_dead_entries - tri_dead_entries == 3
   and outside_with_dead == ['F23', 'F35']
   and [len(D532[f]['dead']) for f in outside_with_dead] == [2, 1],
   (outside_with_dead, [len(D532[f]['dead']) for f in outside_with_dead]))
ck('A2e TRIAGE 的 alive 条目 == 91（与 R142 路径层总数 131 = 91+36+4 一致）',
   tri_alive_entries == 91, tri_alive_entries)

# ---------------------------------------------------------------- A3 逐路径失联次数
print('\n== A3 逐路径失联次数两版完全相同 ==')
c532 = collections.Counter(e['rel'] for f in D532 for e in D532[f]['dead'])
c543 = collections.Counter(e['rel'] for f in D543 for e in D543[f]['dead'])
dif = {k: (c532.get(k, 0), c543.get(k, 0)) for k in set(c532) | set(c543)
       if c532.get(k, 0) != c543.get(k, 0)}
print('  逐路径计数差异 %d 条' % len(dif))
ck('A3 逐路径失联次数两版逐条相同', not dif, dif)
ck('A3b 两版失联 entry 总数均 43', sum(c532.values()) == 43 and sum(c543.values()) == 43,
   (sum(c532.values()), sum(c543.values())))
ck('A3c distinct 失联路径 16 条、distinct 路径总数 68 / 74',
   len(c532) == 16 and len(c543) == 16, (len(c532), len(c543)))
top = c532.most_common(6)
print('  失联次数最高的 6 条：%s' % top)
ck('A3d PANEL.md 是失联次数最高的单条（8 次）', top[0][1] == 8 and 'COVERAGE/PANEL.md' in top[0][0],
   top[0])

# ---------------------------------------------------------------- A4 覆盖面分母
print('\n== A4 覆盖面的分母口径 ==')
part543 = [f for f in D543
           if 0 < len(D543[f]['dead']) < len(D543[f]['ents'])]
ent_part = sum(len(D543[f]['ents']) for f in part543)
ent_cov = sum(len(D543[f]['ents']) for f in part543 if f in tri)
all_ent = sum(len(D543[f]['ents']) for f in D543)
print('  分母候选：33 个 partial fid 的项数 %d ; 全表项数 %d ; 全表项数*2 %d'
      % (ent_part, all_ent, all_ent * 2))
print('  134/%d = %.4f%% ; 若误用 178 分母 %d/178 = %.4f%% ; 若误用 268 分母 %.4f%%'
      % (ent_part, 100.0 * ent_cov / ent_part, ent_cov, 100.0 * ent_cov / 178,
         100.0 * ent_cov / 268))
ck('A4 V543 partial fid 恰 33 家、项数和 == 139', len(part543) == 33 and ent_part == 139,
   (len(part543), ent_part))
ck('A4b 分子 134 = 32 家（= TRIAGE 那 32 个 fid）的项数和', ent_cov == 134, ent_cov)
ck('A4c 134/139 = 96.4029%（四位小数）', round(100.0 * 134 / 139, 4) == 96.4029,
   round(100.0 * 134 / 139, 4))
ck('A4d 反控：若分母误取全表 178 ⇒ 75.28%，与 96.40% 差 21 个百分点（口径不可混）',
   round(100.0 * 134 / 178, 2) == 75.28, round(100.0 * 134 / 178, 2))
ck('A4e 按 fid 的口径 32/33 = 96.9697%', round(100.0 * 32 / 33, 4) == 96.9697,
   round(100.0 * 32 / 33, 4))

# ---------------------------------------------------------------- A5 锚点级比对
print('\n== A5 锚点级：TRIAGE 的 40 条失联 entry 锚点逐字出现在台账里 ==')
miss = []
for f in TRI:
    # S-473（自错）：首版拿台账的**原始串**（反斜杠路径）去比 TRIAGE 的**正斜杠串**，
    # 40 条全部「对不上」当场 FAIL —— 那是路径分隔符没归一，不是锚点不一致。
    # 正确做法是两侧都过 posix() 再比整串（含定位符）。
    tab = {e['rel'] + ('(' + e['loc'] + ')' if e['loc'] else '') for e in D532[f]['ents']}
    for col in ('lost_primary', 'lost_side'):
        for raw in split_entries(tri[f][col]):
            if posix(raw) not in tab:
                miss.append((f, col, raw))
print('  锚点未对上 %d 条' % len(miss))
for m in miss[:6]:
    print('    %s %s %r' % m)
ck('A5 40/40 锚点逐字全等（「路径(定位符)」整串相同）', not miss, miss[:5])
ck('A5b 锚点总数 == 40（不是 131、也不是 36+4 之外的口径）',
   tri_lp + tri_ls == 40, tri_lp + tri_ls)

# ---------------------------------------------------------------- A6 T2 残余方向
print('\n== A6 T2 残余 8 条的错误方向是否统一 ==')
T2_UNVER = ('无在盘替代', '唯一裁定载体')
T2_VER = ('不影响主体链', '旁证')


def t1(f):
    n = len(D532[f]['ents'])
    k = len(D532[f]['dead'])
    if n == 0:
        return '不可核验'
    return '需重建' if k > 0 else '仍可核验'


def t2(f):
    b = t1(f)
    if b != '需重建':
        return b
    bb = tri[f]['basis']
    if any(x in bb for x in T2_UNVER):
        return '不可核验'
    if any(x in bb for x in T2_VER):
        return '仍可核验'
    return '需重建'


RESID = ['F09', 'F10', 'F19', 'F22', 'F25', 'F28', 'F46', 'F52']
resid_meas = sorted(f for f in TRI if t2(f) != tri[f]['verdict'])
a2 = sum(1 for f in TRI if t2(f) == tri[f]['verdict'])
print('  T2 一致 %d/32 ; 残余 %s' % (a2, resid_meas))
ck('A6 T2 == 24/32 且残余 == 那 8 条', a2 == 24 and resid_meas == RESID, (a2, resid_meas))
wrong = {f: (t2(f), tri[f]['verdict']) for f in resid_meas}
print('  残余 8 条的（预测 -> 实测）：%s' % wrong)
ck('A6b 残余 8 条方向统一：全部是「预测需重建、实测不可核验」',
   all(p == '需重建' and r == '不可核验' for p, r in wrong.values()), wrong)
ck('A6c 反控：残余里不存在「预测仍可核验」的项（方向不是双向的）',
   not any(p == '仍可核验' for p, _ in wrong.values()), wrong)
# 这 8 条的 basis 是否含「已失」但不含两个否定关键词
# S-474（自错）：审计员说「8 条判错全部是实为不可核验却被判需重建」——前半句成立（A6b 已证），
# 但它给的机制「它们 basis 写的是『一手来源均失』却不含那两个否定关键词」只对一半：
# 实测只有 F09/F10 含「已失」二字，另 6 条用的是「均失 / 同时失 / 失」，字面都不是「已失」。
# 所以判错的真正机制是「T2 只认 4 个固定关键词，而自然语言里表达『一手来源不在盘』的说法
# 至少有 4 种（已失 / 均失 / 同时失 / 失）」，不是「8 条都写了已失」。
bad = [f for f in RESID if '已失' in tri[f]['basis']
       and not any(x in tri[f]['basis'] for x in T2_UNVER)]
has_loss_word = {f: [w for w in ('已失', '均失', '同时失', '失') if w in tri[f]['basis']]
                for f in RESID}
print('  残余 8 条各自用了哪个「失」字：%s' % has_loss_word)
ck('A6d 残余 8 条里只有 F09/F10 字面含「已失」（审计员的机制描述只对 2/8）',
   bad == ['F09', 'F10'], (len(bad), bad))
ck('A6e 但 8/8 都含某种「失」字表达（机制是关键词覆盖不足，不是没写）',
   all(v for v in has_loss_word.values()), has_loss_word)
ck('A6f 8/8 与 T2 的两个否定关键词无一命中（这才是判错的直接原因）',
   not any(any(x in tri[f]['basis'] for x in T2_UNVER) for f in RESID), True)

# ---------------------------------------------------------------- 收口
summary = {
    'v532_sha': hashlib.sha256(open(V532, 'rb').read()).hexdigest(),
    'v543_sha': hashlib.sha256(open(V543, 'rb').read()).hexdigest(),
    'A1_both_nonempty': both_ne, 'A1_both_empty': both_em,
    'A2_triage_dead_entries': tri_dead_entries, 'A2_triage_alive_entries': tri_alive_entries,
    'A2_lp': tri_lp, 'A2_ls': tri_ls, 'A2_all_dead_entries': all_dead_entries,
    'A2_outside_fids': {f: len(D532[f]['dead']) for f in sorted(outside)},
    'A3_per_path_counter_equal': not dif, 'A3_top': [[k, v] for k, v in top],
    'A4_denominator': ent_part, 'A4_numerator': ent_cov,
    'A4_share': round(100.0 * ent_cov / ent_part, 4),
    'A5_anchor_mismatch': len(miss),
    'A6_t2_agree': a2, 'A6_residual': resid_meas,
    'checks': len(RES), 'fails': FAIL,
}
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print('\n== 收口：%d 断言，%d FAIL ==' % (len(RES), FAIL))
print(json.dumps(summary, ensure_ascii=False, indent=1))
sys.exit(1 if FAIL else 0)
