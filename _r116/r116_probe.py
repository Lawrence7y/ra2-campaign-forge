#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116_probe.py —— 探针：IID 0x7f7c70 / 0x7f7c80 的「客户端 QI 站点」与
ole32!OleSaveToStream / OleLoadFromStream 的耦合关系（R115 未取得项②的新数据面）。

背景：R112–R115 三轮都只在**服务端**（类 slot0 QI 体内的 cmpsd 比较序列）判这两个 IID，
服务端两侧完全对称（同一批 QI 体依次比对 0x7f7c90 → 0x7f7c80 → 0x7f7c70 → 0x7e9ae0，
且 0x7f7c70/0x7f7c80 命中后写回同一个指针 ⇒ 差集 0）⇒ 不可区分。
本轮换面：**客户端**。谁把哪个 IID 常量当参数 push 给 QueryInterface，
以及拿到接口指针之后立刻交给哪个 ole32 API。

内存纪律：disasm_lite，逐函数 <=2000 B 窗口，detail 恒 False。
"""
import collections, json, os, struct, sys

sys.path.insert(0, os.path.join('/home/t628/projects/ra2-campaign-forge', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
MD = L.MD
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r116/r116_probe.json')

IAT = {0x7e15f4: 'OleSaveToStream', 0x7e15f8: 'OleLoadFromStream',
       0x7e15fc: 'CoCreateInstance', 0x7e15f0: 'CLSIDFromString',
       0x7e15d8: 'CoRegisterClassObject', 0x7e15d4: 'OleInitialize'}
IIDS = {0x7f7c70: 'IID_A_0000010C', 0x7f7c80: 'IID_B_00000109',
        0x7f7c90: 'IID_IUnknown_00000000', 0x7f7ca0: 'IID_IClassFactory_00000001',
        0x7ed358: 'IID_ILocomotion', 0x7e9ae0: 'IID_IRTTITypeInfo_raw'}


def insn_starting_at(va, back_max=8):
    """va 处是否是一条指令的**起点**；是则返回该指令 (addr, size, mnem, ops)。"""
    for back in range(1, back_max + 1):
        start = va - back
        if start < TS:
            continue
        g = list(MD.disasm_lite(raw[fo(start):fo(start) + 16], start))
        if not g:
            continue
        s = g[0]
        # 该指令必须从 start 起、且**末端恰好**越过 imm32 的 4 字节 ⇒ 它消费了 va 处这个常量
        if s[0] == start and s[0] + s[1] == va + 4:
            return s
    return None


def imm_sites(iid):
    """返回 [(use_va, form, imm_start)]：form ∈ {push_imm32, mov_imm32}。
    use_va 是那条指令的起点。"""
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out = []
    i = buf.find(pat)
    while i != -1:
        va = TS + i
        s = insn_starting_at(va)
        if s is not None and s[2] in ('push', 'mov') and s[1] in (5, 6, 7):
            out.append((s[0], s[2] + '_imm' + str(s[1]), s[1]))
        i = buf.find(pat, i + 1)
    return out


def fn_of(va):
    import bisect
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


def fn_ole_calls(f):
    """函数体内出现的 ole32 IAT 调用（按地址序）。"""
    out = []
    for a, sz, m, o in L.body(f):
        if m != 'call':
            continue
        mm = o.replace('dword ptr [', '').replace(']', '')
        try:
            v = int(mm, 16)
        except ValueError:
            continue
        if v in IAT:
            out.append((a, IAT[v]))
    return out


def fn_qi_calls(f):
    """函数体内 `call dword ptr [reg]` / `[reg+0]`（= slot0 QueryInterface）站点。"""
    out = []
    for a, sz, m, o in L.body(f):
        if m == 'call' and (o.startswith('dword ptr [e') and ('+ 0]' in o or o.count('+') == 0)):
            out.append(a)
    return out


res = {'iid_sites': {}, 'coupling': {}, 'notes': []}
for iid, nm in IIDS.items():
    s = imm_sites(iid)
    res['iid_sites'][nm] = {'va': hex(iid), 'total': len(s),
                            'forms': dict(collections.Counter(f for _, f, _ in s)),
                            'sites': [hex(a) for a, _, _ in s]}
    print('%-28s %s  total %3d  %s' % (nm, hex(iid), len(s),
                                       dict(collections.Counter(f for _, f, _ in s))))

# ---- 耦合判定：0x7f7c80 的每个 push 站点所在函数，是否在同一函数内、该站点之后
#      出现 ole32 的 OleSaveToStream / OleLoadFromStream 调用 ----
def coupling(iid):
    rows = []
    for site, form, _ in imm_sites(iid):
        if not form.startswith('push'):
            continue
        f = fn_of(site)
        ole = [c for c in fn_ole_calls(f) if c[0] > site]
        kinds = sorted(set(n for _, n in ole))
        rows.append({'site': hex(site), 'fn': hex(f), 'ole_after': kinds})
    return rows


for iid, nm in ((0x7f7c80, 'IID_B_00000109'), (0x7f7c90, 'IID_IUnknown_00000000'),
                (0x7f7c70, 'IID_A_0000010C'), (0x7ed358, 'IID_ILocomotion')):
    r = coupling(iid)
    hit = sum(1 for x in r if any(k.startswith('OleSaveToStream') or k.startswith('OleLoadFromStream')
                                 for k in x['ole_after']))
    res['coupling'][nm] = {'push_sites': len(r), 'with_ole_after': hit, 'rows': r}
    print('%-28s push-sites %3d  with Ole*Stream after %3d  (%.1f%%)'
          % (nm, len(r), hit, 100.0 * hit / len(r) if r else 0.0))

# ---- 反向：43 个 OleSaveToStream 调用点里，有几个其函数内有 0x7f7c80 的 push 在先 ----
save_sites = []
buf = raw[fo(TS):fo(TE)]
pat = struct.pack('<I', 0x7e15f4)
i = buf.find(pat)
while i != -1:
    va = TS + i
    if raw[fo(va) - 2:fo(va)] == b'\xff\x15':
        save_sites.append(va - 2)
    i = buf.find(pat, i + 1)
rows = []
for s in save_sites:
    f = fn_of(s)
    q80 = [a for a, fm, _ in imm_sites(0x7f7c80) if fm.startswith('push') and a < s and fn_of(a) == f]
    q70 = [a for a, fm, _ in imm_sites(0x7f7c70) if fm.startswith('push') and a < s and fn_of(a) == f]
    rows.append({'save_site': hex(s), 'fn': hex(f), 'qi80_before': len(q80), 'qi70_before': len(q70)})
res['reverse'] = {'save_sites': len(save_sites),
                  'with_qi80_before': sum(1 for r in rows if r['qi80_before']),
                  'with_qi70_before': sum(1 for r in rows if r['qi70_before']),
                  'rows': rows}
print('reverse: OleSaveToStream %d sites ; with QI(0x7f7c80) before %d ; with QI(0x7f7c70) before %d'
      % (res['reverse']['save_sites'], res['reverse']['with_qi80_before'],
         res['reverse']['with_qi70_before']))

json.dump(res, open(OUT, 'w'), indent=1)
print('WROTE', OUT)
