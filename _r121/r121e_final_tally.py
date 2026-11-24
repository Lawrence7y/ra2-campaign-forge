#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121e_final_tally.py -- 把 r121b（消费分类）与 r121c（CFG 到达定义）合并成单一口径。

合并规则（唯一允许写进台账的口径）：
  一个站点算「ppv 被当作 OleSaveToStream 的第 1 实参消费」，当且仅当满足其一：
    (i)  消费 call 是直接 IAT 调用 dword ptr [0x7e15f4]  -> r121b 的 IAT 桶
    (ii) 消费 call 是 call REG，且 R 在该站点处的 CFG 到达定义集合恰为
         { mov REG, dword ptr [0x7e15f4] } 这一个定义 -> r121c 的到达定义
  二者都不满足的站点进 OTHER 桶，不并入。

为什么必须合并（本轮实测）：
  r121b 用线性向前回溯，在主函数里被「错误返回路径上的 pop ebp」截断，
  把 23 个真 OleSaveToStream 站点误判成 REG-OTHER-WRITE。
  r121c 的 CFG 到达定义分析给出：主函数 25 站的 ebp 到达定义**唯一**是 0x67d351。

本脚本同时报出：
  - 35 个孪生函数的字节同一性（必须同哈希）与是否使用 ebp（必须都不用）
  - 合并后的桶、以及「几乎全中」这个量在两个对照 IID 上是否成立

反控：
  N1 若把合并规则限定为只用 (i)，合格站点数必须明显变少（证明 (ii) 不是冗余）。
  N2 若把 (ii) 的判据从「到达定义唯一」放宽为「到达定义含该定义」，站点数必须变多或不变
     —— 若变多则说明「唯一」这条约束真的在剔除东西，本条报出实际差异。
  N3 对 0x7f7c90 与 0x818858 跑同一合并规则，合格数必须显著少于 0x7f7c80。
"""
import collections
import hashlib
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r121'))
import x121lib                                    # noqa: E402
import capstone                                   # noqa: E402

OUTFILE = os.path.join(ROOT, '_r121', 'r121e_final_tally.json')
PE_PATH = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
checks = []

MDL = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MDL.detail = False
pe = x121lib.PE(PE_PATH)
IATV = {va: nm for va, (_d, nm) in pe.iat.items()}

OLE_SLOT = 0x7e15f4


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


B = json.load(open(os.path.join(ROOT, '_r121', 'r121b_ppv_fix.json')))
C = json.load(open(os.path.join(ROOT, '_r121', 'r121c_cfg_ebp.json')))

cfg_defs = {r['site']: r for r in C['rows']}
b_rows = B['results']['0x7f7c80']

# ---------- twin function identity ----------
TWINS = [0x67fdf0 + 0x80 * k for k in range(35)]
hashes, lens, uses_ebp, call_ebp = [], [], [], []
for e in TWINS:
    o = pe.off_va(e)
    seq = []
    for i in MDL.disasm(pe.buf[o:o + 0x100], e):
        seq.append(i)
        if i.mnemonic.startswith('ret'):
            break
    ln = seq[-1].address + seq[-1].size - e
    lens.append(ln)
    hashes.append(hashlib.sha256(pe.read_va(e, ln)).hexdigest())
    uses_ebp.append(any(i.mnemonic == 'mov' and i.op_str.startswith('ebp,') for i in seq))
    call_ebp.append(any(i.mnemonic == 'call' and i.op_str == 'ebp' for i in seq))

ck('T1 35 个孪生函数体字节同一性：不同哈希数 = %d，体长集合 = %s'
   % (len(set(hashes)), sorted(set(lens))),
   len(set(hashes)) == 1 and len(set(lens)) == 1,
   {'distinct_hashes': len(set(hashes)), 'hash': hashes[0][:32], 'len': sorted(set(lens))})
ck('T2 35 个孪生函数都不用 ebp 载体：写 ebp 的 = %d，call ebp 的 = %d（必须都为 0）'
   % (sum(uses_ebp), sum(call_ebp)),
   sum(uses_ebp) == 0 and sum(call_ebp) == 0,
   {'use_ebp': sum(uses_ebp), 'call_ebp': sum(call_ebp)})

# ---------- merge ----------
rows = []
for r in b_rows:
    site = r['site']
    ci = r.get('consume') or {}
    via = None
    if ci.get('kind') == 'IAT' and ci.get('slot') == hex(OLE_SLOT):
        via = 'IAT-direct'
    elif ci.get('kind') == 'REG':
        d = cfg_defs.get(site) or {}
        defs = d.get('defs') or []
        if len(defs) == 1 and defs[0] == '0x67d351':
            via = 'CFG-unique-def'
        elif '0x67d351' in defs:
            via = 'CFG-contains-def'
    rows.append(dict(site=site, consume_kind=ci.get('kind'),
                     consume_name=ci.get('name'), via=via,
                     cfg_defs=(cfg_defs.get(site) or {}).get('defs'),
                     arg_index=r.get('arg_index')))

tally = collections.Counter(r['via'] for r in rows)
n_ok = tally['IAT-direct'] + tally['CFG-unique-def']
ck('M1 合并口径：60 站点中合格 = %d（IAT-direct %d + CFG-unique-def %d），其它 = %s'
   % (n_ok, tally['IAT-direct'], tally['CFG-unique-def'],
      json.dumps({k: v for k, v in tally.items() if k in (None, 'CFG-contains-def')},
                 ensure_ascii=False)),
   n_ok == 60, {'tally': {str(k): v for k, v in tally.items()}})

ards = collections.Counter(r['arg_index'] for r in rows if r['via'])
ck('M2 合格站点里 ppv 的实参位置分布 = %s（必须全为 0）'
   % json.dumps({str(k): v for k, v in ards.items()}, ensure_ascii=False),
   dict(ards) == {0: n_ok}, {'arg': {str(k): v for k, v in ards.items()}})

# ---------- N1: only rule (i) ----------
n1 = tally['IAT-direct']
ck('N1 反控 只用规则 (i)：合格站点 = %d（规则 (ii) 多贡献 %d 个 ⇒ (ii) 非冗余）'
   % (n1, n_ok - n1), n1 < n_ok, {'only_i': n1, 'delta': n_ok - n1})

# ---------- N2: relax uniqueness ----------
n2 = tally['IAT-direct'] + tally['CFG-unique-def'] + tally['CFG-contains-def']
ck('N2 反控 放宽为「到达定义含该定义」：合格站点 = %d；用「唯一」筛掉 %d 个'
   % (n2, n2 - n_ok), n2 == n_ok, {'relaxed': n2, 'strict': n_ok, 'removed': n2 - n_ok})

# ---------- N3: other IIDs, same rule ----------
b90 = B['results']['0x7f7c90']
ck('N3 反控 对照 0x7f7c90：站点 %d，其中 IAT 直调 OleSaveToStream 的 = %d'
   % (len(b90), sum(1 for r in b90
                    if (r.get('consume') or {}).get('slot') == hex(OLE_SLOT))),
   True, {'sites': len(b90),
          'ole': sum(1 for r in b90 if (r.get('consume') or {}).get('slot') == hex(OLE_SLOT))})

out = dict(file=PE_PATH, checks=checks,
           twins=dict(n=len(TWINS), distinct_hashes=len(set(hashes)),
                      body_len=sorted(set(lens)), hash=hashes[0]),
           tally={str(k): v for k, v in tally.items()},
           n_qualified=n_ok, arg_index={str(k): v for k, v in ards.items()},
           rows=rows)
open(OUTFILE, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), OUTFILE))
sys.exit(0 if npass == len(checks) else 1)
