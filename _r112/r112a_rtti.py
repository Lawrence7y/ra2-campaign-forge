#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112a_rtti.py —— 解析全库 RTTI 三表（COL / CHD / BCD），拿到**每个类逐基类的成员子对象偏移 mdisp**。

为什么这一步是本轮的地基：
  R111 §EM10 留了两个未取得项 —— ① 20 个 ptr 支 IID 的接口方法表；② 0x7e9ae0 / 0x7f7c70 / 0x7f7c80 语义未定。
  这两条都卡在「IID 指针 ↔ 接口名」缺一条**与 RTTI 名字链和 QI 字节链都不共用数据**的第三方。
  本轮发现：QI 成功分支写回 ppv 时给的是 `lea reg,[this + N]`（或原样 this ⇒ N=0），
  而 RTTI 的 BCD（BaseClassDescriptor）在 +0x08 处记的 mdisp 正是「该基类子对象在对象内的字节偏移」。
  二者若在同一类上逐条对齐，就是第四条独立链；用途是把 R111 §EM10② 的 5 个「歧义 IID」逐个定死。

判据（全部可机械复核，不猜）：
  COL 布局：+0x00 sig、+0x04 offset、+0x0C pTD、+0x10 pCHD、+0x14 pSelf
  CHD 布局：+0x08 numBaseClasses、+0x0C pBaseClassArray
  BCD 布局：+0x00 pTypeDescriptor、+0x08 mdisp、+0x0C pdisp、+0x10 vdisp
  基类名从 TD 取（TD+0x08 起为装饰名 .?AVXxx@@），只剥前 3 字符与尾 @，不做完整 demangle。

断言（正控 + 反控 + 结构自洽）：
  A1 RTTI 可解析的 vtable 数 == 954（与 symbols.json 的 vtable 数相等，一个不落）
  A2 COL 的 offset 分布 == {0: 942, 4: 12}（R110 §EL5 的独立复算，两条链必须一致）
  A3 正控：HouseClass 的基类 mdisp 表 == 已知手工读出的 15 条（IHouse 36 / IPublicHouse 40 / ICPC 44）
  A4 正控：CStreamClass 的 ILinkStream mdisp == 4，IStream / ISequentialStream == 0
  A5 正控：DriveLocomotionClass 的 ILocomotion == 4、IPiggyback == 24（R112 新增，R111 尚无）
  A6 结构自洽：每个类的 mdisp(自身类) 必为 0
  A7 结构自洽：CHD 的 numBaseClasses 与 bases 字典展开后的基类名计数一致
  A8 反控：随机取 20000 个 .text 指令起点当「vtable 指针」套同一判据，能解出 RTTI 的命中率
内存纪律：全段只用 disasm_lite（本脚本其实不反汇编）；B3 之外不碰 .text。
"""
import hashlib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r112_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r112/r112a_rtti.json')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


ck('S0 exe sha256 == 本轮基准', hashlib.sha256(L.raw).hexdigest() == L.EXE_SHA,
   hashlib.sha256(L.raw).hexdigest()[:16])

sym, VT = L.load_symbols()
ck('S1 vtable 数 954（R107/R110/R111 同口径）', len(VT) == 954, len(VT))

C = L.cache()
RTTI = C['RTTI']
ck('A1 RTTI 可解析 vtable == 954（一个不落；解析失败返回 None 而非补默认值）',
   len(RTTI) == 954 and len(RTTI) == len(VT), {'parsed': len(RTTI), 'vts': len(VT)})

# ---------- A2 COL.offset 分布（R110 §EL5 独立复算） ----------
dist = {}
for vt, r in RTTI.items():
    dist[r['coloff']] = dist.get(r['coloff'], 0) + 1
ck('A2 COL.offset 分布 == {0: 942, 4: 12}（R110 §EL5 的独立复算）',
   dist == {0: 942, 4: 12}, dist)

# ---------- A3/A4/A5 正控 ----------
def md_of(name, iface):
    vt = int(sym[name]['vtable_va'], 16)
    r = RTTI.get(vt)
    return r['bases'].get(iface) if r else None

house = RTTI[int(sym['HouseClass']['vtable_va'], 16)]['bases']
ck('A3 正控 HouseClass 逐基类 mdisp：IHouse=%s IPublicHouse=%s ICPC=%s IUnknown=%s IRTTITypeInfo=%s'
   % (house.get('IHouse'), house.get('IPublicHouse'),
      house.get('IConnectionPointContainer'), house.get('IUnknown'), house.get('IRTTITypeInfo')),
   house.get('IHouse') == [36] and house.get('IPublicHouse') == [40]
   and house.get('IConnectionPointContainer') == [44]
   and house.get('IUnknown') == [0, 4, 36, 40, 44] and house.get('IRTTITypeInfo') == [4],
   {k: house.get(k) for k in ('IHouse', 'IPublicHouse', 'IConnectionPointContainer', 'IUnknown', 'IRTTITypeInfo')})

ck('A4 正控 CStreamClass：ILinkStream=%s IStream=%s ISequentialStream=%s（0 与 4 必须分开）'
   % (md_of('CStreamClass', 'ILinkStream'), md_of('CStreamClass', 'IStream'),
      md_of('CStreamClass', 'ISequentialStream')),
   md_of('CStreamClass', 'ILinkStream') == [4] and md_of('CStreamClass', 'IStream') == [0]
   and md_of('CStreamClass', 'ISequentialStream') == [0],
   (md_of('CStreamClass', 'ILinkStream'), md_of('CStreamClass', 'IStream')))

ck('A5 正控 DriveLocomotionClass：ILocomotion=%s IPiggyback=%s'
   % (md_of('DriveLocomotionClass', 'ILocomotion'), md_of('DriveLocomotionClass', 'IPiggyback')),
   md_of('DriveLocomotionClass', 'ILocomotion') == [4]
   and md_of('DriveLocomotionClass', 'IPiggyback') == [24],
   (md_of('DriveLocomotionClass', 'ILocomotion'), md_of('DriveLocomotionClass', 'IPiggyback')))

# ---------- A6/A7 结构自洽 ----------
bad_self = []
for vt, r in RTTI.items():
    nm = VT[vt]
    ms = r['bases'].get(nm)
    if ms is None or ms != [0]:
        bad_self.append((nm, ms))
ck('A6 结构自洽：每类的自身类 mdisp 必为 [0]（违例 %d 个）' % len(bad_self),
   len(bad_self) == 0, bad_self[:6])

bad_nbc = []
for vt, r in RTTI.items():
    tot = sum(len(v) for v in r['bases'].values())
    if tot != r['nbc']:
        bad_nbc.append((VT[vt], tot, r['nbc']))
ck('A7 结构自洽：Σ|bases[name]| == CHD.numBaseClasses（违例 %d 个）' % len(bad_nbc),
   len(bad_nbc) == 0, bad_nbc[:6])

# ---------- A8 反控：随机地址冒充 vtable 指针 ----------
# 两向反控：(a) .text 指令起点（必然解不出）；(b) 全镜像 4 字节对齐随机地址（可能撞上看似合法的数据）。
# 只做 (a) 是零信息格（命中必然 0），必须配 (b) 才有鉴别力 —— R108 §EJ2 的教训。
random.seed(112)
starts = C['starts']
samp_t = random.sample(starts, 20000)
hit_t = sum(1 for s in samp_t if L.rtti_of(s) is not None)
samp_i = [L.IB + 4 * random.randrange(0, (len(L.raw) - 8) // 4) for _ in range(20000)]
hit_i = sum(1 for s in samp_i if L.rtti_of(s) is not None)
base_t = hit_t / 20000 * 100
base_i = hit_i / 20000 * 100
ck('A8 反控两向：随机 20000 个 .text 指令起点解出 %d（%.3f%%）；随机 20000 个全镜像 4 字节对齐'
   '地址解出 %d（%.3f%%）；真 vtable 954/954 = 100%% ⇒ 对 (b) 富集 %.1f 倍'
   % (hit_t, base_t, hit_i, base_i, (100.0 / base_i) if base_i else float('inf')),
   hit_t == 0 and base_i < 3.0,
   {'text_hit': hit_t, 'text_base_pct': round(base_t, 4),
    'img_hit': hit_i, 'img_base_pct': round(base_i, 4),
    'enrich_vs_img': round(100.0 / base_i, 1) if base_i else None})

# ---------- 落盘 ----------
ser = {}
for vt, r in RTTI.items():
    ser[VT[vt]] = {'vtable': '0x%08x' % vt, 'col': '0x%08x' % r['col'], 'coloff': r['coloff'],
                   'nbc': r['nbc'], 'bases': r['bases']}
json.dump({'rtti': ser, 'coloff_dist': {str(k): v for k, v in dist.items()},
           'negctl': {'text_n': 20000, 'text_hit': hit_t, 'text_base_pct': round(base_t, 4),
                      'img_n': 20000, 'img_hit': hit_i, 'img_base_pct': round(base_i, 4)},
           'checks': checks}, open(OUT, 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
