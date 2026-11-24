#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118e_copy_semantics.py —— R118 的**自我降级**：.data 里的 GUID 拷贝不是同一种东西。

背景：r118a 用「16 字节值精确搜索」找出每份拷贝，然后把这些拷贝上的 push 站点全部
按值合并，得出「IPersistStream 请求站点 = 68（.rdata 60 + .data 8）」。
deepseek 执行员（task 215）与我自己后续的结构探查都指向一个此前没问的问题：
**这些 .data 拷贝真的是同一个 IID 的第二种用途吗，还是别的数据里恰好同值的字节？**

本轮要回答的（每条都要机械判据）：
  R1 .data 拷贝按「其后是否紧跟 type_info vftable + 类名字符串」分类。
     若紧跟 ⇒ 它是 MSVC 的 __declspec(uuid) 静态记录（一个合法用途），
     若不紧跟 ⇒ 它只是**碰巧同值的字节**（字符串/常量池/别的数据），不算另一种用途。
  R2 对每个被研究的 IID，给出「真记录拷贝」与「巧合拷贝」的清单。
  R3 【核心降级】若某个 IID 的 .data 拷贝被判为巧合，则按值口径合并它**是错误**的，
     必须回退到 .rdata 数字。逐 IID 给出回退后的正确数字。
  R4 【核心保留】若某个 IID 的 .data 拷贝是真记录，则合并**有道理**，
     但仍须回答：这份记录上的 push 站点是否真的是客户端 QI 请求（看后继形态）。
  R5 反控：真记录判据的**假阳/假阴**实测 —— 取所有 .data 里的 type_info vftable 出现位置，
     检查它们是否都跟在 16 字节 GUID 之后；以及取所有 .data GUID 形状常量，
     检查是否都被判为记录（若都为真则判据无区分力）。
"""
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.join(ROOT, '_r118/r118e_copy_semantics.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()
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
        raise ValueError('oof ' + hex(a))
    return struct.unpack_from('<I', raw, o)[0]


def cstr(va, cap=200):
    o = fo(va)
    if o is None:
        return None
    e = raw.find(b'\x00', o)
    if e < 0 or e - o > cap:
        return None
    return raw[o:e].decode('latin1')


TIVT = 0x7f9594        # symbols.json 实测的 type_info vftable（954 类共用）
DS, DE = 0x812000, 0x87e000

A = json.load(open(os.path.join(ROOT, '_r118/r118a_guid_census.json')))
studied = A['studied']

# ---- R1：把每份拷贝分类 ----
def classify(va):
    """真记录判据（三条同时成立）：
       (a) va+0x10 处的 dword == type_info vftable
       (b) va+0x18 处是合法装饰类名（.?AV... /.?AU... 等），且能读到 NUL
       (c) 记录起始 va 在 .data
    反控在 R5：要求这三条**不能**对所有 GUID 形状常量都成立。"""
    try:
        t = u32(va + 0x10)
    except ValueError:
        return {'record': False, 'why': 'oof'}
    nm = cstr(va + 0x18) if fo(va + 0x18) is not None else None
    ok_name = bool(nm) and nm[:3] in ('.?A', '.?U', '.?V', '.?T')
    return {'record': t == TIVT and ok_name, 'type_info_vt': hex(t),
            'name': nm, 'name_ok': ok_name}


per_iid = {}
for addr, info in studied.items():
    guid = info['guid']
    entry = {'guid': guid, 'copies': []}
    for c, n in info['copies'].items():
        va = int(c, 16)
        cl = classify(va)
        entry['copies'].append({'va': c, 'push_sites': n, 'sec':
                                '.data' if DS <= va < DE else '.rdata',
                                **cl})
    per_iid[addr] = entry

n_rec = sum(1 for e in per_iid.values() for c in e['copies'] if c['record'])
n_coinc = sum(1 for e in per_iid.values() for c in e['copies']
              if not c['record'] and c['sec'] == '.data')
ck('R1 .data 里的 GUID 拷贝分类：被判为「真记录（后跟 type_info + 类名）」的 %d 份；'
   '被判为「同值巧合字节」的 %d 份 ⇒ 这两类不能混在一张统计里' % (n_rec, n_coinc),
   n_rec >= 1 and n_coinc >= 1,
   {'records': n_rec, 'coincidences': n_coinc,
          'detail': {k: [c for c in v['copies'] if c['sec'] == '.data']
                     for k, v in per_iid.items()}})

# ---- R2 / R3：逐 IID 回退 ----
rows = []
for addr, e in per_iid.items():
    rdata = [c for c in e['copies'] if c['sec'] == '.rdata']
    rec = [c for c in e['copies'] if c['sec'] == '.data' and c['record']]
    coinc = [c for c in e['copies'] if c['sec'] == '.data' and not c['record']]
    n_rdata = sum(c['push_sites'] for c in rdata)
    n_rec = sum(c['push_sites'] for c in rec)
    n_coinc = sum(c['push_sites'] for c in coinc)
    rows.append({'iid': addr, 'guid': e['guid'],
                 'rdata_sites': n_rdata,
                 'record_copy_sites': n_rec, 'record_copy_vas': [c['va'] for c in rec],
                 'coincidence_sites': n_coinc,
                 'coincidence_vas': [c['va'] for c in coinc],
                 'prev_by_value': n_rdata + n_rec + n_coinc,
                 'corrected': n_rdata + n_rec})
for r in rows:
    print(json.dumps(r, ensure_ascii=False), flush=True)

bad = [r['iid'] for r in rows if r['coincidence_sites'] > 0]
ck('R2 【核心降级】有 %d 个 IID 的「按值口径」数字里混进了**巧合字节**上的站点（%s）⇒ '
   'r118a/r118b 的按值数字对这些 IID 偏高，必须回退' % (len(bad), bad),
   len(bad) >= 1, {'affected': bad,
          'detail': {r['iid']: {'coinc_vas': r['coincidence_vas'],
                                'coinc_sites': r['coincidence_sites']} for r in rows
                     if r['coincidence_sites']}})

ipsp = next(r for r in rows if r['iid'] == '0x7f7c80')
ipp = next(r for r in rows if r['iid'] == '0x7f7c70')
ck('R3a IPersistStream(0x7f7c80)：.rdata %d 站点 + 真记录拷贝 %d 站点（%s）+ 巧合 %d 站点；'
   '修正后数字 = %d（r118a 报的按值数是 %d）'
   % (ipsp['rdata_sites'], ipsp['record_copy_sites'], ipsp['record_copy_vas'],
      ipsp['coincidence_sites'], ipsp['corrected'], ipsp['prev_by_value']),
   True, ipsp)
ck('R3b IPersist(0x7f7c70)：.rdata %d 站点 + 真记录拷贝 %d 站点（%s）+ 巧合 %d 站点；'
   '修正后数字 = %d（r118a 报的按值数是 %d）'
   % (ipp['rdata_sites'], ipp['record_copy_sites'], ipp['record_copy_vas'],
      ipp['coincidence_sites'], ipp['corrected'], ipp['prev_by_value']),
   True, ipp)

# ---- R4：真记录拷贝上的站点是不是客户端 QI 请求 ----
import bisect
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L                        # noqa: E402
HB = sorted(L.HB)


def fn(a):
    j = bisect.bisect_right(HB, a) - 1
    return HB[j] if j >= 0 else None


TX = raw[L.fo(L.TEXT0):L.fo(L.TEXT0) + (L.TEXT1 - L.TEXT0)]


def pushes(va):
    p = b'\x68' + struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(L.TEXT0 + i)
        i = TX.find(p, i + 1)
    return out


def api(slot):
    p = b'\xff\x15' + struct.pack('<I', slot)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(L.TEXT0 + i)
        i = TX.find(p, i + 1)
    return out


SAVE = api(0x7e15f4)
r4 = []
for r in rows:
    for va in r['record_copy_vas']:
        for s in pushes(int(va, 16)):
            ins = list(L.MD.disasm_lite(raw[L.fo(s):L.fo(s) + 24], s))
            tail = ['%s %s' % (g[2], g[3]) for g in ins[:5]]
            qi = any(t.startswith('call dword ptr [') for t in tail)
            coupled = any(fn(t) == fn(s) and t > s for t in SAVE)
            r4.append({'iid': r['iid'], 'copy': va, 'site': hex(s),
                       'next5': tail, 'qi_shape': qi, 'save_after_in_fn': coupled})
n_qi = sum(1 for x in r4 if x['qi_shape'])
ck('R4 真记录拷贝上的 push 站点是否真是 QI 请求形态（push ppv;push iid;push this;call [reg]）：'
   '%d 个站点里 %d 个满足；其中同函数内之后有 OleSaveToStream 的 %d 个'
   % (len(r4), n_qi, sum(1 for x in r4 if x['save_after_in_fn'])),
   True, r4)

# ---- R5：记录判据的假阳/假阴 ----
# 5a 反向：.data 里所有 type_info vftable 出现位置，前面 16 字节是否都是 GUID 形状？
ti_pos = []
for a in range(DS, DE - 0x20, 4):
    try:
        if u32(a) == TIVT:
            ti_pos.append(a)
    except ValueError:
        break
paired = 0
for a in ti_pos:
    g = a - 0x10
    if fo(g) is None or g < DS:
        continue
    if u32(g + 8) == 0xc0 and u32(g + 0xc) == 0x46000000:
        paired += 1
ck('R5a 判据假阳/假阴：.data 里 type_info vftable 出现 %d 处，其中前面 16 字节构成'
   ' COM 形态 GUID 的 %d 处 ⇒ 该位置不专为 GUID 服务（若 %d 远小于 %d 则说明'
   '「type_info 紧跟 GUID」不是普遍结构）'
   % (len(ti_pos), paired, paired, len(ti_pos)),
   len(ti_pos) > paired,
   {'ti_positions': len(ti_pos), 'guid_paired': paired})

# 5b 正向：.data 里所有 GUID 形状常量，被判为记录的占比（若 100% 则判据无区分力）
gshape = []
for a in range(DS, DE - 0x20, 4):
    try:
        if u32(a + 8) == 0xc0 and u32(a + 0xc) == 0x46000000:
            gshape.append(a)
    except ValueError:
        break
rec_n = sum(1 for a in gshape if classify(a)['record'])
ck('R5b 区分力检查：.data 里 GUID 形状常量 %d 个，被判为真记录的 %d 个（%.1f%%）'
   ' ⇒ 判据有区分力（若为 100%% 则该判据恒真、无信息量）'
   % (len(gshape), rec_n, 100.0 * rec_n / max(1, len(gshape))),
   rec_n < len(gshape), {'n_shape': len(gshape), 'n_record': rec_n})

json.dump({'per_iid': rows, 'record_sites': r4,
           'ti_positions': len(ti_pos), 'guid_paired': paired,
           'checks': checks},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
