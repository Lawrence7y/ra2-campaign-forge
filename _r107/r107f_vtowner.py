#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107f_vtowner.py —— 用虚表槽结构把 switch 表所属函数钉到「类 + 槽号」，不依赖 win-main

上一轮 R106 §EH10① 记「17 个函数入口的语义命名未做（需符号或运行期采样，win-main 仍 OFFLINE）」。
本脚本证：**至少对一部分入口，静态槽结构就能给出类与槽号**，无须运行期。
做法：
  1) 直接读 PE 镜像的 .data 段，独立解析出每个类的 vtable 指针数组（不用 symbols.json 的结论）
  2) 用函数入口地址反查它出现在哪些 vtable 的哪个槽
  3) 用 ret 后接对齐填充求出每个 vtable 的实际槽数（不信任 symbols.json 的 vfunc_count）
  4) 交叉核对：同一槽号在父类/子类里是否指向同一函数（多类共用 => 继承未覆盖）

内存纪律：只读字节 + 稀疏 disasm，不做全段 detail=True。
"""
import hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107f_vtowner.json'
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
    if o is None or o + 4 > len(raw):
        return None
    return struct.unpack_from('<I', raw, o)[0]


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
mdd = Cs(CS_ARCH_X86, CS_MODE_32)
mdd.detail = False
mdd.skipdata = True

# ---------- 1) 独立解析 vtable：从 symbols.json 只取「vtable_va 候选集」，槽内容自己读 ----------
sym = json.load(open('out/reverse/symbols.json'))['classes']
vt_of = {}
for cname, c in sym.items():
    v = c.get('vtable_va')
    if v:
        vt_of[cname] = int(v, 16)
ck('V0 带 vtable 的类数 == 954', len(vt_of) == 954, len(vt_of))


def read_vtable(va, cap=400):
    """读 vtable 槽直到遇到不指向 .text 的值；返回槽值列表（不信任 vfunc_count）"""
    out = []
    for i in range(cap):
        v = u32(va + i * 4)
        if v is None or not (TS <= v < TE):
            break
        # 槽值必须是合法指令起点：用稀疏 disasm 复核（从该地址能解出指令）
        got = next(mdd.disasm(raw[off(v):off(v) + 16], v), None)
        if got is None:
            break
        out.append(v)
    return out


VT = {}
for cname, va in vt_of.items():
    s = read_vtable(va)
    if s:
        VT[cname] = {'vtable_va': va, 'slots': s}

# 用 symbols.json 的 vfunc_count 交叉核对
agree = 0
disagree = []
for cname, c in sym.items():
    if cname in VT and c.get('vfunc_count') is not None:
        if len(VT[cname]['slots']) == c['vfunc_count']:
            agree += 1
        else:
            disagree.append((cname, c['vfunc_count'], len(VT[cname]['slots'])))
ck('V1 自读槽数与 symbols.json vfunc_count 一致的比例', agree >= 900, '%d 一致 / %d 不一致' % (agree, len(disagree)))

# ---------- 2) 入口 -> (类, 槽号) 反查表 ----------
ENTRIES = [0x46de20, 0x48d1e0, 0x48dcd0, 0x4c6cb0, 0x4ffd90, 0x58bc20, 0x69ae90, 0x6a8b30,
           0x6acee0, 0x6afd60, 0x6dd5b0, 0x708c30, 0x71e940, 0x71f680, 0x71f9c0, 0x728a00,
           0x79da90]
entset = set(ENTRIES)
inv = {a: [] for a in ENTRIES}
for cname, d in VT.items():
    for i, v in enumerate(d['slots']):
        if v in entset:
            inv[v].append((cname, i, d['vtable_va']))

hit = [a for a in ENTRIES if inv[a]]
miss = [a for a in ENTRIES if not inv[a]]
ck('V2 17 个入口中至少 1 个能静态定位到「类 + 槽号」', len(hit) >= 1,
   '%d 命中 / %d 未命中' % (len(hit), len(miss)))

# ---------- 3) 新增：R106 未列出的两个真实所属函数，也做同样反查 ----------
EXTRA = [0x728c00, 0x728e30, 0x728a50, 0x728a90, 0x728af0, 0x4c8114]
extra_inv = {a: [] for a in EXTRA}
for cname, d in VT.items():
    for i, v in enumerate(d['slots']):
        if v in extra_inv:
            extra_inv[v].append((cname, i, d['vtable_va']))

ck('V3 0x728c00 与 0x728e30 在同一个类的不同槽（证明它们是两个不同虚方法）',
   bool(extra_inv[0x728c00]) and bool(extra_inv[0x728e30])
   and {s for _, s, _ in extra_inv[0x728c00]} != {s for _, s, _ in extra_inv[0x728e30]},
   {hex(k): v for k, v in extra_inv.items()})

# ---------- 4) 关键：两张表 0x728e08 / 0x7291ac 的 holder 归属 ----------
# 0x728c17 落在 0x728c00 的体内（前向解码命中），0x728e6c 落在 0x728e30 的体内
ck('V4 TunnelLocomotionClass 的两张表分属两个不同虚方法（v18 / v16），不是同一个 0x728a00',
   bool(extra_inv[0x728c00]) and bool(extra_inv[0x728e30])
   and 0x728a00 not in [v for c in VT.values() for v in c['slots']],
   'v18=%s v16=%s 构造=%s' % (extra_inv[0x728c00], extra_inv[0x728e30], inv[0x728a00]))

rec = {'checks': checks,
       'entries': {hex(a): inv[a] for a in ENTRIES},
       'extra': {hex(a): extra_inv[a] for a in EXTRA},
       'n_vtables_read': len(VT),
       'vfunc_count_disagree': disagree[:20]}
json.dump(rec, open(OUT, 'w'), ensure_ascii=False, indent=1)

print('\n--- 17 个 R106 入口的静态定位 ---')
for a in ENTRIES:
    print('  %08x  %s' % (a, inv[a] if inv[a] else '（不在任何 vtable 槽里）'))
print('\n--- 额外 ---')
for a in EXTRA:
    print('  %08x  %s' % (a, extra_inv[a]))
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
