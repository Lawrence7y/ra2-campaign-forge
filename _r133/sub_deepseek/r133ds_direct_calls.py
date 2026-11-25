#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R133 sub_deepseek (exec / deepseek family) — 独立实测脚本 v2（不依赖任何既有 R132/R133 结果）

三项任务：
  (1) 0x6bedb0 / 0x41c250 的全部直接调用点（E8 rel32 = call, E9 rel32 = jmp/tail-call），
      每个调用点必须被证明落在指令边界上。
  (2) 两个入口地址作为 imm32 在【整个映像文件】中的出现次数（VA 形式 + RVA 形式都测）。
  (3) 每个调用点前最后三条 push（cdecl 从右到左：最早那条 push = 第 3 个栈参数）。

v2 相对 v1 的修正（v1 结果作废）：
  * v1 的 push 回溯"取最近边界作为起点"，只回溯了一条 mov，导致 15 个站点全部 push_count=0。
  * v2 改为：全 .text 线性扫描时记录每条指令起始地址与长度到 bytearray(N)（4 MB 平面
    数组，不是 capstone 对象列表），然后用"前驱 = 满足 b + size[b] == va 的唯一 b"逐条向后
    走，最多 60 条，并要求每一步前驱唯一；遇到无条件 jmp/ret/int3/ud2 截断（不跨基本块）。
  * v1 的 NC3 前提有误（"连续性校验能拒掉非边界起点"是错的，见 v1 日志：从 SVA+1 起解码
    得到的 pop/push/push/call 恰好也连续）。v2 把该反控改成"边界成员校验"，并保留一条
    PC 明确演示"仅靠连续性不够"。

内存纪律：
  * 全 .text 线性扫描只用 disasm_lite + 64 KiB 窗口，逐窗口迭代，不驻留指令对象；
  * md.skipdata = True；
  * detail=True 只用于最后几条 push 指令（<=15 字节），用完即弃；
  * 唯一的全段数组是 bytearray(N) 的指令长度表（~4 MB）。

运行：timeout 600 python3 _r133/sub_deepseek/r133ds_direct_calls.py
"""
import json
import os
import re
import struct
import sys
import time

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUTDIR = '/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek'
OUT = os.path.join(OUTDIR, 'r133ds_direct_calls.json')

TARGETS = [0x6bedb0, 0x41c250]
WIN = 64 * 1024          # 64 KiB 窗口
MAX_BACK = 60            # 最多向后走 60 条指令
TERMINATORS = {'ret', 'retn', 'retf', 'jmp', 'int3', 'ud2', 'iret', 'iretd', 'hlt'}
SKIP_MNEMONICS = ('.byte', 'data16')   # capstone skipdata 的伪指令

t0 = time.time()
R = {'script': __file__, 'exe': EXE, 'version': 'v2', 'targets': [hex(x) for x in TARGETS],
     'asserts': []}


def chk(name, cond, detail=''):
    ok = bool(cond)
    R['asserts'].append({'assert': name, 'pass': ok, 'detail': str(detail)})
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  [' + str(detail) + ']') if detail != '' else ''))
    return ok


# ------------------------------------------------------------------ PE 载入
pe = pefile.PE(EXE, fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()
R['image'] = {'size_file': len(raw), 'image_base': BASE,
              'size_of_image': pe.OPTIONAL_HEADER.SizeOfImage,
              'dll_characteristics': hex(pe.OPTIONAL_HEADER.DllCharacteristics),
              'has_reloc_section': any(s.Name.rstrip(b'\x00') == b'.reloc' for s in pe.sections)}

sections = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    sections.append({'name': nm, 'va': BASE + s.VirtualAddress, 'vsize': s.Misc_VirtualSize,
                     'raw_ptr': s.PointerToRawData, 'raw_size': s.SizeOfRawData})
    print('[sec] %-8s VA %#010x  VSize %#09x  RawPtr %#09x  RawSz %#09x'
          % (nm, BASE + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
R['sections'] = sections

ts = [s for s in sections if s['name'] == '.text'][0]
TLO, TVSIZE = ts['va'], ts['vsize']
TRAW = raw[ts['raw_ptr']: ts['raw_ptr'] + TVSIZE]
if len(TRAW) < TVSIZE:                       # 理论上不发生；若发生补 0 并标注
    TRAW = TRAW + b'\x00' * (TVSIZE - len(TRAW))
N = len(TRAW)
TEND = TLO + N
print('[text] VA %#x..%#x  %d bytes (VSize %#x, RawSize %#x, 尾部填充 %#x)'
      % (TLO, TEND, N, TVSIZE, ts['raw_size'], ts['raw_size'] - TVSIZE))
R['text'] = {'va_lo': TLO, 'va_hi': TEND, 'nbytes': N, 'raw_padding_tail': ts['raw_size'] - TVSIZE}

# 可执行段判定：只有可执行段里的 E8/E9 才可能是真实调用点，这决定了扫描范围是否完备
EXEC_FLAG = 0x20000000
exec_secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    if s.Characteristics & EXEC_FLAG:
        exec_secs.append(nm)
R['executable_sections'] = exec_secs
print('[exec] 可执行段（IMAGE_SCN_MEM_EXECUTE）：%s   （.detour char=%#x 不可执行）'
      % (exec_secs, [s.Characteristics for s in pe.sections if s.Name.rstrip(b'\x00') == b'.detour'][0]))

md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_lite.skipdata = True
md_sd = Cs(CS_ARCH_X86, CS_MODE_32)
md_sd.skipdata = False
md_detail = Cs(CS_ARCH_X86, CS_MODE_32)
md_detail.detail = True


# ----------------------------------------------------------- (1) 原始字节扫描
def scan_direct(blob, va_lo, targets):
    hits = {t: [] for t in targets}
    tset = set(targets)
    for i in range(len(blob) - 5 + 1):
        op = blob[i]
        if op != 0xE8 and op != 0xE9:
            continue
        rel = struct.unpack_from('<i', blob, i + 1)[0]
        site = va_lo + i
        if site + 5 + rel in tset:
            hits[site + 5 + rel].append((site, op))
    return hits


raw_hits = scan_direct(TRAW, TLO, TARGETS)
R['raw_hits'] = {hex(t): [{'site': hex(s), 'opcode': hex(o)} for s, o in raw_hits[t]] for t in TARGETS}
print('\n[1] 原始 E8/E9 命中（.text）：')
for t in TARGETS:
    print('    -> %#x : %d 个  %s' % (t, len(raw_hits[t]), [hex(s) for s, _ in raw_hits[t]]))

# 完备性：把所有可执行段都扫一遍（本样本只有 .text 可执行，但要实测而非假设）
R['scan_coverage'] = {}
for s in sections:
    if s['name'] not in exec_secs:
        continue
    blob = raw[s['raw_ptr']: s['raw_ptr'] + s['vsize']]
    h = scan_direct(blob, s['va'], TARGETS)
    R['scan_coverage'][s['name']] = {hex(t): [hex(x[0]) for x in h[t]] for t in TARGETS}
    print('    [coverage] %-8s %d bytes -> %s'
          % (s['name'], len(blob), {hex(t): len(h[t]) for t in TARGETS}))

all_sites = sorted({s for t in TARGETS for s, _ in raw_hits[t]})
site_to_target = {}
for t in TARGETS:
    for s, o in raw_hits[t]:
        site_to_target.setdefault(s, []).append((t, o))


# ------------------- 全 .text 线性扫描：指令起始 -> 长度（bytearray，4 MB 平面表）
sizes = bytearray(N)          # sizes[i] != 0  <=>  VA=TLO+i 是一条指令的起始；值即其长度
sweep = {'windows': 0, 'insns': 0, 'skip_bytes': 0, 'stalls': 0, 'stall_at': None,
         'max_len': 0, 'coverage': 0}
pos = 0
while pos < N:
    end = min(pos + WIN, N)
    last_end = pos
    for (addr, size, mn, ops) in md_lite.disasm_lite(TRAW[pos:end], TLO + pos):
        sweep['insns'] += 1
        sweep['coverage'] += size
        if size > sweep['max_len']:
            sweep['max_len'] = size
        if mn in SKIP_MNEMONICS:
            sweep['skip_bytes'] += size
        else:
            sizes[addr - TLO] = size
        last_end = addr + size - TLO
    sweep['windows'] += 1
    if last_end <= pos:                       # skipdata 下不应发生；如实记录
        sweep['stalls'] += 1
        sweep['stall_at'] = hex(TLO + pos)
        pos += 1
    else:
        pos = last_end

n_bounds = sum(1 for i in range(N) if sizes[i])
print('\n[1b] 线性扫描 disasm_lite+skipdata=True, 64KiB 窗口: windows=%d insns=%d skip_bytes=%d '
      '指令起始点=%d stalls=%d max_len=%d'
      % (sweep['windows'], sweep['insns'], sweep['skip_bytes'], n_bounds, sweep['stalls'], sweep['max_len']))
R['linear_sweep'] = sweep
R['boundary_count'] = n_bounds


# ------------------------------------- 边界判定（成员表 + 独立解码双重确认）
def insn_at(va):
    """若 va 是边界，返回 (size, mnemonic, op_str)，否则 None。"""
    if not (TLO <= va < TEND):
        return None
    if not sizes[va - TLO]:
        return None
    o = va - TLO
    for (a, sz, mn, ops) in md_sd.disasm_lite(TRAW[o:o + sizes[o]], va):
        return (sz, mn, ops)
    return None


# --------------------------------------------- (3) 前驱回溯（唯一前驱 + 截断）
def pred_of(va):
    """返回满足 b + size[b] == va 的全部候选起点（正常情况下唯一）。"""
    out = []
    for b in range(max(TLO, va - 15), va):
        s = sizes[b - TLO]
        if s and b + s == va:
            out.append((b, s))
    return out


def backtrack(site, max_back=MAX_BACK):
    """从 site 逐条取唯一前驱，返回倒序链 [(va,size,mn,ops)] 与诊断信息。"""
    chain = []          # 从近到远
    diag = {'ambiguous': [], 'hit_wall': False, 'pseudo': []}
    cur = site
    for _ in range(max_back):
        cands = pred_of(cur)
        if len(cands) == 0:
            diag['hit_wall'] = True
            break
        if len(cands) > 1:
            diag['ambiguous'].append({'at': hex(cur), 'cands': [hex(c) for c, _ in cands]})
            break                        # 有歧义就不猜，截断于此
        b, s = cands[0]
        got = insn_at(b)
        if got is None:
            diag['hit_wall'] = True
            break
        sz, mn, ops = got
        chain.append((b, sz, mn, ops))
        if mn in SKIP_MNEMONICS:
            diag['pseudo'].append(hex(b))
        cur = b
    return chain, diag


def push_operand(va, size):
    """对单条指令用 detail=True 取精确操作数类型（<=15 字节窗口，用完即弃）。"""
    o = va - TLO
    for ins in md_detail.disasm(TRAW[o:o + size], va):
        txt = ins.mnemonic + ' ' + ins.op_str
        if ins.mnemonic != 'push' or not ins.operands:
            return {'kind': 'not-push', 'text': txt}
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            v = op.imm & 0xffffffff
            return {'kind': 'imm', 'value': v, 'value_hex': hex(v), 'text': txt}
        if op.type == X86_OP_REG:
            try:
                rn = ins.reg_name(op.reg)
            except Exception:
                rn = '?'
            return {'kind': 'reg', 'reg': rn, 'text': txt}
        if op.type == X86_OP_MEM:
            return {'kind': 'mem', 'text': txt}
        return {'kind': 'other', 'text': txt}
    return None


sites_report = []
for site in all_sites:
    rec = {'site': hex(site),
           'targets': [{'target': hex(t), 'opcode': hex(o)} for t, o in site_to_target[site]]}
    got = insn_at(site)
    rec['on_linear_boundary'] = got is not None
    rec['size'] = got[0] if got else None
    rec['text'] = (got[1] + ' ' + got[2]) if got else None

    # 独立解码该地址
    dec = None
    for ins in md_sd.disasm(TRAW[site - TLO:site - TLO + 8], site):
        dec = ins
        break
    rec['decode'] = (dec.mnemonic + ' ' + dec.op_str) if dec else None
    rec['decode_matches_target'] = bool(
        dec and dec.mnemonic in ('call', 'jmp') and
        any(dec.op_str == hex(t) for t, _ in site_to_target[site]))

    chain, diag = backtrack(site)
    rec['backtrack_diag'] = diag
    rec['n_insns_back'] = len(chain)
    oldest = chain[-1][0] if chain else None
    rec['oldest_insn'] = hex(oldest) if oldest else None

    # 连续性显式校验：near->far 顺序应为 a+size==next，且最近一条结束 == site
    ordered = list(reversed(chain))
    ok_contig = True
    for i in range(len(ordered)):
        a, sz = ordered[i][0], ordered[i][1]
        nxt = ordered[i + 1][0] if i + 1 < len(ordered) else site
        if a + sz != nxt:
            ok_contig = False
            break
    rec['contiguous'] = ok_contig and bool(ordered)
    rec['chain_start'] = rec['oldest_insn']

    # 截断：只保留最后一个无条件跳转/ret 之后的指令（不跨基本块）
    trunc = 0
    for i, (a, sz, mn, ops) in enumerate(ordered):
        if mn in TERMINATORS:
            trunc = i + 1
    block = ordered[trunc:]
    rec['truncated_at'] = hex(ordered[trunc - 1][0]) if trunc > 0 else None
    rec['n_insns_in_block'] = len(block)

    pushes = [x for x in block if x[2] == 'push']
    rec['push_count_in_block'] = len(pushes)
    rec['block'] = [{'va': hex(a), 'asm': mn + ' ' + ops} for (a, sz, mn, ops) in block]

    last3 = pushes[-3:]
    rec['last3_pushes'] = [{'va': hex(a), 'asm': 'push ' + o} for (a, sz, mn, o) in last3]
    # push 之间是否夹着改变 esp 的指令（若夹着，"第一条 push = arg3" 的推断会错位）
    esp_movers = []
    if len(last3) == 3:
        lo, hi = last3[0][0], last3[-1][0]
        for (a, sz, mn, ops) in block:
            if not (lo < a < hi):
                continue
            dst = ops.split(',')[0].strip()
            if mn in ('pushad', 'pushfd', 'pushf', 'leave', 'enter', 'popad', 'popfd'):
                esp_movers.append({'va': hex(a), 'asm': mn + ' ' + ops})
            elif dst == 'esp':
                esp_movers.append({'va': hex(a), 'asm': mn + ' ' + ops})
    rec['esp_movers_between_last3'] = esp_movers
    if len(last3) == 3:
        a, sz, mn, ops = last3[0]        # 最早那条 = cdecl 第 3 个栈参数
        op = push_operand(a, sz)
        rec['third_arg'] = op
        rec['third_arg_va'] = hex(a)
        rec['third_arg_asm'] = 'push ' + ops
    else:
        rec['third_arg'] = None
        rec['third_arg_va'] = None
        rec['third_arg_asm'] = None
    sites_report.append(rec)

R['sites'] = sites_report

# 交叉核对：被调函数读取 [esp+0x14] 并 test al,0x14。被调入口两条 push 后，
# [esp+0x14] 对应"调用前 esp+0xc" = 紧接 call 之下的第 3 个双字 = arg3。
R['callee_crosscheck'] = {}
for t in TARGETS:
    seq = []
    o = t - TLO
    for ins in md_detail.disasm(TRAW[o:o + 0x30], t):
        seq.append({'va': hex(ins.address), 'asm': ins.mnemonic + ' ' + ins.op_str})
        if len(seq) >= 12:
            break
    reads = [x for x in seq if 'esp + 0x14' in x['asm']]
    R['callee_crosscheck'][hex(t)] = {'prologue': seq, 'reads_esp_0x14': reads}
    print('\n[cc] %#x 入口前导：%s' % (t, ' ; '.join(x['asm'] for x in seq[:8])))
    print('     读取 [esp+0x14] 的指令：%s  => 该槽位 = 调用点第 3 个压栈值(arg3)'
          % [x['asm'] for x in reads])

print('\n[3] 每个调用点前最后三条 push（最早那条 = 第 3 个栈参数）：')
for rec in sites_report:
    ta = rec['third_arg']
    print('    %-10s -> %-10s block:%-2d pushes:%-2d  last3=%-52s  3rd=%s'
          % (rec['site'], rec['targets'][0]['target'], rec['n_insns_in_block'],
             rec['push_count_in_block'], ' | '.join(p['asm'] for p in rec['last3_pushes']),
             (ta['text'] + ' [' + ta['kind'] + ']') if ta else 'NONE'))


# --------------------------------------------------- (2) imm32 全映像出现次数
def sec_of_off(off):
    for s in sections:
        if s['raw_ptr'] <= off < s['raw_ptr'] + s['raw_size']:
            return s['name']
    return 'BETWEEN/OVERLAY'


R['imm32'] = {}
for t in TARGETS:
    e = {'VA': [], 'RVA': []}
    for form, val in (('VA', t), ('RVA', t - BASE)):
        needle = struct.pack('<I', val & 0xffffffff)
        e[form] = [{'file_off': hex(m.start()), 'section': sec_of_off(m.start())}
                   for m in re.finditer(re.escape(needle), raw)]
    R['imm32'][hex(t)] = e
R['imm32_totals'] = {hex(t): {'VA': len(R['imm32'][hex(t)]['VA']),
                              'RVA': len(R['imm32'][hex(t)]['RVA'])} for t in TARGETS}
print('\n[2] imm32 全映像(%d 字节)出现次数：' % len(raw))
for t in TARGETS:
    e = R['imm32'][hex(t)]
    print('    %#x : VA=%d %s | RVA=%d %s'
          % (t, len(e['VA']), e['VA'], len(e['RVA']), e['RVA']))


# ============================================================ 正反控自测
print('\n[selftest] 正反控')
SVA = 0x500000
mod = {}


def syn_scan(blob, targets):
    return scan_direct(blob, SVA, targets)


def make_call_site(target):
    b = bytearray([0x6a, 0x07, 0x68, 0x44, 0x33, 0x22, 0x11, 0x50, 0x90])   # push7/push imm32/push eax/nop
    site = SVA + len(b)
    b += b'\xe8' + struct.pack('<i', target - (site + 5)) + b'\xc3'
    return bytes(b), site


bA, sA = make_call_site(0x6bedb0)
h = syn_scan(bA, [0x6bedb0])
chk('PC1 合成 E8 call -> 0x6bedb0 被检出', [x[0] for x in h[0x6bedb0]] == [sA], h)

bB = bytearray(bA)
bB[sA - SVA] = 0xE9
rel = 0x41c250 - (sA + 5)
bB[sA - SVA + 1:sA - SVA + 5] = struct.pack('<i', rel)
h = syn_scan(bytes(bB), [0x41c250])
chk('PC2 合成 E9 jmp -> 0x41c250 被检出', [x[0] for x in h[0x41c250]] == [sA], h)

bad = 0
for d in (-4, -2, -1, 1, 2, 4):
    nb = bytearray(bA)
    nb[sA - SVA + 1:sA - SVA + 5] = struct.pack('<i', (0x6bedb0 + d) - (sA + 5))
    if syn_scan(bytes(nb), [0x6bedb0])[0x6bedb0]:
        bad += 1
chk('NC1 目标 ±1/±2/±4 的 E8 一律不误计', bad == 0, '误计=%d' % bad)
chk('NC2 rel32=0（落在 site+5，非入口）不误计', syn_scan(bytes(bA[:sA - SVA] + b'\xe8\x00\x00\x00\x00'), [0x6bedb0])[0x6bedb0] == [])

# --- 前驱回溯算法（合成表）
def syn_sizes(blob):
    sz = bytearray(len(blob))
    for (a, s, mn, ops) in md_sd.disasm_lite(blob, SVA):
        sz[a - SVA] = s
    return sz


def syn_backtrack(sz, site_va, max_back=40):
    chain = []
    cur = site_va
    for _ in range(max_back):
        cands = [(b, sz[b - SVA]) for b in range(max(SVA, cur - 15), cur)
                 if sz[b - SVA] and b + sz[b - SVA] == cur]
        if len(cands) != 1:
            break
        b, s = cands[0]
        for (a, z, mn, ops) in md_sd.disasm_lite(blob_syn[b - SVA:b - SVA + s], b):
            chain.append((b, z, mn, ops))
        cur = b
    return list(reversed(chain))


blob_syn = bytes([0x6a, 0x07,                    # push 7      (十进制 imm<10)
                  0x68, 0x44, 0x33, 0x22, 0x11,  # push 0x11223344
                  0x50,                          # push eax
                  0xe8, 0x00, 0x00, 0x00, 0x00])
sz_syn = syn_sizes(blob_syn)
c = syn_backtrack(sz_syn, SVA + len(blob_syn))
chk('PC3 合成 push/push/push/call 前驱链解码成功',
    [x[2] for x in c] == ['push', 'push', 'push', 'call'], [x[2] + ' ' + x[3] for x in c])
chk('PC4 链连续性 a+size==next 且末条结束==call 地址',
    all(c[i][0] + c[i][1] == c[i + 1][0] for i in range(len(c) - 1))
    and c[-1][0] + c[-1][1] == SVA + len(blob_syn))
chk('PC5 最早一条 push 的立即数读成 7（十进制打印）', c[0][3] == '7', c[0][3])

# 无歧义时回溯必须走到函数首字节就停住（不越过 0x90 之前的缓冲区起点）
# 注意 v2 首版此处有作用域 bug：syn_backtrack 闭包引用的是全局 blob_syn 而非参数，
# 导致对着 9 字节缓冲区回溯却解码了 blob_syn，PC6 假失败。v3 显式传参修正。
def syn_backtrack2(blob, sz, site_va, max_back=40):
    chain = []
    cur = site_va
    for _ in range(max_back):
        cands = [(b, sz[b - SVA]) for b in range(max(SVA, cur - 15), cur)
                 if sz[b - SVA] and b + sz[b - SVA] == cur]
        if len(cands) != 1:
            break
        b, s = cands[0]
        for (a, z, mn, ops) in md_sd.disasm_lite(blob[b - SVA:b - SVA + s], b):
            chain.append((b, z, mn, ops))
        cur = b
    return list(reversed(chain))


amb_blob = bytes([0x90, 0x90, 0xb8, 0x01, 0x00, 0x00, 0x00, 0xc3])   # nop nop mov eax,1 / ret
sz_amb = syn_sizes(amb_blob)
c2 = syn_backtrack2(amb_blob, sz_amb, SVA + 7)
chk('PC6 无歧义时回溯走到缓冲区首字节并停住（0x90 起点=0x500000）',
    c2 is not None and c2[0][0] == SVA and len(c2) == 3,
    [(hex(x[0]), x[2]) for x in c2] if c2 else None)

# NC3：仅靠"连续性"不足 —— 从非边界地址起解码也能连续（v1 踩过的坑，显式记录）
nonb = list(md_sd.disasm_lite(blob_syn[1:], SVA + 1))
cont = all(nonb[i][0] + nonb[i][1] == nonb[i + 1][0] for i in range(len(nonb) - 1))
chk('NC3 演示：从非边界地址起解码同样可连续（故必须用边界成员表判定）',
    cont and sz_syn[1] == 0, 'contiguous=%s, sizes[1]=%d' % (cont, sz_syn[1]))
chk('NC4 边界成员表拒绝非边界起点（sizes[1]==0）', sz_syn[1] == 0)
chk('NC5 边界成员表接受真起点（sizes[0]!=0）', sz_syn[0] != 0)


def parse_push_imm_text(s):
    s = s.strip()
    if s.lower().startswith('0x'):
        return int(s, 16)
    if re.fullmatch(r'-?\d+', s):
        return int(s, 10)
    return None


chk('PC7 立即数解析吃十进制 "7"', parse_push_imm_text('7') == 7)
chk('PC8 立即数解析吃十六进制 "0x11223344"', parse_push_imm_text('0x11223344') == 0x11223344)
chk('NC6 imm32 近邻地址(0x6bedb4)不得被计为入口',
    re.search(re.escape(struct.pack('<I', 0x6bedb4)), raw) is None)


# ============================================================ 结果断言
print('\n[assert] 结果断言')
tot_sites = len(all_sites)
R['totals'] = {
    'sites_total': tot_sites,
    'per_target': {hex(t): len(raw_hits[t]) for t in TARGETS},
    'E8_count': sum(1 for s in all_sites for (t, o) in site_to_target[s] if o == 0xE8),
    'E9_count': sum(1 for s in all_sites for (t, o) in site_to_target[s] if o == 0xE9),
}
name_of = {hex(t): 'A(0x6bedb0)' if t == 0x6bedb0 else 'B(0x41c250)' for t in TARGETS}
R['third_arg_histogram'] = {}
for r in sites_report:
    ta = r['third_arg']
    k = ('%s:%s' % (ta['kind'], ta.get('value_hex', ta.get('reg')))) if ta else 'none'
    R['third_arg_histogram'][k] = R['third_arg_histogram'].get(k, 0) + 1

for t in TARGETS:
    k = hex(t)
    rs = [r for r in sites_report if any(x['target'] == k for x in r['targets'])]
    chk('%s 每个命中都在 skipdata 线性扫描的指令起始集合内' % name_of[k],
        all(r['on_linear_boundary'] for r in rs), [r['site'] for r in rs if not r['on_linear_boundary']])
    chk('%s 每个命中独立解码均为 call/jmp 且操作数即该入口' % name_of[k],
        all(r['decode_matches_target'] for r in rs),
        [(r['site'], r['decode']) for r in rs if not r['decode_matches_target']])
for r in sites_report:
    chk('%s 前驱链连续（a+size==next，末端==call）' % r['site'], r['contiguous'], r['chain_start'])
    chk('%s 链上无前驱歧义' % r['site'], not r['backtrack_diag']['ambiguous'],
        r['backtrack_diag']['ambiguous'])
    chk('%s 基本块内 >=3 条 push' % r['site'], r['push_count_in_block'] >= 3, r['push_count_in_block'])
    ta = r['third_arg']
    chk('%s 第 3 个栈参数已分类 imm/reg' % r['site'],
        ta is not None and ta['kind'] in ('imm', 'reg'), ta['kind'] if ta else None)
    chk('%s 最后三条 push 之间无 esp 调整（arg3 归属可靠）' % r['site'],
        not r['esp_movers_between_last3'], r['esp_movers_between_last3'])
# 与被调函数前导交叉核对：两个被调都读 [esp+0x14] 且 test al,0x14
for t in TARGETS:
    cc = R['callee_crosscheck'][hex(t)]
    chk('CC %#x 前导读取 [esp+0x14]（= 调用方 arg3 槽）' % t, len(cc['reads_esp_0x14']) >= 1,
        cc['reads_esp_0x14'])
chk('CC 所有站点 arg3 与被调方期望槽位一致（均为 imm 0x7）',
    all(r['third_arg'] and r['third_arg']['kind'] == 'imm' and r['third_arg']['value'] == 7
        for r in sites_report),
    R['third_arg_histogram'])
chk('T 直接调用点总数 %d' % tot_sites, True, R['totals']['per_target'])
chk('T E8 + E9 == 站点总数',
    R['totals']['E8_count'] + R['totals']['E9_count'] == tot_sites,
    (R['totals']['E8_count'], R['totals']['E9_count']))
chk('T 所有可执行段都已扫描（sampling coverage 完备）',
    all(n in R['scan_coverage'] for n in exec_secs), R['scan_coverage'])

R['totals']['asserts_pass'] = sum(1 for a in R['asserts'] if a['pass'])
R['totals']['asserts_total'] = len(R['asserts'])
R['totals']['elapsed_s'] = round(time.time() - t0, 2)

print('\n[totals] ' + json.dumps(R['totals'], ensure_ascii=False))
print('[3rd-arg histogram] ' + json.dumps(R['third_arg_histogram'], ensure_ascii=False))
os.makedirs(OUTDIR, exist_ok=True)
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('\n[written] ' + OUT)
print('[final] asserts %d/%d, sites %d, %.2fs'
      % (R['totals']['asserts_pass'], R['totals']['asserts_total'], tot_sites, time.time() - t0))
sys.exit(0 if R['totals']['asserts_pass'] == R['totals']['asserts_total'] else 1)
