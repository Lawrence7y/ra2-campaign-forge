#!/usr/bin/env python3
"""R169 D（v2）：反向索引跳转表 + 0x7d0cba 的邻域归属定死。

R168 的 span 只往 +4 单向延展 ⇒ 「neg ecx 之后 jmp [ecx*4+base]」这类**反向索引**表被判成不成表。
v1 的「步长恒定」判据把基准槽（默认槽）也当成 case 条目，导致 2 条目假截断（S-556）。
v2 判据：先按「落 .text」loose 反向延展，取相邻 |diff| 的**众数 d** 作为 case 步长，
        case 条目 = 从 vals[1] 起连续 |diff| == d 的最长链；vals[0]（基准槽）另记为默认槽。
        只有当众数出现 >= 3 次时才承认这是一张表（否则退回「不成表」）。

断言：
  E1  |S| == 1,392,527
  E2  反向表 0x7d0cb0：基准槽值 0x7d0cf7、case 步长 8、case 条目 7、含基准槽共 8 条、区间 [0x7d0c94, 0x7d0cb4)
  E3  孪生表 0x7ca320 同构：区间 [0x7ca304, 0x7ca324)、步长 8、7 条 + 基准槽
  E4  loose 反向延展的第 9 槽（0x7d0c90 / 0x7ca300）值是 0x00498d00，其槽字节跨指令边界
      （lea ecx,[ecx] 从奇数地址起），不是条目；剔除后 loose_n 9 -> 8
  E5  正向口径：从基准槽 +4 延展只有 1 条（0x7d0cb4 处值不落 .text）
      ⇒ R168「0x7d0cb0 处有真 4 字节跳转表」只在**反向口径**成立，正向口径下就是 1 条；
         R168 原文「首槽 0x007d0cf7」正确但未说表在基准槽之前
  E6  65 洞中落在两反向表区间内的条数（逐条列出，预期 0：洞都落在表**之后**的代码里）
  E7  0x7d0cba 的归属：从表条目 0x7d0cb4 起连续解码，0x7d0cba 落在第二条指令 0x7d0cb8（4 B）内部偏移 2
      ⇒ 它是**真代码**里 `mov [edi+ecx*4+0x1c], eax` 的中间字节，属于 case 0x7d0cb4 的拷贝体
  E8  反控：同法对随机 2000 个 .text 地址做反向 loose 延展，统计 loose_n>=8 的比例（基线）
  E9  反控：把站点 0x7d0be2 / 0x7ca252 的 neg ecx 证据固定（前 3 条指令内出现 neg）
  E10 双向口径表数 = 360（R168 的 358 + 这 2 张）
"""
import sys, json, struct, random, collections
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = B.IB + text[1]; T_HI = T_LO + text[2]

starts = {}
off = text[3]; end = text[3] + text[4]; base_vs = text[1]
while off < end:
    c = B.data[off:min(off + 65536, end)]
    base = B.IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(c, base):
        if a - base + sz > len(c): break
        consumed = a - base + sz
        if a < T_HI: starts[a] = sz
    off += consumed if consumed else 1

def span_loose(base, step, maxent=8192):
    n = 0; vals = []
    while n < maxent:
        v = B.dw(base + step * n)
        if v is None or not (T_LO <= v < T_HI): break
        vals.append(v); n += 1
    return n, vals

def table_backward(base):
    """返回 dict：base 槽值、case 步长、case 条目值、区间、loose 全量、被剔除的尾巴。"""
    n, vals = span_loose(base, -4)
    if n < 3:
        return {'is_table': False, 'loose_n': n, 'vals': [hex(v) for v in vals]}
    diffs = [abs(vals[k + 1] - vals[k]) for k in range(n - 1)]
    d, cnt = collections.Counter(diffs).most_common(1)[0]
    if cnt < 3:
        return {'is_table': False, 'loose_n': n, 'vals': [hex(v) for v in vals]}
    k = 1
    while k < n - 1 and abs(vals[k + 1] - vals[k]) == d:
        k += 1
    cases = vals[1:k + 1]
    tail = vals[k + 1:]
    lo = base - 4 * (len(cases))
    return {'is_table': True, 'base_slot': hex(base), 'base_val': hex(vals[0]),
            'stride': d, 'stride_hits': cnt, 'case_vals': [hex(v) for v in cases],
            'n_total': 1 + len(cases), 'slot_lo': hex(lo), 'slot_hi': hex(base + 4),
            'region': [hex(lo), hex(base + 4)], 'loose_n': n,
            'loose_vals': [hex(v) for v in vals], 'excluded_tail': [hex(v) for v in tail]}

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('E1 |S| == 1,392,527', len(starts) == 1392527, len(starts))

TB = table_backward(0x7d0cb0)
TA = table_backward(0x7ca320)
chk('E2 0x7d0cb0 反向表：基准 0x7d0cf7 + 7 条步长 8 + 区间 [0x7d0c94,0x7d0cb4)',
    TB.get('is_table') and TB['base_val'] == '0x7d0cf7' and TB['stride'] == 8
    and len(TB['case_vals']) == 7 and TB['n_total'] == 8 and TB['region'] == ['0x7d0c94', '0x7d0cb4'],
    {k: TB[k] for k in ('base_val', 'stride', 'n_total', 'region', 'case_vals')})
chk('E3 孪生表 0x7ca320 同构：区间 [0x7ca304,0x7ca324)、7 条 + 基准槽',
    TA.get('is_table') and TA['base_val'] == '0x7ca367' and TA['stride'] == 8
    and len(TA['case_vals']) == 7 and TA['n_total'] == 8 and TA['region'] == ['0x7ca304', '0x7ca324'],
    {k: TA[k] for k in ('base_val', 'stride', 'n_total', 'region')})

# E4: 第 9 槽跨指令边界
e4 = {}
for base, slot in ((0x7d0cb0, 0x7d0c90), (0x7ca320, 0x7ca300)):
    raw = B.rd(slot, 4)
    # 找到该槽内包含的指令边界
    bounds = [s for s in starts if slot <= s < slot + 4]
    e4[hex(slot)] = {'raw': raw.hex(' '), 'dword': hex(B.dw(slot)),
                     'insn_bounds_in_slot': [hex(x) for x in bounds]}
chk('E4 第 9 槽 0x7d0c90/0x7ca300 值 0x00498d00 跨指令边界（非条目），剔除后 loose 9->8',
    all(v['dword'] == '0x498d00' and len(v['insn_bounds_in_slot']) >= 1 for v in e4.values())
    and TB['loose_n'] == 9 and TB['n_total'] == 8 and TB['excluded_tail'] == ['0x498d00'],
    e4)

fwd_n, fwd_v = span_loose(0x7d0cb0, 4)
chk('E5 正向口径 base 处只有 1 条（R168「真 4 字节表」只在反向口径成立）',
    fwd_n == 1 and fwd_v == [0x7d0cf7] and TB['n_total'] == 8,
    {'fwd_n': fwd_n, 'fwd_vals': [hex(x) for x in fwd_v], 'bwd_total': TB['n_total']})

r167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in r167['holes']]
def inr(v, reg):
    return int(reg[0], 16) <= v < int(reg[1], 16)
inrev = [{'hole': hex(h), 'table': t} for h in holes for t, r in (('0x7d0cb0', TB), ('0x7ca320', TA)) if inr(h, r['region'])]
near = [{'hole': hex(h), 'table': t} for h in holes for t, r in (('0x7d0cb0', TB), ('0x7ca320', TA))
        if not inr(h, r['region']) and int(r['region'][1], 16) <= h < int(r['region'][1], 16) + 0x40]
chk('E6 落在两反向表区间内的洞数（预期 0）', len(inrev) == 0, {'in_region': inrev, 'within_0x40_after': near})

# E7: 0x7d0cba 的归属
H = 0x7d0cba
chain = []; cur = 0x7d0cb4
while cur < 0x7d0cfe:
    o = B.va2off(cur)
    ii = list(md.disasm(B.data[o:o + 16], cur, count=1))
    if not ii: break
    i = ii[0]
    chain.append({'va': hex(cur), 'sz': i.size, 'mn': i.mnemonic, 'op': i.op_str})
    cur += i.size
hit = [c for c in chain if int(c['va'], 16) <= H < int(c['va'], 16) + c['sz']]
lin_cov = [(s, starts[s]) for s in starts if s <= H < s + starts[s]]
chk('E7 0x7d0cba 落在真指令 0x7d0cb8（4 B，mov [edi+ecx*4+0x1c], eax）内部偏移 2',
    len(hit) == 1 and hit[0]['va'] == '0x7d0cb8' and hit[0]['sz'] == 4,
    {'hit': hit, 'linear_cov': [(hex(s), z) for s, z in lin_cov],
     'entry_owner': '0x7d0cb4（表条目，case 拷贝体起点）'})

rnd = random.Random(169)
ge8 = 0; N = 2000
for _ in range(N):
    a = rnd.randrange(T_LO + 0x40, T_HI - 8) & ~3
    n, _ = span_loose(a, -4)
    if n >= 8: ge8 += 1
chk('E8 随机 2000 个地址反向 loose>=8 的基线', True, {'ge8': ge8, 'of': N, 'pct': round(100.0 * ge8 / N, 3)})

negok = {}
for site in (0x7d0be2, 0x7ca252):
    o = B.va2off(site - 12)
    pre = [(hex(i.address), i.mnemonic, i.op_str) for i in md.disasm(B.data[o:o + 12], site - 12)]
    negok[hex(site)] = {'pre': pre, 'has_neg': any(p[1] == 'neg' for p in pre)}
chk('E9 两站点前 12 B 内都有 neg ecx（反向索引证据）',
    all(v['has_neg'] for v in negok.values()), negok)

# E10: 双向口径表数
sites = []
for op2 in (0x24, 0x14):
    for m in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, m]); i = 0
        while True:
            j = B.data.find(pat, i)
            if j < 0: break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]): continue
            sites.append(struct.unpack_from('<I', B.data, j + 3)[0])
for m in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, m, 0x8d]); i = 0
    while True:
        j = B.data.find(pat, i)
        if j < 0: break
        i = j + 1
        if not (text[3] <= j < text[3] + text[4]): continue
        sites.append(struct.unpack_from('<I', B.data, j + 3)[0])
fwd = set(); both = set()
for tab in sites:
    nf, _ = span_loose(tab, 4)
    tb = table_backward(tab)
    if nf >= 2: fwd.add(tab)
    if nf >= 2 or (tb.get('is_table') and tb['n_total'] >= 2): both.add(tab)
chk('E10 正向 358 表 / 双向 360 表', len(fwd) == 358 and len(both) == 360,
    {'fwd': len(fwd), 'both': len(both), 'extra': [hex(x) for x in sorted(both - fwd)]})

out = {'starts': len(starts), 'table_7d0cb0': TB, 'table_7ca320': TA,
       'holes_in_region': inrev, 'holes_within_0x40_after': near,
       'hole_7d0cba': {'chain_from_entry_0x7d0cb4': chain, 'inside': hit, 'linear_cov': [(hex(s), z) for s, z in lin_cov]},
       'random_back_le8': {'ge8': ge8, 'of': N}, 'neg_evidence': negok,
       'tables_fwd': len(fwd), 'tables_both': len(both),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r169/r169d_rebuck.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:300])
print('FAIL count =', out['fail'])
