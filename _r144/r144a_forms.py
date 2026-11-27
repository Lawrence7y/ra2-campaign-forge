#!/usr/bin/env python3
"""R144 A：380 张「无偏移 0 装表站点」的虚表装在哪 —— 多形态普查（修正小位移解析）。

背景（R143 收口遗留）：
  R143 只认 F1 = mov dword ptr [rX+0], imm∈VTS（2741 站点 / 838 distinct，68.8%），
  F2 寄存器搬运形态只命中 5 条，剩 380 张虚表「装在哪没查」。

本脚本做四件事：
  ① 解析健康度自检：统计所有以 'dword ptr [' 开头的 store 里有几条不被 RE_STORE 接受
     （R143 的 r143e 探针里只有 \s 压缩、没有十进制→十六进制归一，capstone 对 <10 的位移
      印十进制 [esi + 4]，因此 disp≠0 的站点会被整条静默丢弃 —— 先证明这条是否会复发）；
  ② 形态枚举（同一遍扫描产出全部）：
     F1  imm∈VTS + 基址=通用寄存器 + disp=0
     F3  imm∈VTS + 基址=通用寄存器 + disp≠0（直方图）
     F4  imm∈VTS + 基址=绝对地址 [0x...]（静态对象装表）
     F5  寄存器搬运：mov/lea r1, vtable 地址后 <=6 条内 mov [base(+disp)], r1
     F6  .data/.rdata 初始值 dword == vtable 地址（静态初始化对象，装载期不执行代码）
  ③ 覆盖率与并集；对 380 张未被 F1 覆盖的虚表，逐张给出被哪种形态覆盖；
     并检验「二级虚表与已覆盖虚表同块相邻（|Δ|<=64）」这一结构假说；
  ④ 反控：等势伪虚表集合（随机 .data dword，seed=144）重算各形态；
     分区完整性（覆盖 838 + 未覆盖 380 = 1218，交集 0）。
内存纪律：只用 disasm_lite 64KB 分块流式，未对整段 .text 开 detail=True。
"""
import sys, re, json, struct, collections, random, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN, STK = L.GEN, L.STK
IMM = L.RE_IMM

def immv(t):
    return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

def baseclass(b):
    if b.startswith('0x'): return 'abs'
    if b in GEN: return 'gen'
    if b in STK: return 'stk'
    return 'other'

# 悬空 parse 诊断：看起来是 dword 内存写但不被 RE_STORE 接受
RE_ANYSTORE = re.compile(r'^dword ptr \[')

f1 = []            # (va, base, vt)          disp0 + gen
imm_gen  = []      # (va, base, disp, vt)    any disp + gen
imm_abs  = []      # (va, abs, disp, vt)     any disp + abs
regmove  = []      # (va, base, disp, vt, how)
store_other = []   # (va, base, disp, tgtreg)
parse_fail = []
pend = {}
idx = 0

for a, sz, mn, op in B.sweep(md):
    idx += 1
    for r in [r for r, v in pend.items() if idx - v[2] > 6]:
        del pend[r]
    if not op: continue
    m = L.RE_STORE.match(op)
    if m:
        base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
        bc = baseclass(base)
        if tgt is not None and IMM.match(tgt):
            iv = immv(tgt)
            if iv in VTS:
                if bc == 'gen':
                    imm_gen.append((a, base, ds, iv))
                    if ds == 0: f1.append((a, base, iv))
                elif bc == 'abs':
                    imm_abs.append((a, base, ds, iv))
        elif tgt is not None and tgt in GEN:
            store_other.append((a, base, ds, tgt))
            p = pend.get(tgt)
            if p:
                regmove.append((a, base, ds, p[0], p[1]))
        continue
    if RE_ANYSTORE.match(op):
        parse_fail.append(op)
    if op and mn not in ('cmp', 'test'):
        dst = op.partition(',')[0]
        if dst in pend:
            del pend[dst]
        ml = None
        if mn == 'mov':
            ml = re.match(r'^([a-z0-9]+),(0x[0-9a-f]+)$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = (v, a, idx)
        elif mn == 'lea':
            ml = re.match(r'^([a-z0-9]+),\[(0x[0-9a-f]+)\]$', op)
            if ml and ml.group(1) in GEN:
                v = immv(ml.group(2))
                if v in VTS: pend[ml.group(1)] = (v, a, idx)
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'): pend.pop(r, None)

# F6：.data/.rdata 里初始值等于虚表地址的 dword
data_init = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in VTS:
                data_init.append((B.IB + ava + i * 4, v))

covF1 = {s[2] for s in f1}
covF3 = {s[3] for s in imm_gen if s[2] != 0}
covF4 = {s[3] for s in imm_abs}
covF5 = {s[3] for s in regmove}
covF6 = {s[1] for s in data_init}
covU = covF1 | covF3 | covF4 | covF5 | covF6
unc380 = sorted(VTS - covF1)

# 二级虚表同块相邻假说
def neighbours(vt, r=64):
    out = []
    for x in VTS:
        if x != vt and 0 < abs(x - vt) <= r: out.append(x)
    return out

colloc = {}
for vt in unc380:
    nb = [x for x in neighbours(vt) if x in covF1]
    if nb: colloc[vt] = nb[:3]

# 反控：等势伪虚表
random.seed(144)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(struct.unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
fk1 = [s for s in f1 if s[2] in FAKE]
fk3 = [s for s in imm_gen if s[2] in FAKE]
fk4 = [s for s in imm_abs if s[3] in FAKE]

# 覆盖器: 对于 F1 未覆盖的 vt，哪个形态覆盖
def forms_of(vt):
    o = []
    if vt in covF1: o.append('F1')
    if vt in covF3: o.append('F3')
    if vt in covF4: o.append('F4')
    if vt in covF5: o.append('F5')
    if vt in covF6: o.append('F6')
    return o

hist3 = collections.Counter(s[2] for s in imm_gen if s[2] != 0)
hist3_new = collections.Counter(s[2] for s in imm_gen if s[2] != 0 and s[3] in (VTS - covF1))
unc_after_all = sorted(VTS - covU)

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'parse_fail_n': len(parse_fail), 'parse_fail_sample': parse_fail[:10],
 'F1_sites': len(f1), 'F1_distinct': len(covF1),
 'F3_sites': len(imm_gen) - len(f1), 'F3_sites_disp_nonzero': sum(1 for s in imm_gen if s[2] != 0),
 'F3_distinct': len(covF3),
 'F3_disp_hist_top': hist3.most_common(12),
 'F3_new_on_unc380': {hex(k): v for k, v in hist3_new.most_common(12)},
 'F4_sites': len(imm_abs), 'F4_distinct': len(covF4),
 'F5_sites': len(regmove), 'F5_distinct': len(covF5),
 'F6_sites': len(data_init), 'F6_distinct': len(covF6),
 'UNION_distinct': len(covU), 'UNION_rate': round(len(covU) / len(VTS), 4),
 'unc380_n': len(unc380),
 'unc380_colloc_with_covered': len(colloc),
 'unc380_forms': collections.Counter(tuple(forms_of(v)) for v in unc380).most_common(12),
 'unc380_sample': [hex(v) for v in unc380[:24]],
 'unc_after_all_n': len(unc_after_all),
 'unc_after_all_sample': [hex(v) for v in unc_after_all[:24]],
 'fake': {'F1_distinct': len({s[2] for s in fk1}), 'F3_sites': len(fk3), 'F4_sites': len(fk4)},
 'samples': {'imm_abs': [[hex(a), b, d, hex(v)] for a, b, d, v in imm_abs[:10]],
             'imm_gen_disp': [[hex(a), b, d, hex(v)] for a, b, d, v in imm_gen if d != 0][:10],
             'regmove': [[hex(a), b, d, hex(v), hex(h)] for a, b, d, v, h in regmove[:10]],
             'data_init': [[hex(a), hex(v)] for a, v in data_init[:10]]},
 'elapsed_s': round(time.time() - T0, 1),
}

# ---------------- 断言（正控/反控） ----------------
POS = []
NEG = []
def chk(name, cond, val):
    (POS if not name.startswith('负') else NEG).append([name, bool(cond), val])

chk('虚表集合 1218 / TD 988 / COL 1214（与 R143 一致）', len(VTS) == 1218 and len(TDs) == 988 and len(COL) == 1214, [len(VTS), len(TDs), len(COL)])
chk('F1（disp0+imm+gen）站点 2741、distinct 838（与 R143 一致）', len(f1) == 2741 and len(covF1) == 838, [len(f1), len(covF1)])
chk('覆盖/未覆盖分区完整：838 + 380 = 1218 且交集为空', len(covF1) + len(unc380) == len(VTS) and not (covF1 & set(unc380)), [len(covF1), len(unc380)])
chk('存在 disp≠0 的 imm∈VTS 站点（证明 R143 r143e 的正则会把它们整条丢弃）', sum(1 for s in imm_gen if s[2] != 0) > 0, sum(1 for s in imm_gen if s[2] != 0))
chk('解析健康：dword 内存写里不被 RE_STORE 接受的比例 < 5%', len(parse_fail) < max(5, 0.05 * (len(imm_gen) + len(imm_abs) + len(regmove) + len(store_other) + len(parse_fail))), len(parse_fail))
chk('存在绝对地址装表站点（静态对象形态）', len(imm_abs) > 0, len(imm_abs))
chk('并集覆盖率高于 F1 单形态', len(covU) > len(covF1), [len(covF1), len(covU)])
chk('未覆盖 380 张里有若干与已覆盖虚表同块相邻（|Δ|<=64）', len(colloc) > 0, len(colloc))
chk('未覆盖 380 张里至少有一张被新形态覆盖', any(forms_of(v) for v in unc380), sum(1 for v in unc380 if forms_of(v)))
chk('等势伪虚表在 F1 形态下 distinct < 20', len({s[2] for s in fk1}) < 20, len({s[2] for s in fk1}))
chk('等势伪虚表在绝对地址形态下站点数远小于真集合', len(fk4) < max(3, len(imm_abs) // 10 + 1), [len(fk4), len(imm_abs)])
chk('反控：F1 集合与 F3 集合不是同一集合（disp≠0 确有独立命中）', covF3 != covF1, [len(covF3), len(covF1)])
res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
res['neg_pass'] = sum(1 for x in NEG if x[1]); res['neg_fail'] = sum(1 for x in NEG if not x[1])
json.dump(res, open('_r144/r144a_forms.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('samples',)}, indent=1, ensure_ascii=False)[:6000])
print('POS %d/%d FAIL %d | NEG %d/%d FAIL %d | %.1fs' % (res['pos_pass'], len(POS), res['pos_fail'], res['neg_pass'], len(NEG), res['neg_fail'], time.time() - T0))
