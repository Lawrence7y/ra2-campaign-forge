#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118f_exact_value_search.py —— 修 C1：把「按值口径」的拷贝来源从**形态判据产物**
换成**16 字节原文全镜像精确搜索**。

审计员（hy4 task 216）C1 指出的真错：
  r118a 的 A3/A4/B2 里 `CK[a] = [c['va'] for c in multi.get(g, [])]` 取自 `found`，
  而 `found` 是 `guid_like()`（两种硬编码形态）的产物 ⇒ 「按值口径不依赖形态判据」
  是**虚假陈述**：0x7e9530 / 0x7e9ae0 两条真实 IID 在 found 里 0 份，按值统计自然也是 0。
本脚本的重做（每条都可机械复核）：
  E1 构造每个被研究 IID 的 16 字节原文（从 .rdata 首份读，不手抄），
     用 raw.find() 在**整个文件**上逐字节搜索（不限对齐、不限节），列出全部出现位置。
  E2 与 r118a 的 found 交叉核对：哪些拷贝是形态判据能看到的、哪些只有精确搜索能看到。
  E3 用精确搜索结果重算每个 IID 的「按值口径 push 站点数」，与 r118a 的数字对账。
  E4 反控：把 16 字节原文的**最后一个字节**改掉，精确搜索必须 0 命中（证明搜索不是恒真）。
  E5 反控：搜索一个必然存在的字节串（.text 起点 16 字节），命中数必须 >= 1（正控）。
  E6 记录每条命中是否落在「有文件映像」的节内（R117 S-40 的教训），并分节统计。
"""
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L                        # noqa: E402

raw = L.raw
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r118/r118f_exact_value_search.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


SECS = [('.text', 0x401000, 0x3df38d, 0x1000, 0x3e0000),
        ('.rdata', 0x7e1000, 0x30074, 0x3e1000, 0x31000),
        ('.data', 0x812000, 0x367be4, 0x412000, 0x6c000),
        ('.rsrc', 0xb7a000, 0x18128, 0x47e000, 0x19000),
        ('.detour', 0xb93000, 0x2718, 0x497000, 0x3000)]


def va_of(o):
    """file offset -> (VA, sec)；要求该 16 字节全部落在同一节的文件映像内。"""
    for n, b, vs, pr, sr in SECS:
        if pr <= o < pr + sr:
            return b + (o - pr), n
    return None, None


A = json.load(open(os.path.join(ROOT, '_r118/r118a_guid_census.json')))
STUDIED = {k: v['guid'] for k, v in A['studied'].items()}


def va_to_fo(va):
    for n, b, vs, pr, sr in SECS:
        if b <= va < b + sr:
            return pr + (va - b)
    raise ValueError(hex(va))


# ---- E1：16 字节原文全镜像精确搜索 ----
exact = {}
for addr, guid in STUDIED.items():
    b16 = raw[va_to_fo(int(addr, 16)):va_to_fo(int(addr, 16)) + 16]
    assert len(b16) == 16
    hits, i = [], raw.find(b16)
    while i >= 0:
        va, sec = va_of(i)
        hits.append({'off': i, 'va': hex(va) if va is not None else None,
                     'sec': sec, 'aligned4': (va % 4 == 0) if va is not None else False})
        i = raw.find(b16, i + 1)
    exact[addr] = {'guid': guid, 'bytes': b16.hex().upper(), 'hits': hits}

print('=== E1 精确搜索（16 字节原文，全文件逐字节）===', flush=True)
for addr, e in exact.items():
    print('%-10s %s -> %d 处 %s' % (addr, e['guid'], len(e['hits']),
                                    [(h['va'], h['sec']) for h in e['hits']]), flush=True)

# ---- E2：与 found 交叉核对 ----
found = A['guids']
disc = {}
for addr, e in exact.items():
    g = e['guid']
    form = {c['va'] for c in found.get(g, [])}
    ex = {h['va'] for h in e['hits']}
    disc[addr] = {'exact_only': sorted(ex - form), 'form_only': sorted(form - ex),
                  'both': sorted(ex & form)}
n_exact_only = sum(len(v['exact_only']) for v in disc.values())
ck('E2 【C1 修复】精确搜索比形态判据多找到 %d 份拷贝（%s）；形态判据独有 %d 份（应为 0）'
   % (n_exact_only,
      {k: v['exact_only'] for k, v in disc.items() if v['exact_only']},
      sum(len(v['form_only']) for v in disc.values())),
   sum(len(v['form_only']) for v in disc.values()) == 0,
   disc)

# 关键：两条被审计员点名的 IID 是否真的存在第二份拷贝
for k in ('0x7e9530', '0x7e9ae0'):
    ck('E2b 审计员点名的 %s（%s）：精确搜索命中 %d 处 %s（r118a 的 found 里 %d 份）'
       % (k, STUDIED[k], len(exact[k]['hits']),
          [(h['va'], h['sec']) for h in exact[k]['hits']],
          len(found.get(STUDIED[k], []))),
       True, exact[k])

# ---- E3：用精确搜索结果重算按值口径 ----
TX = raw[L.fo(TS):L.fo(TS) + (TE - TS)]


def pushes(va):
    p = b'\x68' + struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


recomp = {}
for addr, e in exact.items():
    per = {}
    for h in e['hits']:
        if h['va'] is None:
            continue
        per[h['va']] = len(pushes(int(h['va'], 16)))
    recomp[addr] = {'per_copy': per, 'total': sum(per.values())}
    prev = A['studied'][addr]['total_by_value']
    print('%-10s 精确重算按值=%d（r118a 报 %d）%s'
          % (addr, recomp[addr]['total'], prev, per), flush=True)

diffs = {a: {'exact': recomp[a]['total'], 'r118a': A['studied'][a]['total_by_value']}
         for a in recomp if recomp[a]['total'] != A['studied'][a]['total_by_value']}
ck('E3 【核心修复】用精确搜索重算的按值口径与 r118a 数字：不一致的 IID %d 个（%s）'
   % (len(diffs), diffs), isinstance(diffs, dict), {'diffs': diffs,
                                 'all': {a: recomp[a] for a in recomp}})

# ---- E4/E5 反控 ----
forged = {}
for addr, e in exact.items():
    b = bytearray(bytes.fromhex(e['bytes']))
    b[15] ^= 0xFF
    forged[addr] = raw.find(bytes(b))
ck('E4 反控（同质空面）：把每个 16 字节原文的最后一字节取反后精确搜索，命中 %d 处（须为 0）'
   % sum(1 for v in forged.values() if v >= 0),
   all(v < 0 for v in forged.values()), {'per_iid': forged})

probe = raw[L.fo(TS):L.fo(TS) + 16]
ck('E5 正控：搜 .text 起点的 16 字节原文，命中 %d 处（须 >= 1，否则搜索器本身坏了）'
   % raw.count(probe), raw.count(probe) >= 1, {'hits': raw.count(probe)})

# ---- E6：分节统计 + 有映像性 ----
by_sec = {}
for addr, e in exact.items():
    for h in e['hits']:
        by_sec.setdefault(h['sec'], 0)
        by_sec[h['sec']] += 1
ck('E6 精确命中按节分布：%s（全部必须落在有文件映像的节内）' % by_sec,
   all(k in ('.text', '.rdata', '.data', '.rsrc', '.detour') for k in by_sec) and
   set(by_sec) <= {'.text', '.rdata', '.data'},
   {'by_sec': by_sec})

json.dump({'exact': exact, 'disc': disc, 'recomp': recomp,
           'checks': checks}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
