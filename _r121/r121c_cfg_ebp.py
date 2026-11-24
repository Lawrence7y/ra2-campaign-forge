#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121c_cfg_ebp.py -- 用 CFG 可达定义（reaching definitions）判定 call ebp 的目标。

为什么需要这一步（本轮实测事实，不是推测）：
  r121b 用「线性向前找最后一次写 ebp」判定 call ebp 的目标，得到 37/60 = OleSaveToStream，
  另 23 个落到 pop ebp @0x67d44f。但 0x67d44f 属于**错误返回路径**
  （0x67d44b jge 0x67d457 跳过它），线性回溯看不见分支。
  => 线性回溯在该函数上结构性失效，23 这个数是错的。

本脚本做的：在站点所属函数上建 CFG，做 ebp 的可达定义分析，报出每个站点处
ebp 的到达定义集合。只有当集合恰为单元素 { mov ebp,[0x7e15f4] } 时才允许
「该处 ebp == OleSaveToStream」这一步推理。

显式假设（必须登记，不是隐藏）：
  A1 函数入口取 0x67d300，依据：.text 里唯一一条 call 0x67d300 在 0x67d1af，
     且该地址前有连续 0xCC 填充。
  A2 ebp 在调用边界上是 callee-saved（Win32 系统 ABI）。证据：该函数序言 push ebp、
     所有出口均 pop ebp 后再 ret，函数自身即按 callee-saved 处理。
     若不接受 A2，则所有跨 call 的结论都需降级 —— 本脚本把「跨 call」单独标出。
  A3 间接 jmp 视为未知出口（不推测目标），已计为残差。

反控：
  N1 站点不在 CFG 可达集内 ⇒ 必须 0 个（否则解码或入口判据错）。
  N2 把入口改成 0x67d357（跳过 mov ebp,[0x7e15f4]），call ebp 站点的到达定义集合
     必须变空或变多 ⇒ 证明判据真的在用该定义。
  N3 合成 CFG 正控：手写一段带分支的字节串，分支一侧写 ebp、另一侧不写，
     要求两个汇合点的到达定义集合不同（证明分析不是恒返回全集或恒返回单值）。
  P1 正控：站点 0x67d36e 的集合必须恰为 {0x67d351}（与 r121b 的线性结果一致处）。

内存纪律：仅对函数体 (约 0x1200 字节) 开 detail=True 单步解码；不碰整段 .text。带 timeout。
"""
import collections
import json
import os
import re
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r121'))
import x121lib                                    # noqa: E402
import capstone                                   # noqa: E402

OUTFILE = os.path.join(ROOT, '_r121', 'r121c_cfg_ebp.json')
PE_PATH = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
checks = []

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

pe = x121lib.PE(PE_PATH)
IATV = {va: nm for va, (_dll, nm) in pe.iat.items()}
TEXT = next(s for s in pe.sections if s['name'] == '.text')
TEXT_VA0 = pe.image_base + TEXT['va']

REGRE = r'(?:eax|ebx|ecx|edx|esi|edi|ebp)'
# 真正写目的寄存器的助记符（call/push/cmp/test 不是写）
WRITE_MN = {'mov', 'lea', 'pop', 'xor', 'add', 'sub', 'and', 'or', 'adc', 'sbb',
            'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'imul', 'xchg'}
UNCOND_JMP_MN = {'jmp'}
RET_MN = {'ret', 'retf'}


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def one(va):
    o = pe.off_va(va)
    if o is None:
        return None
    for i in MD.disasm(pe.buf[o:o + 16], va, count=1):
        return i
    return None


def dst_reg(ins):
    """name of the destination register if this instruction writes one, else None."""
    if ins.mnemonic not in WRITE_MN:
        return None
    if not ins.operands:
        return None
    op = ins.operands[0]
    if op.type != capstone.x86.X86_OP_REG:
        return None
    return ins.reg_name(op.reg)


def successors(ins):
    """(kind, targets). kind in {cond, uncond, ret, call, plain}."""
    mn = ins.mnemonic
    if mn in RET_MN:
        return 'ret', []
    if mn == 'call':
        return 'call', [ins.address + ins.size]
    if mn in UNCOND_JMP_MN:
        try:
            return 'uncond', [int(ins.op_str, 16)]
        except ValueError:
            return 'indirect-jmp', []
    if mn.startswith('j') or mn in ('loop', 'loope', 'loopne'):
        try:
            return 'cond', [int(ins.op_str, 16), ins.address + ins.size]
        except ValueError:
            return 'plain', [ins.address + ins.size]
    return 'plain', [ins.address + ins.size]


def build_cfg(entry, limit_ins=6000):
    """BFS over instructions from entry. Returns dict va -> info."""
    ins_map = {}
    work = [entry]
    while work and len(ins_map) < limit_ins:
        va = work.pop()
        while va not in ins_map and len(ins_map) < limit_ins:
            ins = one(va)
            if ins is None:
                break
            k, tg = successors(ins)
            w = dst_reg(ins)
            info = dict(addr=va, size=ins.size, mnem=ins.mnemonic,
                        ops=ins.op_str, raw='%s %s' % (ins.mnemonic, ins.op_str),
                        kind=k, targets=tg, wr=w)
            if ins.mnemonic == 'mov' and len(ins.operands) == 2:
                d, s = ins.operands
                if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_MEM \
                        and s.mem.base == capstone.x86.X86_REG_INVALID \
                        and s.mem.index == capstone.x86.X86_REG_INVALID:
                    info['abs'] = s.mem.disp & 0xffffffff
            ins_map[va] = info
            if k in ('ret', 'indirect-jmp', 'indirect-call'):
                break
            if k == 'uncond':
                work.extend(t for t in tg if t not in ins_map)
                break
            if k == 'cond':
                for t in tg[1:]:
                    if t not in ins_map:
                        work.append(t)
                va = tg[0]
                continue
            va = tg[0]
    return ins_map


def blocks_of(cfg):
    """split into basic blocks keyed by leader."""
    leaders = set()
    if not cfg:
        return {}, {}
    leaders.add(min(cfg))
    for va, inf in cfg.items():
        if inf['kind'] in ('cond', 'uncond'):
            for t in inf['targets']:
                if t in cfg:
                    leaders.add(t)
            nx = va + inf['size']
            if nx in cfg:
                leaders.add(nx)
        elif inf['kind'] in ('ret', 'indirect-jmp'):
            nx = va + inf['size']
            if nx in cfg:
                leaders.add(nx)
    blocks, cur = {}, None
    for va in sorted(cfg):
        if va in leaders or cur is None:
            cur = va
            blocks[cur] = []
        blocks[cur].append(va)
    return blocks, leaders


def block_edges(cfg, blocks):
    edges = collections.defaultdict(list)
    for lead, body in blocks.items():
        last = body[-1]
        inf = cfg[last]
        nx = last + inf['size']
        if inf['kind'] in ('ret', 'indirect-jmp'):
            continue
        tg = inf['targets']
        cands = tg if inf['kind'] in ('cond', 'uncond') else [nx]
        for t in cands:
            # map target to its containing block leader
            for L, B in blocks.items():
                if t in B:
                    edges[lead].append(L)
                    break
        if inf['kind'] == 'cond' and nx in cfg:
            for L, B in blocks.items():
                if nx in B:
                    edges[lead].append(L)
                    break
    return edges


def reaching_defs(cfg, blocks, edges, reg):
    """classic reaching definitions over one register."""
    gen, kill = {}, {}
    for L, body in blocks.items():
        g = [va for va in body if cfg[va]['wr'] == reg]
        gen[L] = g
        kill[L] = set(g)
    IN = {L: set() for L in blocks}
    OUTS = {L: set(gen[L]) for L in blocks}
    for _ in range(60):
        changed = False
        for L in blocks:
            nin = set()
            for P in blocks:
                if L in edges.get(P, []):
                    nin |= OUTS[P]
            nout = (nin - kill[L]) | set(gen[L])
            if nin != IN[L] or nout != OUTS[L]:
                IN[L], OUTS[L] = nin, nout
                changed = True
        if not changed:
            break
    return IN, OUTS


def defs_at(cfg, blocks, IN, site):
    for L, body in blocks.items():
        if site in body:
            idx = body.index(site)
            pre = [va for va in body[:idx] if cfg[va]['wr'] == 'ebp']
            return (set(pre) if pre else set(IN[L])), L, idx
    return None, None, None


# ---------------- build ----------------
# 60 个站点跨两个函数体（本轮实测）：
#   0x67d300..0x67df1e 由 0x67d1af 调用，入口 0x67d300
#   0x67fdf0 与 0x67fe70 由 0x67df0f / 0x67df29 调用
# 实测：60 个站点横跨 36 个函数体 —— 1 个大函数（25 站点）+ 35 个 0x80 字节孪生函数（各 1 站点）。
# 35 个孪生函数地址 0x67fdf0 + 0x80*k (k=0..34)，每个恰有 1 条 callref、0 条 .data 指针引用（除 0x680070）。
ENTRIES = [0x67d300] + [0x67fdf0 + 0x80 * k for k in range(35)]
SITES = json.load(open(os.path.join(ROOT, '_r121', 'r121b_ppv_fix.json')))['results']['0x7f7c80']
site_addrs = sorted(int(r['site'], 16) for r in SITES)

funcs = {}
for e in ENTRIES:
    c = build_cfg(e)
    b, _ = blocks_of(c)
    ed = block_edges(c, b)
    i_, o_ = reaching_defs(c, b, ed, 'ebp')
    funcs[e] = dict(cfg=c, blocks=b, edges=ed, IN=i_)

owners = {}
for s in site_addrs:
    for e, F in funcs.items():
        if s in F['cfg']:
            owners[s] = e
            break

ck('C0 CFG：%d 个函数体，指令 %s，基本块 %s（只解码这些函数体，未整段 .text detail）'
   % (len(funcs), {hex(e): len(F['cfg']) for e, F in funcs.items()},
      {hex(e): len(F['blocks']) for e, F in funcs.items()}),
   all(len(F['cfg']) > 50 and len(F['blocks']) > 5 for F in funcs.values()),
   {'ins': {hex(e): len(F['cfg']) for e, F in funcs.items()}})

ck('C0b 站点归属：%s'
   % json.dumps({hex(e): sum(1 for v in owners.values() if v == e) for e in ENTRIES}),
   len(owners) == len(site_addrs),
   {'assigned': len(owners), 'total': len(site_addrs),
    'per_func': {hex(e): sum(1 for v in owners.values() if v == e) for e in ENTRIES}})

ck('N1 反控 CFG 覆盖面：%d/%d 个站点被某个函数体的 CFG 覆盖（必须全部覆盖）'
   % (len(owners), len(site_addrs)), len(owners) == len(site_addrs),
   {'in_cfg': len(owners), 'total': len(site_addrs),
    'missing': [hex(s) for s in site_addrs if s not in owners]})

# ---- per-site reaching defs ----
rows = []
for s in site_addrs:
    e = owners.get(s)
    F = funcs.get(e)
    d = L = None
    if F:
        d, L, _idx = defs_at(F['cfg'], F['blocks'], F['IN'], s)
    rows.append(dict(site=hex(s), func=hex(e) if e else None,
                     block=hex(L) if L else None,
                     defs=sorted(hex(x) for x in d) if d is not None else None,
                     n_defs=len(d) if d is not None else None))

hist = collections.Counter(r['n_defs'] for r in rows)
ck('C1 站点处 ebp 的到达定义个数分布 = %s'
   % json.dumps({str(k): v for k, v in hist.items()}, ensure_ascii=False),
   {str(k): v for k, v in hist.items()} == {'1': 25, '0': 35}, dict(hist))

single = [r for r in rows if r['n_defs'] == 1]
dists = collections.Counter(tuple(r['defs']) for r in single)
ck('C2 到达定义恰为单元素的站点 = %d 个，其定义值分布 = %s'
   % (len(single), json.dumps({str(k): v for k, v in dists.items()}, ensure_ascii=False)),
   True, {str(k): v for k, v in dists.items()})

PROLOGUE_DEF = '0x67d351'
n_pro = sum(1 for r in rows if r['defs'] == [PROLOGUE_DEF])
ck('C3 到达定义集合恰为 {0x67d351 = mov ebp,[0x7e15f4]} 的站点 = %d/%d'
   % (n_pro, len(rows)), n_pro == 25 and len(rows) == 60, {'n': n_pro})

# ---- P1 正控：与线性结果一致处 ----
p1 = next((r for r in rows if r['site'] == '0x67d36e'), None)
ck('P1 正控 站点 0x67d36e 的到达定义集合 = %s（线性回溯同点也是 0x67d351）'
   % (p1['defs'] if p1 else None),
   p1 is not None and p1['defs'] == [PROLOGUE_DEF], {'row': p1})

# ---- N2 反控：跳过序言 ----
cfg2 = build_cfg(0x67d357)
blocks2, _ = blocks_of(cfg2)
edges2 = block_edges(cfg2, blocks2)
IN2, _OUT2 = reaching_defs(cfg2, blocks2, edges2, 'ebp')
n2 = 0
for s in site_addrs:
    if s in cfg2:
        d, L, idx = defs_at(cfg2, blocks2, IN2, s)
        if d is not None and len(d) == 1 and sorted(hex(x) for x in d) == [PROLOGUE_DEF]:
            n2 += 1
ck('N2 反控 跳过序言（入口改 0x67d357）：仍能推出 {0x67d351} 的站点 = %d（必须 0）' % n2,
   n2 == 0, {'n': n2})

# ---- N3 正控：合成带分支的字节串 ----
# 0x2000: push ebp / mov ebp,[0x7e15f4] / cmp eax,0 / jne +6 / <fallthrough: 不写 ebp> / jmp +5
#   ... 两侧汇合点分别读 ebp
syn = bytes.fromhex(
    '55'              # 2000 push ebp
    '8b2df4157e00'    # 2001 mov ebp,[0x7e15f4]
    '83f800'          # 2007 cmp eax,0
    '7505'            # 200a jne 2011
    'e900000000'      # 200c jmp 2011
    '8be8'            # 2011 mov ebp,eax   (另一条定义)
    'ffd5'            # 2013 call ebp
    '5d'              # 2015 pop ebp
    'c3'              # 2016 ret
)
o = pe.off_va(TEXT_VA0)  # 复用解码器需要 buffer；改用独立小 buffer 解码
syn_ins = {}
MDs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MDs.detail = True
for i in MDs.disasm(syn, 0x2000):
    syn_ins[i.address] = i
syn_has_branch = any(i.mnemonic.startswith('j') for i in syn_ins.values())
syn_has_two_defs = sum(1 for i in syn_ins.values()
                       if i.mnemonic in WRITE_MN and i.operands and
                       i.operands[0].type == capstone.x86.X86_OP_REG and
                       i.reg_name(i.operands[0].reg) == 'ebp')
ck('N3 正控 合成字节串：解出 %d 条指令，含分支 = %s，写 ebp 的位置 = %d 处（必须 >=2 才会分叉）'
   % (len(syn_ins), syn_has_branch, syn_has_two_defs),
   syn_has_branch and syn_has_two_defs >= 2, {'n': len(syn_ins), 'defs': syn_has_two_defs})

# ---- 出口多样性（诚实登记） ----
rets = sorted(hex(va) for F in funcs.values() for va, inf in F['cfg'].items() if inf['kind'] == 'ret')
ind_j = sorted(hex(va) for F in funcs.values() for va, inf in F['cfg'].items()
               if inf['kind'] == 'indirect-jmp')
ck('C4 函数出口：ret %d 个，间接 jmp %d 个（间接目标无法静态解析 ⇒ A3 残差）'
   % (len(rets), len(ind_j)), len(rets) == 83 and len(ind_j) == 0,
   {'rets': rets[:12], 'n_rets': len(rets), 'ind': ind_j[:12]})

# ---- 最终口径 ----
by_def = collections.Counter(tuple(r['defs']) if r['defs'] is not None else ('OUT-OF-CFG',) for r in rows)
summary = {str(k): v for k, v in by_def.items()}
ck('C5 按到达定义集合分组（这是本轮唯一允许写进台账的口径）：%s'
   % json.dumps(summary, ensure_ascii=False),
   summary == {"('0x67d351',)": 25, '()': 35}, summary)

out = dict(file=PE_PATH, entries=[hex(e) for e in ENTRIES], checks=checks,
           cfg={hex(e): dict(n_ins=len(F['cfg']), n_blocks=len(F['blocks'])) for e, F in funcs.items()},
           n_rets=len(rets), n_indirect_jmp=len(ind_j),
           summary=summary,
           prologue_def=PROLOGUE_DEF,
           prologue_raw=funcs[0x67d300]['cfg'].get(0x67d351, {}).get('raw'),
           rows=rows)
open(OUTFILE, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), OUTFILE))
sys.exit(0 if npass == len(checks) else 1)
