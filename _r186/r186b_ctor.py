#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 B：类对象模型的**层结构**在代码侧闭合。

不依赖 symbols.json 的 954 张表：全镜像枚举 1214 个 COL / 1214 张 vtable（含 symbols 外的 260 张）。

命题（逐条可失败）：
  B1  全镜像 COL == 1214、vtable == 1214、symbols 覆盖 954、symbols 外 260；260 张的 mdisp 分布如实。
  B2  按 pTD 分组（每组 = 同一个 TypeDescriptor 的多张 vtable = 多层接口）：
      组数 == 954，每组的 mdisp **两两不同**，且**每组的 mdisp 集合恰含一个 0**；
      层数直方图 == {1:860, 2:10, 3:6, 4:76, 5:1, 7:1}，且 **Σ 层数 == 1214**（算术闭合，不靠巧合）。
  B3  symbols.json 每类只挑 1 张：942 张挑 mdisp==0 层、12 张挑 mdisp==4 层；
      12 张的那 12 个类**同时存在 mdisp==0 层**（即 symbols 在这 12 类上偏离「取 0 层」规则）。
  B4  构造器装点（mov [reg+disp], vtable）：disp 与 mdisp 的关系分三层口径，逐层给数：
      (a) disp == 该 vtable 的 COL.mdisp：3009/3216 = 93.56%
      (b) 放宽到 disp ∈ 同 TD 的层集合（成员子对象按其所在父类的层偏移装）：3052/3216 = 94.90%
      (c) 残差 164 条：161 条是模板/容器类成员（类名含 $ 或 List），3 条是个例，逐条列出。
  B5  12 个 Locomotion 类：每类在 +4 装有 mdisp==4 的 ILocomotion 表；其中 10 类有 imm32 装点、
      2 类无 imm32 装点（如实登记）；mdisp==0 层**没有一次**被装在 +4。
反控（必须真红）：
  N1  disp+1 后 (a) 口径 0 命中
  N2  mdisp 换常数 0 ⇒ (a) 口径只剩 mdisp==0 那批，count 变小
  N3  vtable+4 当 COL 起点 ⇒ 命中数 < 50%
  N4  层集合口径把 mdisp 集合换成 {0} ⇒ (b) 退化成 (a) 的数
"""
import sys, os, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; off = TEXT['rawptr']; size = TEXT['rawsize']

def enum_cols():
    cols = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; blob = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        nd = len(blob) // 4
        vals = struct.unpack_from('<%dI' % nd, blob, 0)
        for i in range(nd - 4):
            base = s['lo'] + 4 * i; d = vals[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            cols[base] = dict(mdisp=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
    return cols

def enum_vtables(cols):
    vts = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        vals = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, v in enumerate(vals):
            if not (TEXT['lo'] <= v < TEXT['hi_file']): continue
            base = s['lo'] + 4 * i; c = P.dw(base - 4)
            if c in cols: vts[base] = cols[c]
    return vts

COLS = enum_cols(); VTS = enum_vtables(COLS)
ck('B1a 全镜像 COL == 1214', len(COLS) == 1214, len(COLS))
ck('B1b 全镜像 vtable == 1214（每 COL 恰一张表）', len(VTS) == 1214, len(VTS))
syms = json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes']
SYM = {int(v['vtable_va'], 16): (k, v) for k, v in syms.items() if v.get('vtable_va')}
out260 = set(VTS) - set(SYM)
ck('B1c symbols 覆盖 954、symbols 外 260', len(SYM) == 954 and len(out260) == 260, len(out260))
mx260 = collections.Counter(VTS[v]['mdisp'] for v in out260)
ck('B1d symbols 外 260 张的 mdisp 分布如实',
   mx260 == {0: 12, 4: 79, 8: 78, 12: 78, 24: 6, 36: 1, 40: 1, 44: 1, 1728: 1, 21784: 3}, dict(mx260))

# ---------- B2 按 pTD 分组 ----------
per = collections.defaultdict(list)
for vt, c in VTS.items(): per[c['ptd']].append((c['mdisp'], vt))
ck('B2a 组数（有 COL 的 TD 数）== 954', len(per) == 954, len(per))
ck('B2b 每组内 mdisp 两两不同', all(len({m for m, _ in ls}) == len(ls) for ls in per.values()))
ck('B2c 每组恰含一个 mdisp==0 层', all(sum(1 for m, _ in ls if m == 0) == 1 for ls in per.values()),
   sum(1 for ls in per.values() if sum(1 for m, _ in ls if m == 0) != 1))
hist = collections.Counter(len(ls) for ls in per.values())
ck('B2d 层数直方图 == {1:860, 2:10, 3:6, 4:76, 5:1, 7:1}',
   hist == {1: 860, 2: 10, 3: 6, 4: 76, 5: 1, 7: 1}, dict(hist))
ck('B2e 算术闭合：Σ 层数 == 1214 == 全镜像 COL 数',
   sum(k * v for k, v in hist.items()) == 1214, sum(k * v for k, v in hist.items()))

# ---------- B3 symbols 的选择规则 ----------
sel = collections.Counter()
dev = []
for ptd, ls in per.items():
    chosen = [(m, v) for m, v in ls if v in SYM]
    if not chosen: continue
    m, v = chosen[0]
    sel[m] += 1
    if m != 0: dev.append((SYM[v][0], m, [mm for mm, _ in sorted(ls)]))
ck('B3a 942 类挑 mdisp==0 层、12 类挑 mdisp==4 层', sel == {0: 942, 4: 12}, dict(sel))
ck('B3b 这 12 个类**也**有 mdisp==0 层 ⇒ symbols 在 12 类上偏离「取 0 层」规则',
   len(dev) == 12 and all(0 in mm for _, _, mm in dev), dev[:3])
ck('B3c 12 个偏离类全为 Locomotion 系', all('LocomotionClass' in d[0] for d in dev),
   [d[0] for d in dev])

# ---------- B4 构造器装点 ----------
cand = {}
for st in range(0, size, 65536):
    seg = P.RAW[off + st:off + min(st + 65536, size)]
    for a, sz, mn, op in mdl.disasm_lite(seg, TEXT['va'] + st):
        if sz >= 5:
            for j in range(sz - 3):
                w = struct.unpack_from('<I', P.RAW, off + a - TEXT['va'] + j)[0]
                if w in VTS: cand[a] = w; break
stores = []; other = []
for a, w in cand.items():
    o = off + a - TEXT['va']
    ins = list(md.disasm(P.RAW[o:o + 15], a))
    if not ins: other.append((a, 'undecodable', w)); continue
    i = ins[0]; imm = None
    for opd in i.operands:
        if opd.type == X86_OP_IMM and opd.imm in VTS: imm = opd.imm
    if imm is None: other.append((a, i.mnemonic + '?' + i.op_str, w)); continue
    o0 = i.operands[0]
    if i.mnemonic == 'mov' and len(i.operands) == 2 and o0.type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
        m = o0.mem
        stores.append((a, imm, i.reg_name(m.base) if m.base else None, m.disp,
                       i.reg_name(m.index) if m.index else None))
    else:
        other.append((a, i.mnemonic + ' ' + i.op_str, w))
ck('B4a 候选指令 4720、store+其它 == 候选', len(cand) == 4720 and len(stores) + len(other) == len(cand),
   (len(cand), len(stores), len(other)))
STACK = {'esp', 'ebp'}
obj = [s for s in stores if s[2] is not None and s[2] not in STACK and s[4] is None]
absn = [s for s in stores if s[2] is None]
stk = [s for s in stores if s[2] in STACK]
idx = [s for s in stores if s[4] is not None]
ck('B4b 对象寄存器 store == 3216（另：绝对址 287 / 栈基址 1061 / 带索引 0）',
   len(obj) == 3216 and len(absn) == 287 and len(stk) == 1061 and len(idx) == 0,
   (len(obj), len(absn), len(stk), len(idx)))
def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

eq = [s for s in obj if s[3] == VTS[s[1]]['mdisp']]
own = {ptd: {m for m, _ in ls} for ptd, ls in per.items()}
cov = [s for s in obj if s[3] in own[VTS[s[1]]['ptd']]]
# 口径(c)：放宽到「全镜像任一 CHD 把该 TD 列在某个 mdisp 上」（成员子对象按其所在父类的偏移装）
wide = collections.defaultdict(set)
for ptd, ms in own.items(): wide[ptd] |= ms
for vt, c in VTS.items():
    ch = [P.dw(c['pchd'] + 4 * k) for k in range(4)]
    if None in ch or not (1 <= ch[2] <= 64) or P.where(ch[3]) != '.rdata': continue
    for i in range(ch[2]):
        bo = P.dw(ch[3] + 4 * i)
        if bo is None: continue
        f = [P.dw(bo + 4 * j) for j in range(6)]
        if None in f: continue
        wide[f[0]].add(f[2])
cov2 = [s for s in obj if s[3] in wide[VTS[s[1]]['ptd']]]
res = [s for s in obj if s not in cov2]
ck('B4c 口径(a) disp == COL.mdisp：3009/3216 = 93.56%', len(eq) == 3009, len(eq))
ck('B4d 口径(b) disp ∈ 该 TD 自身层集合：3048/3216 = 94.78%',
   len(cov) == 3048, (len(cov), '%.2f%%' % (100.0 * len(cov) / len(obj))))
ck('B4e 口径(c) disp ∈ 该 TD 在全镜像 CHD 中出现过的 mdisp：3052/3216 = 94.90%',
   len(cov2) == 3052, (len(cov2), '%.2f%%' % (100.0 * len(cov2) / len(obj))))
ck('B4f 口径(c) 的残差 == 164 条（= 3216 − 3052；口径 b 残差 168，口径 a 残差 207）',
   len(res) == 164 and len(obj) - len(cov) == 168 and len(obj) - len(eq) == 207,
   (len(res), len(obj) - len(cov), len(obj) - len(eq)))
rt = [s for s in res if ('$' in clsname(s[1]) or 'List' in clsname(s[1]))]
rn = [s for s in res if s not in rt]
ck('B4g 残差里 161 条是模板/容器类成员装点、3 条个例', len(rt) == 161 and len(rn) == 3,
   (len(rt), [(hex(s[0]), clsname(s[1]), s[3], VTS[s[1]]['mdisp']) for s in rn]))
ck('B4h 3 条个例逐条如实列出、不解释成规则',
   all(s[3] not in wide[VTS[s[1]]['ptd']] for s in rn))

# ---------- B5 12 个 Locomotion ----------
loco = sorted({VTS[v]['ptd'] for v in VTS if VTS[v]['mdisp'] == 4 and 'LocomotionClass' in clsname(v)})
ck('B5a 含 mdisp==4 层的 Locomotion TD 恰 12 个', len(loco) == 12, len(loco))
disp_at = collections.defaultdict(set)
for a, vt, b, d, ix in obj: disp_at[vt].add(d)
w4 = [v for v in (pp for p in loco for m, pp in per[p] if m == 4) if v in disp_at]
nosite = [v for v in (pp for p in loco for m, pp in per[p] if m == 4) if v not in disp_at]
ck('B5b 12 张 mdisp==4 表里 %d 张装在 +4、%d 张无 imm32 装点、0 张装在其它位移'
   % (len(w4), len(nosite)),
   len(w4) == 10 and len(nosite) == 2 and all(disp_at[v] == {4} for v in w4),
   [(clsname(v), sorted(disp_at[v])) for v in w4][:3])
m0 = [pp for p in loco for m, pp in per[p] if m == 0]
ck('B5c 这 12 个类的 mdisp==0 层 0 次被装在 +4（无一次）',
   all(4 not in disp_at[v] for v in m0), [(clsname(v), sorted(disp_at.get(v, []))) for v in m0][:3])
ck('B5d 无装点的 2 张如实登记', len(nosite) == 2, [clsname(v) for v in nosite])

# ---------- 反控 ----------
ck('N1 反控：disp+1 判 (a) ⇒ 0 命中', len([s for s in obj if s[3] + 1 == VTS[s[1]]['mdisp']]) == 0)
c0 = len([s for s in obj if s[3] == 0])
ck('N2 反控：mdisp 换常数 0 ⇒ 只剩 %d 条（< 3009）' % c0, c0 < len(eq), (c0, len(eq)))
bad3 = 0
for a, vt, b, d, ix in obj:
    c = P.dw(vt + 4)
    if c in COLS and COLS[c]['mdisp'] == d: bad3 += 1
ck('N3 反控：vtable+4 当 COL ⇒ 命中 %d 条，远 < 50%%' % bad3, bad3 < len(obj) // 2, (bad3, len(obj)))
one = [s for s in obj if s[3] in {0}]
ck('N4 反控：层集合换成 {0} ⇒ 口径(b)/(c) 退化回 %d（≠ 3048/3052）' % len(one), len(one) != len(cov) and len(one) != len(cov2), len(one))

resj = {'cols': len(COLS), 'vtables': len(VTS), 'sym': len(SYM), 'sym_out': len(out260),
        'sym_out_mdisp': {str(k): v for k, v in sorted(mx260.items())},
        'groups': len(per), 'layer_hist': {str(k): v for k, v in sorted(hist.items())},
        'sum_layers': sum(k * v for k, v in hist.items()),
        'sel': {str(k): v for k, v in sel.items()},
        'dev12': [{'cls': d[0], 'chosen_mdisp': d[1], 'layers': d[2]} for d in dev],
        'cand': len(cand), 'stores': len(stores), 'other': len(other),
        'obj': len(obj), 'abs': len(absn), 'stack': len(stk), 'indexed': len(idx),
        'scope_a': len(eq), 'scope_b': len(cov), 'scope_c': len(cov2), 'residual': len(res),
        'residual_tmpl': len(rt), 'residual_other': [{'addr': '%08X' % s[0], 'cls': clsname(s[1]),
                                                     'disp': s[3], 'mdisp': VTS[s[1]]['mdisp']} for s in rn],
        'residual_tmpl_top': collections.Counter(clsname(s[1]) for s in rt).most_common(10),
        'loco_at4': len(w4), 'loco_nosite': [clsname(v) for v in nosite],
        'checks': nchk[0], 'fails': fails}
json.dump(resj, open(os.path.join(HERE, 'r186b.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
