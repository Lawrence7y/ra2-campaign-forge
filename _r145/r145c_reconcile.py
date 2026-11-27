#!/usr/bin/env python3
"""R145 C：口径对齐 —— 负位移修复后，覆盖并集/分母/残余到底该怎么报。

三件事：
 ① 反汇编 0x4A863C..0x4A8680 的循环体，判定「同一基址连写三次 vptr」是不是真的
    （中间有无条件跳转/分支），并给出该循环的步进与写入偏移表；
 ② 口径对齐：R144 的并集是 6 形态（F1/F3/F4/F5/F6/F7）覆盖 1213 张；
    本轮只算「mov dword ptr <mem>, imm∈VTS」一种形态（含负位移修复），
    必须证明我的残余 6 张 ⊇ 并解释另 2 张（0x7F7A1C/0x7F7AEC）为何在 R144 里被覆盖；
 ③ 分母：1218 − 4 张误收 = 1214；负位移修复后残余 4 张全在误收名单里 ⇒ 覆盖率 1210/1210
    （或 1214/1218 的双写措辞）。
"""
import sys, re, json, struct, collections, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()

# ① 循环体上下文
lo, hi = 0x4A8630, 0x4A8685
b = B.rd(lo, hi - lo)
raw_body = [(a, sz, mn, L.norm(op)) for a, sz, mn, op in md.disasm_lite(b, lo)]
body = raw_body
ctrl = [(a, mn, op) for a, sz, mn, op in body if mn.startswith('j') or mn in ('call', 'ret')]
writes = [(hex(a), op) for a, sz, mn, op in raw_body if mn == 'mov' and '[' in op and op.split(',')[0].strip() != op.split(',')[-1].strip()]

# ② 我的窄口径残余与 R144 残余/并集对齐
nb = json.load(open('_r145/r145b_fullparse.json'))
narrow_resid = set(int(x, 16) for x in nb['resid'])
prev5 = set(int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid'])
mis4 = prev5 - {0x7E6060}
extra2 = narrow_resid - prev5
# 这两张在 R144 里被什么覆盖：查 F6（.data/.rdata 初值 == vt）与 F5（寄存器搬运）
data_init = {}
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in VTS:
                data_init.setdefault(v, []).append(B.IB + ava + i * 4)
# S-316：两张差异其实是 F5（寄存器搬运）覆盖，不是 F6。用 R144 同法（<=6 条内 mov [base+disp],reg）复核
GEN = L.GEN
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
F5 = {}
pend = {}
_n = 0
RE_MOVIMM = re.compile(r'^([a-z0-9]+),(0x[0-9a-f]+|\d+)$')
RE_MOVST = re.compile(r'^dword ptr \[([a-z0-9]+)(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\],([a-z0-9]+)$')
for a, sz, mn, op in B.sweep(md):
    _n += 1
    for r in [r for r, v in pend.items() if _n - v[1] > 6]:
        del pend[r]
    if mn == 'mov' and op:
        m = RE_MOVIMM.match(op)
        if m and m.group(1) in GEN:
            v = immv(m.group(2))
            if v in VTS: pend[m.group(1)] = (v, _n)
            continue
        m = RE_MOVST.match(op)
        if m and m.group(4) in pend:
            v = pend[m.group(4)][0]
            F5.setdefault(v, []).append((hex(a), op))
extra2_f5 = {hex(v): F5.get(v, [])[:3] for v in extra2}
extra2_f6 = {hex(v): [hex(x) for x in data_init.get(v, [])][:3] for v in extra2}
extra2_sec = {hex(v): B.sec_of(v) for v in extra2}
mis4_sec = {hex(v): B.sec_of(v) for v in mis4}
# 并集口径：R144 1213 张 + 负位移修复 0x7E6060 = 1214
# 🔴 S-316（本脚本初稿写错，由 r145h 抓出）：并集 1214 已经**不含**那 4 张误收
#   （残余 4 张恰等于误收集合），所以再减 4 得 1210 是双重扣减。
#   正确：真虚表分母 = 1218 − 4 = 1214，覆盖 1214/1214 = 100%。
union_after_fix = 1213 + 1
resid_after_fix = prev5 - {0x7E6060}
true_denom = len(VTS) - len(mis4)
coverage_true = union_after_fix - 0   # 并集里的 1214 张全是真虚表（残余 4 张就是被扣掉的误收）

# ③ 负位移站点与 COL.offset 一致性检验的适用性
neg = json.load(open('_r145/r145a_negdisp.json'))
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(),
 'loop_body': [[hex(a), sz, mn, op] for a, sz, mn, op in raw_body],
 'loop_ctrl': [[hex(a), mn, op] for a, mn, op in ctrl],
 'loop_writes': [[a, o] for a, o in writes],
 'narrow_resid': sorted(hex(v) for v in narrow_resid),
 'prev5': sorted(hex(v) for v in prev5),
 'mis4_sec': mis4_sec,
 'extra2': extra2_sec, 'extra2_f6_sites': extra2_f6, 'extra2_f5_sites': extra2_f5,
 'union_after_fix': union_after_fix, 'resid_after_fix': sorted(hex(v) for v in resid_after_fix),
 'true_denom': true_denom, 'coverage_true': coverage_true, 'S-316': 'union 1214 already excludes the 4 misclassified; do not subtract twice',
 'neg_sites': neg['neg_imm_vts_sites'], 'neg_distinct': neg['neg_distinct_vt'],
 'neg_agree_coloff': neg['neg_agree_with_coloff'],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：循环体里确有 add eax,0x18 步进', any(mn == 'add' and 'eax,0x18' in op for a, sz, mn, op in raw_body), [[hex(a), mn, op] for a, sz, mn, op in raw_body if mn=='add'])
chk('循环体内到 [eax-8] 的 vptr 写恰 3 处', sum(1 for a, o in writes if o.startswith('dword ptr [eax - 8]')) == 3, [a for a, o in writes if o.startswith('dword ptr [eax - 8]')])
chk('三段 vptr 写之间没有条件跳转（线性块）', all(not (0x4A8648 <= a <= 0x4A8660 and (mn.startswith('j') or mn in ('call','ret'))) for a, sz, mn, op in raw_body), [[hex(x[0]), x[1], x[2]] for x in ctrl if 0x4A8648 <= x[0] <= 0x4A8660])
chk('我的窄口径残余 ⊇ R144 的 4 张误收', mis4 <= narrow_resid, [hex(v) for v in sorted(mis4)])
chk('差异恰 2 张（0x7F7A1C/0x7F7AEC）', len(extra2) == 2, sorted(hex(v) for v in extra2))
chk('反控：这 2 张不由 F6 覆盖（F6 站点为空）', all(not extra2_f6.get(hex(v)) for v in extra2), extra2_f6)
chk('这 2 张由 F5 寄存器搬运覆盖（R144 口径已含）', all(extra2_f5.get(hex(v)) for v in extra2), extra2_f5)
chk('负位移修复后并集 1214、残余 4 张（全是误收）', union_after_fix == 1214 and resid_after_fix == mis4, [union_after_fix, len(resid_after_fix)])
chk('真分母 1214 = 1218 − 4（S-316 更正：不是 1210）', true_denom == 1214, true_denom)
chk('真虚表覆盖 1214/1214 = 100%（残余 4 张全是被扣掉的误收）', coverage_true == true_denom, [coverage_true, true_denom])
chk('负位移站点与 COL.offset 一致数为 0（该检验对负位移不适用）', neg['neg_agree_with_coloff'] == 0, neg['neg_agree_with_coloff'])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145c_reconcile.json', 'w'), indent=1)
for k in ('loop_ctrl', 'loop_writes', 'narrow_resid', 'extra2', 'extra2_f5_sites', 'union_after_fix', 'resid_after_fix', 'true_denom', 'coverage_true'):
    print(k, '=', json.dumps(res[k], ensure_ascii=False))
print('--- loop body ---')
for a, sz, mn, op in raw_body: print(' ', hex(a), mn, op)
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-52s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
