#!/usr/bin/env python3
"""R146 J：复算审计员 #326 的三条批评（规则 D —— 逐条自证，不采信转述）。

批评 1（断言 B 歧义）：.?AVINoticeSource@@ 被两个地址指代 —— 自有虚表 0x7E1FB4（COL locator=0）
  与 AbstractClass 组的 locator=12 子对象虚表 0x7E1F24。审计员称 0x7E1F24 在 .text 出现 5 次、
  位移全 12、基址 {eax,ecx,esi}；0x7E1FB4 出现 3 次、全 eax。
批评 2（断言 C 事实性错误）：LayerClass 的 CHD numBaseClasses=3，但 [0] 是**类自身**，
  真基类只有 2 个；写成「基类链长度 3」会被读成「3 个基类」。
批评 3（计数口径）：按「原始对齐 dword」与「解码后的立即数」计数会不同，
  审计员举 0x7E1FC8 raw=3 / decode=0 为例。

本脚本逐条复算，并给出「两种计数口径」的完整对照表（不只挑一个例子）。
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

def tdof(col):
    return B.dw(col + 12) if col else None
def chd_of(col):
    p = B.dw(col + 16)
    return p if p and B.sec_of(p) else None
def parse_chd(p):
    n, arr = B.dw(p + 8), B.dw(p + 12)
    out = []
    if arr and B.sec_of(arr):
        for i in range(min(n or 0, 64)):
            bp = B.dw(arr + 4 * i)
            if not bp or not B.sec_of(bp): continue
            out.append({'td': B.dw(bp), 'name': TDname.get(B.dw(bp)),
                        'ncb': B.dw(bp + 4),
                        'mdisp': struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0],
                        'pdisp': struct.unpack('<i', struct.pack('<I', B.dw(bp + 12)))[0],
                        'vdisp': struct.unpack('<i', struct.pack('<I', B.dw(bp + 16)))[0]})
    return {'chd_va': p, 'numBaseClasses': n, 'pArray': arr, 'bcds': out}

# ---------- 批评 1：两个地址的站点 ----------
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

# 决定 0x7E1F24 / 0x7E1FB4 / 0x7E1F50 / 0x7E1F34 各自是谁
who = {}
for vt in (0x7E1F24, 0x7E1FB4, 0x7E1F50, 0x7E1F34, 0x7E1F2C, 0x7E1FBC, 0x7E1FC8):
    c = COLof.get(vt)
    who[hex(vt)] = {'col': hex(c) if c else None,
                    'locator': B.dw(c + 4) if c else None,
                    'td': hex(tdof(c)) if c else None,
                    'td_name': TDname.get(tdof(c)) if c else None,
                    'in_VTS': vt in VTS}

TARGETS = (0x7E1F24, 0x7E1FB4, 0x7E1F50, 0x7E1F34, 0x7E1F2C, 0x7E1FBC, 0x7E1FC8)
TARGET = set(TARGETS)
decode_sites = collections.defaultdict(list)
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    mt = TOL.match(op)
    if not mt: continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    t = (mt.group(2) or '').strip()
    if L.RE_IMM.match(t) and immv(t) in TARGET:
        decode_sites[immv(t)].append({'va': a, 'base': pm[0], 'disp': pm[1], 'mn': mn})

# raw 对齐 dword 计数（各节）
raw = {}
for nm, ava, vs, rr, rs in B.secs:
    blob = B.data[rr:rr + rs]
    for vt in TARGETS:
        pat = vt.to_bytes(4, 'little')
        n = 0; i = blob.find(pat)
        while i >= 0:
            n += 1; i = blob.find(pat, i + 1)
        if n: raw.setdefault(hex(vt), {})[nm] = n

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'who': who,
       'decode_count': {hex(v): len(decode_sites[v]) for v in TARGET},
       'decode_bases': {hex(v): sorted({s['base'] for s in decode_sites[v]}) for v in TARGET},
       'decode_disps': {hex(v): sorted({s['disp'] for s in decode_sites[v]}) for v in TARGET},
       'decode_sites': {hex(v): [[hex(s['va']), s['base'], s['disp']] for s in sorted(decode_sites[v], key=lambda x: x['va'])] for v in TARGET},
       'raw_dword': raw}

# ---------- 批评 2：LayerClass 与 AbstractClass 的 CHD 是否把「自身」放在 [0] ----------
def chain_of(vt):
    c = COLof.get(vt)
    return parse_chd(chd_of(c)) if c else None
lay = chain_of(0x7E6060)
abs_ = chain_of(0x7E1F50)
res['C_layer'] = lay
res['C_abstract'] = abs_
res['C_layer_self_at_0'] = (lay and lay['bcds'] and lay['bcds'][0]['td'] == tdof(COLof[0x7E6060]))
res['C_abstract_self_at_0'] = (abs_ and abs_['bcds'] and abs_['bcds'][0]['td'] == tdof(COLof[0x7E1F50]))
# 真基类数 = numBaseClasses - 1；嵌套读法（沿 ncb 链）也数一遍
def nested_len(entry):
    """按 numContainedBases 递归展开的祖先个数（不含自身）。"""
    if entry['ncb'] == 0: return 0
    if entry['ncb'] == 1 and entry is not None: return 1
    return entry['ncb']
res['C_layer_ncb'] = [b['ncb'] for b in (lay['bcds'] if lay else [])]

# ---------- 批评 3：raw vs decode 全表 ----------
mismatch = {}
for v, d in res['decode_count'].items():
    r = sum(raw.get(v, {}).values())
    if r != d: mismatch[v] = {'raw': r, 'decode': d, 'raw_by_sec': raw.get(v, {})}
res['raw_vs_decode_mismatch'] = mismatch

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('0x7E1F24 是 AbstractClass 的 locator=12 虚表（不是 INoticeSource 自有虚表）',
    who['0x7e1f24']['td_name'] == '.?AVAbstractClass@@' and who['0x7e1f24']['locator'] == 12, who['0x7e1f24'])
chk('0x7E1FB4 是 INoticeSource 的 locator=0 自有虚表',
    who['0x7e1fb4']['td_name'] == '.?AVINoticeSource@@' and who['0x7e1fb4']['locator'] == 0, who['0x7e1fb4'])
chk('审计员批评 1 成立：0x7E1F24 解码命中 5 次', res['decode_count']['0x7e1f24'] == 5, res['decode_count']['0x7e1f24'])
chk('0x7E1F24 的 5 处位移全为 12',
    res['decode_disps']['0x7e1f24'] == [12], res['decode_disps']['0x7e1f24'])
chk('0x7E1F24 的基址集合含 3 个寄存器（不是全 eax）',
    len(res['decode_bases']['0x7e1f24']) == 3, res['decode_bases']['0x7e1f24'])
chk('0x7E1FB4 解码命中 3 次且全 eax、全位移 12',
    res['decode_count']['0x7e1fb4'] == 3 and res['decode_bases']['0x7e1fb4'] == ['eax']
    and res['decode_disps']['0x7e1fb4'] == [12],
    [res['decode_count']['0x7e1fb4'], res['decode_bases']['0x7e1fb4'], res['decode_disps']['0x7e1fb4']])
chk('审计员批评 2 成立：LayerClass CHD 的 [0] 就是 LayerClass 自身', res['C_layer_self_at_0'], res['C_layer_self_at_0'])
chk('LayerClass numBaseClasses=3 但真基类只有 2 个',
    lay['numBaseClasses'] == 3 and len(lay['bcds']) == 3 and lay['bcds'][0]['name'] == '.?AVLayerClass@@',
    [lay['numBaseClasses'], [b['name'] for b in lay['bcds']]])
chk('AbstractClass CHD 的 [0] 也是自身（8 项 = 自身 + 7 基类）',
    res['C_abstract_self_at_0'] and abs_['numBaseClasses'] == 8, [abs_['numBaseClasses'], abs_['bcds'][0]['name']])
chk('LayerClass 三项 pdisp 全 -1', all(b['pdisp'] == -1 for b in lay['bcds']), [b['pdisp'] for b in lay['bcds']])
chk('审计员批评 3 成立：至少存在一个 raw != decode 的地址', len(mismatch) >= 1, mismatch)
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146j_audit_recheck.json', 'w'), indent=1, ensure_ascii=False)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'])
