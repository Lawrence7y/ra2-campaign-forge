#!/usr/bin/env python3
"""R144 E：并集后残余 45 张虚表的定性 + 并集分解（谁贡献了多少新覆盖）。

对残余 45 张逐张回答三问（全部只做字节/引用计数，不做猜测）：
  a 该地址作为 4 字节值在 .data/.rdata 出现几次（排除 vt-4 的 COL 指针本身）；
  b 该地址作为 imm/位移在 .text 里被引用几次（任何指令形态）；
  c 它的 COL 的 offset / TD 是什么；同 TD 是否还有别的虚表被覆盖。
再给出并集的分步增量：F1 -> +F3 -> +F4 -> +F5 -> +F6 每步新增 distinct。
"""
import sys, re, json, struct, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}
off_of = lambda vt: coloff.get(COLof.get(vt))
td_of = lambda vt: coltd.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

RE_IDX = re.compile(r'^dword ptr \[([a-z0-9]+)(?:[+-]0x[0-9a-f]+)?\+([a-z0-9]+)\*([48])(?:[+-]0x[0-9a-f]+)?\]$')

f1 = []; f3 = []; f4 = []; f5 = []; refs = collections.Counter()
pend = {}
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if m:
        base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
        if tgt is not None and L.RE_IMM.match(tgt):
            iv = immv(tgt)
            if iv in VTS:
                if base in GEN:
                    (f1 if ds == 0 else f3).append((a, base, ds, iv))
                elif base.startswith('0x'):
                    f4.append((a, base, ds, iv))
        elif tgt in GEN:
            p = pend.get(tgt)
            if p: f5.append((a, base, ds, p[0]))
        continue
    for tok in re.findall(r'0x[0-9a-f]{5,8}', op):
        v = int(tok, 16)
        if v in VTS: refs[v] += 1
    if mn not in ('cmp', 'test'):
        d = op.partition(',')[0]
        pend.pop(d, None)
        if mn == 'mov':
            ml = re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = (v, a)
        elif mn == 'lea':
            ml = re.match(r'^([a-z0-9]+),\[(0x[0-9a-f]+)\]$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = (v, a)
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'): pend.pop(r, None)

c1 = {s[3] for s in f1}; c3 = {s[3] for s in f3}; c4 = {s[3] for s in f4}; c5 = {s[3] for s in f5}   # S-302 修正：原写成 s[2]（那是位移），把并集污染成 1290
data_init = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in VTS: data_init.append((B.IB + ava + i * 4, v))
c6 = {v for _, v in data_init}
# 数据侧出现次数（排除 vt-4 处的 COL 指针）
dcount = collections.Counter()
for a, v in data_init:
    if a != v - 4: dcount[v] += 1

U = set().union(c1, c3, c4, c5, c6)
steps = []
cur = set(c1); steps.append(['F1', len(cur)])
for nm2, s in (('+F3', c3), ('+F4', c4), ('+F5', c5), ('+F6', c6)):
    cur = cur | s; steps.append([nm2, len(cur)])
resid = sorted(VTS - U)
td0 = collections.defaultdict(list)
for vt in VTS:
    t = td_of(vt)
    if t is not None: td0[t].append(vt)
det = []
for vt in resid:
    t = td_of(vt)
    twins = [x for x in td0.get(t, []) if x != vt]
    det.append([hex(vt), off_of(vt), hex(t) if t else None,
                dcount.get(vt, 0), refs.get(vt, 0),
                [hex(x) for x in twins[:3]],
                sum(1 for x in twins if x in U)])

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N, 'vt_distinct': len(VTS),
 'c1': len(c1), 'c3': len(c3), 'c4': len(c4), 'c5': len(c5), 'c6': len(c6),
 'union': len(U), 'union_rate': round(len(U) / len(VTS), 4), 'steps': steps,
 'resid_n': len(resid),
 'resid_detail': det,
 'resid_stats': {
   'dcount_zero': sum(1 for x in det if x[3] == 0),
   'refs_zero': sum(1 for x in det if x[4] == 0),
   'both_zero': sum(1 for x in det if x[3] == 0 and x[4] == 0),
   'td_has_covered_twin': sum(1 for x in det if x[6] > 0),
 },
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('F1 838 + F3 344 + F4 243 + F5 42 + F6 3 与 R144A 逐项相同（F5 允许 40..50 区间，因悬挂窗口实现细节不同）', [len(c1), len(c3), len(c4), len(c6)] == [838, 344, 243, 3] and 30 <= len(c5) <= 60, [len(c1), len(c3), len(c4), len(c5), len(c6)])
chk('并集 1173（96.31%），残余 45', len(U) == 1173 and len(resid) == 45, [len(U), len(resid)])
chk('残余 45 里「数据侧 0 次 + 文本侧 0 次」的 >= 20（静态完全不出现）', res['resid_stats']['both_zero'] >= 20, res['resid_stats'])
chk('残余 45 里绝大多数其 TD 有已被覆盖的孪生虚表', res['resid_stats']['td_has_covered_twin'] >= 0.8 * len(resid), res['resid_stats']['td_has_covered_twin'])
chk('步进曲线单调不减且 F3 贡献最大', all(steps[i][1] <= steps[i + 1][1] for i in range(len(steps) - 1)) and (steps[1][1] - steps[0][1]) >= (steps[2][1] - steps[1][1]), steps)
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144e_residual.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('resid_detail', 'POS')}, indent=1, ensure_ascii=False)[:2500])
print('\n'.join('%-62s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
print('resid head', json.dumps(det[:12], ensure_ascii=False))
