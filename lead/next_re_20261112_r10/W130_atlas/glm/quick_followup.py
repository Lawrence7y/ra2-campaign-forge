# -*- coding: utf-8 -*-
"""收尾证据: 共享桩识别 / UNCERTAIN 形态分布 / NOT_VTABLE 明细 / multiref COL / MouseClass 对。"""
import json, struct, sys
from collections import Counter

import pefile
import capstone

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
HERE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\glm'
d = json.load(open(HERE + r'\vtable_candidates.json', encoding='utf-8'))
cands = d['candidates']
for c in cands:
    c['vt_i'] = int(c['vt'], 16)
    c['col_i'] = int(c['col'], 16)

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe', fast_load=True)
raw = pe.__data__


def rd(va, n=20):
    rva = va - 0x400000
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            off = rva - s.VirtualAddress
            if off + n <= s.SizeOfRawData:
                return raw[s.PointerToRawData + off:s.PointerToRawData + off + n]
    return None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True


def dis(va, n=6):
    b = rd(va)
    if b is None:
        return '(no bytes)'
    return ' | '.join('%s %s' % (i.mnemonic, i.op_str) for i in md.disasm(b, va))


print('== 0x004C9150 (两个纯接口唯一槽 / AbstractClass 主虚表内多次出现) ==')
print('   ', dis(0x4C9150))
print('== 0x00410260 (最高频槽值 x300) ==')
print('   ', dis(0x410260, 8))
print('== 0x00410210 (x224) ==')
print('   ', dis(0x410210, 6))
print('== 0x00410220 (x230) ==')
print('   ', dis(0x410220, 4))
print('== 0x00410300 (x222) ==')
print('   ', dis(0x410300, 4))

# --- UNCERTAIN 形态分布 ---
def shape(c):
    s = c['slots']
    if s[0]['tag'] not in ('C', 'P'):
        return 'slot0_not_code'
    if c['run'] == 12:
        return 'full12_but_flagged?'
    nxt = s[c['run']]
    if nxt['tag'] == 'D' and nxt['ann'].startswith('COL:'):
        return 'run%d_then_nextCOL' % c['run']
    return 'run%d_then_%s(%s)' % (c['run'], nxt['tag'], (nxt['ann'] or 'data')[:24])


unc = [c for c in cands if c['verdict'] == 'UNCERTAIN']
print('\n== UNCERTAIN %d 个的形态分布 ==' % len(unc))
for k, v in Counter(shape(c) for c in unc).most_common():
    print('   %-28s %d' % (k, v))

print('\n== NOT_VTABLE %d 个 ==' % len([c for c in cands if c['verdict'] == 'NOT_VTABLE']))
for c in cands:
    if c['verdict'] == 'NOT_VTABLE':
        print('   vt=%s col=%s off=%d %s | %s' % (c['vt'], c['col'], c['offset'],
                                                  c['name_raw'], c['reason']))

print('\n== 抽样 40 逐个判定 ==')
samp = set(d['stats']['sample'])
for c in cands:
    if c['vt'] in samp:
        print('   %s %-14s run=%2d xr=%3d %s' % (c['vt'], c['verdict'], c['run'], c['xr_text'],
                                                 c['name_disp'][:44]))

print('\n== MouseClass 相邻对 ==')
for c in cands:
    if c['vt_i'] in (0x7E195C, 0x7E1964):
        print('   vt=%s col=%s off=%d verdict=%s run=%d slots=%s' % (
            c['vt'], c['col'], c['offset'], c['verdict'], c['run'],
            ','.join(s['tag'] for s in c['slots'][:8])))

print('\n== CCINIClass 簇 (A2-A5) ==')
for c in cands:
    if c['vt_i'] in (0x7E1AF4, 0x7E1AFC, 0x7E1B04, 0x7E1B0C):
        print('   vt=%s col=%s off=%d verdict=%s slot0=%s slot0dis=%s' % (
            c['vt'], c['col'], c['offset'], c['verdict'], c['slots'][0]['val'], dis(int(c['slots'][0]['val'], 16), 3)))

# --- multiref COL ---
cols = set(c['col_i'] for c in cands)
cnt = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00')
    if nm not in (b'.rdata', b'.data'):
        continue
    for o in range(0, s.SizeOfRawData - 3, 4):
        v = struct.unpack_from('<I', raw, s.PointerToRawData + o)[0]
        if v in cols:
            cnt[v] = cnt.get(v, 0) + 1
multi = {('%08X' % k): v for k, v in cnt.items() if v > 1}
print('\n== 被引用 >1 次的 COL ==')
print('   ', multi)

# --- AbstractClass 主虚表(0x7E1F50) 里 0x4C9150 的槽位 ---
ac = [c for c in cands if c['vt_i'] == 0x7E1F50]
if ac:
    c = ac[0]
    print('\n== AbstractClass 主虚表 %s (off=%d) 前 24 槽 ==' % (c['vt'], c['offset']))
    print('   ', ', '.join('%d:%s(%s)' % (s['i'], s['val'], s['tag'] + (':pure?' if s['val'] == '0x004C9150' else '')) for s in c['slots']))
