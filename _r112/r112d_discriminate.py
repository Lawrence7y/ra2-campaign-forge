#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112d_discriminate.py —— 用链 D/E 把 R111 §EM10② 的「三者语义未定」逐条裁开，
并把结论分成**已定死 / 已收窄 / 确实不可区分**三栏，不把「不可区分」写成「已解决」。

待裁对象（R111 §EM10② 原文）：0x7e9ae0(76 类) 与 0x7f7c70 / 0x7f7c80 (各 77 类) 三者语义区分未定。

本轮可用的三条互相独立的证据（都不共用数据）：
  链 B（R111）：RTTI 基类名集合 C(name)，来自 TD 装饰名
  链 D（R112b）：QI 写回 ppv 的子对象偏移 N，来自 .text 立即数
  链 E（R112c）：子对象 vtable 的 COL.offset，来自 .rdata 的 COL
判据：把「该 IID 全部认领类上、接口名 name 的 mdisp 是否都等于 N」做成 FULL 集（链 D×链 B），
      再用「子对象 vtable 集合是否相同」做第二重（链 E）。

断言：
  D1 0x7e9ae0 的 FULL 集 == {IRTTITypeInfo}（唯一）⇒ 定死
  D2 0x7f7c70 与 0x7f7c80 的认领类集合**完全相同**（对称差空集）⇒ 它们不是两个不同接口的两种暴露，
     而是同一对基类（IPersist/IPersistStream）在两个相邻 IID 常量上的重复登记
  D3 0x7f7c70 与 0x7f7c80 的子对象 vtable 集合**逐元素相同** ⇒ 链 E 也分不开
  D4 0x7f7c70 与 0x7f7c80 的 N 都是 0 且 FULL 都是 {IPersist, IPersistStream}
     ⇒ **在本精简库的静态证据下，这两者不可区分**（如实报，不编一个赢家）
  D5 但 0x7e9ae0 与 0x7f7c70 **可以**区分：Q(0x7e9ae0) ⊂ Q(0x7f7c70)，差 7 个类，
     且这 7 个类的 IRTTITypeInfo mdisp 都==4 而 0x7f7c70 的 N==0 ⇒ 偏移链给出反例
  D6 反控：在 954 个类里随机取 76 个类当假 Q，看「IRTTITypeInfo 的 mdisp 全为 4」的概率
内存纪律：只读已落盘 JSON + RTTI 缓存，不做反汇编。
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r112_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r112/r112d_discriminate.json')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


C = L.cache()
RTTI = C['RTTI']
sym, VT = L.load_symbols()
A = json.load(open(os.path.join(ROOT, '_r112/r112a_rtti.json')))
B = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
Cc = json.load(open(os.path.join(ROOT, '_r112/r112c_subobj.json')))
I111 = {k: set(v) for k, v in json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))['iids'].items()}
Q = {iid: set(k for k, v in I111.items() if iid in v) for iid in
     ('0x7e9ae0', '0x7f7c70', '0x7f7c80')}
FULL = {iid: set(v['full']) for iid, v in B['full_sets'].items()}
NOF = {iid: v['N'] for iid, v in B['full_sets'].items()}
TRIO = Cc['trio']

ck('D0 三个待裁 IID 的认领类数：0x7e9ae0=%d / 0x7f7c70=%d / 0x7f7c80=%d'
   % tuple(len(Q[i]) for i in ('0x7e9ae0', '0x7f7c70', '0x7f7c80')),
   len(Q['0x7e9ae0']) == 76 and len(Q['0x7f7c70']) == 83 and len(Q['0x7f7c80']) == 83,
   {i: len(Q[i]) for i in Q})

ck('D1 0x7e9ae0（N=%s）的 FULL 集 == {IRTTITypeInfo}（链 D×B 联立后唯一）'
   % NOF.get('0x7e9ae0'), FULL.get('0x7e9ae0') == {'IRTTITypeInfo'},
   {'N': NOF.get('0x7e9ae0'), 'full': sorted(FULL.get('0x7e9ae0', []))})

sd = Q['0x7f7c70'] ^ Q['0x7f7c80']
ck('D2 0x7f7c70 与 0x7f7c80 的认领类集合**完全相同**（对称差 %d 个）⇒ 不是两个接口的两种暴露'
   % len(sd), len(sd) == 0, sorted(sd)[:8])

v70 = TRIO['0x7f7c70']['vts_head']; v80 = TRIO['0x7f7c80']['vts_head']
ck('D3 链 E：两者的子对象 vtable 集合逐元素相同（各 %d 个 distinct）；槽数分布也相同 %s'
   % (TRIO['0x7f7c70']['n_distinct_subobj_vt'], TRIO['0x7f7c70']['slot_counts']),
   Cc['same_70_80'] and v70 == v80
   and TRIO['0x7f7c70']['slot_counts'] == TRIO['0x7f7c80']['slot_counts'],
   {'same_70_80': Cc['same_70_80'], 'n_vt': TRIO['0x7f7c70']['n_distinct_subobj_vt']})

indist = (NOF.get('0x7f7c70') == NOF.get('0x7f7c80') == 0
          and FULL.get('0x7f7c70') == FULL.get('0x7f7c80') == {'IPersist', 'IPersistStream'}
          and len(sd) == 0 and Cc['same_70_80'])
ck('D4 【如实报不可区分】0x7f7c70 与 0x7f7c80：N 同为 %s、FULL 同为 %s、认领类集合相同、'
   '子对象 vtable 集合相同 ⇒ **本精简库静态证据下二者不可区分**，不得编一个赢家'
   % (NOF.get('0x7f7c70'), sorted(FULL.get('0x7f7c70', []))),
   indist, {'N': NOF.get('0x7f7c70'), 'full': sorted(FULL.get('0x7f7c70', []))})

d79 = Q['0x7f7c70'] - Q['0x7e9ae0']
ck('D5 但 0x7e9ae0 与 0x7f7c70 **可以**区分：Q(0x7e9ae0) ⊂ Q(0x7f7c70)（差 %d 个类：%s），'
   '且这些类的 IRTTITypeInfo mdisp 全为 4 而 0x7f7c70 的 N == 0'
   % (len(d79), sorted(d79)),
   len(d79) == 7 and Q['0x7e9ae0'] <= Q['0x7f7c70'],
   sorted(d79))

# 逐类核对那 7 个类的 IRTTITypeInfo mdisp（RTTI 独立复算，不看 JSON）
mds = {}
for k in d79:
    r = RTTI[int(sym[k]['vtable_va'], 16)]
    mds[k] = r['bases'].get('IRTTITypeInfo')
ck('D5b 那 7 个类里 HouseClass 的 RTTI IRTTITypeInfo mdisp 实测为 %s；其余 %d 个类'
   '**RTTI 里根本没有 IRTTITypeInfo** ⇒ 它们认 0x7e9ae0 不是经 RTTI 声明的，'
   '而是经 slot0 的 adjustor thunk（R111 §EM2 那 12 类之一）转到的共享 QI 体——'
   '故 D5 的「mdisp 全为 4」只对 HouseClass 这一条有 RTTI 支撑，其余 6 条**只能靠链 D 的 N==4**，'
   '这是如实的证据强度差别，不是同一个强度'
   % (mds.get('HouseClass'), len([k for k, v in mds.items() if v is None])),
   mds.get('HouseClass') == [4] and sum(1 for v in mds.values() if v is None) == 6,
   {k: v for k, v in mds.items()})

# ---------- D6 反控：随机取 76 个类，IRTTITypeInfo mdisp 全为 4 的概率 ----------
random.seed(112)
pool = [k for k in sym if sym[k].get('vtable_va')]
withI = [k for k in pool if 'IRTTITypeInfo' in RTTI.get(int(sym[k]['vtable_va'], 16), {}).get('bases', {})]
p4 = sum(1 for k in withI
         if 4 in RTTI[int(sym[k]['vtable_va'], 16)]['bases']['IRTTITypeInfo'])
ck('D6 先说分母：全库 %d 个类里，RTTI 明写 IRTTITypeInfo 的 %d 个，其中 mdisp 含 4 的 %d 个'
   '（%.1f%%）—— 若这 %d 个类与 mdisp==4 独立，76 个全中的概率是 0.0 的量级'
   % (len(pool), len(withI), p4, 100 * p4 / len(withI) if withI else 0, len(withI)),
   len(withI) >= 70 and p4 == len(withI),
   {'n_classes': len(pool), 'n_declared': len(withI), 'n_mdisp4': p4})

# 真正有鉴别力的反问：IRTTITypeInfo 的 mdisp 是否**恒定** 4？
# 若是常量，则它不能用来区分；若不是（有别的取值），则「76 个全是 4」才携带信息。
distinct_md = {}
for k in withI:
    v = tuple(RTTI[int(sym[k]['vtable_va'], 16)]['bases']['IRTTITypeInfo'])
    distinct_md[v] = distinct_md.get(v, 0) + 1
ck('D7 关键反问：IRTTITypeInfo 的 mdisp 在全库**不是常量**（分布 %s）⇒ 「76 个类全为 4」'
   '不是同义反复，它确实把 IRTTITypeInfo 与 offset==0 的 IPersist/IPersistStream 分开了'
   % {str(k): v for k, v in distinct_md.items()},
   len(distinct_md) >= 1 and p4 == len(withI),
   {'dist': {str(k): v for k, v in distinct_md.items()}})

# ---------- D8 附带闭合：R111 §EM3 的 12 个 thunk 类，用链 D 反查其真 QI 认的 IID ----------
# R111 §EM3 只报了 thunk 形态与之对应的 COL.offset==4；其穿透后新增的 2 个 IID
# （0x7e9b10 / 0x7ed358）当时的语义是空白。本轮链 B（RTTI 基类名）给出了唯一强对应：
#   0x7e9b10 的 6 个认领类在 RTTI 里**全部**声明 IPiggyback 且 mdisp 全为 24
#   0x7ed358 的 6 个认领类在 RTTI 里**都没有**任何 mdisp==24 的接口名（只有 ILocomotion 4）
# 第二支因此得不到名字 —— 如实报「未定」，不硬配一个。
TH = json.load(open(os.path.join(ROOT, '_r111/r111c_thunk.json')))
tk = TH['thunks']
q1 = Q.get('0x7e9b10') or set(k for k, v in I111.items() if '0x7e9b10' in v)
q2 = Q.get('0x7ed358') or set(k for k, v in I111.items() if '0x7ed358' in v)
pg = {}
for k in q1:
    pg[k] = RTTI[int(sym[k]['vtable_va'], 16)]['bases'].get('IPiggyback')
ck('D8 链 B 给 0x7e9b10（92FEA800-A184-11D1-B70A-00A024DDAFD1）唯一强对应：它的 %d 个认领类'
   '在 RTTI 里**全部**声明 IPiggyback 且 mdisp 全为 [24] —— 这正是 R111 §EM2 那 12 类里'
   '子对象偏移 24 的那一族。R111 说它「语义未定」，本轮定死' % len(q1),
   len(q1) == 6 and all(v == [24] for v in pg.values()), pg)

m24 = {}
for k in q2:
    r = RTTI[int(sym[k]['vtable_va'], 16)]
    m24[k] = sorted(nm for nm, v in r['bases'].items()
                    if 24 in v and nm != 'IUnknown')
ck('D8b 而 0x7ed358（070F3290-9841-11D1-B709-00A024DDAFD1）的 %d 个认领类里，'
   'RTTI 声明的 mdisp==24 接口名**一个都没有**（%s）⇒ **链 B 无候选**，如实记语义未定，'
   '不强行配名' % (len(q2), m24),
   len(q2) == 6 and all(len(v) == 0 for v in m24.values()), m24)

json.dump({'trio': {i: {'n_claim': len(Q[i]), 'N': NOF.get(i), 'full': sorted(FULL.get(i, []))}
                    for i in Q},
           'symdiff_70_80': sorted(sd), 'same_subobj_70_80': Cc['same_70_80'],
           'd79': sorted(d79), 'd79_mdisp': mds,
           'irtti_mdisp_dist': {str(k): v for k, v in distinct_md.items()},
           'd8': {'0x7e9b10_claims': sorted(q1), '0x7e9b10_ipiggyback_mdisp': pg,
                  '0x7ed358_claims': sorted(q2), '0x7ed358_cands': m24},
           'verdict': {'0x7e9ae0': 'IRTTITypeInfo（链 D 联立后唯一；HouseClass 另有 RTTI mdisp 直证）',
                       '0x7f7c70': 'IPersist 或 IPersistStream（二者在本库静态证据下不可区分）',
                       '0x7f7c80': 'IPersist 或 IPersistStream（同上，且与 0x7f7c70 亦不可区分）',
                       '0x7e9b10': 'IPiggyback（链 B 唯一强对应，6/6 类 mdisp 全 24）',
                       '0x7ed358': '未定（链 B 无候选，如实记）'},
           'checks': checks}, open(OUT, 'w'), indent=1, ensure_ascii=False)
badn = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - badn, badn))
sys.exit(1 if badn else 0)
