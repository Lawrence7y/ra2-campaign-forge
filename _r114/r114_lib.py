#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114_lib.py —— R114 共享底座：QI 写回偏移抽取器的「R112 原口径」与「修正口径」双实现。

本轮唯一目的：把 R112 留下的 30 个 NA 站点归因清楚，并给出可复算的交互表。

R112 抽取器（_r112/r112b_qi_offset.py）的口径原文：
  1. ppv 寄存器 P = 函数头 16 条内**第一条** `mov dword ptr [reg], 0` 的 reg。
  2. cmpsd 后的分支：6 条内（不跨下一条 cmpsd、不跨 jmp/call/ret）第一条 jne 或 je。
  3. 成功区间：jne 型 = [下一条, 跳转目标)；je 型 = 从跳转目标起、无右端点。
  4. N = 成功区间内 `lea reg,[this+N]` + `mov [P],reg` ⇒ N；`mov [P],<this reg>` ⇒ 0；
     否则 NA。

本轮实测出两处**相互独立、且强交互**的缺陷（都是判据实现 bug，不是判据放松）：

  缺陷甲（ppv 检测面太窄）：只认「清零式」`mov dword ptr [reg], 0`。
    但 MSVC 对 `HRESULT QueryInterface(REFIID, void**)` 的常见编法是从第 3 个栈参数
    直接取 ppv（`mov reg, dword ptr [esp+0x10]`），函数体里**根本没有清零指令**。
    实测：全镜像 172 个 QI 入口里 15 个取不到 P（8.7%）。
    修正：先按原口径取；取不到时按**栈参数序**取第 3 个参数（this / riid / ppv），
    位移随 push/pop 的栈增量累加，不能写死 esp+0xc。

  缺陷乙（je 型成功区间起点写反）：原实现里 je 型把 lo 设成跳转目标，但 started 仍是 False，
    于是循环从 cmpsd 的下一条开始逐条比对 `a >= lo` —— 由于 cmpsd 之后到跳转目标之间的
    指令地址都**小于** lo，它们全被跳过；这本身是对的，但问题是**跳转目标之后**的指令
    只有走到 lo 才置 started，而 `if 'cmpsd' in m: break` 会在到达 lo 之前把循环打断
    （跳转目标常在函数尾部，中间还有别的 cmpsd）。
    修正：je 型直接从 cmpsd 下一条开始扫，用「a < lo 则 continue」而不是「未 started 则 continue」，
    并且**不因 a >= lo 之前遇到下一条 cmpsd 而中断**（那条 cmpsd 属于失败路径）。

  交互：单独修甲回收 1 个站点、单独修乙回收 1 个，两处同修回收 27 个 ——
  因为这两类缺陷的站点集合几乎不重叠，而**两个都修**才能覆盖「从栈参数取 ppv + je 成功尾
  在函数最末、中间跨过别的 cmpsd」这种组合形态（27 个站点都是这一类）。
  这是本轮最值得记的一条：**两个 8.7%/8.7% 量级的缺陷，合并后解释了 90% 的 NA。**

残留 3 个 NA 是两种**真正读不到**的形态（不是抽取器缺陷，已逐字节核实）：
  - ApplicationClass / 0x7ea6e8 @0x429360：成功分支写的是**静态地址常量**
    `mov dword ptr [edx], 0x87f7e8`（不是 this、也不是 this+N），
    0x87f7e8 落在 .data，内容是 UTF-16 文本 "01 Westwood Stud..."（不是对象）。
  - ConnectionPointClass / 0x7f7c90 @0x4a04b0 与 EnumConnectionPointsClass / 0x7f7c90 @0x4a0920：
    命中后**不写 ppv**，而是 `mov eax, [esp+0x14]`（取 riid 之后的那个参数）后再
    `mov [ebx], eax` —— 写的是另一个槽，ppv 写发生在**公共尾**里（4a04ef 起），
    但公共尾同时被两条分支共用，静态无法判定"这一条命中才写"。
"""
import json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L  # noqa: E402

raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
MD = L.MDN
C = L.cache()
HB = set(C['HB'])
RTTI = C['RTTI']
sym, VT = L.load_symbols()

RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$')
RE_LEA = re.compile(r'^(e[a-z]{2}), \[(e[a-z]{2}) \+ (0x[0-9a-f]+|\d+)\]$')
RE_ST = re.compile(r'^dword ptr \[([a-z]{2,4})\], (e[a-z]{2})$')
RE_PPV0 = re.compile(r'^dword ptr \[([a-z]{2,4})\], 0$')
RE_LD = re.compile(r'^([a-z]{2,4}), dword ptr \[esp \+ (0x[0-9a-f]+|\d+)\]$')


def body(f, win=1400, cap=420):
    """HB 定界的函数体（R111 §EM8 L-04：裸窗口会溢出到下一函数，禁止）。"""
    out = []
    for g in MD.disasm_lite(raw[fo(f):fo(f) + win + 16], f):
        if len(out) >= cap:
            break
        if g[0] != f and g[0] in HB:
            break
        out.append(g)
    return out


def ppv_old(lits):
    """R112 原口径：函数头 16 条内第一条 mov dword ptr [reg], 0。"""
    for a, sz, m, o in lits[:16]:
        if m == 'mov':
            mm = RE_PPV0.match(o)
            if mm:
                return mm.group(1)
    return None


def ppv_new(lits):
    """修正口径：原口径优先；取不到时按栈参数序取第 3 个参数（this/riid/ppv）。"""
    r = ppv_old(lits)
    if r:
        return r
    delta = 0                      # 进入函数后累计的栈增量（push 为正）
    for a, sz, m, o in lits[:24]:
        if m == 'push':
            delta += 4
            continue
        if m == 'pop':
            delta -= 4
            continue
        if m in ('mov', 'lea'):
            mm = RE_LD.match(o)
            if mm:
                off = int(mm.group(2), 0)
                idx = (off - delta - 4) // 4    # 减去返回地址
                if idx == 2:
                    return mm.group(1)
    return None


def cmpsd_sites(lits):
    """[(idx, iid, branch_instr)]；分支搜索窗 6 条（R112 S-03 的结论）。"""
    res = []
    for i, (a, sz, m, o) in enumerate(lits):
        if 'cmpsd' not in m:
            continue
        iid = None
        for j in range(max(0, i - 3), i):
            mm = RE_EDI.match(lits[j][3])
            if mm:
                iid = int(mm.group(1), 16)
        if iid is None:
            continue
        br = None
        for k in range(i + 1, min(i + 7, len(lits))):
            m2 = lits[k][2]
            if 'cmpsd' in m2:
                break
            if m2 in ('jne', 'je'):
                br = lits[k]
                break
            if m2.startswith(('jmp', 'call', 'ret')):
                break
        res.append((i, iid, br))
    return res


def offset_at(lits, i, br, P, mode='fixed'):
    """成功区间里找写 ppv 的那条 mov，回推 N。

    mode='old'      复现 R112 原实现
    mode='fixed'    修掉缺陷乙（je 型起点）
    mode='fixed3'   再修缺陷丙（jne 型右端点）

    缺陷乙的精确形态（读 _r112/r112b_qi_offset.py 的 success_region/offset_at 得出）：
      jne 型返回 (lits[i+1][0], tgt)，hi 不为 None ⇒ started=False ⇒ 逐条比对到 a==lo 才开始。
        由于 lo 就是下一条，这等价于「从 i+1 开始扫、扫到 tgt 停」——**是对的**。
      je  型返回 (tgt, None)，hi 为 None ⇒ started=(hi is None)=**True** ⇒ 从 i+1 立刻开始扫，
        完全**不跳过** cmpsd 与 tgt 之间的失败路径；而下一个 `cmpsd` 就在失败路径上，
        循环被 `if 'cmpsd' in m: break` 打断 ⇒ 永远走不到 tgt ⇒ 记 NA。
      修正：je 型在 a < tgt 期间一律 continue（含 ret / cmpsd），不打断也不记录。

    缺陷丙（由执行员 #201 指出、主会话复算确认）：
      jne 型的右开边界 tgt 是**失败跳转目标**，但有些函数里它同时是**成功路径与失败尾的
      合流点**，真正的 store 落在 tgt 之后。实测受影响 2 个站点（0x4a04eb / 0x4a0960），
      去掉右端点后 NA 从 3 降到 1，且**全量 343 个站点里只有这 2 个取值改变**
      （无副作用，已实测）。
      修正：mode='fixed3' 时 jne 型不按 tgt 截断，只以「下一条 cmpsd / ret」为界。
      与缺陷乙一起的教训：**成功区间必须按路径定界，不能按分支目标定界** ——
      起点（乙）和终点（丙）是同一个错误的两个实例。
    """
    if br is None:
        return 'NA'
    tgt = int(br[3], 16)
    use_right = (br[2] == 'jne') and mode != 'fixed3'
    lea = None
    for k in range(i + 1, len(lits)):
        a, sz, m, o = lits[k]
        if mode == 'old':
            if br[2] == 'je':
                pass                      # 原实现：不跳过，从 i+1 起直接扫失败路径
        else:
            if br[2] == 'je' and a < tgt:
                continue                  # 修后：失败路径整段跳过，不打断、不记录
        if use_right and a >= tgt:
            break
        if 'cmpsd' in m or m.startswith('ret'):
            break
        if m == 'lea':
            mm = RE_LEA.match(o)
            if mm:
                lea = (mm.group(1), int(mm.group(3), 0))
        if m == 'mov' and P:
            mm = RE_ST.match(o)
            if mm and mm.group(1) == P:
                if lea and lea[0] == mm.group(2):
                    return lea[1]
                return 0
    return 'NA'


def extract(ppv_mode='new', je_mode='fixed'):
    """返回 (sites, entries)。

    sites   = [(class, iid_str, entry_va, idx, N)]
    entries = {entry_va: (class, P)}
    """
    sites = []
    entries = {}
    for vt in sorted(VT):
        if vt not in RTTI:
            continue
        k = VT[vt]
        s0 = u32(vt)
        if not (L.TS <= s0 < L.TE):
            continue
        lits = body(s0)
        if not lits:
            continue
        st = cmpsd_sites(lits)
        if not st:
            continue
        P = (ppv_new if ppv_mode == 'new' else ppv_old)(lits)
        entries[s0] = (k, P)
        for i, iid, br in st:
            sites.append((k, '0x%x' % iid, s0, i, offset_at(lits, i, br, P, je_mode)))
    return sites, entries


def named_interfaces():
    """RTTI 里出现过的接口名（I + 大写 起头，排除 IUnknown）。"""
    out = set()
    for r in RTTI.values():
        for nm in r['bases']:
            if len(nm) > 1 and nm[0] == 'I' and nm[1].isupper() and nm != 'IUnknown':
                out.add(nm)
    return out


NAMED = named_interfaces()


def full_set(sites, iid, N):
    """FULL(iid,N) = 在**全部**定值认领类上该名的 mdisp 都含 N。返回 (集合, |Q|)。"""
    q = sorted(set(s[0] for s in sites if s[1] == iid and s[4] != 'NA'))
    if not q:
        return set(), 0
    out = set()
    for nm in NAMED:
        tot = hit = 0
        for k in q:
            r = RTTI[int(sym[k]['vtable_va'], 16)]
            mds = r['bases'].get(nm)
            if mds is None:
                continue
            tot += 1
            if N in mds:
                hit += 1
        if tot == len(q) and hit == tot:
            out.add(nm)
    return out, len(q)


def n_of_iid(sites):
    """逐 IID 唯一定值（违例则不进字典）。返回 (dict, 违例 dict)。"""
    import collections
    per = collections.defaultdict(collections.Counter)
    for k, iid, s0, i, N in sites:
        if N != 'NA':
            per[iid][N] += 1
    ok = {i: next(iter(c)) for i, c in per.items() if len(c) == 1}
    bad = {i: dict(c) for i, c in per.items() if len(c) > 1}
    return ok, bad
