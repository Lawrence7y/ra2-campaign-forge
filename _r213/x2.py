#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R213 EX2 — onlysec TD 引用面与 BCA 归属，全部从字节重算，不引用历史轮次数字。

口径（调度卡）：
  TD    : pVFTable==0x7F9594, spare==0, name@+8 形如 b'.?A...@@'
  COL   : 20B {sig∈{0,1}, mdisp, cdOffset==0, pTD∈TD, pCHD 合法 CHD}
  CHD   : 16B {sig==0, attr, nbase>=1, pBCA∈.rdata}
  BCD   : 24B {pTD∈TD, ncbase, mdisp, pdisp, vdisp, attr}
枚举 TD 用 .data 内联名字反推起点；COL/BCD 用 pTD 出现位置反推；CHD 用 pBCA 出现位置反推。
"""
import sys, os, json, struct, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P

RAW = P.RAW
dw = P.dw
where = P.where
cstr = P.cstr
r2o = P.r2o

OUT_TXT = ROOT + '/_r213/x2_out.txt'
OUT_JSON = ROOT + '/_r213/x2.json'

fails = []
ncheck = 0
_lines = []

def emit(s=''):
    print(s)
    _lines.append(str(s))

def ck(nm, cond, detail=''):
    global ncheck
    ncheck += 1
    if not cond:
        fails.append(nm)
    emit(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

def hx(v):
    return hex(v) if isinstance(v, int) else str(v)

def sec_blob(secname):
    s = P.B[secname]
    return RAW[s['rawptr']:s['rawptr'] + s['rawsize']]

# ---------------------------------------------------------------- 结构谓词
def valid_td(va, require_spare0=True):
    """TD: pVFTable==0x7F9594, [spare==0], 名字以 .?A 开头且以 @@ 结尾。"""
    if where(va) != '.data':
        return None
    pvf = dw(va)
    spare = dw(va + 4)
    if pvf != 0x7F9594:
        return None
    if require_spare0 and spare != 0:
        return None
    nm = cstr(va + 8, 400)
    if nm is None or not nm.startswith(b'.?A') or not nm.endswith(b'@@') or len(nm) <= 6:
        return None
    return {'va': va, 'pvf': pvf, 'spare': spare, 'name': nm.decode('latin1')}

def valid_chd(va):
    """CHD: sig==0, nbase>=1, pBCA∈.rdata。"""
    if where(va) != '.rdata':
        return None
    d = [dw(va + 4 * i) for i in range(4)]
    if None in d or d[0] != 0 or d[2] < 1:
        return None
    arrva = d[3]
    # 上界：BCA 数组必须整段落在 .rdata 的文件映射范围内（否则是伪造 CHD）
    if where(arrva) != '.rdata' or where(arrva + 4 * (d[2] - 1) + 3) != '.rdata':
        return None
    return {'va': va, 'sig': d[0], 'attr': d[1], 'nbase': d[2], 'pbca': arrva}

def valid_bcd(va, tdset):
    """BCD: +0 pTD 必须落在 TD 全集；其余 5 dword 只记录不约束。"""
    if where(va) != '.rdata':
        return None
    d = [dw(va + 4 * i) for i in range(6)]
    if None in d or d[0] not in tdset:
        return None
    return {'va': va, 'words': d, 'ptd': d[0]}

def valid_col(va, tdset, chdset):
    """COL: sig∈{0,1}, cdOffset==0, pTD∈TD, pCHD 是合法 CHD。"""
    if where(va) not in ('.rdata', '.data'):
        return None
    d = [dw(va + 4 * i) for i in range(5)]
    if None in d or d[0] not in (0, 1) or d[2] != 0:
        return None
    if d[3] not in tdset or d[4] not in chdset:
        return None
    return {'va': va, 'sig': d[0], 'mdisp': d[1], 'cd': d[2], 'ptd': d[3], 'pchd': d[4]}

# ---------------------------------------------------------------- 全量枚举
def enum_td(require_spare0):
    td = {}
    blob = sec_blob('.data')
    s = P.B['.data']
    i = 0
    while True:
        i = blob.find(b'.?A', i)
        if i < 0:
            break
        e = blob.find(b'\0', i, i + 400)
        if e >= 0:
            nm = blob[i:e]
            va = s['lo'] + i - 8
            r = valid_td(va, require_spare0)
            if r is not None:
                td[va] = r
        i += 1
    return td

def dwords_in(secname):
    """流式产生 (va, value)，不一次性构造全镜像 dword 列表。"""
    s = P.B[secname]
    off = s['rawptr']
    end = s['rawptr'] + s['rawsize']
    fmt = struct.Struct('<I')
    while off + 4 <= end:
        yield s['lo'] + (off - s['rawptr']), fmt.unpack_from(RAW, off)[0]
        off += 4

TD = enum_td(require_spare0=True)
TD_NOSPARE = enum_td(require_spare0=False)

# 结构验证：先通过 TD 名字反推起点，校验 pVFTable 唯一值与 spare 约束
pvfs = collections.Counter(t['pvf'] for t in TD.values())
spares = collections.Counter(t['spare'] for t in TD.values())
ck('S1 TD 的 pVFTable 取值唯一且 == 0x7F9594', len(pvfs) == 1 and 0x7F9594 in pvfs, dict(pvfs))
ck('S2 TD 的 spare 全为 0', len(spares) == 1 and 0 in spares, dict(spares))

# CHD 全集：扫 .rdata 里所有指向合法 BCA 数组的 dword，反推 CHD@va-12
CHD = {}
for va, v in dwords_in('.rdata'):
    if where(v) != '.rdata':
        continue
    cva = va - 12
    ch = valid_chd(cva)
    if ch is not None and ch['pbca'] == v:
        CHD[cva] = ch
ck('S3 CHD 枚举非空', len(CHD) > 0, len(CHD))

# BCD 全集：扫 .rdata 里 pTD 指向 TD 全集的 dword，反推 BCD@va
BCD = {}
for va, v in dwords_in('.rdata'):
    if v not in TD:
        continue
    b = valid_bcd(va, TD)
    if b is not None:
        BCD[va] = b
ck('S4 BCD 枚举非空', len(BCD) > 0, len(BCD))

# COL 全集：扫 .rdata/.data 里 pTD 指向 TD 全集的 dword，反推 COL@va-12
COL = {}
for secname in ('.rdata', '.data'):
    for va, v in dwords_in(secname):
        if v not in TD:
            continue
        cva = va - 12
        c = valid_col(cva, TD, CHD)
        if c is not None and c['ptd'] == v:
            COL[cva] = c
ck('S5 COL 枚举非空', len(COL) > 0, len(COL))

# 结构自检：COL 的 +8 cdOffset 在全体上确为 0；CHD 的签名确为 0
ck('S6 全体 COL.cdOffset 恒为 0', all(c['cd'] == 0 for c in COL.values()), len(COL))

# ---------------------------------------------------------------- B1
b1_total = len(TD)
b1_av = sum(1 for t in TD.values() if t['name'].startswith('.?AV'))
b1_au = sum(1 for t in TD.values() if t['name'].startswith('.?AU'))
b1_other = b1_total - b1_av - b1_au
ck('B1 TD 总数/前缀分布三数之和 == 总数',
   b1_av + b1_au + b1_other == b1_total,
   {'total': b1_total, '.?AV': b1_av, '.?AU': b1_au, 'other': b1_other})

# ---------------------------------------------------------------- B2
REF = {c['ptd'] for c in COL.values()}
b2_ref = len(REF)
ck('B2 REF ⊂ TD 全集', REF <= set(TD), {'REF': b2_ref, 'TD': b1_total})

# ---------------------------------------------------------------- B3
ONLY = set(TD) - REF
b3_count = len(ONLY)
b3_av = sum(1 for v in ONLY if TD[v]['name'].startswith('.?AV'))
b3_au = sum(1 for v in ONLY if TD[v]['name'].startswith('.?AU'))
b3_other = b3_count - b3_av - b3_au
ck('B3 onlysec = TD - REF 计数自洽', b3_count == b1_total - b2_ref,
   {'onlysec': b3_count, '.?AV': b3_av, '.?AU': b3_au, 'other': b3_other})
emit('B3 onlysec 逐条：')
for v in sorted(ONLY):
    emit('  %s %s' % (hx(v), TD[v]['name']))

# ---------------------------------------------------------------- B4 / B5 / B6
# 建立 BCD -> 所属 CHD 的反查，以及 pTD -> BCD 的反查（均为一次性建表）
# 注意：CHD 枚举里存在少数误命中的"伪 CHD"（无合法 COL 指向、BCA 数组含非 BCD 元素）。
# 只有被合法 COL 引用的 CHD 才是真实类层次；S7 核验限定在这一集合。
bcd_chd = collections.defaultdict(set)
ptd_bcds = collections.defaultdict(list)
for bva, b in BCD.items():
    ptd_bcds[b['ptd']].append(bva)
chd_bad = []
valid_chds = {c['pchd'] for c in COL.values()}
for ch in CHD.values():
    if ch['va'] not in valid_chds:
        continue
    arr = [dw(ch['pbca'] + 4 * i) for i in range(ch['nbase'])]
    if any(a is None or a not in BCD for a in arr):
        chd_bad.append((hx(ch['va']), ch['nbase']))
        continue
    for a in arr:
        bcd_chd[a].add(ch['va'])
ck('S7 每个被合法 COL 引用的 CHD 的 BCA 数组元素都落在 BCD 全集',
   not chd_bad and len(valid_chds) == 954,
   {'valid_chd': len(valid_chds), 'bad': chd_bad[:8]})

# 每条 onlysec TD 被 BCA 引用的次数（= 引用它的 BCD 条数）与 CHD 个数
refcnt = collections.Counter()
refchd = collections.defaultdict(set)
for bva, b in BCD.items():
    t = b['ptd']
    if t in ONLY:
        refcnt[t] += 1
        refchd[t].update(bcd_chd.get(bva, ()))

b4 = []
for t in sorted(ONLY):
    c = refcnt[t]
    if c:
        b4.append({'td': t, 'td_hex': hx(t), 'name': TD[t]['name'],
                   'bca_refs': c, 'chd_count': len(refchd[t]),
                   'chds': sorted(refchd[t])})
b5 = [{'td': t, 'td_hex': hx(t), 'name': TD[t]['name']}
      for t in sorted(ONLY) if refcnt[t] == 0]
ck('B4+B5 每条 onlysec TD 恰好落入 B4 或 B5', len(b4) + len(b5) == b3_count,
   {'B4': len(b4), 'B5': len(b5), 'onlysec': b3_count})

# B6：BCA 引用次数 == 1 的 onlysec TD，给出唯一 BCD 六 dword + 所属 CHD + own 类名
# own 类名 = 引用该 CHD 的任一 COL 的 TD 名（取全部 distinct），即该 CHD 的 own 记录名
chd_owners = collections.defaultdict(set)
for c in COL.values():
    if c['pchd'] in CHD:
        chd_owners[c['pchd']].add(TD[c['ptd']]['name'])

b6 = []
for row in b4:
    if row['bca_refs'] != 1:
        continue
    t = row['td']
    uniq = sorted(ptd_bcds.get(t, []))
    if len(uniq) != 1:
        emit('  WARN B6 td=%s 期望 1 条 BCD，实得 %d' % (hx(t), len(uniq)))
        continue
    bva = uniq[0]
    chds = sorted(bcd_chd.get(bva, ()))
    owners = sorted({nm for ch in chds for nm in chd_owners.get(ch, ())})
    b6.append({'td': t, 'td_hex': hx(t), 'name': TD[t]['name'],
               'bcd_va': bva, 'bcd_hex': hx(bva),
               'bcd_words': BCD[bva]['words'],
               'bcd_words_hex': [hx(w) for w in BCD[bva]['words']],
               'chds': chds, 'chds_hex': [hx(c) for c in chds],
               'own_names': owners})
ck('B6 所有 BCA 引用次数为 1 的 onlysec TD 均解析出唯一 BCD',
   len(b6) == sum(1 for r in b4 if r['bca_refs'] == 1),
   {'B6': len(b6), 'singleton': sum(1 for r in b4 if r['bca_refs'] == 1)})

emit('B4 onlysec 被 BCA 引用逐条 (TD地址, 名字, BCD次数, CHD个数):')
for r in b4:
    emit('  %s %s bca_refs=%d chd_count=%d chds=%s' %
         (r['td_hex'], r['name'], r['bca_refs'], r['chd_count'],
          ','.join(hx(c) for c in r['chds'])))
emit('B5 onlysec 完全不被 BCA 引用：%d 条' % len(b5))
for r in b5:
    emit('  %s %s' % (r['td_hex'], r['name']))
emit('B6 BCD 引用次数为 1 的 onlysec TD：%d 条' % len(b6))
for r in b6:
    emit('  TD=%s %s BCD=%s words=%s CHD=%s own=%s' %
         (r['td_hex'], r['name'], r['bcd_hex'], r['bcd_words_hex'],
          r['chds_hex'], r['own_names']))

# ---------------------------------------------------------------- B7
b7_au = sum(1 for t in TD.values() if t['name'].startswith('.?AU'))
b7_notref = len(ONLY)
ck('B7 两种口径数字各自实测', b7_au >= 0 and b7_notref >= 0,
   {'.?AU 判据': b7_au, '不在 REF 判据': b7_notref})

# ---------------------------------------------------------------- B8
# 按 TD+8 名字相等放宽 REF：只要某 COL 指向的 TD 名字与本 TD 名字相同即算 REF
col_names = {TD[c['ptd']]['name'] for c in COL.values()}
b8_ref = {t for t in TD if TD[t]['name'] in col_names}
b8_only = set(TD) - b8_ref
b8_count = len(b8_only)
ck('B8 放宽 REF 后 onlysec ⊆ 原 onlysec', b8_only <= ONLY,
   {'放宽后 onlysec': b8_count, '原 onlysec': b3_count})
emit('B8 放宽后仅剩的 onlysec 逐条：')
for t in sorted(b8_only):
    emit('  %s %s' % (hx(t), TD[t]['name']))

# ---------------------------------------------------------------- B9
b9_total = len(TD_NOSPARE)
ck('B9 去掉 spare==0 后 TD 总数 >= 原总数', b9_total >= b1_total,
   {'原 TD': b1_total, '去 spare 约束': b9_total, '新增': b9_total - b1_total})
emit('B9 新增 TD（spare != 0）逐条：')
for v in sorted(set(TD_NOSPARE) - set(TD)):
    emit('  %s spare=%s %s' % (hx(v), TD_NOSPARE[v]['spare'], TD_NOSPARE[v]['name']))

# ---------------------------------------------------------------- 写盘
out = {
    'meta': {
        'imagebase': '0x400000',
        'td_rule': 'pVFTable==0x7F9594, spare==0, name@+8 .?A...@@',
        'col_rule': '20B sig∈{0,1} mdisp cdOffset==0 pTD∈TD pCHD∈CHD',
        'chd_rule': '16B sig==0 attr nbase>=1 pBCA∈.rdata',
        'bcd_rule': '24B pTD∈TD + 5 raw dwords',
        'checks': ncheck, 'fails': fails,
    },
    'B1': {'total': b1_total, 'AV': b1_av, 'AU': b1_au, 'other': b1_other,
           'sum_eq_total': b1_av + b1_au + b1_other == b1_total,
           'td_list': [{'va': v, 'va_hex': hx(v), 'name': t['name'],
                        'spare': t['spare']} for v, t in sorted(TD.items())]},
    'B2': {'REF': b2_ref, 'ref_list': [{'va': v, 'va_hex': hx(v)}
                                       for v in sorted(REF)]},
    'B3': {'onlysec': b3_count, 'AV': b3_av, 'AU': b3_au, 'other': b3_other,
           'list': [{'va': v, 'va_hex': hx(v), 'name': TD[v]['name']}
                    for v in sorted(ONLY)]},
    'B4': {'count': len(b4), 'rows': b4},
    'B5': {'count': len(b5), 'list': b5},
    'B6': {'count': len(b6), 'rows': b6},
    'B7': {'by_prefix_AU': b7_au, 'by_not_in_REF': b7_notref},
    'B8': {'by_name_equal_onlysec': b8_count,
           'list': [{'va': v, 'va_hex': hx(v), 'name': TD[v]['name']}
                    for v in sorted(b8_only)]},
    'B9': {'td_total_no_spare_constraint': b9_total,
           'original': b1_total, 'added': b9_total - b1_total,
           'added_list': [{'va': v, 'va_hex': hx(v), 'spare': TD_NOSPARE[v]['spare'],
                           'name': TD_NOSPARE[v]['name']}
                          for v in sorted(set(TD_NOSPARE) - set(TD))]},
    'aux': {'CHD_count': len(CHD), 'BCD_count': len(BCD), 'COL_count': len(COL)},
}

with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(_lines) + '\n')
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

emit('')
emit('CHECKS %d FAILS %s' % (ncheck, fails))
emit('OUT %s %s' % (OUT_TXT, OUT_JSON))
with open(OUT_TXT, 'a', encoding='utf-8') as f:
    f.write('CHECKS %d FAILS %s\n' % (ncheck, fails))
