#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116j_refiid.py —— 链 M：OleLoadFromStream 的 **REFIID 形参位**（第 2 实参）这条
独立切面上，0x7f7c70 同样 0 次，而 ILocomotion(0x7ed358) 5 次。

为什么这是**第四条**判据来源（与前三轮都不同）：
  · R112–R115 服务端面：类 slot0 的 cmpsd 比对序列（识别集）
  · R116 客户端面 A：QueryInterface 的 riid（请求集，push imm32）
  · R116 客户端面 B：OleSaveToStream 的第 1 实参（类型上要求 IPersistStream*）
  · 本链 C：OleLoadFromStream 的第 2 实参 REFIID —— 这是一个**外部 API 明确要求
    一个 IID 指针**的位置。若 0x7f7c70 是某个"常用接口"（如 IPersist），
    反序列化路径上理应出现；实测 0 次。

断言：
  A1 OleLoadFromStream 全部 8 个调用点的第 2 实参逐个解出（立即数或寄存器）
  A2 其中立即数形态的：0x7ed358 出现 5 次、0x7e9af0 出现 1 次、0x7f7c70 **0 次**
  A3 对 2 个寄存器形态的站点，回溯其来源，如实登记（不得跳过不报）
  K1 反控：同一位置上 0x7ed358 出现 5 次 ⇒ 该位置确实被用来传 IID，不是"没人传 IID"
  K2 反控：把判据放宽成"整个函数内出现过 0x7f7c70"（不限形参位）仍为 0 —— 与 T1 一致
内存纪律：disasm_lite；detail 恒 False。
"""
import collections, json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
IAT_LOAD = 0x7e15f8
OUT = os.path.join(ROOT, '_r116/r116j_refiid.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


buf = raw[fo(TS):fo(TE)]
pat = struct.pack('<I', IAT_LOAD)
sites, i = [], buf.find(pat)
while i != -1:
    v = TS + i
    if raw[fo(v) - 2:fo(v)] == b'\xff\x15':
        sites.append(v - 2)
    i = buf.find(pat, i + 1)

rows = []
for s in sites:
    g = list(L.MD.disasm_lite(raw[fo(s) - 24:fo(s)], s - 24))
    pushes = [x for x in g if x[2] == 'push']
    arg1 = pushes[-1][3] if pushes else None
    arg2 = pushes[-2][3] if len(pushes) >= 2 else None
    rows.append({'site': hex(s), 'arg1_pStm': arg1, 'arg2_REFIID': arg2,
                 'npushes': len(pushes)})

ck('A1 OleLoadFromStream 全部 %d 个调用点的栈实参（cdecl：最后压 = arg1 pStm，'
   '倒数第二 = arg2 REFIID）：%s' % (len(sites), [(r['site'], r['arg1_pStm'], r['arg2_REFIID']) for r in rows]),
   len(sites) == 8, rows)

imm = collections.Counter(r['arg2_REFIID'] for r in rows if r['arg2_REFIID'] and r['arg2_REFIID'].startswith('0x'))
ck('A2 REFIID 位上的立即数分布：%s；0x7f7c70 出现 %d 次'
   % (dict(imm), imm.get('0x7f7c70', 0)),
   imm.get('0x7f7c70', 0) == 0 and imm.get('0x7ed358', 0) == 5,
   dict(imm))

import bisect
HB = sorted(L.HB)


def f_of(va):
    j = bisect.bisect_right(HB, va) - 1
    return HB[j] if j >= 0 else None


regs = [r for r in rows if r['arg2_REFIID'] and not r['arg2_REFIID'].startswith('0x')]
k2 = []
for r in regs:
    site = int(r['site'], 16)
    f = f_of(site)                      # 真正的宿主函数入口（不是站点自身）
    seg = raw[fo(f):fo(f) + min(2000, int(TE) - f)] if f else b''
    hit70 = struct.pack('<I', 0x7f7c70) in seg
    k2.append({'site': r['site'], 'reg': r['arg2_REFIID'],
               'fn': hex(f) if f else None, 'i70_in_fn': hit70})
ck('A3 %d 个寄存器形态的 REFIID 站点逐个回溯：%s ⇒ 其所在函数内**均未出现** 0x7f7c70；'
   '如实登记：寄存器来源未完全解出，不臆断其值' % (len(regs), k2),
   len(regs) == 2 and all(not x['i70_in_fn'] for x in k2), k2)

ck('K1 反控：同一 REFIID 位置上 ILocomotion(0x7ed358) 出现 %d 次 ⇒ 该形参位确实承载 IID，'
   '0x7f7c70 的 0 不是"这个位置没人用"造成的' % imm.get('0x7ed358', 0),
   imm.get('0x7ed358', 0) == 5, {'ed358': imm.get('0x7ed358', 0)})

whole70 = 0
for s in sites:
    f = f_of(s)
    if f is None:
        continue
    if struct.pack('<I', 0x7f7c70) in raw[fo(f):fo(f) + min(2000, int(TE) - f)]:
        whole70 += 1
ck('K2 反控：把判据放宽成「8 个调用点所在函数内出现过 0x7f7c70」（不限形参位），命中 %d'
   % whole70, whole70 == 0, {'whole_fn_hits': whole70})

json.dump({'sites': rows, 'refiid_imm': dict(imm), 'reg_sites': k2, 'checks': checks},
          open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
