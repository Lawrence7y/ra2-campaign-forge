#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106e_recheck.py —— §2.12 规则 D：主会话亲自复算（刻意换实现路径）

纪律要求：不读、不 import 任何子代理脚本。本脚本全部自己写，且刻意与 r106d 走不同的路：
  - 不用 iced_x86，改用 capstone 5.0.7（两个子代理里 exec 用 capstone、audit 未知）
  - 表基址不硬编码，从「jmp dword ptr [reg*4+disp]」指令反向扫出来（r106d 是给定基址再验指令）
  - 字节表地址不硬编码，从前置 mov cl/dl/al,[reg+disp] 取（r106d 也是，但解码器不同）
  - 索引依赖不用 op_access 工厂，改用手写的「capstone regs_access + base/index 判据」
  - 分组统计用与 r106d 不同的数据结构（dict of list vs OrderedDict）

复算 14 项，逐项与 r106d 比：
  C1  表基址集合（反向扫出来的 19 个基址是否与 r106d 的相同集合）
  C2  项数合计 292
  C3  去重项值数 276
  C4  重复组数 8
  C5  含重复的表数 5
  C6  多出项数 16
  C7  8 个重复组的目标地址集合
  C8  重复组分布表集合（5 张）
  C9  两级形态 10 张表的字节表地址与上界（逐表相等）
  C10 10 张表表长 == 上界+1
  C11 10 张表 distinct 字节值数 == 项数（满射）
  C12 10 张表输入域合计 476、case 槽合计 61
  C13 0x728e08 项值序列
  C14 0x728e08 的 4 项同值 + 2 个前置块常量（5 与 7）
自错登记也要写进产物。
"""
import hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_RET, CS_GRP_JUMP
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM, X86_REG_EAX, X86_REG_ECX, X86_REG_EDX

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r106/r106e_recheck.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
REF = '_r106/r106d_final.json'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

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
    return struct.unpack_from('<I', raw, off(va))[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
# 自错登记 E-rc1：capstone 默认遇到第一个拒解字节就停止迭代。
# 不设 skipdata 时 .text 只解出 155,215 条指令（约占应有点位数 11%），
# 与 R105 D4 栽的是同一个坑（「用只读了 11% 的扫描出结论」）。
# 设 skipdata 后才铺满，并且能检出全部 jmp [reg*4+base] 持有指令。
md.skipdata = True

# 自错登记 E-rc2（本轮 OOM 事故，如实保留）：
# 本脚本上一版把 detail=True 的同一个 md 用于整段 .text 的 md.disasm()，
# 实测被内核 OOM Killer 杀掉（exit 137，输出只停在 S0 一行）。
# 这正是任务卡「防 OOM 内存硬红线」明文禁止的写法。
# 改法：全段扫描改用 detail=False 的独立解码器 + disasm_lite + 64 KB 分块流式迭代，
# 只对少数候选地址单独用 detail=True 的 md 解码。
md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_lite.detail = False
md_lite.skipdata = True

def dis(va, n=1):
    o = off(va)
    return list(md.disasm(raw[o:o + 15 * n + 40], va))[:n]

# ---------- C1 反向扫：从指令里找出所有 jmp dword ptr [reg*4+base] ----------
# 不硬编码表基址：扫整个 .text，收集「jmp 且唯一操作数是内存 且 scale==4 且 base 为空」
# 必须按指令起点顺序走。分块策略：每次解 [pos, pos+64K+16) 但只采纳地址 < pos+64K 的指令，
# 下一块从最后一条被采纳指令的末尾继续 —— 这样跨块指令不会被截断也不会被跳过。
text_sec = next(s for s in secs if s[0] == '.text')
tname, trva, tvs, tra, trs = text_sec
tstart = IB + trva
tend = tstart + tvs
CHUNK = 64 * 1024
cand = {}
cnt_insn = 0
scan_fail = 0
pos = tstart
while pos < tend:
    lo = off(pos)
    hi_va = min(pos + CHUNK, tend)
    buf = raw[lo:off(hi_va) + 16]
    last_end = pos
    for addr, size, mnem, opstr in md_lite.disasm_lite(buf, pos):
        if addr >= hi_va:
            break
        cnt_insn += 1
        last_end = addr + size
        if mnem == 'jmp' and opstr.startswith('dword ptr [') and '*4' in opstr:
            body = opstr[len('dword ptr ['):].rstrip(']')
            # 只接受「纯 索引*4 + 绝对基址」形态：无 base 寄存器
            parts = [p.strip() for p in body.split('+')]
            if len(parts) == 2 and parts[0].endswith('*4') and parts[1].startswith('0x') \
                    and not parts[1].endswith('*4'):
                try:
                    disp = int(parts[1], 16)
                except ValueError:
                    disp = None
                if disp is not None:
                    cand.setdefault(disp, []).append((addr, parts[0][:-2]))
    if last_end <= pos:          # 整块解不出任何指令（不应发生），推进 1 字节避免死循环
        scan_fail += 1
        last_end = pos + 1
    pos = last_end
print('  .text 线性解码指令数 %d  分块 %d KB  扫描停滞点数 %d'
      % (cnt_insn, CHUNK // 1024, scan_fail), flush=True)

# 用 detail=True 解码器逐个复核候选持有指令（lite 侧只做粗筛，detail 侧做定性）
cand_verified = {}
for disp, lst in cand.items():
    keep = []
    for addr, idxname in lst:
        ins = dis(addr, 1)
        if not ins:
            continue
        i = ins[0]
        if i.mnemonic == 'jmp' and len(i.operands) == 1 \
                and i.operands[0].type == X86_OP_MEM:
            m = i.operands[0].mem
            if (m.disp & 0xFFFFFFFF) == disp and m.scale == 4 and m.base == 0 \
                    and i.reg_name(m.index) == idxname:
                keep.append((addr, idxname))
    if keep:
        cand_verified[disp] = keep
cand = cand_verified

# 表长不自带：从 base 起逐 DWORD 读，直到项值不再是 .text 内地址（上限 512），n>=2 才算表。
# 这一步是 r105a 的算法（不是 r106d 给的），故 C1 是真正的独立重算。
TAB = {}
for disp, lst in cand.items():
    if not (tstart <= disp < tend):
        continue
    n = 0
    while n < 512:
        v = u32(disp + 4 * n)
        if v is None or not (tstart <= v < tend):
            break
        n += 1
    if n >= 2:
        TAB[disp] = {'n': n, 'holders': lst, 'vals': [u32(disp + 4 * k) for k in range(n)]}
print('  指针表 n>=2 共 %d 张 / %d 项' % (len(TAB), sum(v['n'] for v in TAB.values())), flush=True)
ck('C1a 独立重扫得 360 张指针表（与 R104/R105 三处独立实现同值）', len(TAB) == 360, len(TAB))
ck('C1b 360 张表合计 2702 项（与 R105 Q1 同值）',
   sum(v['n'] for v in TAB.values()) == 2702, sum(v['n'] for v in TAB.values()))

# 19 张「B1 用到」的表：用 R101 的 41 行 B1 宿主（去重 31）反查所在表
bc = json.load(open('_r101/_exec/r101_bc.json'))
B1_HOSTS = sorted({int(x['host'], 16) for x in bc['detail'] if x['class'] == 'B1'})

def tab_of_addr(a):
    for b, v in TAB.items():
        if b <= a < b + 4 * v['n']:
            return b
    return None

used_bases = sorted({tab_of_addr(h) for h in B1_HOSTS if tab_of_addr(h) is not None})
ck('C1c B1 的 31 个去重宿主落在 19 张表内（与 R104/R105 同值）', len(used_bases) == 19, len(used_bases))
ck('C1d 这 19 张表合计 292 项（与 R105 Q2 同值）',
   sum(TAB[b]['n'] for b in used_bases) == 292, sum(TAB[b]['n'] for b in used_bases))

REFD = json.load(open(REF))['R']
ref_tables = {int(r['table'], 16): r['n'] for r in REFD['K_duplicate_census']['rows']}
ck('C1 反查出的 19 张表基址集合与 r106d 完全相同',
   set(used_bases) == set(ref_tables),
   {'mine': len(used_bases), 'ref': len(ref_tables),
    'only_mine': [hex(x) for x in sorted(set(used_bases) - set(ref_tables))],
    'only_ref': [hex(x) for x in sorted(set(ref_tables) - set(used_bases))]})
ck('C1e 19 张表逐表项数也与 r106d 相等',
   all(TAB[b]['n'] == ref_tables[b] for b in used_bases),
   [(hex(b), TAB[b]['n'], ref_tables[b]) for b in used_bases if TAB[b]['n'] != ref_tables[b]])

# ---------- 项值读取（全部来自上面独立重扫的 TAB，不借 r106d 的表） ----------
vals = {b: TAB[b]['vals'] for b in used_bases}
cand = {b: TAB[b]['holders'] for b in used_bases}
hold = {b: TAB[b]['holders'][0] for b in used_bases}

ck('C2 项数合计 292', sum(len(v) for v in vals.values()) == 292,
   sum(len(v) for v in vals.values()))
allv = [v for vs in vals.values() for v in vs]
ck('C3 去重项值 276', len(set(allv)) == 276, len(set(allv)))

# ---------- C4..C8 重复普查（不同实现：按值聚合再看跨表） ----------
from collections import defaultdict
byval = defaultdict(list)
for base, vs in vals.items():
    for idx, v in enumerate(vs):
        byval[v].append((base, idx))
dupgroups = {v: lst for v, lst in byval.items() if len(lst) > 1}
ck('C4 重复组 8 组', len(dupgroups) == 8, len(dupgroups))
tables_with_dup = sorted({b for lst in dupgroups.values() for b, _ in lst})
ck('C5 含重复的表 5 张', len(tables_with_dup) == 5, [hex(x) for x in tables_with_dup])
ck('C6 多出项数 16', 292 - len(set(allv)) == 16, 292 - len(set(allv)))

ref_dup_targets = set()
ref_dup_tables = set()
for r in REFD['K_duplicate_census']['rows']:
    for d in r['dups']:
        ref_dup_targets.add(int(d['target'], 16))
        ref_dup_tables.add(int(r['table'], 16))
ck('C7 重复目标地址集合与 r106d 相同',
   set(dupgroups) == ref_dup_targets,
   {'only_mine': [hex(x) for x in sorted(set(dupgroups) - ref_dup_targets)],
    'only_ref': [hex(x) for x in sorted(ref_dup_targets - set(dupgroups))]})
ck('C8 含重复的表集合与 r106d 相同',
   set(tables_with_dup) == ref_dup_tables,
   {'only_mine': [hex(x) for x in sorted(set(tables_with_dup) - ref_dup_tables)],
    'only_ref': [hex(x) for x in sorted(ref_dup_tables - set(tables_with_dup))]})

# ---------- C9..C12 两级形态：从持有指令往前找 cmp reg,imm / ja / mov r8,byte ptr [reg+disp] ----------
# 自错登记 E-rc3：上一版用 jmp 的索引寄存器去匹配字节表基址寄存器，实测只中 5/10。
# 真实 idiom 是：lea eax,[input-K]  →  cmp eax,BOUND  →  ja default
#              →  xor ecx,ecx  →  mov cl,byte ptr [eax + BYTETAB]   （字节表用 eax 索引）
#              →  jmp dword ptr [ecx*4 + TABLE]                     （表用 ecx 索引）
# 两个寄存器不同，故字节表基址必须按「任意寄存器 + .text 内绝对位移」找，不能绑定 jmp 的 index。
def find_bound_and_bytetab(holder_va):
    """在持有指令之前 200 字节内解码，找最后的 cmp reg,imm 与 mov r8,byte ptr [reg+disp(.text)]"""
    lo = holder_va - 200
    got = list(md.disasm(raw[off(lo):off(lo) + 200], lo))
    bound = None
    bytetab = None
    load_at = None
    ja_at = None
    for i in got:
        if i.address >= holder_va:
            break
        if i.mnemonic == 'cmp' and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_IMM:
            bound = i.operands[1].imm & 0xFFFFFFFF
        if i.mnemonic.startswith('ja'):
            ja_at = i.address
        if i.mnemonic == 'mov' and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_MEM:
            m = i.operands[1].mem
            disp = m.disp & 0xFFFFFFFF
            if m.base != 0 and m.index == 0 and m.scale == 1 and (tstart <= disp < tend) \
                    and 'byte ptr' in i.op_str:
                bytetab = disp
                load_at = i.address
    return bound, bytetab, ja_at, load_at

TWO = []
ONE = []
for base in sorted(used_bases):
    hv, regname = hold[base]
    b, bt, ja_at, load_at = find_bound_and_bytetab(hv)
    two = (bt is not None and b is not None and load_at is not None
           and ja_at is not None and load_at < hv and b < 256)
    rec = (base, TAB[base]['n'], hv, regname, b, bt, ja_at, load_at)
    (TWO if two else ONE).append(rec)

ck('C9a 两级形态恰好 10 张 / 直接形态 9 张', len(TWO) == 10 and len(ONE) == 9,
   {'two': len(TWO), 'one': len(ONE),
    'one_list': [hex(r[0]) for r in ONE]})
ref_two = {int(r['table'], 16): (r['bound'], int(r['byte_table'], 16))
           for r in REFD['M_input_to_case']['rows']}
ok9 = all((r[4], r[5]) == ref_two[r[0]] for r in TWO)
ck('C9b 10 张表的 (上界, 字节表地址) 逐表与 r106d 相等', ok9,
   [(hex(r[0]), r[4], r[5], ref_two.get(r[0])) for r in TWO
    if (r[4], r[5]) != ref_two.get(r[0])])
ck('C9c 直接形态 9 张表的集合与 r106d 的 9 张相同',
   {r[0] for r in ONE} == (set(ref_tables) - set(ref_two)),
   {'only_mine': [hex(x) for x in sorted({r[0] for r in ONE} - (set(ref_tables) - set(ref_two)))],
    'only_ref': [hex(x) for x in sorted((set(ref_tables) - set(ref_two)) - {r[0] for r in ONE})]})

ok10 = True
ok11 = True
bad = []
tot_in = 0
tot_slot = 0
detail = []
for base, n, hv, rn, b, bt, ja_at, load_at in TWO:
    bs = raw[off(bt):off(bt) + b + 1]
    if len(bs) != b + 1:
        ok10 = False
    distinct = len(set(bs))
    tot_in += len(bs)
    tot_slot += n
    detail.append({'table': hex(base), 'n': n, 'bound': b, 'byte_table': hex(bt),
                   'idx_reg': rn, 'n_bytes': len(bs), 'distinct': distinct,
                   'max_byte': max(bs), 'holder': hex(hv),
                   'ja_at': hex(ja_at), 'load_at': hex(load_at)})
    if distinct != n:
        ok11 = False
        bad.append((hex(base), n, distinct))
ck('C10 10 张表表长 == 上界+1', ok10, [(d['table'], d['n_bytes'], d['bound']) for d in detail])
ck('C11 10 张表 distinct 字节值数 == 项数（满射，与 r106d 独立同结论）', ok11, bad)
ck('C12 输入域合计 476、case 槽合计 61', tot_in == 476 and tot_slot == 61, (tot_in, tot_slot))
ck('C12b 10 张表 max(byte) < n 逐表成立（无越界值）',
   all(d['max_byte'] < d['n'] for d in detail),
   [(d['table'], d['max_byte'], d['n']) for d in detail if d['max_byte'] >= d['n']])

# ---------- C13 / C14 0x728e08 ----------
v728 = vals[0x728e08]
ck('C13 0x728e08 项值序列 == r106d',
   [hex(v) for v in v728] == ['0x728de0', '0x728dd9', '0x728dd0', '0x728c1e',
                              '0x728de0', '0x728de0', '0x728de0'], [hex(v) for v in v728])
ck('C14a 0x728de0 被 4 项引用',
   [hex(v) for v in v728].count('0x728de0') == 4, '')
# 独立读两个前置块的常量：capstone 解 mov dword ptr [edi+0x14], imm
def first_imm_store(va):
    i = dis(va, 1)[0]
    if i.mnemonic == 'mov' and i.operands[0].type == X86_OP_MEM \
            and i.operands[1].type == X86_OP_IMM:
        return i.operands[1].imm, i.operands[0].mem.disp & 0xFFFFFFFF, i.op_str
    return None
a = first_imm_store(0x728dd9)
b2 = first_imm_store(0x728dd0)
ck('C14b 0x728dd9 写常量 7 到 [edi+0x14]', a is not None and a[0] == 7 and a[1] == 0x14, a)
ck('C14c 0x728dd0 写常量 5 到 [edi+0x14]', b2 is not None and b2[0] == 5 and b2[1] == 0x14, b2)
# 0x728dd0 是否 jmp 到 0x728de0；0x728dd9 是否落穿
i2 = dis(0x728dd0, 2)
ck('C14d 0x728dd0 第 2 条是 jmp 到 0x728de0',
   i2[1].mnemonic == 'jmp' and i2[1].operands[0].type == X86_OP_IMM
   and i2[1].operands[0].imm == 0x728de0,
   (i2[1].mnemonic, i2[1].op_str))
i3 = dis(0x728dd9, 2)
ck('C14e 0x728dd9 第 2 条就是公共尾块首条（落穿，无跳转）',
   i3[1].address == 0x728de0, hex(i3[1].address))

d = {'checks': checks,
     'tables_all': len(TAB), 'entries_all': sum(v['n'] for v in TAB.values()),
     'used_tables': [hex(x) for x in sorted(used_bases)],
     'two_level_detail': detail, 'dup_targets': [hex(x) for x in sorted(dupgroups)],
     'dup_tables': [hex(x) for x in sorted(tables_with_dup)],
     'required': 19, 'scan_undecodable_positions': scan_fail,
     'self_errors': [
         'E-rc1 初版未开 skipdata，capstone 只覆盖 11%（同 R105 D4 坑）',
         'E-rc2 初版 detail=True 全段 md.disasm() 被 OOM Killer 杀掉（exit 137），'
         '改为 detail=False + disasm_lite + 64KB 分块',
         'E-rc3 初版用 jmp 的 index 寄存器匹配字节表基址，只中 5/10；'
         '真 idiom 是字节表用 eax 索引、跳转表用 ecx 索引，两个寄存器不同',
     ]}
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
print('产物 %s (%d B)' % (OUT, os.path.getsize(OUT)), flush=True)
sys.exit(0 if not fails else 1)
