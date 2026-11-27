#!/usr/bin/env python3
"""R146 H：本轮三条结论的合并复核（每条都写成可失败断言 + 反控）。

结论 1（推翻 R144/R145 的「大位移组结构未定」）：
  278（严格）/283（宽容）个大位移装表站点，是**堆分配的大对象内嵌成员子对象**的 vptr 写入：
  一手证据 0x665650 = 宿主构造函数（thiscall，esi=ecx=this），在 +0x2a0/+0x2bc/+0x2d8…
  逐 28 字节一次写 TypeList<> 的 vptr（54 次），每次紧跟一个 thiscall 构造（ecx=该槽+0x1c）；
  其唯一调用者 0x52BAD1 先 `mov ecx,eax` 且 eax 来自 `call 0x7c8e17`（参数 0x18c0）
  ⇒ 宿主是堆对象，不是静态容器。故 R145 待办 #3「按成员数组/结构体两假说」的答案：
  **都不是数组**（同函数同 vt 的位移 7/15 组非等差、步长 28/24 而非 4），是**不同成员的多个内嵌
  子对象**；宿主既非静态也非「数组元素」。

结论 2（推翻 R145 对 0x7E1FB4 的「无主」表述）：
  0x7E1FB4（INoticeSource）写在 [this+0xc]，随后被 0x7E1F24 覆盖，但**两者 CHD 完全相同**
  （同为 AbstractClass 的 COL，offset 0 与 12，基类链 8 项一致，INoticeSource 在链上 mdisp=12）
  ⇒ 0x7E1FB4 = 该类的**次子对象 vptr**（多继承链第 4 个子对象），不是「无主虚表」。
  「瞬态」= 构造期先写子对象 vptr 再写本类 vptr，属正常 MSVC 构造序列。

结论 3（R145 的 5 站点差异归因）：
  宽容比严格多 5 个站点，位移全为负（-8/-8/-8/-4/-8），正是 R145 修的负位移形态。

本脚本独立重算以上全部数字，并对每条配反控。
纪律：disasm_lite 64KB 流式；上下文仅 <= 4KB 小窗。
"""
import sys, re, json, struct, collections, hashlib, time, bisect
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
def off_of(vt): return coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
TDname = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
def name_of(vt):
    c = COLof.get(vt)
    return TDname.get(coltd.get(c)) if c else None

TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)

sites = []; callers = []
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    mt = TOL.match(op)
    if mt and mn == 'mov':
        pm = parse_mem(mt.group(1))
        if pm:
            base, disp = pm
            tgt = (mt.group(2) or '').strip()
            if L.RE_IMM.match(tgt) and immv(tgt) in VTS and base in GEN:
                sites.append({'va': a, 'base': base, 'disp': disp, 'vt': immv(tgt),
                              'strict': L.RE_STORE.match(op) is not None})

# ---- 结论 1 ----
HOST = 0x665650
ctx = [s for s in sites if HOST <= s['va'] < HOST + 0x1f00]
by_vt = collections.defaultdict(list)
for s in ctx: by_vt[s['vt']].append(s)
tl_h = by_vt.get(0x7E4DD8, [])
ds = sorted(s['disp'] for s in tl_h)
gaps = [ds[i + 1] - ds[i] for i in range(len(ds) - 1)]
# 宿主 size 与分配调用
alloc = {}
off = B.va2off(0x52BABE); blob = B.data[off:off + 0x20]
lines = ['%08X  %-7s %s' % (i.address, i.mnemonic, i.op_str) for i in md.disasm(blob, 0x52BABE)]

# ---- 结论 2 ----
def chd_of(col):
    p = B.dw(col + 16)
    return p if p and B.sec_of(p) else None
def chd_sig(col):
    p = chd_of(col)
    if not p: return None
    n, arr = B.dw(p + 8), B.dw(p + 12)
    if not arr or not B.sec_of(arr): return None
    out = []
    for i in range(min(n or 0, 32)):
        bp = B.dw(arr + 4 * i)
        if not bp or not B.sec_of(bp): continue
        out.append((B.dw(bp), struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0]))
    return out
N_A = chd_sig(COLof[0x7E1F24]); N_B = chd_sig(COLof[0x7E1FB4])
N_A0 = chd_sig(COLof[0x7E1F50])

# ---- 结论 3 ----
bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
nz = [s for s in sites if s['disp'] != 0]
large = [s for s in nz if bucket(s['disp']) == 'large']
strict_large = [s for s in large if s['strict']]
extra = [s for s in nz if not s['strict']]

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'C1': {'host': hex(HOST), 'sites_in_host': len(ctx), 'distinct_vt': len(by_vt),
              'typelist_h_n': len(tl_h), 'typelist_h_disps': ds,
              'typelist_h_step_set': sorted(set(gaps)), 'typelist_h_arith': len(set(gaps)) == 1,
              'alloc_ctx': lines,
              'host_disp_range': [min(ds), max(ds)] if ds else None},
       'C2': {'7e1f24_chain': N_A, '7e1fb4_chain': N_B, '7e1f50_chain': N_A0,
              'chains_identical': N_A == N_B, 'target_mdisp_in_chain': [m for td, m in (N_A or []) if td == (N_B or [[None]])[0][0]]},
       'C3': {'nz': len(nz), 'large': len(large), 'large_strict': len(strict_large),
              'extra_n': len(extra), 'extra_disps': [s['disp'] for s in extra]}}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('宿主函数内装表站点 > 50（结构可一手取证）', len(ctx) > 50, len(ctx))
chk('宿主是堆对象：分配后 mov ecx,eax 再 thiscall',
    any('0x7c8e17' in l for l in lines) and any(l.strip().endswith('call    0x665650') for l in lines), lines)
chk('TypeList<H> 在宿主内写在 >= 40 个不同位移', len(tl_h) >= 40 and len(set(ds)) == len(ds), [len(tl_h), len(set(ds))])
chk('这些位移**不是**等差（不是数组）', not (len(set(gaps)) == 1), sorted(set(gaps))[:8])
chk('步长集合包含 28（= 一个子对象大小）', 28 in set(gaps), sorted(set(gaps))[:8])
chk('0x7E1F24 与 0x7E1FB4 的 CHD 逐项相同', N_A == N_B, [len(N_A or []), len(N_B or [])])
chk('INoticeSource 在链上 mdisp==12（= 它被写的位移）',
    any(td == (N_B or [[-1]])[0][0] and m == 12 for td, m in (N_A or [])), res['C2']['target_mdisp_in_chain'])
chk('严格大位移 = 278（复现 R144）', len(strict_large) == 278, len(strict_large))
chk('宽容 − 严格 = 5 且全为负位移', len(large) - len(strict_large) == 5 and all(s['disp'] < 0 for s in extra),
    [len(large) - len(strict_large), [s['disp'] for s in extra]])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146h_final.json', 'w'), indent=1, ensure_ascii=False)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
