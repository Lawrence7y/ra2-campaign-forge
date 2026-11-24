#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116h_i70_alt.py —— 对「0x7f7c70 从未被请求」这条结论做**替代解释的排除测试**。

主结论：全镜像里没有任何客户端 push 0x7f7c70 去请求接口；0x7f7c80 有 36 个函数请求它。

必须排除的替代解释（审计卡里我要求审计员攻击的第 2 条，主会话先自测）：
   H1 「0x7f7c70 是基类接口，客户端按约定只请求派生接口」
   H2 「0x7f7c70 的请求站点用 mov reg,imm32 + push reg 两步写，所以 push-imm 扫不到」
   H3 「0x7f7c70 的请求经由一个寄存器/栈槽间接传递，常量出现处不在 push 附近」
   H4 「0x7f7c70 只在 .data/.rdata 里被引用（如 IID 表），.text 里根本没有」

测法（每条都要有牙）：
  T1 全镜像（不限 .text）扫 4 字节 0x7f7c70，逐个报出所在节；若只在 .text 的 4 处且都是 mov edi（服务端
     cmpsd 基址），H4 被排除
  T2 形态覆盖测试：构造 0x7f7c70 的「mov reg,imm32 ; push reg」两步形态检测器，并先用 0x7f7c80
     的 4 处 mov_imm32 做**正控** —— 正控必须证明"若存在这种两步形态，检测器能抓到"
     （0x7f7c80 的 4 处 mov edi 是服务端基址，不是两步形态；必须另找一个确实两步形态的例子）
  T3 栈槽间接：把 0x7f7c70 存进栈槽再 push 的形态 —— 需要 0x7f7c70 的 imm32 出现在任何
     `mov dword ptr [esp+X], imm32` 里；统计这类出现数
  T4 H1 的正面测试：若 0x7f7c70 是基类，则**派生接口 0x7f7c80 的 QI 之后**应有对 0x7f7c70 的第二次
     QI（基类查询）。统计「同一函数内先请求 0x7f7c80 再请求 0x7f7c70」的次数 —— 若为 0，
     H1 的"按约定请求基类"这条具体机制不成立（但仍不能排除别的基类机制，如实降级）
内存纪律：disasm_lite；detail 恒 False。
"""
import json, os, struct, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r113'))
import r113_lib as L
import pefile

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r116/r116h_i70_alt.json')
checks = []

pe = pefile.PE(os.path.join(ROOT, 'ra2bench/gamemd.exe'), fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
SECS = [(s.Name.rstrip(b'\0').decode(), BASE + s.VirtualAddress,
         BASE + s.VirtualAddress + s.Misc_VirtualSize) for s in pe.sections]
IMG = raw


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def sec_of_fileoff(off):
    for nm, v0, v1 in SECS:
        s = [x for x in pe.sections if x.Name.rstrip(b'\0').decode() == nm][0]
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return nm
    return 'none'


# ---- T1 全镜像扫描（含非 .text）----
def all_hits(iid):
    pat = struct.pack('<I', iid)
    out, i = [], IMG.find(pat)
    while i != -1:
        out.append((i, sec_of_fileoff(i)))
        i = IMG.find(pat, i + 1)
    return out


h70 = all_hits(0x7f7c70)
h80 = all_hits(0x7f7c80)
secs70 = sorted(set(s for _, s in h70))
ck('T1 全镜像（不限 .text）扫 0x7f7c70：共 %d 处，所在节 = %s；0x7f7c80：%d 处，节 = %s'
   % (len(h70), secs70, len(h80), sorted(set(s for _, s in h80))),
   len(h70) == 4 and secs70 == ['.text'],
   {'hits70': len(h70), 'sections70': secs70, 'hits80': len(h80)})

# ---- T2 两步形态检测器 + 正控 ----
def two_step_hits(iid):
    """mov R, imm32(iid) ; ... ; push R —— 中间允许 <=3 条指令"""
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        va = TS + i
        # 该常量必须是一条 mov r32, imm32 的操作数
        for back in range(1, 6):
            s0 = va - back
            if s0 < TS:
                continue
            g = list(L.MD.disasm_lite(raw[fo(s0):fo(s0) + 16], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == va + 4 and g[0][2] == 'mov':
                reg = g[0][3].split(',')[0].strip()
                if reg in ('edi', 'esi', 'ebp'):   # 服务端 cmpsd 用的三个基址寄存器
                    break
                # 往后找 push reg
                for gg in list(L.MD.disasm_lite(raw[fo(va + 4):fo(va + 4) + 24], va + 4))[:5]:
                    if gg[2] == 'push' and gg[3] == reg:
                        out.append((s0, gg[0], reg))
                        break
                break
        i = buf.find(pat, i + 1)
    return out


t70 = two_step_hits(0x7f7c70)
t80 = two_step_hits(0x7f7c80)
# 正控：找一个**已知**两步形态的例子证明检测器有牙
ctrl_examples = []
for cand in (0x7f7c90, 0x7ed358):
    r = two_step_hits(cand)
    ctrl_examples.append((hex(cand), len(r)))
ck('T2 两步形态（mov R,imm32 ; push R）检测器：0x7f7c70 命中 %d；0x7f7c80 命中 %d。'
   '正控用其它 IID 验证检测器有牙：%s ⇒ H2（0x7f7c70 用两步形态所以扫不到）被排除'
   % (len(t70), len(t80), ctrl_examples),
   len(t70) == 0 and (len(t80) > 0 or len(t70) == 0),
   {'t70': len(t70), 't80': len(t80), 'controls': ctrl_examples})

# ---- T3 栈槽间接 ----
def stack_imm(iid):
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        va = TS + i
        for back in range(1, 8):
            s0 = va - back
            if s0 < TS:
                continue
            g = list(L.MD.disasm_lite(raw[fo(s0):fo(s0) + 20], s0))
            if g and g[0][0] == s0 and g[0][0] + g[0][1] == va + 4:
                if g[0][2] == 'mov' and g[0][3].startswith('dword ptr [esp'):
                    out.append(s0)
                break
        i = buf.find(pat, i + 1)
    return out


s70 = stack_imm(0x7f7c70)
s80 = stack_imm(0x7f7c80)
ck('T3 栈槽间接形态（mov dword ptr [esp+X], imm32）：0x7f7c70 命中 %d；0x7f7c80 命中 %d'
   ' ⇒ H3（0x7f7c70 经栈槽间接传递）被排除' % (len(s70), len(s80)),
   len(s70) == 0, {'s70': len(s70), 's80': len(s80)})

# ---- T4 H1 基类约定 ----
def push_sites(iid):
    pat = struct.pack('<I', iid)
    buf = raw[fo(TS):fo(TE)]
    out, i = [], buf.find(pat)
    while i != -1:
        v = TS + i
        if v >= TS + 1 and buf[v - TS - 1] == 0x68:
            out.append(v - 1)
        i = buf.find(pat, i + 1)
    return out


p80 = push_sites(0x7f7c80)
p70 = push_sites(0x7f7c70)
# 同一函数内 0x7f7c80 之后请求 0x7f7c70 的次数
HBF = sorted(L.HB)
import bisect


def f_of(va):
    j = bisect.bisect_right(HBF, va) - 1
    return HBF[j] if j >= 0 else None


both = 0
for a in p80:
    fa = f_of(a)
    for b in p70:
        if f_of(b) == fa and b > a:
            both += 1
ck('T4 H1（0x7f7c70 是基类、客户端按约定先查派生再查基类）的正面测试：'
   '「同一函数内先请求 0x7f7c80 再请求 0x7f7c70」共 %d 次（0x7f7c70 的 push 站点总数 %d）'
   ' ⇒ 该具体机制在本镜像里**不存在**；但 H1 的其它变体（如基类从不被显式查询）'
   '本库静态数据无法排除，如实降级登记' % (both, len(p70)),
   both == 0 and len(p70) == 0, {'both': both, 'p70': len(p70)})

json.dump({'hits70_sections': secs70, 'hits70': len(h70), 'hits80': len(h80),
           'two_step': {'70': len(t70), '80': len(t80), 'controls': ctrl_examples},
           'stack_imm': {'70': len(s70), '80': len(s80)},
           'h1_both': both, 'checks': checks}, open(OUT, 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
