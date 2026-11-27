#!/usr/bin/env python3
"""R144 H：第五形态 F7 = 把虚表地址写进栈帧（[esp+d]/[ebp+d]）—— 残余 45 张的真归属。

R144E 的 `refs` 计数器有自错（S-303）：它在 `RE_STORE.match` 命中后立即 continue，
而 `mov dword ptr [esp+0x20],0x7e3844` 正是 RE_STORE 的形态（base=esp 不在 GEN），
于是**所有栈写入都被跳过**，才造出「44/45 文本侧 0 引用」这个假事实。

本脚本：
  F7  站点：mov dword ptr [stk+d], imm∈VTS（stk ∈ {esp, ebp}）
  覆盖：F7 distinct
  并集：F1+F3+F4+F5+F6+F7 → 覆盖率、残余
  反控：F7 的 imm 换成等势伪虚表集合（seed=144）后的 distinct；
        栈写入的位移直方图（应与栈帧布局一致，集中在 0x8..0x50）
  另：对残余项给出「在哪个函数附近」的最近 call 目标（仅作定位提示，不作结论）
"""
import sys, json, struct, collections, hashlib, random, re
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN, STK = L.GEN, L.STK
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

f7 = []; disp_hist = collections.Counter(); allimm = []
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if not m: continue
    base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
    if tgt is None or not L.RE_IMM.match(tgt): continue
    iv = immv(tgt)
    if base in STK:
        allimm.append((a, base, ds, iv))
        if iv in VTS:
            f7.append((a, base, ds, iv)); disp_hist[ds] += 1

c7 = {s[3] for s in f7}
prev = json.load(open('_r144/r144e_residual.json'))
prior_cov = set()
# 重建 F1..F6 覆盖集合（与 r144a 同口径，最小重复实现）
f1 = []; f3 = []; f4 = []; f5 = []; pend = {}
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    m = L.RE_STORE.match(op)
    if m:
        base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
        if tgt is not None and L.RE_IMM.match(tgt):
            iv = immv(tgt)
            if iv in VTS:
                if base in GEN: (f1 if ds == 0 else f3).append((a, base, ds, iv))
                elif base.startswith('0x'): f4.append((a, base, ds, iv))
        elif tgt in GEN:
            p = pend.get(tgt)
            if p: f5.append((a, base, ds, p))
        continue
    if mn not in ('cmp', 'test'):
        d = op.partition(',')[0]; pend.pop(d, None)
        if mn == 'mov':
            ml = re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = v
        elif mn == 'lea':
            ml = re.match(r'^([a-z0-9]+),\[(0x[0-9a-f]+)\]$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = v
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'): pend.pop(r, None)
di = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in VTS and B.IB + ava + i * 4 != v - 4: di.append(v)
prior_cov = {s[3] for s in f1} | {s[3] for s in f3} | {s[3] for s in f4} | {s[3] for s in f5} | set(di)
U = prior_cov | c7
resid = sorted(VTS - U)

# 反控
random.seed(144)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4): pool.append(struct.unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
fk = {s[3] for s in f7 if s[3] in FAKE}

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS),
 'F7_sites': len(f7), 'F7_distinct': len(c7), 'F7_rate': round(len(c7) / len(VTS), 4),
 'F7_disp_hist_top': disp_hist.most_common(10),
 'F7_base': dict(collections.Counter(s[1] for s in f7)),
 'stack_imm_stores_total': len(allimm),
 'stack_imm_distinct_vt_share': round(len(c7) / len(VTS), 4),
 'prior_cov': len(prior_cov), 'union': len(U), 'union_rate': round(len(U) / len(VTS), 4),
 'resid_n': len(resid), 'resid': [hex(v) for v in resid],
 'resid_in_prior45': len(set(resid) & {int(x, 16) for x in [d[0] for d in prev['resid_detail']]}),
 'fake_F7_distinct': len(fk),
 'samples': [[hex(a), b, d, hex(v)] for a, b, d, v in f7[:12]],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('F7（栈帧写虚表）站点数 >= 100', len(f7) >= 100, len(f7))
chk('F7 解释了残余 45 张里的至少 40 张（S-304：原断言写成交集减残余，恒为 0，已改为 45-残余）', prev['resid_n'] - len(resid) >= 40, [prev['resid_n'], len(resid)])
chk('加上 F7 后覆盖率 > 99%', len(U) / len(VTS) > 0.99, round(len(U) / len(VTS), 4))
chk('F7 栈位移落在非负且 0x400 以内（栈帧/参数字区，非任意大偏移）', sum(n for d, n in disp_hist.items() if 0 <= d <= 0x400) / max(1, len(f7)) > 0.95, round(sum(n for d, n in disp_hist.items() if 0 <= d <= 0x400) / max(1, len(f7)), 3))
chk('反控：等势伪虚表的 F7 distinct 远小于真集合', len(fk) < len(c7) / 5, [len(fk), len(c7)])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144h_stack.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('POS',)}, indent=1, ensure_ascii=False)[:2600])
print('\n'.join('%-62s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
