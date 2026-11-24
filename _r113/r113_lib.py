#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113_lib.py —— R113 共享底座：全镜像 COL/vtable 普查 + 指令级函数体 + QI 闭包。

与 R112 的差别（这是本轮唯一的判据新增，必须记住）：
  1. R112 的「子对象 vtable」是从 .text 的 `mov [reg+disp], <imm32>` 装配点反推的，
     只能看到**被装配过的** vtable（2517 个点、去重后覆盖不全）。
     本轮改用 .rdata 侧的全量普查：扫所有 dword，若其值 v 满足「v-4 处是合法 COL」，
     则 v 是一个 vtable 起点（COL 紧贴在 vtable 之前 4 字节，这是 MSVC 的固定布局）。
     实测 1214 个，其中 954 个与 symbols.json 完全重合、260 个是 symbols.json 没有的
     二级/虚拟基子对象 vtable。**这 260 个不是猜的：它们的 CHD 与主 vtable 的 CHD 相同。**
  2. 槽数（方法表长度）有三把尺子，本轮全部实测：
       T 尺 = 从 vtable 起连续落在 .text 的 dword 个数（R112 用的，会越界到常量池）
       B 尺 = 「下一个 COL 指针所在地址」减去 vtable 起点（结构上界，不依赖 .text）
       E 尺 = 连续「像函数入口」的 dword 个数（在指令起点集内 且 入口前有填充）
     三者的关系是 R113 的一个断言（B 尺必须 >= T 尺，否则说明 COL 普查漏了东西）。
  3. QI 闭包：R111/R112 的认领类集合只数**本类 slot0 体内**的 cmpsd，
     漏掉两类真实形态：
       (a) adjustor thunk：slot0 = `sub dword ptr [esp+4],N ; jmp T`，真 QI 在 T
       (b) 委托：slot0 体内 `call <另一类的 QI 入口>`，命中第二个 IID 才继续
     本轮对 jmp 目标与 call 目标都下钻（只在 HB 函数入口处下钻，浅递归、去环），
     得到**闭包认领集**，并用它做 FULL 集判定。
内存纪律：disasm_lite + 64 KB 分块，detail 恒 False；函数体一律 HB 定界 + 2000 B 上限。
"""
import json, os, pickle, re, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L   # 复用 R112 的 PE/RTTI/HB 底座（同一 sha 已断言）

raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
IB, TS, TE = L.IB, L.TS, L.TE
in_img = L.in_img
MD = L.MDN
HB = set(L.cache()['HB'])
STARTS = set(L.cache()['starts'])
RTTI = L.cache()['RTTI']

RD0, RD1 = 0x7e1000, 0x811074          # .rdata 区间（pefile 实测，R113 a 会重新断言）
TEXT0, TEXT1 = TS, TE

CENSUS = os.path.join(ROOT, '_r113/census.pkl')
CLOSURE = os.path.join(ROOT, '_r113/closure.pkl')


def is_td(v):
    """v 处是不是一个 TypeDescriptor（MSVC 装饰名以 .?AU/.?AV/.?AV/.?T 开头）。"""
    return in_img(v) and raw[fo(v) + 8:fo(v) + 11] in (b'.?A', b'.?U', b'.?V', b'.?T')


def valid_col(a):
    """a 处是不是一个合法 COL：sig==0、pTD 合法、pCHD 合法、BCD 数组全部合法。"""
    if not in_img(a) or not in_img(a + 0x14):
        return False
    if u32(a) != 0:
        return False
    if not is_td(u32(a + 0xc)):
        return False
    chd = u32(a + 0x10)
    if not in_img(chd) or not in_img(chd + 0x10):
        return False
    nbc = u32(chd + 8)
    pbca = u32(chd + 0xc)
    if not (1 <= nbc <= 96) or not in_img(pbca) or not in_img(pbca + 4 * nbc - 4):
        return False
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        if not in_img(bcd) or not in_img(bcd + 0x1c) or not is_td(u32(bcd)):
            return False
    return True


def col_census():
    return set(a for a in range(RD0, RD1 - 0x18, 4) if valid_col(a))


def vtable_census():
    """返回 {vtable_va: col_va}：全 .rdata 里所有「前一 dword 是合法 COL」的槽位。"""
    cols = col_census()
    out = {}
    for x in range(RD0, RD1 - 4, 4):
        d = u32(x)
        if d in cols and TEXT0 <= u32(x + 4) < TEXT1:
            out[x + 4] = d
    return out, cols


def textrun(v, cap=4000):
    n = 0
    while n < cap and TEXT0 <= u32(v + 4 * n) < TEXT1:
        n += 1
    return n


def _pad_before(a):
    q = fo(a) - 1
    for _ in range(3):
        if raw[q] in (0x90, 0xcc, 0x00):
            return True
        q -= 1
    return False


def entrylike(a):
    return TEXT0 <= a < TEXT1 and a in STARTS and (a in HB or _pad_before(a))


def entryrun(v, cap=4000):
    n = 0
    while n < cap and entrylike(u32(v + 4 * n)):
        n += 1
    return n


def boundary_run(v, colptr_sorted):
    """B 尺：下一个 COL 指针与 vtable 起点之间的 dword 数（结构上界）。"""
    p = v - 4
    i = colptr_sorted.index(p) if p in colptr_sorted else None
    if i is None:
        raise KeyError(hex(p))
    nxt = colptr_sorted[i + 1] if i + 1 < len(colptr_sorted) else RD1
    return (nxt - v) // 4, nxt


def build_census():
    V2C, cols = vtable_census()
    colptr = sorted(v - 4 for v in V2C)
    d = {'V2C': V2C, 'colptr': colptr, 'cols': sorted(cols), 'sha': L.EXE_SHA,
         'T': {v: textrun(v) for v in V2C},
         'E': {v: entryrun(v) for v in V2C},
         'B': {v: boundary_run(v, colptr)[0] for v in V2C}}
    pickle.dump(d, open(CENSUS, 'wb'), protocol=4)
    return d


def census():
    if not os.path.exists(CENSUS):
        return build_census()
    d = pickle.load(open(CENSUS, 'rb'))
    if d.get('sha') != L.EXE_SHA or len(d.get('V2C', {})) == 0:
        return build_census()
    return d


# ---------------- 指令级函数体 / QI 闭包 ----------------
RE_IMM = re.compile(r'^(e[a-z]{2}), (0x[0-9a-f]+)$')
RE_TGT = re.compile(r'^(0x[0-9a-f]+)$')
RE_SUB = re.compile(r'^dword ptr \[esp \+ 4\], (0x[0-9a-f]+|\d+)$')


def body(f, win=2000, cap=1600):
    """HB 定界的函数体（R111 §EM8 L-04：裸窗口会溢出到下一函数，禁止）。"""
    out = []
    for g in MD.disasm_lite(raw[fo(f):fo(f) + win + 16], f):
        if len(out) >= cap:
            break
        if g[0] != f and g[0] in HB:
            break
        out.append(g)
    return out


def direct_iids(lits):
    """本函数体内的 cmpsd IID 立即数（按出现顺序，去重保序）。"""
    out, iid = [], None
    for a, sz, m, o in lits:
        if m == 'mov':
            mm = RE_IMM.match(o)
            if mm and mm.group(1) == 'edi':
                iid = int(mm.group(2), 16)
        elif 'cmpsd' in m:
            if iid is not None:
                out.append(iid)
                iid = None
    return out


def edges(lits):
    """从函数体抽出两类跨函数边：(thunk jmp 目标, call 目标)。
    只认落在 .text 且是 HB 函数入口的目标，避免钻进函数中部造成假闭包。"""
    jmps, calls = [], []
    for i, (a, sz, m, o) in enumerate(lits):
        if m in ('jmp', 'call'):
            mm = RE_TGT.match(o)
            if not mm:
                continue
            t = int(mm.group(1), 16)
            if not (TEXT0 <= t < TEXT1) or t not in HB:
                continue
            # thunk 形态：函数头 <=3 条内出现 `sub dword ptr [esp+4], N` 后的 jmp
            prev = [x[2] + ' ' + x[3] for x in lits[max(0, i - 3):i]]
            is_thunk = (m == 'jmp') and any(p.startswith('sub dword ptr [esp + 4],') for p in prev)
            (jmps if is_thunk else calls).append(t)
    return jmps, calls


def closure_iids(entry, depth=2):
    """QI 闭包：本体内 cmpsd + thunk jmp 目标 + （浅层）call 委托目标。"""
    seen, out = set(), set()

    def go(f, d):
        if f in seen or len(seen) > 64:
            return
        seen.add(f)
        lits = body(f)
        for i in direct_iids(lits):
            out.add(i)
        jmps, calls = edges(lits)
        for t in jmps:
            go(t, d)                 # thunk 不消耗深度：它是同一实现的入口搬运
        if d > 0:
            for t in calls:
                go(t, d - 1)
    go(entry, depth)
    return out


def iid_guid(va):
    d1 = u32(va); d2 = u32(va + 4) & 0xffff; d3 = u32(va + 4) >> 16
    b = raw[fo(va) + 8:fo(va) + 16]
    return '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, b[:2].hex().upper(), b[2:].hex().upper())
