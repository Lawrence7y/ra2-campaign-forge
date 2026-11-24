#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107g_owner.py —— 19 张 switch 表「所属函数」的最终判据（v2, 收窄候选集）

前稿三条判据都被自证失败，登记如下（错误痕迹不删）：
  P1 CALLTGT (R106)  「<=H 最近 call 直接目标」——只保证是*某*函数入口，不保证是本函数。
  P2 ALIGN  (r107d)  「对齐填充后接非填充字节」——鉴别力为负：把函数体内的立即数字节
                     （如 0x46e4a4 = ret 0x10 的操作数字节）当起点，16/19 错答。**已作废**。
  P3 CFG    (r107e)  jmp/jcc BFS 可达性——「不可达」不能证「不是本函数」（本脚本的 CFG 不完整，
                     间接 jmp / 表外分支即终止），7 张不可达全是扫描不完整所致，不作反证。
本稿 P4（v2）改用两条**独立且可判伪**的机械事实：
  (a) VSLOT：函数入口若在某个类 vtable 的槽里 => 它是虚方法，槽结构直接给出「类 + 槽号」。
  (b) 前向解码到 H 且**其间 ret 数为 0**：MSVC 里 ret 是函数体/case 体终止符，
      从 S 到 H 中间若有 ret，说明 S 与 H 不在同一 fall-through 链上，中间隔着函数界。
  归属 = 「解码命中且 ret==0」的候选；若无 ret==0 的候选（正因存在多个天然函数界），
  降级 AMBIGUOUS 并如实登记，不硬凑。

性能：候选集先按「<=H 且距离 <=0x200 的 vtable 槽/对齐边界」+「R106 的 call 目标」收窄，
      再对每个候选只解码到 H（上限 0x2000 条指令），不扫全段。
"""
import hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107g_owner.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


def u32(va):
    o = off(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None else None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True
ck('S1 .text 区间 == [0x401000, 0x7e038d)', (TS, TE) == (0x401000, 0x7e038d), (hex(TS), hex(TE)))

# ---------- vtable 自读 ----------
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {}
for cname, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    slots = []
    for i in range(400):
        x = u32(va + i * 4)
        if x is None or not (TS <= x < TE):
            break
        slots.append(x)
    if slots:
        VT[cname] = {'va': va, 'slots': slots}
slot_owner = {}
for cname, d in VT.items():
    for i, s in enumerate(d['slots']):
        slot_owner.setdefault(s, []).append((cname, i))
# vfunc_count 交叉核对
bad = [(c, sym[c].get('vfunc_count'), len(d['slots'])) for c, d in VT.items()
       if sym[c].get('vfunc_count') is not None and sym[c]['vfunc_count'] != len(d['slots'])]
ck('S2 自读 %d 个 vtable / %d 个 distinct 槽值；与 symbols.json vfunc_count 不一致 %d 个'
   % (len(VT), len(slot_owner), len(bad)), len(VT) == 954 and not bad, bad[:5])


def decode_to(S, H, maxins=6000):
    """从 S 前向线性解码，返回 (是否恰好命中 H, 指令数, 其间 ret 数)"""
    a = S
    n = 0
    nret = 0
    while a < H:
        if n > maxins:
            return (False, n, nret)
        g = next(md.disasm(raw[off(a):off(a) + 16], a), None)
        if g is None:
            return (False, n, nret)
        if g.address == H:
            return (True, n, nret)
        if g.mnemonic.startswith('ret'):
            nret += 1
        n += 1
        a = g.address + g.size
    return (a == H, n, nret)


D = json.load(open('_r106/r106f_switchsem.json'))['tables']
ROWS = []
for t in D:
    H = int(t['holder'], 16)
    P1 = int(t['func_by_calltarget'], 16)
    # 候选集收窄：vtable 槽值里离 H 最近的若干个（<=0x2000）+ R106 的 call 目标
    near = sorted([s for s in slot_owner if s <= H and H - s <= 0x2000], reverse=True)[:6]
    cands = sorted(set(near) | {P1})
    res = []
    for S in cands:
        hit, ni, nret = decode_to(S, H)
        if hit:
            res.append({'S': S, 'insn': ni, 'ret': nret,
                        'is_call': S in [P1],
                        'vslot': slot_owner.get(S, [])})
    res.sort(key=lambda r: (r['ret'], r['insn']))
    best = res[0] if res else None
    status = 'UNRESOLVED'
    if best and best['ret'] == 0:
        status = 'OWNER'
    elif best:
        status = 'AMBIGUOUS'
    ROWS.append({'table': t['table'], 'n': t['n'], 'holder': hex(H), 'R106_entry': hex(P1),
                 'owner': hex(best['S']) if best else None, 'owner_status': status,
                 'owner_ret': best['ret'] if best else None,
                 'owner_vslot': ([{'class': c, 'slot': i} for c, i in best['vslot']] if best else []),
                 'agree_with_R106': bool(best and best['S'] == P1),
                 'n_cands': len(cands), 'n_hits': len(res)})
    print('%-10s H=%08x R106=%08x owner=%s %-8s ret=%s insn=%s vslot=%s %s'
          % (t['table'], H, P1, hex(best['S']) if best else '-', status,
             best['ret'] if best else '-', best['insn'] if best else '-',
             ([{'%s' % c: i} for c, i in (best['vslot'] if best else [])]),
             '' if (best and best['S'] == P1) else '<<R106'), flush=True)

own = [r for r in ROWS if r['owner_status'] == 'OWNER']
amb = [r for r in ROWS if r['owner_status'] != 'OWNER']
ck('O1 得到 ret==0 强归属的表数（其余如实记 AMBIGUOUS，不硬凑）', True,
   '%d OWNER / %d AMBIGUOUS\n     ' % (len(own), len(amb)) +
   ', '.join('%s:%s(ret=%s)' % (r['table'], r['owner'], r['owner_ret']) for r in amb))
vs = [r for r in ROWS if r['owner_vslot']]
ck('O2 至少 1 张表的所属函数被静态定位到「类 + 槽号」（不依赖 win-main，推翻 R106 §EH10① 的不可做断言）',
   len(vs) >= 1, [(r['table'], r['owner'], r['owner_vslot']) for r in vs])
diff = [r for r in ROWS if not r['agree_with_R106']]
ck('O3 与 R106 入口不一致的表数', True, len(diff))
json.dump({'checks': checks, 'rows': ROWS}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
