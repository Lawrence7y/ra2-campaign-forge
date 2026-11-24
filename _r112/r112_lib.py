#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112_lib.py —— R112 共享底座：PE 节、RTTI（COL / CHD / BCD）、HB 函数边界、QI 体抽取。

设计要点（本轮唯一证据来源，四个脚本共用，避免各写一份判据）：
  1. HB 边界沿用 r109e/r111 同构造（ret 后仅 0x90/0xCC 填充、对齐到 4、落在指令起点）。
  2. RTTI 布局由 R110 的 COL.offset 分布 {0:942, 4:12} 反证已对上（不是手抄）：
       COL+0x04 = offset（vtable 在对象内的字节偏移）
       COL+0x10 = pCHD
       CHD+0x08 = numBaseClasses, CHD+0x0C = pBaseClassArray
       BCD+0x00 = pTypeDescriptor, BCD+0x08 = mdisp（该基类子对象在对象内的字节偏移）
  3. QI 体抽取：全局只建一次，缓存到 _r112/cache.pkl，三个脚本复用（否则每个脚本都要重扫 4 MB）。
"""
import json, os, pickle, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
CACHE = os.path.join(ROOT, '_r112/cache.pkl')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()
fo = lambda v: v - IB
u32 = lambda v: struct.unpack_from('<I', raw, fo(v))[0]
i32 = lambda v: struct.unpack_from('<i', raw, fo(v))[0]
in_img = lambda v: IB <= v <= IB + len(raw) - 4

# detail=False 全程；60 万个 QI 站点也只是 lite 解码
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = False; MD.skipdata = True
MDN = Cs(CS_ARCH_X86, CS_MODE_32); MDN.detail = False; MDN.skipdata = False


def build_hb():
    """全段线性扫描（64 KB 分块，disasm_lite）→ (指令起点列表, ret 列表, HB 集合)。"""
    starts, rets = [], []
    pos = TS
    while pos < TE:
        hi = min(pos + 65536, TE); last = pos
        for a, sz, m, o in MD.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
            if a >= hi: break
            last = a + sz; starts.append(a)
            if m.startswith('ret'): rets.append(a)
        if last <= pos: last = pos + 1
        pos = last
    SS = set(starts)

    def rsz(r):
        q = fo(r)
        while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
            q += 1
        return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)

    HB = set()
    for r in sorted(rets):
        q = r + rsz(r); n = 0
        while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
            q += 1; n += 1
        if n and q % 4 == 0 and q in SS:
            HB.add(q)
    return starts, sorted(HB)


def demangle_type(va):
    """MSVC 装饰名 .?AVHouseClass@@ → HouseClass。

    自错 S-01（本轮，由断言 A6 当场抓住）：上一稿用 s.rstrip('@')，把模板名自身的尾 @ 也剥了
    —— `?$DynamicVectorClass@PAUButtonFadeEffect@@` 被剥成 `...ButtonFadeEffect`，与
    symbols.json 的类名对不上 ⇒ 488 个类的「自身类 mdisp==0」判负。
    正确做法：只剥**一次** `@@` 终止符，中间与尾部的名字字符一律不动。
    """
    s = raw[fo(va) + 8:fo(va) + 8 + 200].split(b'\x00')[0].decode('ascii', 'replace')
    if len(s) > 3 and s[0] == '.' and s[1] == '?' and s[2] == 'A':
        s = s[3:]
        if s and s[0] in 'VUT':
            s = s[1:]
    if s.endswith('@@'):
        s = s[:-2]
    elif s.endswith('@'):
        s = s[:-1]
    return s


def rtti_of(vt):
    """vt → {'col','coloff','bases': {base_name: sorted set of mdisp}}；解析失败返回 None。"""
    if not in_img(vt - 4):
        return None
    col = u32(vt - 4)
    if not in_img(col) or not in_img(col + 0x14):
        return None
    coloff = u32(col + 4)
    chd = u32(col + 0x10)
    if not in_img(chd):
        return None
    nbc = u32(chd + 8); pbca = u32(chd + 0xc)
    if nbc < 1 or nbc > 96 or not in_img(pbca) or not in_img(pbca + 4 * nbc):
        return None
    bases = {}
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        if not in_img(bcd) or not in_img(bcd + 0x1c):
            return None
        ptd = u32(bcd)
        if not in_img(ptd):
            return None
        nm = demangle_type(ptd)
        if not nm or not all(32 <= ord(c) < 127 for c in nm):
            return None
        bases.setdefault(nm, set()).add(i32(bcd + 8))
    return {'col': col, 'coloff': coloff, 'chd': chd, 'nbc': nbc,
            'bases': {k: sorted(v) for k, v in bases.items()}}


def load_symbols():
    sym = json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))['classes']
    VT = {}
    for k, c in sym.items():
        va = c.get('vtable_va')
        if va:
            VT[int(va, 16)] = k
    return sym, VT


def build_cache():
    starts, HB = build_hb()
    sym, VT = load_symbols()
    RTTI = {}
    for vt in VT:
        r = rtti_of(vt)
        if r: RTTI[vt] = r
    d = {'starts': sorted(starts), 'HB': sorted(HB), 'RTTI': RTTI,
         'VTs': sorted(VT), 'sha': EXE_SHA}
    pickle.dump(d, open(CACHE, 'wb'), protocol=4)
    return d


def cache():
    if not os.path.exists(CACHE):
        return build_cache()
    d = pickle.load(open(CACHE, 'rb'))
    if d.get('sha') != EXE_SHA:
        return build_cache()
    return d
