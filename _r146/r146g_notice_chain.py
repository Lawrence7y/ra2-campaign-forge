#!/usr/bin/env python3
"""R146 G：0x7E1FB4 的归属定案 —— 用 CHD 继承链 + 同函数其余 vptr 交叉判定。

r146f 的一手现场（0x410170 起，INoticeSource 构造函数）：
    mov [eax+8],0x7e1fbc ; mov [eax+0xc],0x7e1fb4     <- 先写（基类子对象）
    ...                  ; mov [eax],0x7e1f50 ; mov [eax+4],0x7e1f34
    mov [eax+8],0x7e1f2c ; mov [eax+0xc],0x7e1f24      <- 再覆盖（本类 vptr）
⇒ 0x7e1fb4 写在 +0xc，且被同槽覆盖，但**覆盖者 0x7e1f24 也是同一类的 vptr 槽之一**。
故「瞬态」不等于「无主」。本脚本判定这几张虚表各自属于哪个类、在继承链的哪一层：

  Q1 六张虚表（0x7e1f50/0x7e1f34/0x7e1f2c/0x7e1f24/0x7e1fbc/0x7e1fb4）各是谁：
     COL→TD 名、COL.offset、CHD 基类链（名字 + mdisp + pdisp + vdisp）。
  Q2 0x7e1fb4 是否在 0x7e1f24 的 CHD 基类链里出现（若是 ⇒ 它确实是本类的一个基类子对象）。
  Q3 虚继承判定：若链上存在 pdisp != -1 的项 ⇒ 虚基类，子对象不嵌在对象内，
     其 vptr 槽由 vtordisp 偏移决定；这正是「写 +0xc 再覆盖」的结构来源。
  Q4 反控：把同一套判定套到 0x7e6060（LayerClass，R145 已证持久）上，看结构是否不同。
"""
import sys, json, struct, hashlib
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
TDname = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c

def col_of(vt):
    return COLof.get(vt)
def chd_of(col):
    p = B.dw(col + 16)
    return p if p and B.sec_of(p) else None
def parse_chd(p):
    n, arr = B.dw(p + 8), B.dw(p + 12)
    out = []
    if arr and B.sec_of(arr):
        for i in range(min(n or 0, 32)):
            bp = B.dw(arr + 4 * i)
            if not bp or not B.sec_of(bp): continue
            ptd = B.dw(bp)
            mdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0]
            pdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 12)))[0]
            vdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 16)))[0]
            out.append({'pTD': hex(ptd), 'name': TDname.get(ptd),
                        'numContained': B.dw(bp + 4),
                        'mdisp': mdisp, 'pdisp': pdisp, 'vdisp': vdisp})
    return {'sig': B.dw(p), 'numBase': n, 'bcds': out}

SIX = [0x7E1F50, 0x7E1F34, 0x7E1F2C, 0x7E1F24, 0x7E1FBC, 0x7E1FB4]
res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'vt': {}}
for vt in SIX + [0x7E6060]:
    c = col_of(vt)
    row = {'in_VTS': vt in VTS, 'col': hex(c) if c else None}
    if c:
        row.update({'td': hex(B.dw(c + 12)), 'td_name': TDname.get(B.dw(c + 12)),
                    'col_offset': B.dw(c + 4), 'cdOffset': B.dw(c + 8),
                    'col_dwords': [B.dw(c + 4 * k) for k in range(5)]})
        p = chd_of(c)
        if p:
            ch = parse_chd(p)
            row['chd'] = ch
            row['chain_names'] = [b['name'] for b in ch['bcds']]
            row['has_virtual_base'] = any(b['pdisp'] != -1 for b in ch['bcds'])
            row['vdisps'] = [b['vdisp'] for b in ch['bcds']]
    res['vt'][hex(vt)] = row

# Q2：0x7e1fb4 是否在其它五张的链里
tgt = TDname.get(B.dw(col_of(0x7E1FB4) + 12)) if col_of(0x7E1FB4) else None
res['target_td_name'] = tgt
res['appears_in_chain_of'] = {}
for vt in SIX + [0x7E6060]:
    r = res['vt'][hex(vt)]
    chain = r.get('chain_names') or []
    res['appears_in_chain_of'][hex(vt)] = [n for n in chain if n == tgt]

# Q3：six 的 vptr 槽位（写 +0/+4/+8/0xc 说明对象内 4 个 vptr）
# 用 .text 里对这六张虚表的写站点位移来定
import re, collections, bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
S = set(SIX)
hits = collections.defaultdict(list)
for a, sz, mn, op in B.sweep(md):
    if mn != 'mov' or not op: continue
    mt = TOL.match(op)
    if not mt: continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    tgt2 = (mt.group(2) or '').strip()
    if L.RE_IMM.match(tgt2) and immv(tgt2) in S:
        hits[immv(tgt2)].append((a, pm[0], pm[1]))
res['six_store_sites'] = {hex(v): [[hex(a), b, d] for a, b, d in sorted(hits[v])] for v in SIX}
res['six_disp_sets'] = {hex(v): sorted({d for _, _, d in hits[v]}) for v in SIX}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('六张虚表全在 VTS 里', all(v in VTS for v in SIX), [hex(v) for v in SIX if v not in VTS])
chk('0x7E1FB4 的 COL.offset == 0', res['vt']['0x7e1fb4'].get('col_offset') == 0, res['vt']['0x7e1fb4'].get('col_offset'))
chk('0x7E1F24 与 0x7E1FB4 写在同一批位移上（同槽覆盖）',
    set(res['six_disp_sets']['0x7e1f24']) & set(res['six_disp_sets']['0x7e1fb4']) != set(),
    [res['six_disp_sets']['0x7e1f24'], res['six_disp_sets']['0x7e1fb4']])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146g_notice_chain.json', 'w'), indent=1, ensure_ascii=False)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'])
