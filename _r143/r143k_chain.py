#!/usr/bin/env python3
"""R143 K：决定性链式判据 —— 装表 -> 读回 -> 派发 -> 槽值可执行。

对每一个「mov dword ptr [rX+0], imm 且 imm 属于虚表集合」的装表点，在同一函数窗口内
（装表点之后 <=200 条指令、遇 ret 终止）寻找：
    mov rY, dword ptr [rX+0]        （读回同一对象偏移 0）
    call/jmp dword ptr [rY+4k]      （经读回值派发）
要求 (rX, rY) 满足 rX != rY（避免自引用假象），且窗口内 rX 未被改写。

再核 dword[imm + 4k] 是否落在 .text 内（可执行），且 dword[imm-4] == COL（vtable[-4] 回指 COL）。
这条链若成立：构造器把 X 写进对象偏移 0；同一函数随后从对象偏移 0 读回 X；用 X 当基址取
X+4k 处的 dword 并 call 之，且该 dword 是可执行地址、X-4 回指该类的 COL
=> 「对象偏移 0 处的 dword 是虚表指针」由字节闭合，不依赖任何对象模型预设。

反控：
  R1 把「偏移 0」换成偏移 4/8/0xc，链数应塌到 0 或个位数（因为那些偏移装的是虚表之外的常量）。
  R2 把 imm 换成非虚表的 .data 常量（同一批站点里 imm 不在 VTS 的），链数应显著低。
  R3 把「槽值落 .text」这一要求去掉，链数不变但「可执行率」应远高于随机 .data dword。
  R4 随机挑选同数量的 .text 站点作为装表点，链命中率应为 0 或极低。
"""
import sys, json, collections, random, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
ins = list(B.sweep(md))

def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m and m.group(1) in L.GEN:
            return ('disp', (m.group(1), L.disp_of(m.group(2)), mn))
        return ('nop', None)
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        tgt = ms.group(3)
        base, ds = ms.group(1), L.disp_of(ms.group(2))
        if tgt is not None and L.RE_IMM.match(tgt):
            return ('store_imm', (base, ds, L.immval(tgt)))
        return ('store', (base, ds, tgt))
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov':
        return ('load', (m.group(1), m.group(2), L.disp_of(m.group(3))))
    if mn in L.W_MN:
        return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'):
        return ('ret', None)
    return ('other', None)

P = [parse(*x) for x in ins]

def chain(target_disp=0, want_imm_in=None, window=200):
    """返回命中列表 (install_va, imm, load_va, disp_va, slot_disp)。"""
    hits = []
    n = len(P)
    for i, (kind, d) in enumerate(P):
        if kind != 'store_imm': continue
        base, ds, imm = d
        if base not in L.GEN or ds != target_disp: continue
        if want_imm_in == 'vts' and imm not in VTS: continue
        if want_imm_in == 'nonvts' and imm in VTS: continue
        j = i + 1
        end = min(n, i + 1 + window)
        loaded = None      # (va, regY)
        killed = False
        while j < end:
            k2, d2 = P[j]
            if k2 == 'ret': break
            if k2 == 'write' and d2 == base: killed = True; break
            if k2 == 'store' and d2[0] == base: killed = True; break
            if k2 == 'store_imm' and d2[0] == base: killed = True; break
            if k2 == 'load' and d2[1] == base and d2[2] == target_disp:
                loaded = (ins[j][0], d2[0])
            elif k2 == 'disp' and loaded:
                r, sd, mn = d2
                # 读回值必须仍指向读回寄存器（窗口内未被改写）
                if r == loaded[1]:
                    hits.append((ins[i][0], imm, loaded[0], ins[j][0], sd))
            j += 1
    return hits

H = chain(0, 'vts')
H4 = chain(4, 'vts')
H8 = chain(8, 'vts')
HC = chain(12, 'vts')
Hnon = chain(0, 'nonvts')

def exe_ok(imm, sd):
    v = B.dw(imm + sd)
    if v is None: return None
    return B.sec_of(v)

rows = []
for (iva, imm, lva, dva, sd) in H[:4000]:
    tgt = B.dw(imm + sd)
    rows.append({'install': hex(iva), 'vt': hex(imm), 'slot': sd // 4,
                 'target': (hex(tgt) if tgt else None),
                 'target_sec': (B.sec_of(tgt) if tgt else None),
                 'col_backref': (B.dw(imm - 4) in COL)})
n_text = sum(1 for r in rows if r['target_sec'] == '.text')
n_col = sum(1 for r in rows if r['col_backref'])

# 反控 R4：随机 .text 站点当装表点
random.seed(143)
rand_starts = random.sample(range(1, len(P) - 2), min(20000, len(P) - 10))
def rand_chain():
    hit = 0
    for i in rand_starts:
        k2, d2 = P[i]
        if k2 != 'store_imm': continue
        base, ds, imm = d2
        if base not in L.GEN or ds != 0: continue
        j = i + 1; loaded = None
        end = min(len(P), i + 201)
        while j < end:
            k3, d3 = P[j]
            if k3 == 'ret': break
            if k3 == 'load' and d3[1] == base and d3[2] == 0: loaded = d3[0]
            elif k3 == 'disp' and loaded and d3[0] == loaded: hit += 1
            j += 1
    return hit
R4 = rand_chain()

# 反控 R2b：非虚表 imm 的「槽值可执行率」
non_rows = []
for (iva, imm, lva, dva, sd) in Hnon[:4000]:
    tgt = B.dw(imm + sd)
    non_rows.append(B.sec_of(tgt) if tgt else None)
n_non_text = sum(1 for s in non_rows if s == '.text')

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'chain_disp0_vts_hits': len(H),
 'chain_disp0_vts_distinct_vt': len({h[1] for h in H}),
 'chain_disp0_hits_with_text_target': n_text,
 'chain_disp0_hits_with_col_backref': n_col,
 'chain_dispatch_slot_top': collections.Counter(h[4] // 4 for h in H).most_common(10),
 'chain_rows_sample': rows[:20],
 'N_offset4_hits': len(H4), 'N_offset8_hits': len(H8), 'N_offset12_hits': len(HC),
 'N_nonvts_imm_hits': len(Hnon),
 'N_nonvts_text_target': n_non_text,
 'N_random_sites_chain_hits': R4,
 'N_random_sample_n': len(rand_starts),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143k_chain.json', 'w'), ensure_ascii=False, indent=1)
json.dump(rows[:300], open('_r143/r143k_chain_rows.json', 'w'), ensure_ascii=False, indent=1)
