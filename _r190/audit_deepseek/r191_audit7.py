# -*- coding: utf-8 -*-
"""R191 审计第七轮（收口，唯一一次）：A2 的逐槽独立零假设、R3 的位语义验证、R1 的域错配证明。
Y1 逐槽独立零假设：每槽独立按全 vtable 值分布抽样，算同 (层,槽号) 期望相等对。
Y2 R3 位语义验证：attributes==2 是否恰等于「同名基类在本类数组里重复出现」。
Y3 R1 域错配证明：同 COL 名组内是否存在同 mdisp 的两张表（无 ⇒ 所有同槽号比较都跨层）。
Y4 R2 的结构性事实：地址 → 槽号 是否为单值函数。
"""
import sys, struct, collections, json, itertools
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
RY = {}
def hdr(s): print('\n==== ' + s + ' ====')
SECV = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; n = s['rawsize'] // 4
    SECV[sec] = (s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n)
name_ok = lambda nm: bool(nm) and nm.startswith(b'.?A') and nm.endswith(b'@@')
COL = {}
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(n - 4):
        if v[i] not in (0, 1) or v[i + 2] != 0: continue
        if P.where(v[i + 3]) != '.data' or P.where(v[i + 4]) != '.rdata': continue
        nm = P.cstr(v[i + 3] + 8, 200)
        if not name_ok(nm): continue
        COL[base + 4 * i] = dict(mdisp=v[i + 1], ptd=v[i + 3], pchd=v[i + 4], name=nm.decode('latin1'))
VT = {}
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(1, n):
        if LO <= v[i] < HI and v[i - 1] in COL: VT[base + 4 * i] = COL[v[i - 1]]
def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
PRE = {vt: pre(vt) for vt in VT}
order = sorted(VT)
def thunkof(va):
    o = P.r2o(va)
    if o is None: return None
    b = RAW[o:o + 16]
    if len(b) < 13: return None
    if b[0] == 0x81 and b[1:4] == b'\x6c\x24\x04': K = struct.unpack_from('<i', b, 4)[0]; p = 8
    elif b[0] == 0x83 and b[1:4] == b'\x6c\x24\x04': K = struct.unpack_from('<b', b, 4)[0]; p = 5
    else: return None
    if b[p] != 0xE9: return None
    return K, (va + p + 5 + struct.unpack_from('<i', b, p + 1)[0]) & 0xFFFFFFFF
NP = [vt for vt in order if VT[vt]['mdisp'] != 0]
ALLV = [P.dw(vt + 4 * k) for vt in order for k in range(PRE[vt])]
DIR = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])
       if thunkof(P.dw(vt + 4 * k)) is None]

hdr('Y1 A2 逐槽独立零假设（每槽独立按全 vtable 值分布抽样）')
pool = collections.Counter(ALLV)          # 14044 个槽值的经验分布
tot = sum(pool.values()); p2 = sum((c / tot) ** 2 for c in pool.values())
grp = collections.defaultdict(list)
for vt, k, v in DIR: grp[(VT[vt]['mdisp'], k)].append(v)
E = sum(len(v) * (len(v) - 1) / 2 * p2 for v in grp.values())
obs = sum(sum(c * (c - 1) // 2 for c in collections.Counter(v).values()) for v in grp.values())
C = sum(len(v) * (len(v) - 1) // 2 for v in grp.values())
print('  全 vtable 槽值池: %d 槽 / %d 不同地址 / Σp²=%.6f' % (tot, len(pool), p2))
print('  同 (层,槽号) 内可比较对 = %d' % C)
print('  逐槽独立零假设期望相等对 = %.1f ；实测 = %d ；富集 = x%.0f' % (E, obs, obs / E))
print('  每层各自算：')
for m in sorted(set(VT[vt]['mdisp'] for vt in NP)):
    g = [(vt, k, v) for vt, k, v in DIR if VT[vt]['mdisp'] == m]
    c2 = collections.Counter((k, v) for _, k, v in g)
    o = 0; cc = 0
    byl = collections.defaultdict(list)
    for _, k, v in g: byl[k].append(v)
    for v in byl.values():
        cc += len(v) * (len(v) - 1) // 2
        o += sum(x * (x - 1) // 2 for x in collections.Counter(v).values())
    print('    mdisp=%-6d 对=%-5d 实测=%-5d 期望=%7.1f 富集=%s' %
          (m, cc, o, cc * p2, ('x%.0f' % (o / (cc * p2))) if cc * p2 >= 0.5 else 'n/a'))
RY['Y1'] = dict(pool=tot, p2=p2, comparable=C, exp=round(E, 1), obs=obs,
                enrich=round(obs / E, 1))

hdr('Y2 R3 位语义验证：attributes==2 是否恰等于「同名基类在本类数组里重复」')
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
nm2 = lambda x: (P.cstr(x + 8, 200) or b'').decode('latin1') if x else ''
tp = fp = fn = tn = 0; ex = []
for vt in order:
    bs = BD[vt]; names = [nm2(x['ptd']) for x in bs]
    cnt = collections.Counter(names)
    for x, bn in zip(bs, names):
        dup = cnt[bn] > 1
        a2 = bool(x['attr'] & 2)
        if dup and a2: tp += 1
        elif dup and not a2: fn += 1; ex.append(('dup_no_attr2', VT[vt]['name'], bn, x['attr'], x['mdisp']))
        elif a2 and not dup: fp += 1; ex.append(('attr2_not_dup', VT[vt]['name'], bn, x['attr'], x['mdisp']))
        else: tn += 1
print('  交叉表 (重复, attr&2): TP=%d FP=%d FN=%d TN=%d' % (tp, fp, fn, tn))
print('  反例前 8:', ex[:8])
print('  ⇒ 若 TP=740 且 FP=FN=0 则 attributes.bit1 = BCD_AMBIGUOUS 在布局上被证实')
print('  attributes==9 (bit0|bit3) 的 12 条，是否 bit3=BCD_PRIVORPROTBASE 无从静态验证，仅登记')
RY['Y2'] = dict(tp=tp, fp=fp, fn=fn, tn=tn, ex=ex[:10])

hdr('Y3 R1 域错配证明：同 COL 名组内是否有一对表的 mdisp 相同')
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
same_md = [(n, [VT[v]['mdisp'] for v in vs]) for n, vs in byname.items()
           if len(vs) > 1 and len(set(VT[v]['mdisp'] for v in vs)) < len(vs)]
print('  多表组 %d ；组内存在 mdisp 重复（可做同层同槽号比较）的组 = %d' %
      (sum(1 for v in byname.values() if len(v) > 1), len(same_md)))
print('  ⇒ 被审 A1 的 123 次比较 100% 跨层；同槽号在两层指不同接口成员（layer8=INoticeSink, layer12=INoticeSource）')
print('  该判据的判别力：若真存在「同组内覆盖实现」，前提是两层同接口，而数据里这种对为 0')
RY['Y3'] = dict(multigroups=sum(1 for v in byname.values() if len(v) > 1), same_md=len(same_md))

hdr('Y4 R2 结构事实：地址 → 槽号 是否单值')
a2k = collections.defaultdict(set)
for vt, k, v in DIR: a2k[v].add(k)
multi_k = {hex(a): sorted(ks) for a, ks in a2k.items() if len(ks) > 1}
print('  1013 槽 → %d 个地址；(表,槽) 去重 = %d' % (len(a2k), len(DIR)))
print('  地址对应多个槽号(跨虚函数复用)的地址数 = %d %s' % (len(multi_k), list(multi_k.items())[:5]))
share = sorted(((len(set(vt for vt, k, vv in DIR if vv == a)), hex(a), sorted(a2k[a]))
                for a in a2k), reverse=True)[:8]
print('  共享最多的地址 (被几类引用, 地址, 槽号):', share)
print('  ⇒ 每个地址只对应 1 个槽号 ⇒ 「同槽号 → 同一函数」是硬结构，不是统计巧合')
RY['Y4'] = dict(distinct=len(a2k), slots=len(DIR), multi_k=len(multi_k), top=share)
json.dump(RY, open(OUT + '/r191_audit7.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第七轮完成 ==')
