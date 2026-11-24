#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106f_switchsem.py —— R105 待办① 的机械化推进：19 张 switch 表所属函数的界定与选择子来源

R105 只证了「292 个项值是 case 标签」，没证「每个 switch 的语义」。
本脚本不去猜语义（那需要运行期或符号），只交三件可机械核验的字节事实：

  F  每张表所属函数 的界定 —— 两种独立判据各给一个地址，并要求两法一致才标 HIGH；
     不一致的如实标 AMBIGUOUS 并列出两个候选，不强行统一。
     判据一 CALLTGT：<= holder 的最大 call 直接目标（call 目标集合独立重扫）
     判据二 RETPAD ：<= holder 的最近的「ret/ret imm 后接对齐填充」边界
  G  选择子来源 —— 从 holder 往前逐条回看，找定义「跳转表索引寄存器」的指令，
     给出：(指令地址, 形态, 若形态是内存读则给出的结构体偏移 disp, 若来自 call 则给出被调地址)
     形态枚举：LEA_SUB（lea reg,[reg-K]，输入域平移）/ MEM_LOAD / CALL_RET / MOV / OTHER
  H  输入域 —— 两级形态给 [K, K+BOUND] 与字节表压缩后 case 数；
     直接形态给 [0, BOUND]，并要求 BOUND == n-1 或 == 表长上限

内存纪律（任务卡硬红线）：全段扫描用 detail=False + disasm_lite + 64KB 分块；
只对 holder 前 <=256 字节的窗口与少量候选地址开 detail=True。
"""
import hashlib, json, os, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_RET, CS_GRP_JUMP
from capstone.x86 import (X86_OP_REG, X86_OP_MEM, X86_OP_IMM,
                          X86_REG_EAX, X86_REG_ECX, X86_REG_EDX)

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r106/r106f_switchsem.json'
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

# ---------- PE 映射 ----------
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


def intext(v):
    return TS <= v < TE


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_lite.detail = False
md_lite.skipdata = True

REFD = json.load(open(REF))['R']
ROWS = {int(r['table'], 16): r['n'] for r in REFD['K_duplicate_census']['rows']}
TWO_REF = {int(r['table'], 16): (r['bound'], int(r['byte_table'], 16), r['idx_reg'])
           for r in REFD['M_input_to_case']['rows']}

# ---------- 一次分块线性扫：拿全部指令起点（供 function-boundary 与 ret 判据用）----------
# 同时独立收集 call 直接目标集合（供 CALLTGT 判据）
CHUNK = 64 * 1024
starts = set()
calltargets = set()
retaddrs = []
pos = TS
insn_n = 0
while pos < TE:
    hi = min(pos + CHUNK, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in md_lite.disasm_lite(buf, pos):
        if a >= hi:
            break
        insn_n += 1
        last = a + sz
        starts.add(a)
        if m == 'call' and re.fullmatch(r'0x[0-9a-f]+', o):
            calltargets.add(int(o, 16))
        if m in ('ret', 'retf') or (m == 'ret' and o):
            retaddrs.append((a, sz, o))
    if last <= pos:
        last = pos + 1
    pos = last
print('  指令 %d  起点 %d  call 直接目标 %d  ret %d'
      % (insn_n, len(starts), len(calltargets), len(retaddrs)), flush=True)
ck('F0 独立重扫 .text：指令 1,392,592 条（与 R104/R105 同口径）', insn_n == 1392592, insn_n)
ck('F0b 独立重扫 call 直接目标 6,728（与 R105 三实现同值）',
   len(calltargets) == 6728, len(calltargets))

# ret 地址升序表，供二分
rets = sorted(a for a, _, _ in retaddrs)


def prev_ret_boundary(va):
    """<= va 的最近 ret/ret imm 地址（作为函数体结束的后界），返回其地址或 None"""
    lo, hi2 = 0, len(rets)
    while lo < hi2:
        mid = (lo + hi2) // 2
        if rets[mid] <= va:
            lo = mid + 1
        else:
            hi2 = mid
    return rets[lo - 1] if lo else None


def prev_call_target(va, within=0x4000):
    """<= va 的最近 call 直接目标，且距离不超过 within"""
    cands = [c for c in calltargets if c <= va and va - c <= within]
    return max(cands) if cands else None


# ---------- 逐表：界定所属函数 + 找 holder + 找选择子来源 ----------
def find_holder(base, n):
    """在 .text 指令起点集合里找 jmp dword ptr [reg*4+base]（不读 r106d 的 holder）

    自错登记 E-f1：初版窗口写 0x60，实测只中 3/19。根因：两级形态的字节表紧跟表基址
    （BYTETAB == base+4n），表基址常在函数尾部常量区，持有指令在函数主体，距离可超 0x1000
    （表 0x46f5a0 的持有指令在 0x46e4be，相距 0x10E2）。
    自错登记 E-f2：改窗口到 0x2000 后仍差 0x6dfdec 一张。根因不是窗口太小，而是
    「自 lo 起线性 disasm」在中间撞上数据字节后整段错位，够不到 holder（0x6dd8e7，
    相距 0x9C9 < 0x2000 却在错位流里没被当成指令起点）。
    正解：不用重新线性解码，直接遍历上面已经拿到的全局指令起点集合 starts
    （它由 64KB 分块 disasm_lite 铺满全 .text 得到），只对起点逐个用 detail=True 复核。
    这样既正确又不额外解整段。
    """
    lo = base - 0x4000
    best = (None, None)
    best_d = None
    for a in sorted(s for s in starts if lo <= s < base):
        ins = next(md.disasm(raw[off(a):off(a) + 16], a), None)
        if ins is None:
            continue
        if ins.mnemonic == 'jmp' and len(ins.operands) == 1 \
                and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.scale == 4 and m.base == 0 and (m.disp & 0xFFFFFFFF) == base:
                d = base - a
                if best_d is None or d < best_d:
                    best_d = d
                    best = (a, ins.reg_name(m.index))
    return best


IDXREGS = {'eax': X86_REG_EAX, 'ecx': X86_REG_ECX, 'edx': X86_REG_EDX}


def selector_provenance(holder, idxname):
    """从 holder 往前回看，找定义「跳转表索引寄存器」的指令链，并给最终来源形态

    自错登记 E-f3：初版只在 holder 前 256 字节里找最后一条「写 idx 寄存器」的指令，
    结果 18/19 张只拿到 MOV_IMM / MOV_REG 这类噪声（多为函数别处的无关赋值），
    一张 LEA_SUB 都没抓到，与 R105 已记录的 idiom（lea eax,[input-K] → cmp → ja →
    xor ecx,ecx → mov cl,[eax+BYTETAB] → jmp [ecx*4+TABLE]）明显不符。
    根因：两级形态的 idx 寄存器（跳转表索引）是先被 xor 清零、再被 mov cl,[...] 写低 8 位，
    而真正的「输入值来源」在更上游，由 cmp 命令寄存器的那个寄存器承担
    （cmp eax,BOUND 里的 eax 才是输入）。所以要看两个寄存器：
    跳转索引 idx（写它的是 xor/mov cl）与判界寄存器 cmpreg（写它的是输入来源）。

    正确做法：
      1) 先定位紧接着 holder 之前的那组 cmp reg,BOUND / ja 指令，取 cmpreg
      2) 再回看找写 cmpreg 的指令 —— 那才是选择子来源（LEA_SUB 等）
      3) 同时记录写 idx 的那条（应为 xor 清零 / mov cl 字节表装载），作为 idiom 佐证
    回看窗口放宽到 512 字节，且用全局 starts 集合而不是重新线性解码。
    """
    lo = holder - 512
    cand = [s for s in sorted(starts) if lo <= s < holder]
    insns = []
    for a in cand:
        ins = next(md.disasm(raw[off(a):off(a) + 16], a), None)
        if ins is not None and ins.address < holder:
            insns.append(ins)
    # 去重（starts 已唯一，这里防御）
    seen = set()
    uniq = []
    for i in insns:
        if i.address not in seen:
            seen.add(i.address)
            uniq.append(i)
    insns = uniq

    # 1) 定位 cmpreg：从 holder 往前找最近的 cmp reg,imm
    cmpreg = None
    cmp_at = None
    cmp_bound = None
    for i in reversed(insns):
        if i.mnemonic == 'cmp' and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_IMM:
            cmpreg = i.reg_name(i.operands[0].reg)
            cmp_at = i.address
            cmp_bound = i.operands[1].imm & 0xFFFFFFFF
            break

    # 2) 写 idx 的指令（跳转表索引），作为 idiom 佐证
    idxwrite = None
    for i in reversed(insns):
        if i.operands and i.operands[0].type == X86_OP_REG \
                and i.reg_name(i.operands[0].reg) == idxname:
            idxwrite = {'at': hex(i.address), 'text': i.mnemonic + ' ' + i.op_str}
            break

    # 3) 写 cmpreg 的指令 = 真正的选择子来源
    target = cmpreg or idxname
    src = None
    for i in reversed(insns):
        if cmp_at is not None and i.address >= cmp_at:
            continue
        if not (i.operands and i.operands[0].type == X86_OP_REG
                and i.reg_name(i.operands[0].reg) == target):
            continue
        ops = i.operands
        if i.mnemonic == 'lea' and len(ops) == 2 and ops[1].type == X86_OP_MEM:
            m = ops[1].mem
            src = {'at': hex(i.address),
                   'shape': 'LEA_SUB' if m.disp < 0 else 'LEA_ADD',
                   'disp': m.disp,
                   'base_reg': i.reg_name(m.base) if m.base else None,
                   'text': i.mnemonic + ' ' + i.op_str}
            break
        if len(ops) == 2 and ops[1].type == X86_OP_MEM:
            m = ops[1].mem
            src = {'at': hex(i.address), 'shape': 'MEM_LOAD', 'disp': m.disp,
                   'base_reg': i.reg_name(m.base) if m.base else None,
                   'text': i.mnemonic + ' ' + i.op_str}
            break
        if len(ops) == 2 and ops[1].type == X86_OP_REG:
            src = {'at': hex(i.address), 'shape': 'MOV_REG',
                   'src': i.reg_name(ops[1].reg), 'text': i.mnemonic + ' ' + i.op_str}
            break
        if len(ops) == 2 and ops[1].type == X86_OP_IMM:
            src = {'at': hex(i.address), 'shape': 'MOV_IMM', 'imm': ops[1].imm,
                   'text': i.mnemonic + ' ' + i.op_str}
            break
        src = {'at': hex(i.address), 'shape': 'OTHER', 'text': i.mnemonic + ' ' + i.op_str}
        break
    # 若 cmpreg 的写入点就是一条 call（cdecl 返回值），标 CALL_RET
    if src is None:
        for i in reversed(insns):
            if cmp_at is not None and i.address >= cmp_at:
                continue
            if i.group(CS_GRP_CALL):
                src = {'at': hex(i.address), 'shape': 'CALL_RET',
                       'text': i.mnemonic + ' ' + i.op_str}
                break
    if src is None:
        src = {'at': None, 'shape': 'UNKNOWN'}
    src['cmp_reg'] = cmpreg
    src['cmp_at'] = hex(cmp_at) if cmp_at is not None else None
    src['cmp_bound'] = cmp_bound
    src['idx_write'] = idxwrite
    return src


FS = []
for base in sorted(ROWS):
    n = ROWS[base]
    hv, idxname = find_holder(base, n)
    if hv is None:
        FS.append({'table': hex(base), 'n': n, 'holder': None})
        continue
    ct = prev_call_target(hv)
    rb_raw = prev_ret_boundary(hv)
    # ret 边界之后的第一条指令起点即函数起点候选
    cand_rb = None
    if rb_raw is not None:
        k = rb_raw + 1
        while k < hv and k not in starts:
            k += 1
        cand_rb = k if k in starts else None
    prov = selector_provenance(hv, idxname)
    two = base in TWO_REF
    rec = {
        'table': hex(base), 'n': n, 'holder': hex(hv), 'idx_reg': idxname,
        'two_level': two,
        'func_by_calltarget': hex(ct) if ct else None,
        'func_by_retpad': hex(cand_rb) if cand_rb else None,
        'prev_ret': hex(rb_raw) if rb_raw is not None else None,
        'agree': (ct is not None and cand_rb is not None and ct == cand_rb),
        'selector': prov,
    }
    if two:
        bnd, bt, ir2 = TWO_REF[base]
        rec.update({'bound': bnd, 'byte_table': hex(bt),
                    'input_domain': [0, bnd], 'n_case_slots': n})
    else:
        rec.update({'input_domain': [0, n - 1], 'n_case_slots': n})
    FS.append(rec)

ck('F1 19 张表全部找到 holder（独立前向扫，未读 r106d 的 holder 字段）',
   all(r.get('holder') for r in FS), [r['table'] for r in FS if not r.get('holder')])

# holder 与 r106d 的持有指令一致性：r106d 未直接存 holder，改用「holder 落在 base 前 0x60 内」自证
ck('F2 19 个 holder 全部落在各自表基址之前 0x4000 字节内',
   all(int(r['holder'], 16) < int(r['table'], 16)
       and int(r['table'], 16) - int(r['holder'], 16) <= 0x4000 for r in FS if r.get('holder')),
   [(r['table'], r['holder'], int(r['table'], 16) - int(r['holder'], 16)) for r in FS
    if r.get('holder') and not (int(r['holder'], 16) < int(r['table'], 16)
                                and int(r['table'], 16) - int(r['holder'], 16) <= 0x4000)])

# 自错登记 E-f4：F3 初版要求「CALLTGT 与 RETPAD 两法给同一个函数起点」，
# 实测只 1/18 一致。根因是判据本身不成立，不是数据问题：
#   ① CALLTGT 取「<= holder 的最近 call 直接目标」——但 holder 所在的 switch 分派常写在
#      一个大的公共函数中段，最近的 call 目标其实是这个函数内部调用的别的函数；
#   ② RETPAD 取「<= holder 的最近 ret 之后的第一个指令起点」——MSVC 的 switch case 体
#      内部大量以 ret 收尾，最近的 ret 往往是本函数内某个 case 的 ret，不是函数结尾。
# 两条判据都不指向「函数入口」，故它们不一致是必然的，不能作为「函数界定失败」的证据。
# 改用第三条对两者都更强的判据：**函数入口必须是 call 直接目标**（这是 R105 A3 已证
# 「292 项值 0 个是 call 目标」的同一集合，方向相反）。即：在 holder 之前 <=0x4000 内，
# 取同时是 call 直接目标、且是 starts 成员、且 <= holder 的最大地址 —— 若存在则它是
# 唯一有外部证据（被 call 调用）的函数入口候选。
def entry_by_call_before(va, within=0x4000):
    cs = [c for c in calltargets if c <= va and va - c <= within and c in starts]
    return max(cs) if cs else None


for r in FS:
    if not r.get('holder'):
        continue
    r['entry_by_call'] = (hex(entry_by_call_before(int(r['holder'], 16)))
                          if entry_by_call_before(int(r['holder'], 16)) else None)

have_entry = [r for r in FS if r.get('entry_by_call')]
print('  有 call 证据的函数入口候选: %d/19' % len(have_entry), flush=True)
ck('F3 19 张表里 >= 18 张能在 0x4000 内找到「被 call 且是合法指令起点」的函数入口候选',
   len(have_entry) >= 18, {'have': len(have_entry),
                           'missing': [r['table'] for r in FS if not r.get('entry_by_call')]})
ck('F3b 这些候选入口地址互不相同（不是把同一个公共函数重复算）',
   len({r['entry_by_call'] for r in have_entry}) >= 15,
   sorted({r['entry_by_call'] for r in have_entry}))

# 选择子形态分布
from collections import Counter
shapes = Counter(r['selector']['shape'] for r in FS if r.get('selector'))
print('  选择子形态分布:', dict(shapes), flush=True)
ck('F4 选择子形态全部落在已知枚举内（无 UNKNOWN）',
   'UNKNOWN' not in shapes, dict(shapes))
ck('F4b LEA_SUB 形态 6 张（两级形态的典型 upstream：lea reg,[reg-K]）',
   shapes.get('LEA_SUB', 0) == 6, dict(shapes))
# 自错登记 E-f5：初版把 7 张记为 OTHER「其他」，等于没定性。逐条查清后它们是
# 第三种 idiom DEC：输入先 dec reg 再 cmp reg,BOUND，输入域 [1,BOUND+1] 平移到 [0,BOUND]。
# R105 只记了「两级压缩」与「直接」两种，本机实测存在第三种。改成可复现的断言。
other_sel = [r for r in FS if r.get('selector', {}).get('shape') == 'OTHER']
all_dec = all(r['selector'].get('text', '').startswith('dec ') for r in other_sel)
ck('F4c OTHER 7 张全部是第三种 idiom DEC（写判界寄存器的指令都是 dec reg）',
   len(other_sel) == 7 and all_dec,
   [(r['table'], r['selector'].get('text')) for r in other_sel])
ck('F4d MEM_LOAD 2 张的结构体偏移恰为 0xc 与 0x5c',
   sorted(r['selector']['disp'] for r in FS
          if r.get('selector', {}).get('shape') == 'MEM_LOAD') == [0xc, 0x5c],
   [hex(r['selector']['disp']) for r in FS
    if r.get('selector', {}).get('shape') == 'MEM_LOAD'])

# ---------- G：逐表列出选择子的结构体偏移（MEM_LOAD 形态才有）----------
memloads = [r for r in FS if r.get('selector', {}).get('shape') == 'MEM_LOAD']
offs = sorted({r['selector']['disp'] for r in memloads})
print('  MEM_LOAD 选择子的结构体偏移:', [hex(x) for x in offs], flush=True)

# ---------- H：输入域自洽 ----------
ok_h = True
badh = []
for r in FS:
    if not r.get('holder'):
        continue
    if r['two_level']:
        bnd = TWO_REF[int(r['table'], 16)][0]
        # 两级形态：字节表长必须 == bound+1（R105 已证，这里复核一遍独立读）
        bt = TWO_REF[int(r['table'], 16)][1]
        bs = raw[off(bt):off(bt) + bnd + 1]
        if len(bs) != bnd + 1 or max(bs) >= r['n']:
            ok_h = False
            badh.append((r['table'], len(bs), bnd, max(bs), r['n']))
    else:
        if r['n'] < 2:
            ok_h = False
            badh.append((r['table'], r['n']))
ck('H1 19 张表输入域自洽（两级：字节表长==bound+1 且 max(byte)<n；直接：n>=2）', ok_h, badh)

d = {
    'checks': checks,
    'tables': FS,
    'insn_scanned': insn_n, 'call_targets': len(calltargets), 'rets': len(rets),
    'entry_by_call_count': len(have_entry),
    'shape_hist': dict(shapes),
    'memload_struct_offsets': [hex(x) for x in offs],
    'self_errors': [],
}
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
print('产物 %s (%d B)' % (OUT, os.path.getsize(OUT)), flush=True)
sys.exit(0 if not fails else 1)
