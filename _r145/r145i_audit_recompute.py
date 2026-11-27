#!/usr/bin/env python3
"""R145 I：复算审计 #323（deepseek，audit）的三条可核验断言（§2.12 规则 D）。

审计结论（不可直接采信，须复算）：
  A1 三张虚表 vptr 在 .text 的「原始 4 字节出现」数分别是 18 / 10 / 1，
     且 0x7E6060 的唯一出现是 0x4A8663（= 0x4A8660 指令的第 4 字节，立即数起点）。
  A2 LayerClass 的 CHD numBase=3，基类顺序 Layer -> DynamicVector -> Vector，mdisp 全 0、pdisp 全 -1。
  A3 结论性措辞：不能由「有装表指令」推「运行时持有」；分母应 1214/1218 并列再给 1214/1214。
A1/A2 是事实断言，必须复算；A3 是措辞建议，主会话据此改写正文（不属复算）。
"""
import sys, json, struct, hashlib, collections
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
raw = {}
for vt in (0x7E192C, 0x7E4F64, 0x7E6060):
    pat = struct.pack('<I', vt)
    hits = []; i = B.data.find(pat)
    while i >= 0:
        hits.append(i); i = B.data.find(pat, i + 1)
    raw[vt] = hits
text_lo = B.T[3]; text_hi = B.T[3] + B.T[4]
text_hits = {vt: [h for h in hs if text_lo <= h < text_hi] for vt, hs in raw.items()}
va_of = lambda off: B.IB + B.T[1] + (off - B.T[3])
name_of = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
def chd_chain(vt):
    c = B.dw(vt - 4); p = B.dw(c + 16)
    n = B.dw(p + 8); arr = B.dw(p + 12)
    out = []
    for k in range(n):
        bp = B.dw(arr + 4 * k)
        ptd = B.dw(bp)
        mdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0]
        pdisp = struct.unpack('<i', struct.pack('<I', B.dw(bp + 12)))[0]
        out.append({'name': name_of.get(ptd), 'mdisp': mdisp, 'pdisp': pdisp})
    return n, out

chain = {hex(vt): chd_chain(vt) for vt in (0x7E192C, 0x7E4F64, 0x7E6060)}
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(),
 'raw_hits_all': {hex(k): [hex(va_of(o)) for o in v] for k, v in raw.items()},
 'text_hits_n': {hex(k): len(v) for k, v in text_hits.items()},
 'text_hits_va': {hex(k): [hex(va_of(o)) for o in v][:20] for k, v in text_hits.items()},
 'chain': chain,
 'in_vts': {hex(vt): vt in VTS for vt in (0x7E192C, 0x7E4F64, 0x7E6060)},
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('A1a 三张在 .text 的原始 4 字节出现数 = 18 / 10 / 1（审计数字）', [len(text_hits[v]) for v in (0x7E192C, 0x7E4F64, 0x7E6060)] == [18, 10, 1], [len(text_hits[v]) for v in (0x7E192C, 0x7E4F64, 0x7E6060)])
chk('A1b 0x7E6060 的唯一出现地址是 0x4A8663（立即数起点，非指令起点 0x4A8660）', [hex(va_of(o)) for o in text_hits[0x7E6060]] == ['0x4a8663'], [hex(va_of(o)) for o in text_hits[0x7E6060]])
chk('A1c 0x4A8663 − 0x4A8660 = 3（mov 的 imm32 偏移）', [va_of(o) - 0x4A8660 for o in text_hits[0x7E6060]] == [3], [va_of(o) - 0x4A8660 for o in text_hits[0x7E6060]])
chk('A2a LayerClass CHD numBase = 3（审计数字）', chain['0x7e6060'][0] == 3, chain['0x7e6060'][0])
chk('A2b 基类顺序 Layer -> DynamicVector -> Vector', [b['name'] for b in chain['0x7e6060'][1]] == ['.?AVLayerClass@@', '.?AV?$DynamicVectorClass@PAVObjectClass@@', '.?AV?$VectorClass@PAVObjectClass@@'], [b['name'] for b in chain['0x7e6060'][1]])
chk('A2c 三条链 mdisp 全 0、pdisp 全 -1', all(all(b['mdisp'] == 0 and b['pdisp'] == -1 for b in ch[1]) for ch in chain.values()), {k: [(b['mdisp'], b['pdisp']) for b in v[1]] for k, v in chain.items()})
chk('反控：三张都在 VTS 内（不是审计自己选的假地址）', all(v for v in res['in_vts'].values()), res['in_vts'])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145i_audit_recompute.json', 'w'), indent=1)
for k in ('text_hits_n','text_hits_va','chain','in_vts'):
    print(k, '=', json.dumps(res[k], ensure_ascii=False)[:700])
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-62s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
