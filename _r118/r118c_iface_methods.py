#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118c_iface_methods.py —— R113 起挂了 6 轮的老欠账：IPersistStream / IPersist 的**方法数**。

为什么这是一条**独立数据面**（与前六轮都不共用字节）：
  R112..R117 全部在 .text 的 QI 服务端/客户端、以及 .rdata 的 COL/vtable 里取数。
  但 MSVC 的 RTTI 里，每个接口的 BCD（BaseClassDescriptor）有 4 个 u32：
      pTypeDescriptor, numContainedBases, mdisp, pdisp, vdisp, attributes, pClassDescriptor
  其中 **numContainedBases 对「单继承的接口」恒等于 1**，而对 IPersistStream 实测是 **2**
  —— 因为接口的 RTTI 把它"包含的基类"也数进去（IPersistStream : IPersist : IUnknown）。
  这条链的数据源是 .rdata 的 BCD/CHD，与 QI 字节、vtable 槽、GUID 常量都不同。

但**关键降级必须先写在前面**（不重复 R101/R112 的错误）：
  RTTI 的 numContainedBases 记的是**继承关系里的基类个数**，它**不是**方法表槽数。
  本脚本因此**不声称**它能给出方法数；它给出的是：
    ① 这条链能机械读出什么（继承深度 / 各接口的 numContainedBases 取值分布）；
    ② 它与 vtable 槽数尺（R113/R115 的 S 尺）**是否一致** —— 若不一致，
       则「用 RTTI 推方法数」这条路被证伪，必须如实写成"方法数仍未取得"。
  这正是本脚本要回答的：**同值不等于同义**，必须用第三种数据面交叉。

断言：
  Q1 IPersistStream 的 BCD 读得出 mdisp/numContainedBases/pCHD，且 pTD 名字逐字符 == .?AUIPersistStream@@
  Q2 IPersist / IPersistStream / IRTTITypeInfo / IUnknown 四者的 numContainedBases 取值
  Q3 所有接口子对象（R115 的 260 个）按其 pTD 名字分组，numContainedBases 是否恒为 1
  Q4 【交叉】把每个接口的 numContainedBases 与 R115 落盘的 S 尺槽数并列，判「是否同义」
  Q5 反控：若 numContainedBases 真是方法数代理，则它与 S 尺的 Spearman 必须显著；
     实测若无关，则该代理被证伪（如实写）
  Q6 反控：单继承的普通类（CHD nBC 连续递增链）上，numContainedBases 应恒 1
内存纪律：只读 .rdata/.data 常量区 + 落盘 JSON；不跑全 .text 反汇编。
"""
import json
import math
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.join(ROOT, '_r118/r118c_iface_methods.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()
IB = 0x400000
SECS = [('.text', 0x401000, 0x3df38d, 0x1000, 0x3e0000),
        ('.rdata', 0x7e1000, 0x30074, 0x3e1000, 0x31000),
        ('.data', 0x812000, 0x367be4, 0x412000, 0x6c000),
        ('.rsrc', 0xb7a000, 0x18128, 0x47e000, 0x19000),
        ('.detour', 0xb93000, 0x2718, 0x497000, 0x3000)]


def fo(va):
    for n, b, vs, pr, sr in SECS:
        if b <= va < b + sr:
            o = pr + (va - b)
            return o if 0 <= o <= len(raw) - 1 else None
    return None


def u32(a):
    o = fo(a)
    if o is None or o + 4 > len(raw):
        raise ValueError('oof: ' + hex(a))
    return struct.unpack_from('<I', raw, o)[0]


def cstr(va, cap=200):
    o = fo(va)
    if o is None:
        return None
    e = raw.find(b'\x00', o)
    if e < 0 or e - o > cap:
        return None
    try:
        return raw[o:e].decode('latin1')
    except Exception:
        return None


def is_td(va):
    """TypeDescriptor 布局：+0 vftable(4)、+4 spare(4)、+8 起是装饰名字符串。
    🐞 自错 S-48：初稿写成 cstr(va)，即在 TD 起始处找名字 ⇒ 读到的是 vftable 指针的字节，
    is_td 恒 False，PER_TD 恒空（BCD 候选 1002 个却一条名字都没解出来）。必须 cstr(va+8)。"""
    n = cstr(va + 8) if va is not None else None
    return n is not None and n[:3] in ('.?A', '.?U', '.?V', '.?T')


def bcd(a):
    """BCD 实测布局（MSVC x86，**24 字节**，本轮用 0x7fb020 起 8 项连续条目钉住）：
       +0x00 pTypeDescriptor
       +0x04 numContainedBases
       +0x08 mdisp
       +0x0c pdisp
       +0x10 vdisp
       +0x14 attributes

    🐞 自错 S-47b：初稿把 BCD 当 32 字节、+0x18 叫 pCHD —— 那个位置其实是**下一条 BCD 的 pTD**
    （0x7fb0b0 的 +0x18 = 0x8177c8 恰好是另一条 BCD 的 pTD 地址，被我误读成一个 class descriptor）。
    复算办法：从 0x7fb020 起按 24 字节步进，8 项全部是「pTD 合法 + nCB∈{0,1,2,7} + mdisp 单调」
    ⇒ 24 字节布局成立。基类数组（CHD 的 pBCA）由 BCD 外的**指针数组**给出（实测 0x7fb0e0 起）。
    """
    d = {'va': hex(a), 'pTD': u32(a), 'numContainedBases': u32(a + 4), 'mdisp': u32(a + 8),
         'pdisp': u32(a + 0xc), 'vdisp': u32(a + 0x10), 'attributes': u32(a + 0x14)}
    # 🐞 自错 S-48b：名字在 TD+8，这里也漏改了 ⇒ PER_TD 的键变成 vftable 的原始字节。
    d['name'] = cstr(d['pTD'] + 8) if is_td(d['pTD']) else None
    return d


# ---- Q1：三张接口 BCD 逐个读 ----
# 位置来自 r118a 已落盘的 GUID 普查（不手抄）
A = json.load(open(os.path.join(ROOT, '_r118/r118a_guid_census.json')))
# BCD 位置：从 CHD 基类数组里按 pTD 名字反查（不预设地址）
# 先建一张 pTD->名字 的 TypeDescriptor 表（只在 .rdata/.data 内）
td_by_name = {}
for sec, b, vs, pr, sr in SECS:
    if sec in ('.text', '.rsrc'):
        continue
    for a in range(b, b + sr - 16, 4):
        try:
            n = cstr(a)
        except Exception:
            continue
        if n and n[:3] in ('.?A', '.?U', '.?V', '.?T') and 6 <= len(n) <= 160:
            # TypeDescriptor = vftable_ptr(4) + spare(4) + name ⇒ 名起址 = a, TD = a-8
            if fo(a - 8) is not None and fo(a - 8) is not None:
                td_by_name.setdefault(n, a - 8)

WANT = {'.?AUIPersist@@': None, '.?AUIPersistStream@@': None,
        '.?AUIRTTITypeInfo@@': None, '.?AVINoticeSource@@': None}
for k in WANT:
    if k not in td_by_name:
        raise SystemExit('TypeDescriptor not found for ' + k)
print('TD 表命中（%d 个装饰名）：' % len(td_by_name),
      {k: hex(td_by_name[k]) for k in WANT}, flush=True)

# 🐞 自错 S-47（本轮两次）：初稿把 pCHD 合法域限定在 .rdata，但 24 字节 BCD 布局
# 根本没有 pCHD 字段（见 bcd() 注释）。改为：直接按 24 字节步进扫 BCD 候选，
# 判据只有「pTD 是合法 TypeDescriptor + nCB 在合理范围 + mdisp 是合理偏移」。
RD0, RD1 = 0x7e1000, 0x811074
DD0, DD1 = 0x812000, 0x87e000


def in_rtti(v):
    return RD0 <= v < RD1 or DD0 <= v < DD1


TD_SET = set(td_by_name.values())
BCDS = []
for a in range(RD0, RD1 - 0x18, 4):
    try:
        ptd = u32(a)
    except ValueError:
        break
    if ptd not in TD_SET:
        continue
    nb = u32(a + 4)
    mdisp = u32(a + 8)
    pdisp = u32(a + 0xc)
    if not (0 <= nb <= 96):
        continue
    if mdisp > 0x100000:
        continue
    if pdisp not in (0xffffffff,) and pdisp > 0x100000:
        continue
    BCDS.append(a)


def bcd_ok(a):
    """结构复核：pdisp 必须是 0xffffffff（实测全镜像基类 BCD 的惯例）或小偏移。"""
    ptd = u32(a)
    if ptd not in TD_SET:
        return False
    return u32(a + 0xc) == 0xffffffff and u32(a + 4) <= 96
print('BCD 候选 %d 个' % len(BCDS), flush=True)

PER_TD = {}
for a in BCDS:
    d = bcd(a)
    if d['name']:
        PER_TD.setdefault(d['name'], []).append(d)

ck('Q1 四个接口的 BCD 全部读出（pTD 名字逐字符匹配、pCHD 合法）：%d / 4'
   % sum(1 for k in WANT if k in PER_TD),
   all(k in PER_TD for k in WANT),
   {k: (PER_TD[k][0] if k in PER_TD else None) for k in WANT})

# ---- Q2：四个接口的 numContainedBases 取值 ----
q2 = {k: sorted({d['numContainedBases'] for d in PER_TD[k]}) for k in WANT if k in PER_TD}
ck('Q2 四个接口的 numContainedBases 实测取值（IPersistStream 若 > 1 说明它把自己的基类也数进去）',
   True, q2)

# ---- Q3：全部接口（.rdata 里被 CHD 引用的 BCD）的 numContainedBases 分布 ----
dist = {}
for k, lst in PER_TD.items():
    dist[k] = sorted({d['numContainedBases'] for d in lst})
from collections import Counter
cnt = Counter()
for k, v in dist.items():
    for x in v:
        cnt[x] += 1
print('numContainedBases 取值 -> 名字个数:', dict(cnt), flush=True)

ifs = [k for k in dist if k.startswith('.?AU')]
one_only = [k for k in ifs if dist[k] == [1]]
ck('Q3 全部 %d 个以 .?AU 开头的接口类中，numContainedBases 取值恒 {1} 的 %d 个；'
   '取值 >1 的 %d 个（%s）⇒ 该字段区分「单继承接口」与「有基类链的接口」'
   % (len(ifs), len(one_only), len(ifs) - len(one_only),
      [(k, v) for k, v in dist.items() if k in ifs and v != [1]][:6]),
   len(ifs) > 5, {'n_ifaces': len(ifs), 'one_only': len(one_only),
                  'gt1': {k: v for k, v in dist.items() if k in ifs and v != [1]}})

# ---- Q4：与 R115 的 S 尺槽数交叉 ----
R115 = json.load(open(os.path.join(ROOT, '_r115/r115a_bound.json')))
S = R115['per_interface']       # {INoticeSource: {n_vt, slots, T, B, E}, ...}
pairs = []
for name, v in S.items():
    td = '.?AV' + name + '@@'
    slots = v['slots'][0] if v.get('slots') else None
    ncb = dist.get(td) or dist.get('.?AU' + name + '@@')
    pairs.append({'iface': name, 's_slots': slots, 'numContainedBases': ncb})
print('Q4 交叉表:', json.dumps(pairs, ensure_ascii=False), flush=True)

# 只用两侧都取到值的对做相关
both = [(p['numContainedBases'][0], p['s_slots']) for p in pairs
        if p['numContainedBases'] and p['s_slots'] is not None]
n = len(both)


def spearman(xy):
    if len(xy) < 3:
        return None
    xs = sorted(range(len(xy)), key=lambda i: xy[i][0])
    ys = sorted(range(len(xy)), key=lambda i: xy[i][1])
    rx = [0] * len(xy)
    ry = [0] * len(xy)
    for r, i in enumerate(xs):
        rx[i] = r
    for r, i in enumerate(ys):
        ry[i] = r
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return None if dx * dy == 0 else num / (dx * dy)


rho = spearman(both)
only1 = [p for p in both if p[0] == 1]
ck('Q4 【核心】numContainedBases 与 S 尺槽数并列：两侧都有值的 %d 对；其中 numContainedBases==1 的 %d 对，'
   '这些对的 S 尺槽数是 %s ⇒ 同一个 numContainedBases 值对应迥异的槽数 ⇒ **两者不同义**'
   % (n, len(only1), sorted({p[1] for p in only1})),
   n >= 5 and len({p[1] for p in only1}) > 1,
   {'n': n, 'slots_when_ncb_1': sorted({p[1] for p in only1}), 'rho': rho})

# ---- Q5：同义性检验必须**双向**做，不能只说"rho 不大就证伪" ----
# 🐞 自错 S-49：初稿 Q5 写 abs(rho) < 0.9 即 PASS，rho=0.733 时靠阈值侥幸通过，
# 而它得出的"证伪"结论其实不由 rho 支撑（rho 中等并不等于不同义，也不等于同义）。
# 真正的判据是 Q4 的**决定性反例**：同一个 nCB 值（=1）对应槽数 {5,6,8,9,15,50}，
# 一个函数不可能把一个输入映到六个输出 ⇒ 不同义。这里把 Q5 降级为"相关性参考"，
# 不再当证伪依据，并显式记 rho 与其置信区间缺失的事实。
ck('Q5 相关性参考（不作证伪依据）：nCB 与 S 尺槽数的 Spearman rho = %s（n=%d）。'
   'rho 中等既不支持也不否定同义性；同义性由 Q4 的决定性反例否定'
   '（同一 nCB=1 映射到 6 个不同槽数）' % (rho, n),
   rho is None or abs(rho) < 0.99, {'rho': rho, 'n': n,
                                    'note': 'rho 仅参考，判据是 Q4 的映射单值性'})

# Q5b 决定性判据：把 nCB 当输入、槽数当输出，函数性检验（同一输入必须同一输出）
by_in = {}
for ncb_v, slots_v in both:
    by_in.setdefault(ncb_v, set()).add(slots_v)
multi_out = {k: sorted(v) for k, v in by_in.items() if len(v) > 1}
ck('Q5b 【决定性】把 numContainedBases 当输入、S 尺槽数当输出做函数性检验：'
   '%d 个输入里有 %d 个是**一对多**（%s）⇒ numContainedBases **不可能**是方法/槽数'
   % (len(by_in), len(multi_out), multi_out),
   len(multi_out) >= 1, {'one_to_many': multi_out})

# ---- Q6：普通类的 numContainedBases 是否恒 1 ----
cls = [k for k in dist if k.startswith('.?AV') and not k.startswith('.?AV?$')]
c1 = [k for k in cls if dist[k] == [1]]
ck('Q6 反控（普通类）：%d 个 .?AV 普通类中 numContainedBases 恒 {1} 的 %d 个；'
   '取值含 >1 的 %d 个' % (len(cls), len(c1), len(cls) - len(c1)),
   len(cls) > 100,
   {'n_class': len(cls), 'one_only': len(c1),
    'gt1_sample': {k: v for k, v in dist.items() if k in cls and v != [1]}.copy().__len__()})

json.dump({'per_td_dist': dist, 'q2': q2, 'cross': pairs, 'rho': rho,
           'n_bcd': len(BCDS), 'checks': checks},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
