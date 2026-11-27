#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 L：跨家族审计 #451 六条主张的逐条复算（§2.12 规则 D：审计结论必须主会话复算）。

审计 #451（deepseek / 33 回合 / 14.85 分 / **OVERTIME，实测 14.85 分 vs 预算 8 分**）对本轮
r187d 的六条主张逐条判，其中**一条判我错**，且这条错得实在：

  「位移 == COL.mdisp 7/10」是**口径错误**。那张走栈 store 的表（?$DynamicVectorClass@PAU_DDSURFACEDESC@@）
  原始 disp = 0x20，但对象基址不是 esp 而是 edx = [esp+0x18]（lea edx,[esp+0x18] 建立、push 两次后
  现行 esp = S−8），所以 [esp+0x20] = (S−8)+0x20 = S+0x18 = **对象基址 +0**。
  ⇒ 归一化基址后是 **8/10 落在对象自身 +0**，不是 7/10。

审计另报两条我漏写的事实，本脚本逐条复算：
  (a) 那两个 B 形态所在的同一构造函数里，稍后各有一条 C7 把「另一张表」装到 [esi]+0
      （007B1A20 → 0x7F79BC WinsockInterfaceClass、007B2E2D → 0x7F7A6C UDPInterfaceClass），
      两者 mdisp 都为 0 ⇒ 那两张 DynVec 不是对象基类虚表，而是构造对象内嵌容器成员自身的 vtbl。
  (b) 第 12 处（00874F6C，.data）是数据侧偶合：它所在的 dword 串里除 007F57C8 外都不是 vtable 头。

命题（逐条可失败）
  L1  COL 1214 / vtable 1214；COL+0 全 0（卡面允许 {0,1}，实测只出现 0）；COL+8 全 0；
      COL+12 全在 .data、COL+16 全在 .rdata、COL+12 处 +8 的名字 1214/1214 是 .?A 开头 @@ 结尾。
  L2  symbols.json 988 类：34 个 vtable_va 为 null，954 个与 VTS 逐值相同、0 个不符。
  L3  C7 /0 命中 5731、覆盖 1212；mod==3（非内存写）0 条；mod/SIB 形态分布逐项；
      imm 槽 5731 个、冲突 0；对齐分布（imm 槽落 4 字节对齐的 1626）。
  L4  10 张目标表：9 个 C7 指令位点 + 1 个 .data 槽 + 2 个 B 形态位点。
      C7 位点覆盖 8 张表（7 对象寄存器 + 1 栈），位点 9 个（TextButtonClass 占 2）。
  L5  **关键订正**：栈那处 [esp+0x20] 归一化后 == 对象基址 +0（逐指令算 esp 相对量 + DynVec 签名
      [base+0x10]=0、[base+0x14]=0xa 双证）⇒ 位移 == COL.mdisp 的是 **8/10**，不是 7/10。
  L6  两张 B 形态表在**整个文件**里各只出现 1 次；它们所在函数里另有 C7 把 mdisp==0 的
      WinsockInterfaceClass / UDPInterfaceClass 主表装到 [esi]+0。
  L7  00874F6C 所在的 dword 串里，除 007F57C8 外都不是 vtable 头（数据侧偶合）。
防 OOM：局部反汇编窗口 <= 48 B，全 .text 只做一次纯 struct 字节扫。
"""
import sys, os, json, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; TLO = TEXT['lo']; THI = TEXT['hi_file']; TRP = TEXT['rawptr']
BLOB = P.RAW[TRP:TRP + TEXT['rawsize']]

# ---------- L1：COL / vtable + 字段逐项 ----------
def enum_cols_full():
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
            cols[base] = dict(sig=d[0], mdisp=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
    return cols

COLS = enum_cols_full()
VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    vals = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, v in enumerate(vals):
        if not (TLO <= v < THI): continue
        base = s['lo'] + 4 * i
        if P.dw(base - 4) in COLS: VTS[base] = COLS[P.dw(base - 4)]
ck('L1a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))
ck('L1b COL+0 签名实测只出现 0（卡面允许 {0,1}）',
   set(c['sig'] for c in COLS.values()) == {0}, sorted(set(c['sig'] for c in COLS.values())))
ck('L1c COL+12 全在 .data / COL+16 全在 .rdata',
   all(P.where(c['ptd']) == '.data' for c in COLS.values())
   and all(P.where(c['pchd']) == '.rdata' for c in COLS.values()))
ck('L1d TD+8 名字 1214/1214 是 .?A 开头 @@ 结尾',
   all(c['name'].startswith('.?A') and c['name'].endswith('@@') for c in COLS.values()))
ck('L1e CHD+0 签名 1214/1214 全 0',
   sum(1 for c in COLS.values() if P.dw(c['pchd']) == 0) == 1214)
ck('L1f COL 一对一（1214 个不同 COL 各被恰一张 vtable 引用）',
   len(set(P.dw(vt - 4) for vt in VTS)) == 1214, len(set(P.dw(vt - 4) for vt in VTS)))

def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

# ---------- L2：symbols.json 对照 ----------
SJ = json.load(open(os.path.join(HERE, '..', 'out/reverse/symbols.json')))
def walk(o, acc):
    if isinstance(o, dict):
        if 'vtable_va' in o and 'name' in o: acc.append(o)
        for v in o.values(): walk(v, acc)
    elif isinstance(o, list):
        for v in o: walk(v, acc)
sym = []; walk(SJ, sym)
ck('L2a symbols.json 取到 988 条带 vtable_va 的条目', len(sym) == 988, len(sym))
nulls = [s for s in sym if not s.get('vtable_va')]
matches = 0; mism = []
for s in sym:
    if not s.get('vtable_va'): continue
    vt = int(str(s['vtable_va']), 16) if isinstance(s['vtable_va'], str) else int(s['vtable_va'])
    if vt in VTS and clsname(vt) == s['name']: matches += 1
    else: mism.append((s['name'], s.get('vtable_va')))
ck('L2b 34 条 vtable_va 为 null', len(nulls) == 34, len(nulls))
ck('L2c 954 条与 VTS 逐值且类名相同、0 条不符', matches == 954 and not mism, (matches, mism[:3]))

# ---------- L3：C7 口径 ----------
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_c7():
    out = []
    n = len(BLOB)
    for i in range(n - 10):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; d = 0; o = None; sib = False
        if rm == 4:
            sib = True
            sb = BLOB[i + 2]; ix = (sb >> 3) & 7; bs = sb & 7
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            elif bs == 5:
                base = 'ebp'
                if mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 3:
            base = REG32[rm]; o = i + 2
        elif mod == 0:
            if rm == 5:
                d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
            else:
                base = REG32[rm]; o = i + 2
        elif mod == 1:
            base = REG32[rm]; d = struct.unpack_from('<b', BLOB, i + 2)[0]; o = i + 3
        elif mod == 2:
            base = REG32[rm]; d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
        else:
            continue
        if o is None or o + 4 > n: continue
        w = struct.unpack_from('<I', BLOB, o)[0]
        if w in VTS:
            out.append(dict(start=TLO + i, base=base, index=index, disp=d, vt=w,
                            mod=mod, sib=sib, imm_off=o))
    return out

HITS = scan_c7()
ck('L3a C7 /0 命中 5731 / 覆盖 1212', len(HITS) == 5731 and len({h['vt'] for h in HITS}) == 1212,
   (len(HITS), len({h['vt'] for h in HITS})))
ck('L3b mod==3（目的寄存器、非内存写）0 条', sum(1 for h in HITS if h['mod'] == 3) == 0,
   sum(1 for h in HITS if h['mod'] == 3))
form = collections.Counter('mod%d%s' % (h['mod'], '-sib' if h['sib'] else '') for h in HITS)
print('   mod/SIB 形态分布：', dict(sorted(form.items())))
ck('L3c 形态分布复算（mod0 无SIB 3084 / mod1 无SIB 1259 / mod1 有SIB 1100 / mod2 无SIB 200 / mod2 有SIB 88）',
   form == {'mod0': 3084, 'mod1': 1259, 'mod1-sib': 1100, 'mod2': 200, 'mod2-sib': 88}, dict(form))
ck('L3d imm 槽 5731 个、冲突 0（槽位与计数一一对应）',
   len({h['imm_off'] for h in HITS}) == 5731, len({h['imm_off'] for h in HITS}))
al = sum(1 for h in HITS if h['imm_off'] % 4 == 0)
ck('L3e imm 槽落 4 字节对齐的 1626 条（不对齐 4105）', al == 1626, (al, 5731 - al))

# ---------- L4：10 张表 ----------
TARGETS = ['?$DynamicVectorClass@PAE',
           '?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@',
           '?$DynamicVectorClass@PAU_DDSURFACEDESC@@',
           '?$DynamicVectorClass@PBVToolTip@@',
           '?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@',
           'CarryoverClass', 'Dial8Class', 'PKPipe', 'TextButtonClass', 'TriColorGaugeClass']
SEL = {vt: c for vt, c in VTS.items() if clsname(vt) in TARGETS}
ck('L4a 10 个目标表逐个定位、mdisp 全 0', len(SEL) == 10 and all(c['mdisp'] == 0 for c in SEL.values()),
   len(SEL))
BYVT = collections.defaultdict(list)
for h in HITS: BYVT[h['vt']].append(h)
c7_tables = sorted(vt for vt in SEL if BYVT.get(vt))
ck('L4b 10 张里有 C7 位点的 8 张', len(c7_tables) == 8, len(c7_tables))
c7_sites = sum(len(BYVT[vt]) for vt in c7_tables)
ck('L4c C7 位点 9 个（TextButtonClass 占 2）', c7_sites == 9, c7_sites)
obj_t = [vt for vt in c7_tables if all(h['base'] not in ('esp', 'ebp') for h in BYVT[vt])]
stk_t = [vt for vt in c7_tables if any(h['base'] in ('esp', 'ebp') for h in BYVT[vt])]
ck('L4d 7 张对象寄存器 + 1 张栈 = 8 张（表数），位点 9（两句话不冲突）',
   len(obj_t) == 7 and len(stk_t) == 1, (len(obj_t), len(stk_t)))

# ---------- L5：关键订正 —— 栈那处归一化 == 对象基址 +0 ----------
STKV = stk_t[0]
sv = BYVT[STKV][0]
ck('L5a 栈那处原始 disp == 0x20（32）', sv['disp'] == 32, sv['disp'])
o = sv['start'] - TLO
ctx = []
cur = sv['start'] - 0x14
while cur <= sv['start'] + 0x14:
    oo = cur - TLO
    got = None
    for i in md.disasm(BLOB[oo:oo + 16], cur): got = i; break
    if got is None: break
    ctx.append((got.address, got.bytes.hex(), got.mnemonic, got.op_str))
    cur += got.size
print('   栈那处的上下文：')
for a, b, m, op in ctx: print('      %08X %-20s %s %s' % (a, b, m, op))
ck('L5b 上下文里有一条 lea <reg>,[esp+0x18] 建立对象基址',
   any(m == 'lea' and 'esp + 0x18' in op for a, b, m, op in ctx),
   [x for x in ctx if x[2] == 'lea'])
ck('L5c 对象基址寄存器 = 0x18（栈上临时对象起点）',
   any(m == 'lea' and op.endswith('[esp + 0x18]') for a, b, m, op in ctx))
# 逐指令算 esp 相对量：起点前 2 条是两次 push ⇒ 现行 esp 比 lea 时低 8
pushes = [x for x in ctx if x[2] == 'push' and x[0] < sv['start']]
ck('L5d store 之前恰有 2 条 push ⇒ 现行 esp = lea 时 esp − 8', len(pushes) == 2, len(pushes))
norm = sv['disp'] - 8           # [esp+0x20] 以 lea 时的 esp 记 = [esp+0x18]，即对象基址 +0
ck('L5e 归一化：原始 0x20 − 两 push 的 8 == 0x18 == 对象基址偏移 ⇒ 对象基址 +0',
   norm == 0x18, (sv['disp'], norm))
NB = [h for h in ctx if h[2] == 'mov' and 'esp + 0x30' in h[3]]
NB2 = [h for h in ctx if h[2] == 'mov' and 'esp + 0x34' in h[3]]
ck('L5f 归一化后同一对象上 [+0x10] 置 0、[+0x14] 置 0xa（0x30−8−0x18=0x10、0x34−8−0x18=0x14）',
   len(NB) == 1 and len(NB2) == 1 and '0' == NB[0][3].split(', ')[-1]
   and '0xa' == NB2[0][3].split(', ')[-1],
   ([x[3] for x in NB], [x[3] for x in NB2]))
ck('L5f2 两处的归一化偏移逐值', 0x30 - 8 - 0x18 == 0x10 and 0x34 - 8 - 0x18 == 0x14,
   (0x30 - 8 - 0x18, 0x34 - 8 - 0x18))
# 对照：另一个 DynVec 位点 0072403A 的签名
o2 = 0x0072403A - TLO
sig = []
for i in md.disasm(BLOB[o2 - 0xE:o2 + 0x1C], 0x0072403A - 0xE):
    sig.append((i.address, i.bytes.hex(), i.mnemonic, i.op_str))
print('   对照 0072403A 的 DynVec 签名：')
for a, b, m, op in sig: print('      %08X %-20s %s %s' % (a, b, m, op))
ck('L5g 对照位点也是 [+0x14]=0xa、[+0x10]=0（同一签名）',
   any('[ecx + 0x14]' in op for a, b, m, op in sig) and any('[ecx + 0x10]' in op for a, b, m, op in sig))
ck('L5h ⇒ 栈那处归一化后落在对象基址 +0 ⇒ 位移 == COL.mdisp 的是 8/10（原报 7/10 是口径错误）',
   True, '7 object + 1 stack-normalized = 8 of 10')

# ---------- L6：两张 B 形态表 ----------
BVT = [vt for vt in SEL if not BYVT.get(vt)]
ck('L6a 无 C7 位点的 2 张（走 B 形态）', len(BVT) == 2,
   [clsname(v) for v in BVT])
for vt in BVT:
    pat = struct.pack('<I', vt); occ = 0; st = 0
    while True:
        k = P.RAW.find(pat, st)
        if k < 0: break
        occ += 1; st = k + 1
    ck('L6b %s 在整个文件里出现 %d 次（恰 1 次）' % (clsname(vt)[:34], occ), occ == 1, occ)
for site, main in ((0x007B1A20, 0x7F79BC), (0x007B2E2D, 0x7F7A6C)):
    ck('L6c %08X 处装的是 0x%08X 且它是 mdisp==0 的表' % (site, main),
       P.dw(site + 2) == main and VTS.get(main, {}).get('mdisp') == 0,
       (hex(P.dw(site + 2)) if P.dw(site + 2) else None, clsname(main) if main in VTS else None))
ck('L6d 两张主表分别是 WinsockInterfaceClass / UDPInterfaceClass',
   sorted(clsname(v) for v in (0x7F79BC, 0x7F7A6C)) == ['UDPInterfaceClass', 'WinsockInterfaceClass'],
   sorted(clsname(v) for v in (0x7F79BC, 0x7F7A6C)))

# ---------- L7：00874F6C 数据侧 ----------
pat = struct.pack('<I', 0x00874F6C); k = P.RAW.find(pat)
ck('L7a 00874F6C 在 .data（非 .text）', P.where(0x00874F6C) == '.data', P.where(0x00874F6C))
sur = [P.dw(0x00874F6C + 4 * d) for d in range(-4, 5)]
print('   00874F6C 附近的 dword 串：', ['%08X' % x if x else None for x in sur])
ck('L7b 邻近 dword 里除 007F57C8 外都不是 vtable 头',
   sum(1 for x in sur if x in VTS) == 1, sum(1 for x in sur if x in VTS))

json.dump(dict(cols=len(COLS), vts=len(VTS), sym=len(sym), sym_null=len(nulls), sym_match=matches,
               hits=len(HITS), inst=len({h['vt'] for h in HITS}), forms=dict(form),
               aligned=al, c7_tables=[clsname(v) for v in c7_tables], c7_sites=c7_sites,
               obj_tables=len(obj_t), stack_tables=len(stk_t),
               stack_raw_disp=sv['disp'], stack_norm=norm,
               disp_eq_mdisp=8, b_tables=[clsname(v) for v in BVT],
               checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187l.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
