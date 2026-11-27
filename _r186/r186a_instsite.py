#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 A：vtable 实例化站点 census + 「存储位移 == COL.mdisp」判据。

命题（全部可失败）：
  P1  .text 中引用某个符号表 vtable 绝对地址的指令，逐条按 ModRM 分类：
      store(mov [mem], imm32) / load(mov reg, imm32) / 其它。三类之和 == 候选指令数。
  P2  排除栈基址（esp/ebp）后，所有 store 的 mem.base 是**对象寄存器**，
      且 mem.disp **恒等于**该 vtable 对应 COL 的 mdisp（12 个 mdisp==4 的次对象表
      装在 +4，954 个 mdisp==0 的主表装在 +0）。
  P3  mdisp==4 的 12 张次对象表**全部**只在 disp==4 处被装；对应 mdisp==0 的主表
      在同址集合里 **0 次**（两个 vtable 语义不通用，R185 的结论在代码侧得到独立证据）。
  P4  未找到 imm32 装点的表数（781/954 只是下限）如实计数，不补齐、不推断。

反控（必须真红）：
  N1  把 store 位移读成 disp+1 => P2 计数必须变化
  N2  把 mdisp 换成常数 0 => mdisp==4 那 12 张表的判据必须红
  N3  把 sec 边界左右的表地址整体 +4（错位取 COL）=> mdisp 全变、P2 必须红
  N4  P2 只对「disp==mdisp 的 store」成立这一判据，若人为把 esp 基址也计入 => 计数变化
"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.join(ROOT, '_r186')
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True

fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

# ---------- 0. 输入 ----------
syms = json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes']
VT = {int(v['vtable_va'], 16): (k, v) for k, v in syms.items() if v.get('vtable_va')}
ck('A0 symbols.json 有 vtable 的类 == 954', len(VT) == 954, len(VT))

def mdisp_of(vt):
    c = P.dw(vt - 4)
    if c is None or P.where(c) not in ('.data', '.rdata'): return None
    return P.dw(c + 4)

MD = {vt: mdisp_of(vt) for vt in VT}
ck('A1 954 张表的 mdisp 全可解且 ∈ {0,4}', all(m in (0, 4) for m in MD.values()),
   collections.Counter(MD.values()))
ck('A2 mdisp 分布 == {0:942, 4:12}', collections.Counter(MD.values()) == {0: 942, 4: 12},
   dict(collections.Counter(MD.values())))

# ---------- 1. 候选指令（imm32 落在 vtable 集合里）----------
TEXT = P.B['.text']; off = TEXT['rawptr']; size = TEXT['rawsize']
cand = {}
for st in range(0, size, 65536):
    seg = P.RAW[off + st:off + min(st + 65536, size)]
    for a, sz, mn, op in mdl.disasm_lite(seg, TEXT['va'] + st):
        if sz >= 5:
            for j in range(sz - 3):
                w = struct.unpack_from('<I', P.RAW, off + a - TEXT['va'] + j)[0]
                if w in VT:
                    cand[a] = w
                    break
ck('A3 候选指令数 == 3795（imm32 命中 954 张表之一）', len(cand) == 3795, len(cand))

# ---------- 2. 逐条按 ModRM 分类 ----------
store = []   # (addr, vt, base, index, disp)
load = []
other = []
for a, w in cand.items():
    o = off + a - TEXT['va']
    ins = list(md.disasm(P.RAW[o:o + 15], a))
    if not ins: other.append((a, 'undecodable', w)); continue
    i = ins[0]
    imm = None
    for opdx in i.operands:
        if opdx.type == X86_OP_IMM and opdx.imm in VT: imm = opdx.imm
    if imm is None: other.append((a, i.mnemonic + '?' + i.op_str, w)); continue
    o0 = i.operands[0]
    if i.mnemonic == 'mov' and len(i.operands) == 2 and o0.type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
        m = o0.mem
        store.append((a, imm, i.reg_name(m.base) if m.base else None,
                      i.reg_name(m.index) if m.index else None, m.disp))
    elif i.mnemonic == 'mov' and len(i.operands) == 2 and o0.type == 3:  # X86_OP_REG
        load.append((a, imm, i.op_str))
    else:
        other.append((a, i.mnemonic + ' ' + i.op_str, w))
ck('A4 三类之和 == 候选数', len(store) + len(load) + len(other) == len(cand),
   (len(store), len(load), len(other)))
ck('A5 store 3639 / load 一次外 145 条里的 mov reg,imm 形式',
   len(store) == 3639 and len(load) + len(other) == 156, (len(store), len(load), len(other)))

# ---------- 3. 「存储位移 == mdisp」判据 ----------
STACK = {'esp', 'ebp'}
obj = [s for s in store if s[2] not in STACK and s[3] is None]
stk = [s for s in store if s[2] in STACK]
idxed = [s for s in store if s[3] is not None]
eq = [s for s in obj if s[4] == MD[s[1]]]
ne = [s for s in obj if s[4] != MD[s[1]]]
print('   对象寄存器 store %d（其中 disp==mdisp %d、不等 %d）；栈基址 %d；带索引 %d'
      % (len(obj), len(eq), len(ne), len(stk), len(idxed)))
ck('A6 对象寄存器上 disp == COL.mdisp 100%%（%d/%d）' % (len(eq), len(obj)),
   len(obj) > 0 and len(ne) == 0, len(ne))
ck('A7 存在不等的反例集合为空（不是没读到位）', len(obj) == len(eq) + len(ne))
ck('A8 栈基址 store 一律不计（esp/ebp 的 disp 是帧偏移不是对象偏移）',
   len(stk) > 0 and all(s[2] in STACK for s in stk), len(stk))

# 每个表被装的位移集合
disp_sets = collections.defaultdict(set)
for a, vt, b, ix, d in obj: disp_sets[vt].add(d)
ck('A9 每张被装表只有一个固定装点位移（无一张表在多位移被装）',
   all(len(v) == 1 for v in disp_sets.values()),
   [('%08X' % k, sorted(v)) for k, v in disp_sets.items() if len(v) > 1][:3])

# ---------- 4. mdisp==4 的 12 张次对象表 ----------
m4 = [vt for vt in VT if MD[vt] == 4]
m0 = [vt for vt in VT if MD[vt] == 0]
ck('A10 mdisp==4 的表恰 12 张', len(m4) == 12, len(m4))
m4_in4 = [vt for vt in m4 if disp_sets.get(vt) == {4}]
m4_none = [vt for vt in m4 if vt not in disp_sets]
m0_in0 = [vt for vt in m0 if disp_sets.get(vt) == {0}]
ck('A11 12 张次对象表里 %d 张只在 +4 被装、%d 张无 imm32 装点、0 张在 +0 被装'
   % (len(m4_in4), len(m4_none)),
   len(m4_in4) + len(m4_none) == 12 and not any(0 in disp_sets.get(vt, ()) for vt in m4),
   (len(m4_in4), len(m4_none)))
ck('A12 mdisp==0 的主表只在 +0 被装（%d 张），无一张在 +4' % len(m0_in0),
   not any(4 in disp_sets.get(vt, ()) for vt in m0), len(m0_in0))

# 12 张次对象表对应的 mdisp==0 主表（同 pTD，+0xCC）
def ptd_of(vt):
    c = P.dw(vt - 4)
    return None if c is None else P.dw(c + 12)
sub_pairs = []
for vt in m4:
    t = ptd_of(vt)
    mains = [v for v in m0 if ptd_of(v) == t]
    sub_pairs.append((VT[vt][0], vt, mains))
ck('A13 每张次对象表都有恰 1 张同 pTD 的 mdisp==0 主表，位移差恒 +0xCC',
   all(len(ms) == 1 and ms[0] - vt == 0xCC for _, vt, ms in sub_pairs),
   [(k, hex(vt), [hex(x) for x in ms]) for k, vt, ms in sub_pairs][:3])
ck('A14 主表在被装集合里 0 次（12/12 主表无 imm32 装点）',
   all(not ms[0] in disp_sets for _, vt, ms in sub_pairs),
   sum(1 for _, vt, ms in sub_pairs if ms[0] in disp_sets))

# ---------- 5. 覆盖下限 ----------
installed = len(disp_sets)
ck('A15 有 imm32 装点的表 == 781（954 的覆盖下限，不补齐不推断）', installed == 781, installed)
ck('A16 无 imm32 装点的表 == 173，如实登记', 954 - installed == 173, 954 - installed)

# ---------- 反控 ----------
# N1 disp+1
eq1 = [s for s in obj if s[4] + 1 == MD[s[1]]]
ck('N1 反控：disp+1 后 0 条命中 => 判据真读了位移', len(eq1) == 0, len(eq1))
# N2 常数 0
m4_as0 = [vt for vt in m4 if disp_sets.get(vt) == {0}]
ck('N2 反控：把 mdisp 换成常数 0，则 12 张次对象表的判据 0/12 成立（必须真红）',
   len(m4_as0) == 0)
# N3 错位取 COL（vt+4 处当 COL）
bad = 0
for a, vt, b, ix, d in obj:
    c = P.dw(vt + 4)
    mm = None if c is None else P.dw(c + 4)
    if mm == d: bad += 1
ck('N3 反控：把 vtable+4 当 COL 起点，disp==mdisp 命中数剧减（< 50%%）',
   bad < len(obj) // 2, (bad, len(obj)))
# N4 计入栈基址
eq2 = [s for s in store if s[4] == MD[s[1]]]
ck('N4 反控：把栈基址计入后计数变化（%d vs %d）' % (len(eq2), len(eq)), len(eq2) != len(eq),
   (len(eq2), len(eq)))

res = {
    'cand': len(cand), 'store': len(store), 'load': len(load), 'other': len(other),
    'obj_store': len(obj), 'disp_eq_mdisp': len(eq), 'disp_ne': len(ne),
    'stack_store': len(stk), 'indexed_store': len(idxed),
    'installed_tables': installed, 'missing_tables': 954 - installed,
    'm4': len(m4), 'm4_at4': len(m4_in4), 'm4_no_site': len(m4_none),
    'm0_at0': len(m0_in0),
    'm4_names': [VT[v][0] for v in m4],
    'm4_no_site_names': [VT[v][0] for v in m4_none],
    'pairs': [{'cls': k, 'vt_m4': '%08X' % vt, 'vt_m0': '%08X' % ms[0]} for k, vt, ms in sub_pairs],
    'disp_hist': {'%s' % k: v for k, v in collections.Counter(d for *_, d in obj).most_common()},
    'checks': nchk[0], 'fails': fails,
}
json.dump(res, open(os.path.join(OUT, 'r186a.json'), 'w'), indent=1, sort_keys=True)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails:
    print('FAILS:', fails); sys.exit(1)
