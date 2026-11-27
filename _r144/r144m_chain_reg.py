#!/usr/bin/env python3
"""R144 M：R143「68 条链式闭合」的召回回归 —— 加入 F7（栈帧装表）后是否仍成立。

R143 的 S2 判据只在「装表到对象偏移 0」这批站点上找链。R144H 发现第三批站点
（写栈帧的 mov dword ptr [esp+d], imm∈VTS，1337 处）被整批漏掉。
本脚本按 R143 同型判据（同函数窗口内：装表 -> 从同一基址/位移读回 -> 经读回值 call [reg+4k]）
重跑两次，只改「装表来源集合」：
  A 只用 F1（复现 R143 的 68）
  B 用 F1 ∪ F7
判据阈值全同 R143；目的只是给「68 是下界」一个可复算的幅度，不重定义判据。
"""
import sys, json, re, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN, STK = L.GEN, L.STK
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
RE_CALL = L.RE_CALL

# 单遍扫描同时产出：装表站点(F1/F7)、读回站点、派发站点（带函数边界：以 ret 结尾/新函数起点估计）
# 函数边界用「call 目标集合」与「ret 后对齐填充」的简法：这里用「遇到 ret 则清空窗口」。
def scan(include_stack):
    chains = []            # (install_va, vt, base, disp, readva, callva, slot)
    win = {}               # (base, disp) -> (vt, install_va)
    lastload = {}          # reg -> (base, disp, readva)
    for a, sz, mn, op in B.sweep(md):
        if not op: continue
        if mn in ('ret', 'retn'):
            win.clear(); lastload.clear(); continue
        # S-308：RE_STORE 也匹配 call/jmp 的操作数（'dword ptr [ecx+0x10]' 作为整条 op），
        # 若先判 store 会把所有「经读回值派发」吞掉 -> 链数恒为 0。必须先判 call/jmp。
        mc0 = RE_CALL.match(op)
        if mc0 and mn in ('call', 'jmp'):
            base = mc0.group(1); ds = L.disp_of(mc0.group(2))
            ll = lastload.get(base)
            if ll:
                b2, d2, rva = ll
                w = win.get((b2, d2))
                if w: chains.append([a, w[0], b2, d2, rva, a, ds])
            continue
        m = L.RE_STORE.match(op)
        if m:
            base = m.group(1); ds = L.disp_of(m.group(2)); tgt = m.group(3)
            if tgt is not None and L.RE_IMM.match(tgt):
                iv = immv(tgt)
                if iv in VTS:
                    if base in GEN or (include_stack and base in STK):
                        win[(base, ds)] = (iv, a)
            continue
        ml = L.RE_LOAD.match(op)
        if ml and mn == 'mov':
            dst, base, ds = ml.group(1), ml.group(2), L.disp_of(ml.group(3))
            if base in GEN or base in STK:
                lastload[dst] = (base, ds, a)
            continue
        if mn not in ('cmp', 'test'):
            d = op.partition(',')[0]
            lastload.pop(d, None)
    return chains

cA = scan(False)
cB = scan(True)
uniq = lambda cs: {(c[1], c[5]) for c in cs}

def txt_target(slot, vt):
    return B.sec_of(B.dw(vt + slot)) == '.text' if B.dw(vt + slot) else False

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS),
 'A_chains': len(cA), 'A_distinct_vt': len({c[1] for c in cA}),
 'A_text_ok': sum(1 for c in cA if txt_target(c[6], c[1])),
 'B_chains': len(cB), 'B_distinct_vt': len({c[1] for c in cB}),
 'B_text_ok': sum(1 for c in cB if txt_target(c[6], c[1])),
 'B_extra_over_A': len(uniq(cB) - uniq(cA)),
 'A_samples': [[hex(c[0]), hex(c[1]), c[2], c[3], hex(c[4]), hex(c[5]), c[6]] for c in cA[:6]],
 'B_samples_only_new': [[hex(c[0]), hex(c[1]), c[2], c[3], hex(c[4]), hex(c[5]), c[6]] for c in cB if (c[1], c[5]) not in uniq(cA)][:8],
 'elapsed_s': round(time.time() - T0, 1),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('A（只用 F1）复现 R143 的量级 60..80 条', 60 <= len(cA) <= 80, len(cA))
chk('B（F1 ∪ F7）比 A 严格更多链', len(cB) > len(cA), [len(cA), len(cB)])
chk('B 的槽值落 .text 比例 >= 0.95（判据强度不被拉低）', res['B_text_ok'] / max(1, len(cB)) >= 0.95, round(res['B_text_ok'] / max(1, len(cB)), 4))
chk('B 的 distinct 虚表数 >= A 的（覆盖不缩水）', res['B_distinct_vt'] >= res['A_distinct_vt'], [res['A_distinct_vt'], res['B_distinct_vt']])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144m_chain_reg.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False)[:3000])
print('\n'.join('%-58s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
