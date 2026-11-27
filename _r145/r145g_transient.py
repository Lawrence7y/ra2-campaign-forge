#!/usr/bin/env python3
"""R145 G：把「有装表站点」拆成「站点持久」与「站点被后续同槽写覆盖」（transient）两类。

r145e/r145f 证明 0x4A863C 这个循环是把 LayerClass 的基类链逐层写进**同一个槽**：
  VectorClass vptr → DynamicVectorClass vptr → LayerClass vptr（last-store-wins）。
即「静态出现过该虚表的装表指令」并不等于「运行时该对象最终持有该虚表」。
本脚本在全 .text 上做一次线性流式扫描，按基本块（遇 jmp/jcc/call/ret 断开）维护
(key = base reg + disp) 的「最后一次写入」，把每个 imm∈VTS 站点分成：
  persistent —— 块内没有后续对同一 (base,disp) 的 dword 立即数写
  transient  —— 块内后续被同一 (base,disp) 的 dword 立即数写覆盖（给出覆盖者）
然后按虚表统计：只被 transient 站点覆盖的虚表有哪些（这类表的「活」性无静态证据）。
内存纪律：disasm_lite 64 KB 流式，不开 detail=True。
"""
import sys, re, json, struct, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    base = m.group(1)
    if m.group(3) is None: return base, 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return base, (-v if m.group(2) == '-' else v)

sites = []    # (va, base, disp, vt)
block = 0
last = {}     # (base,disp) -> (va, vt, block)
BREAK = {'jmp','je','jne','jz','jnz','jb','jae','jl','jg','jle','jge','js','jns','ja','jbe',
         'ret','call','loop','jecxz','ja','jna','jnae','jnb','jnc','jng','jnge','jnl','jnle',
         'jno','jnp','jns','jo','jp','jpe','jpo'}
for a, sz, mn, op in B.sweep(md):
    if mn in BREAK or mn.startswith('j'):
        block += 1; last.clear(); continue
    if not op or not op.startswith('dword ptr ['): continue
    m = TOL.match(op)
    if not m: continue
    pm = parse_mem(m.group(1))
    if pm is None: continue
    base, disp = pm
    tgt = (m.group(2) or '').strip()
    if L.RE_IMM.match(tgt):
        iv = immv(tgt)
        sites.append((a, base, disp, iv, block))
        last[(base, disp)] = (a, iv, block, True)     # True = 立即数写
    elif tgt in GEN:
        last[(base, disp)] = (a, None, block, False)  # 寄存器写：来源未知

# 判定 persistent / transient：同块内存在更晚的同一 (base,disp) 写
by_key = collections.defaultdict(list)
for s in sites: by_key[(s[1], s[2])].append(s)
verdict = {}
for key, lst in by_key.items():
    lst.sort()
    for i, s in enumerate(lst):
        later = [x for x in lst[i + 1:] if x[4] == s[4]]
        verdict[s[0]] = ('transient', hex(later[0][3]), hex(later[0][0])) if later else ('persistent', None, None)

vt_persist = collections.defaultdict(set)
vt_trans = collections.defaultdict(set)
for a, base, disp, iv, blk in sites:
    if iv not in VTS: continue
    v = verdict.get(a, ('persistent', None, None))[0]
    (vt_persist if v == 'persistent' else vt_trans)[iv].add((hex(a), base, disp))
covP = set(vt_persist); covT = set(vt_trans); covAll = covP | covT
only_trans = sorted(covT - covP)
resid4 = [0x877000, 0x877010, 0x87B17C, 0x87B18C]
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N, 'vt_distinct': len(VTS),
 'sites_total': len(sites), 'imm_vts_sites': sum(1 for s in sites if s[3] in VTS),
 'persistent_sites': sum(1 for a, b, d, v, k in sites if v in VTS and verdict.get(a, ('persistent',))[0] == 'persistent'),
 'transient_sites': sum(1 for a, b, d, v, k in sites if v in VTS and verdict.get(a, ('persistent',))[0] == 'transient'),
 'blocks': block,
 'cov_all': len(covAll), 'cov_persistent': len(covP), 'cov_transient': len(covT),
 'only_transient_n': len(only_trans), 'only_transient': [hex(v) for v in only_trans],
 'only_transient_detail': [{'vt': hex(v), 'sites': sorted(vt_trans[v])[:4],
                            'verdicts': [[hex(int(st[0], 16)), verdict.get(int(st[0], 16))] for st in sorted(vt_trans[v])[:4]]} for v in only_trans],
 'resid4_in_all': [hex(v) for v in resid4 if v in covAll],
 'resid4_none': [hex(v) for v in resid4 if v not in covAll],
 'samples_chain': [[hex(a), b, d, hex(v), verdict.get(a)] for a, b, d, v, k in sites if 0x4A8640 <= a <= 0x4A8670],
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：0x4A8648/0x4A864F 判为 transient，0x4A8660 判为 persistent', verdict.get(0x4A8648, ('',))[0] == 'transient' and verdict.get(0x4A864F, ('',))[0] == 'transient' and verdict.get(0x4A8660, ('',))[0] == 'persistent', [verdict.get(0x4A8648), verdict.get(0x4A864F), verdict.get(0x4A8660)])
chk('正控：0x4A8648 的覆盖者是 0x7E4F64、0x4A864F 的覆盖者是 0x7E6060（链序）', verdict.get(0x4A8648, ('', None))[1] == '0x7e4f64' and verdict.get(0x4A864F, ('', None))[1] == '0x7e6060', [verdict.get(0x4A8648), verdict.get(0x4A864F)])
chk('块数 > 10000（断开点足够，判定不是单块累积）', block > 10000, block)
chk('persistent 覆盖 >= 1200 张（绝大多数虚表都有持久的静态装表）', len(covP) >= 1200, len(covP))
chk('存在只被 transient 覆盖的虚表（这一类「活」性无静态证据）', len(only_trans) >= 1, len(only_trans))
chk('这 4 张残余在两类口径下都没有站点（与 r145d 一致）', all(v not in covAll for v in resid4), res['resid4_none'])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145g_transient.json', 'w'), indent=1)
for k in ('sites_total','imm_vts_sites','persistent_sites','transient_sites','blocks','cov_all','cov_persistent','cov_transient','only_transient_n','only_transient','only_transient_detail','resid4_none','samples_chain'):
    print(k, '=', json.dumps(res[k], ensure_ascii=False))
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-60s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d elapsed %ss' % (res['pos_pass'], len(POS), res['pos_fail'], res['elapsed_s']))
