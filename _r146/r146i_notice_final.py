#!/usr/bin/env python3
"""R146 I：0x7E1FB4（INoticeSource 的虚表）归属定案 —— 修正 r146h 那条错误断言。

r146h 里我写了「0x7E1F24 与 0x7E1FB4 的 CHD 逐项相同」，实测 FAIL：两者是**不同类**的 COL
（0x7E1F24 → TD=AbstractClass，链 8 项；0x7E1FB4 → TD=INoticeSource，链 1 项）。
正确的结构是「基类子对象构造完 → 派生类 ctor 把同一槽全覆写」，本脚本把它钉成可失败断言：

  S1 六张虚表的 TD / COL.offset / CHD 长度各自独立取，不假设任何两张同链。
  S2 0x410170 那段的写入序列按地址排序，逐条给出 (位移, vtable, 该类在该链上的 mdisp)，
     验证「基类子对象 vptr 写在它自己的 mdisp 槽上」：INoticeSink→+8、INoticeSource→+0xc。
  S3 覆盖者 0x7E1F24 的 COL.offset 恰为 12 ⇒ 它写在同一槽 [this+0xc]，是**派生类**在此槽的 vptr。
  S4 是否存在「INoticeSource 作为最派生类被构造」的路径：若三处写 0x7E1FB4 的函数全都是
     被更大 ctor 内联/调用的子对象 ctor（即同函数里还有对其它槽的写、或调用者另有 thiscall），
     则现盘没有 INoticeSource 独占实例 ⇒ 该虚表**永不静止存在**，但其归属明确、不是「无主」。
  S5 反控：LayerClass 0x7E6060 的 CHD 有 3 项且 mdisp 全 0（R145 已证），与本组结构不同。
"""
import sys, re, json, struct, collections, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
TDname = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c

def chain(col):
    p = B.dw(col + 16)
    if not p or not B.sec_of(p): return None
    n, arr = B.dw(p + 8), B.dw(p + 12)
    if not arr or not B.sec_of(arr): return None
    out = []
    for i in range(min(n or 0, 32)):
        bp = B.dw(arr + 4 * i)
        if not bp or not B.sec_of(bp): continue
        out.append({'td': B.dw(bp), 'name': TDname.get(B.dw(bp)),
                    'mdisp': struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0],
                    'pdisp': struct.unpack('<i', struct.pack('<I', B.dw(bp + 12)))[0]})
    return out

SIX = [0x7E1F50, 0x7E1F34, 0x7E1F2C, 0x7E1F24, 0x7E1FBC, 0x7E1FB4]
res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'vt': {}}
for vt in SIX + [0x7E6060]:
    c = COLof.get(vt)
    res['vt'][hex(vt)] = {'td': hex(B.dw(c + 12)) if c else None,
                          'td_name': TDname.get(B.dw(c + 12)) if c else None,
                          'col_offset': B.dw(c + 4) if c else None,
                          'chain_len': len(chain(c)) if c else None,
                          'chain': chain(c) if c else None}

# ---- S2：0x410170 段的写入序列 ----
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

seq = []
for a, sz, mn, op in B.sweep(md):
    if mn != 'mov' or not op: continue
    mt = TOL.match(op)
    if not mt: continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    t = (mt.group(2) or '').strip()
    if L.RE_IMM.match(t) and immv(t) in VTS:
        seq.append((a, pm[0], pm[1], immv(t)))
W = [s for s in seq if 0x410170 <= s[0] < 0x410200]
# 对每张写在 [eax+disp] 的虚表，找「同一条链上该表自己 TD 的 mdisp」
def mdisp_in(chain_of_col, td):
    for b in (chain_of_col or []):
        if b['td'] == td: return b['mdisp']
    return None
cols = {vt: COLof.get(vt) for vt in SIX}
abstract_chain = chain(cols[0x7E1F50]) if cols.get(0x7E1F50) else None
annot = []
for a, base, disp, vt in sorted(W):
    own_td = B.dw(cols[vt] + 12) if cols.get(vt) else None
    annot.append({'va': hex(a), 'base': base, 'disp': disp, 'vt': hex(vt),
                  'own_td': TDname.get(own_td),
                  'mdisp_of_own_td_in_abstract_chain': mdisp_in(abstract_chain, own_td)})
res['S2_window'] = annot
res['S2_abstract_chain'] = abstract_chain

# ---- S4：三处写 0x7E1FB4 的函数里，有没有别的 vptr 写（= 是子对象 ctor 而非独占 ctor） ----
sites = [(a, b, d) for a, b, d, v in seq if v == 0x7E1FB4]
from capstone import Cs as _Cs
calltgt = []
for a, sz, mn, op in B.sweep(md):
    if mn == 'call' and op and re.match(r'^0x[0-9a-f]+$', op): calltgt.append(int(op, 16))
ct = sorted(set(calltgt))
import bisect
def func_of(va):
    i = bisect.bisect_right(ct, va) - 1
    return ct[i] if i >= 0 else None
per = {}
for a, b, d in sites:
    f = func_of(a)
    others = [(hex(x), bb, dd, hex(v)) for x, bb, dd, v in seq
              if func_of(x) == f and v != 0x7E1FB4]
    # 该函数是否也被当作被调用者（有 call 指向它）
    called = f in ct
    per[hex(a)] = {'func': hex(f) if f else None, 'other_vptr_writes_in_func': others[:12],
                   'n_other': len(others), 'func_is_call_target': called}
res['S4'] = per

# ---- S5 反控 ----
lay = res['vt']['0x7e6060']
res['S5'] = {'layer_chain_len': lay['chain_len'],
             'layer_mdisps': [b['mdisp'] for b in (lay['chain'] or [])],
             'abstract_chain_len': len(abstract_chain or [])}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('C2 更正：0x7E1F24 与 0x7E1FB4 属于不同 TD（r146h 那条断言是错的）',
    res['vt']['0x7e1f24']['td'] != res['vt']['0x7e1fb4']['td'],
    [res['vt']['0x7e1f24']['td_name'], res['vt']['0x7e1fb4']['td_name']])
chk('INoticeSink 的虚表写在 +8 = 它在 AbstractClass 链上的 mdisp',
    any(x['vt'] == '0x7e1fbc' and x['disp'] == 8 and x['mdisp_of_own_td_in_abstract_chain'] == 8 for x in annot),
    [x for x in annot if x['vt'] == '0x7e1fbc'][:2])
chk('INoticeSource 的虚表写在 +0xc = 它在 AbstractClass 链上的 mdisp',
    any(x['vt'] == '0x7e1fb4' and x['disp'] == 12 and x['mdisp_of_own_td_in_abstract_chain'] == 12 for x in annot),
    [x for x in annot if x['vt'] == '0x7e1fb4'][:2])
chk('覆盖者 0x7E1F24 的 COL.offset == 12（同一槽）',
    res['vt']['0x7e1f24']['col_offset'] == 12, res['vt']['0x7e1f24']['col_offset'])
chk('三处写 0x7E1FB4 的函数里都有对别的槽的 vptr 写（子对象 ctor，非独占 ctor）',
    all(v['n_other'] >= 2 for v in per.values()), {k: v['n_other'] for k, v in per.items()})
chk('S5 反控：LayerClass 链长 3 且 mdisp 全 0（与本组结构不同）',
    lay['chain_len'] == 3 and all(b['mdisp'] == 0 for b in lay['chain']),
    [lay['chain_len'], [b['mdisp'] for b in lay['chain']]])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146i_notice_final.json', 'w'), indent=1, ensure_ascii=False)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'])
