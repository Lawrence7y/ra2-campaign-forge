#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 hy4 独立复核：MSVC RTTI COL/CHD/BCA/BCD 字节布局（只读输入，仅写本脚本产物 JSON）。
自己重写扫描与判据，不 import 主会话 _r204/m1_chd.py 或 _r204/m2_chd2.py。
"""
import sys, struct, json, collections, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

JSON_PATH = '/home/t628/projects/ra2-campaign-forge/_r204/hy4_layout.json'

def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]

def words(sn):
    s = P.B[sn]
    n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

def jd(c, by_value=False):
    """JSON-safe histogram; optional value-desc ordering."""
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0])) if by_value else sorted(c.items())
    return {str(k): v for k, v in items}

def fmt(c, top=None):
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    return str(items if top is None else items[:top]) + (' ...' if top and len(items) > top else '')

report = {}

# ===== 1. COL 记录独立扫描 =====
col = {}                      # va -> (mdisp, ptd, pchd, name)
raw_hits = 0
seg_hits = collections.Counter()
for sn in ('.rdata', '.data'):
    base, w, n = words(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0:
            continue
        ptd, pchd = w[i + 3], w[i + 4]
        if P.where(ptd) != '.data' or P.where(pchd) != '.rdata':
            continue
        nm = P.cstr(ptd + 8, 400)
        if not nm or not nm.startswith(b'.?A') or not nm.endswith(b'@@'):
            continue
        raw_hits += 1
        seg_hits[sn] += 1
        col[base + 4 * i] = (s32(w[i + 1]), ptd, pchd, nm.decode('latin1'))
names = set(v[3] for v in col.values())
report['item1_col'] = {
    'raw_hits': raw_hits,
    'distinct_va': len(col),
    'distinct_class_names': len(names),
    'hits_by_segment': jd(seg_hits),
}
print('[1] COL raw_hits=%d distinct_va=%d distinct_class_names=%d by_segment=%s' %
      (raw_hits, len(col), len(names), fmt(seg_hits)))

# ===== 2. 仅用 pCHD 分组（不读类名） =====
byp = collections.defaultdict(list)
for va, rec in col.items():
    byp[rec[2]].append(va)     # rec[2] = pchd，判据与类名无关
gd = collections.Counter(len(v) for v in byp.values())
pchd_sec = collections.Counter(P.where(a) for a in byp)
report['item2_pchd_groups'] = {
    'distinct_pchd': len(byp),
    'col_count_per_group_hist': jd(gd),
    'pchd_section_hist': jd(pchd_sec),
}
print('[2] distinct_pchd=%d group_size_hist=%s pchd_sections=%s' %
      (len(byp), fmt(gd), fmt(pchd_sec)))

# ===== 3. CHD 四字段 =====
chds = sorted(byp)
f0, f4, f8, f12sec, f12val = (collections.Counter() for _ in range(5))
for a in chds:
    f0[P.dw(a)] += 1
    f4[P.dw(a + 4)] += 1
    f8[P.dw(a + 8)] += 1
    v12 = P.dw(a + 12)
    f12sec[P.where(v12)] += 1
    f12val[v12] += 1
report['item3_chd_fields'] = {
    'chd_count': len(chds),
    'off0_hist': jd(f0),
    'off4_hist': jd(f4),
    'off8_hist': jd(f8),
    'off8_max': max(f8),
    'off8_count_gt200': sum(c for v, c in f8.items() if v > 200),
    'off12_section_hist': jd(f12sec),
    'off12_distinct_values': len(f12val),
}
print('[3] CHD +0=%s' % fmt(f0))
print('[3] CHD +4=%s' % fmt(f4))
print('[3] CHD +8=%s (max=%d, >200=%d)' % (fmt(f8), max(f8), report['item3_chd_fields']['off8_count_gt200']))
print('[3] CHD +12 sections=%s distinct_values=%d' % (fmt(f12sec), len(f12val)))

# ===== 4. BCA 取元素 =====
bca = {}
allb = []
n_hist = collections.Counter()
for a in chds:
    n = P.dw(a + 8)
    arr = P.dw(a + 12)
    vs = [P.dw(arr + 4 * j) for j in range(n)]
    bca[a] = vs
    allb.extend(vs)
    n_hist[n] += 1
uniq = sorted(set(allb))
uniq_set = set(uniq)
bcd_sec = collections.Counter(P.where(b) for b in uniq)
report['item4_bca'] = {
    'bca_reference_count': len(allb),
    'distinct_bcd_count': len(uniq),
    'bcd_section_hist': jd(bcd_sec),
    'bca_length_hist': jd(n_hist),
}
print('[4] BCA refs=%d distinct_BCD=%d BCD_sections=%s length_hist=%s' %
      (len(allb), len(uniq), fmt(bcd_sec), fmt(n_hist)))

# ===== 5. 排序后相邻地址差与 24 字节定长证据 =====
# 5a: 严格按卡片字面要求：所有排序后不同 BCD 地址的相邻差
diffs = sorted({b - a for a, b in zip(uniq, uniq[1:])})
# 5b: 关键订正：BCD 基址在 8 字节边界上以 24n+16 模式紧密排布
#     （相邻实际槽位间距恰为 24，跨过相邻槽的「空隙」产生 8/16 的模差）。
mods8 = collections.Counter(b % 8 for b in uniq)
mods24 = collections.Counter(b % 24 for b in uniq)
# 验证相邻 BCD 候选槽（b-16）是否确为结构内的常量字段，输出其取值直方图用于机械核对
slot24_16 = collections.Counter(P.dw(b - 16) if b >= 16 else None for b in uniq)
report['item5_bcd_stride'] = {
    'sorted_unique_bcd_count': len(uniq),
    'adjacent_diff_set': diffs,
    'adjacent_diff_count': len(diffs),
    'all_diffs_multiple_of_24': all(d % 24 == 0 for d in diffs),
    'min_diff': min(diffs) if diffs else None,
    'max_diff': max(diffs) if diffs else None,
    'mod8_hist': jd(mods8),
    'mod24_hist': jd(mods24),
    'b_minus_16_dword_hist': jd(slot24_16),
}
print('[5a] literal adjacent_diff_set=%s count=%d all_multiple_of_24=%s min=%s max=%s' %
      (diffs, len(diffs), report['item5_bcd_stride']['all_diffs_multiple_of_24'],
       report['item5_bcd_stride']['min_diff'], report['item5_bcd_stride']['max_diff']))
print('[5b] mod8=%s mod24=%s; dword@(b-16) hist=%s' %
      (fmt(mods8), fmt(mods24), fmt(slot24_16, top=6)))

# 5c: 最强机械证据 —— BCA 内部相邻引用差（绝大多数为 -24，说明 BCD 按 24 字节槽排列）
bca_gap = collections.Counter()
for a in chds:
    for x, y in zip(bca[a], bca[a][1:]):
        bca_gap[y - x] += 1
bca_gap_24mul = sum(c for d, c in bca_gap.items() if d % 24 == 0)
report['item5_bcd_stride']['bca_adjacent_diff_hist_top'] = jd(
    collections.Counter(dict(bca_gap.most_common(16))))
report['item5_bcd_stride']['bca_adjacent_diff_total'] = sum(bca_gap.values())
report['item5_bcd_stride']['bca_adjacent_diff_multiple_of_24'] = bca_gap_24mul
report['item5_bcd_stride']['bca_adjacent_diff_multiple_of_24_ratio'] = (
    bca_gap_24mul / sum(bca_gap.values()) if bca_gap else None)
print('[5c] BCA相邻差 top16=%s' % fmt(bca_gap, top=16))
print('[5c] BCA相邻差总数=%d 其中24倍数=%d 占比=%.4f' %
      (sum(bca_gap.values()), bca_gap_24mul,
       report['item5_bcd_stride']['bca_adjacent_diff_multiple_of_24_ratio']))

# ===== 6. BCA 是否严格 {pBCA, pBCA-24, ...} =====
# 卡片字面判据：BCA[i] == BCA[0] - 24*i（CHD+12 是数组基址，BCA[0] 为其首个 dword，实测无 0/954 相等）
strict = 0
fails = []
arr_eq_first = 0
for a in chds:
    v = bca[a]
    if v and v[0] == P.dw(a + 12):
        arr_eq_first += 1
    if v == [v[0] - 24 * i for i in range(len(v))]:
        strict += 1
    else:
        fails.append(a)

# 补充判据（考虑到 CHD+12 指向数组基址）：BCA 由若干段严格降序的 -24 序列拼接，
# 且每段长度 >=2（允许段间大跳转，对应 BCA 合并多个不相交 BCD 数组段）。
def desc_runs(v):
    runs = []
    if not v:
        return runs
    cur = [v[0]]
    for x, y in zip(v, v[1:]):
        if y - x == -24:
            cur.append(y)
        else:
            runs.append(cur)
            cur = [y]
    runs.append(cur)
    return runs

runs_ok = 0
runs_all_ok = 0
len_hist = collections.Counter(len(bca[a]) for a in chds)
# 关键区分：把 BCA 元素集合降序/升序排序后再验等差，区分「顺序交叉」与「非等差」
sorted_desc_ok = 0
sorted_asc_ok = 0
not_even_sorted = []
for a in chds:
    v = bca[a]
    runs = desc_runs(v)
    if all(len(r) >= 2 for r in runs):
        runs_ok += 1
    if all(len(r) >= 2 for r in runs) and len(bca[a]) == P.dw(a + 8):
        runs_all_ok += 1
    sv = sorted(v)
    if sv == list(range(sv[0], sv[0] + 24 * len(sv), 24)) if sv else False:
        sorted_asc_ok += 1
    sd = sorted(v, reverse=True)
    if sd == [sd[0] - 24 * i for i in range(len(sd))] if sd else False:
        sorted_desc_ok += 1
    else:
        not_even_sorted.append(a)
report['item6_descending_bca'] = {
    'chd_count': len(chds),
    'strict_descending_24_count': strict,
    'strict_fail_count': len(fails),
    'fail_sample_vas': [hex(a) for a in fails[:12]],
    'arr_equals_first_element_count': arr_eq_first,
    'arr_equals_last_element_count': sum(1 for a in chds if bca[a] and P.dw(a + 12) == bca[a][-1]),
    'all_runs_len_ge2_count': runs_ok,
    'sorted_asc_24_arithmetic_count': sorted_asc_ok,
    'sorted_desc_24_arithmetic_count': sorted_desc_ok,
    'not_even_sorted_count': len(not_even_sorted),
    'not_even_sorted_sample': [hex(a) for a in not_even_sorted[:8]],
    'bca_length_hist': jd(len_hist),
}
print('[6a] strict(BCA[i]==BCA[0]-24*i)=%d/%d fails=%d arr_equals_first=%d arr_equals_last=%d fail_samples=%s' %
      (strict, len(chds), len(fails), arr_eq_first,
       report['item6_descending_bca']['arr_equals_last_element_count'], [hex(a) for a in fails[:12]]))
print('[6b] all_runs_len_ge2(segments of -24)=%d/%d' % (runs_ok, len(chds)))
print('[6c] sorted_asc_24_arith=%d sorted_desc_24_arith=%d not_even_sorted=%d samples=%s' %
      (sorted_asc_ok, sorted_desc_ok, len(not_even_sorted),
       [hex(a) for a in not_even_sorted[:8]]))

# ===== 7. BCD 六字段 =====
g0, g4, g8, g12, g16, g20, g0sec = (collections.Counter() for _ in range(7))
for b in uniq:
    ptd = P.dw(b)
    g0[ptd] += 1
    g0sec[P.where(ptd)] += 1
    g4[P.dw(b + 4)] += 1
    g8[s32(P.dw(b + 8))] += 1
    g12[s32(P.dw(b + 12))] += 1
    g16[s32(P.dw(b + 16))] += 1
    g20[P.dw(b + 20)] += 1
report['item7_bcd_fields'] = {
    'bcd_count': len(uniq),
    'off0_pTD_hist_full': jd(g0, by_value=True),
    'off0_pTD_distinct': len(g0),
    'off0_pTD_section_hist': jd(g0sec),
    'off4_ncb_hist': jd(g4),
    'off8_mdisp_hist_full': jd(g8, by_value=True),
    'off8_mdisp_distinct': len(g8),
    'off12_pdisp_hist': jd(g12),
    'off16_vdisp_hist': jd(g16),
    'off20_attributes_hist': jd(g20),
}
print('[7] BCD +0(pTD) distinct=%d sections=%s top=%s' % (len(g0), fmt(g0sec), fmt(g0, top=8)))
print('[7] BCD +4(ncb)=%s' % fmt(g4))
print('[7] BCD +8(mdisp) distinct=%d top=%s' % (len(g8), fmt(g8, top=8)))
print('[7] BCD +12(pdisp)=%s' % fmt(g12))
print('[7] BCD +16(vdisp)=%s' % fmt(g16))
print('[7] BCD +20(attributes)=%s' % fmt(g20))

report['sha256'] = {
    'gamemd.exe': hashlib.sha256(P.RAW).hexdigest(),
}
with open(JSON_PATH, 'w') as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print('JSON written:', JSON_PATH)
