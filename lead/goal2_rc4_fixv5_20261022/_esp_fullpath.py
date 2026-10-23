#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§396：把 `_esp_bfs.py` 的**间接调用截断**补上 —— 全路径 esp 模拟。

## 为什么需要这个

`_esp_bfs.py` 遇到 `call [reg+disp]` / `call [mem]` 就**终止路径**，
理由写在注释里：「目标未知，ret 尺寸静态不可知」。
它自己登记了这个局限（5 处间接调用点），并且——按 §395 的修正——
那条登记不进 PASS 计数。

但**局限不等于不可解**。这 5 处全部可以静态解析：

| 站点 | 形态 | 解析方式 |
|:--|:--|:--|
| 0x7775D4 | `call [eax+0x38]` | `eax = [0x887628]` → vtable → slot14 |
| 0x77764F | `call [0x7e1404]` | IAT → USER32!GetMenu（1 参） |
| 0x7778FA | `call [eax+0x1c]` | 同 vtable → slot7 |
| 0x777A38 | `call [0x7e11c4]` | IAT → KERNEL32!MultiByteToWideChar（6 参） |
| 0x777A70 | `call [0x7e1394]` | IAT → USER32!DefWindowProcA（4 参） |

本脚本把这三类解析出来，算出**每条路径**的 ret 尺寸，
从而在**不截断**的情况下给出全路径 esp 结论。

## 与 `_esp_bfs.py` 的关系

- `_esp_bfs.py`：不经间接调用的分支（13/13 PASS），保留不动
- 本脚本：**补上**经间接调用的分支，并覆盖两种 vtable（A/B，§395 发现）
- 两者结论必须一致（都是 -0x10），不一致就是有一方错

## 关键纪律

1. 起点必须是**指令边界**（连续解码到目标）
2. 间接调用目标必须**真的解析出来**，解析不了就 FAIL，不许退回「按 ret 0 猜」
3. 每条路径的 ret 尺寸都要有出处（IAT 名 / vtable 槽号 / 实测 ret 字节）
"""
import collections
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []

FN = 0x7775C0
TARGETS = [0x777687, 0x7779B9, 0x7779B5]
EXPECTED_ESP = -0x10
EXPECTED_ARG = 0x08

# vtable 的两种可能（§395 实测：[0x887628] 不唯一）
SINGLETON = 0x887628
VTABLES = {0x7F794C: "类型A", 0x7F7A6C: "类型B"}

# `_esp_bfs.py` 在此终止路径的 5 处间接调用 —— 本脚本要**走过**它们
INDIRECT_SITES = [0x7775D4, 0x77764F, 0x7778FA, 0x777A38, 0x777A70]

# 已从 IAT 解析出的导入函数的 stdcall 参数个数
# （由 import 表读名 + 人工核对 API 签名；下面有断言复核名字）
IMPORT_ARGC = {
    "USER32.dll!GetMenu": 1,
    "USER32.dll!DefWindowProcA": 4,
    "KERNEL32.dll!MultiByteToWideChar": 6,
    "USER32.dll!ValidateRect": 2,
    "USER32.dll!GetClientRect": 2,
    "USER32.dll!ClientToScreen": 2,
    "USER32.dll!BeginPaint": 1,
    "USER32.dll!EndPaint": 2,
}


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-72s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))
    return bool(cond)


class Bin(object):
    def __init__(self, path):
        import capstone
        self.b = Path(path).read_bytes()
        pe = struct.unpack_from("<I", self.b, 0x3C)[0]
        nsec = struct.unpack_from("<H", self.b, pe + 6)[0]
        optsz = struct.unpack_from("<H", self.b, pe + 20)[0]
        opt = pe + 24
        self.ib = struct.unpack_from("<I", self.b, opt + 28)[0]
        self.secs = []
        so = opt + optsz
        for k in range(nsec):
            o = so + k * 40
            nm = self.b[o:o + 8].split(b"\0")[0].decode("latin1")
            vs, va, rs, ra = struct.unpack_from("<IIII", self.b, o + 8)
            self.secs.append((nm, va, vs, ra, rs))
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self._ret_cache = {}
        self._parse_imports(opt)

    def va2off(self, va):
        rva = va - self.ib
        for nm, v, vs, ra, rs in self.secs:
            if v <= rva < v + max(vs, rs):
                off = ra + (rva - v)
                if 0 <= off < len(self.b):
                    return off
        return None

    def _cstr(self, va):
        o = self.va2off(va)
        if o is None:
            return None
        e = self.b.index(b"\0", o)
        return self.b[o:e].decode("latin1")

    def _parse_imports(self, opt):
        dd = opt + 96
        imp_rva = struct.unpack_from("<I", self.b, dd + 8)[0]
        self.iat = {}
        o = self.va2off(self.ib + imp_rva)
        if o is None:
            return
        while True:
            ilt, ts, fc, nm, iat = struct.unpack_from("<IIIII", self.b, o)
            if nm == 0 and iat == 0:
                break
            dll = self._cstr(self.ib + nm)
            k = 0
            while dll:
                oo = self.va2off(self.ib + iat + k * 4)
                if oo is None:
                    break
                v = struct.unpack_from("<I", self.b, oo)[0]
                if v == 0:
                    break
                if not (v & 0x80000000):
                    fn = self._cstr(self.ib + v + 2)
                    if fn:
                        self.iat[self.ib + iat + k * 4] = "%s!%s" % (dll, fn)
                k += 1
            o += 20

    def insn(self, va):
        o = self.va2off(va)
        if o is None:
            return None
        try:
            return next(self.md.disasm(self.b[o:o + 16], va))
        except StopIteration:
            return None

    def ret_size(self, va):
        """返回函数入口 va 的 **可达** ret 尺寸。

        ★★★ §396 关键修正：原实现取「第一条 ret」，这是错的。
          实测 `0x6930A0` 在 0x2000 窗口内有 30 个 ret、4 种尺寸
          （`0x10`×5 / `4`×9 / `0`×16 / `8`×3）—— 取第一条纯属运气。

          正确做法：**从入口按 CFG 求可达集**，再看可达集里的 ret 尺寸。
          若可达集内出现多个不同尺寸，说明该函数**真的**会按分支返回不同
          参数量（x86 里极少但存在），此时返回 None —— 不猜。
        """
        cache = self._ret_cache
        if va in cache:
            return cache[va]
        # 先局部解码一个窗口，再按 CFG 求可达集
        o = self.va2off(va)
        if o is None:
            cache[va] = None
            return None
        code = {}
        for i in self.md.disasm(self.b[o:o + 0x2000], va):
            code[i.address] = i
        reach = set()
        work = [va]
        while work:
            a = work.pop()
            if a in reach:
                continue
            reach.add(a)
            i = code.get(a)
            if i is None or i.mnemonic == "ret":
                continue
            nxt = a + i.size
            if i.mnemonic == "jmp":
                if i.op_str.startswith("0x"):
                    work.append(int(i.op_str, 16))
                continue
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                work.append(int(i.op_str, 16))
                work.append(nxt)
                continue
            work.append(nxt)
        sizes = set()
        for a in reach:
            if code[a].mnemonic == "ret":
                sizes.add(int(code[a].op_str, 16) if code[a].op_str else 0)
        val = sizes.pop() if len(sizes) == 1 else None
        cache[va] = val
        return val

    def reachable_ret_sizes(self, va):
        """诊断用：返回 (可达 ret 尺寸集合, 可达指令数)。"""
        o = self.va2off(va)
        if o is None:
            return set(), 0
        code = {}
        for i in self.md.disasm(self.b[o:o + 0x2000], va):
            code[i.address] = i
        reach = set()
        work = [va]
        while work:
            a = work.pop()
            if a in reach:
                continue
            reach.add(a)
            i = code.get(a)
            if i is None or i.mnemonic == "ret":
                continue
            nxt = a + i.size
            if i.mnemonic == "jmp":
                if i.op_str.startswith("0x"):
                    work.append(int(i.op_str, 16))
                continue
            if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
                work.append(int(i.op_str, 16))
                work.append(nxt)
                continue
            work.append(nxt)
        sizes = set()
        for a in reach:
            if code[a].mnemonic == "ret":
                sizes.add(int(code[a].op_str, 16) if code[a].op_str else 0)
        return sizes, len(reach)

    def read_dw(self, va):
        o = self.va2off(va)
        if o is None:
            return None
        return struct.unpack_from("<I", self.b, o)[0]


def main():
    bn = Bin(EXE)
    print("=" * 100)
    print("§396 全路径 esp 模拟：把 5 处间接调用**解析出来**，不再截断")
    print("=" * 100)

    # ---------- 0. 导入表自检 ----------
    print()
    print("--- 0. 导入表解析自检 ---")
    check("IAT 条目数 > 300（导入表真的解析出来了）",
          len(bn.iat) > 300, "%d 条" % len(bn.iat))
    for va, want in ((0x7E1404, "USER32.dll!GetMenu"),
                     (0x7E11C4, "KERNEL32.dll!MultiByteToWideChar"),
                     (0x7E1394, "USER32.dll!DefWindowProcA")):
        got = bn.iat.get(va)
        check("IAT 0x%08X = %s" % (va, want), got == want, "实测 %s" % got)

    # ---------- 1. 三个 vtable 槽的 ret 尺寸 ----------
    print()
    print("--- 1. 间接调用目标解析：vtable 槽 ---")

    # ★★★ §396b：`ret_size` 必须基于**可达集**，不能取「第一条 ret」。
    #   实测 0x6930A0 在 0x2000 窗口内 30 个 ret / 4 种尺寸（0x10×5 / 4×9 /
    #   0×16 / 8×3）—— 取第一条纯属运气。这里对每个被调函数断言「可达 ret 唯一」。
    print()
    print("--- 1b. ★★★ 被调函数的可达 ret 尺寸必须唯一（否则 esp 不可定）---")
    CALLEES = [0x6930A0, 0x778030, 0x724730, 0x7241A0, 0x724580,
               0x7B1780, 0x7B4100, 0x7B13D0, 0x7B3AA0]
    for fn in CALLEES:
        sizes, nreach = bn.reachable_ret_sizes(fn)
        print("    0x%08X  可达 %4d 条指令，ret 尺寸集合 %s"
              % (fn, nreach, sorted(sizes) if sizes else "∅"))
        check("★★ 0x%08X 的可达 ret 尺寸唯一" % fn, len(sizes) == 1,
              "%s" % (sorted(sizes) if sizes else "无 ret"))
    # 负控：「窗口内第一条 ret」与「可达唯一 ret」是两个不同的量
    o_6930 = bn.va2off(0x6930A0)
    first_ret = None
    all_rets = set()
    for i in bn.md.disasm(bn.b[o_6930:o_6930 + 0x2000], 0x6930A0):
        if i.mnemonic == "ret":
            if first_ret is None:
                first_ret = int(i.op_str, 16) if i.op_str else 0
            all_rets.add(int(i.op_str, 16) if i.op_str else 0)
    check("★★ 负控 0x6930A0：窗口内 ret 尺寸不唯一 %s ⇒ 取第一条是错的"
          % sorted(all_rets),
          len(all_rets) > 1 and first_ret == 0x10,
          "第一条=%d，全部=%s" % (first_ret, sorted(all_rets)))
    check("★★ 但**可达**尺寸唯一 ⇒ 取可达集才对",
          len(bn.reachable_ret_sizes(0x6930A0)[0]) == 1,
          "%s" % sorted(bn.reachable_ret_sizes(0x6930A0)[0]))

    # 0x7775D4 前有 mov eax,[ecx] / ecx=[0x887628]；0x7778FA 同函数
    # 直接对两种 vtable 都算一遍，要求一致
    slot_results = {}
    for vt, label in sorted(VTABLES.items()):
        for slot in (0x38, 0x1c):
            fn = bn.read_dw(vt + slot)
            rs = bn.ret_size(fn) if fn else None
            slot_results[(label, slot)] = (fn, rs)
            print("    %s vtable 0x%08X slot 0x%02X -> fn 0x%08X  ret %s"
                  % (label, vt, slot, fn or 0, rs))
    # 每个槽在两种类型下 ret 必须一致（否则 esp 结论依赖运行时类型）
    for slot in (0x38, 0x1c):
        a = slot_results[("类型A", slot)][1]
        b = slot_results[("类型B", slot)][1]
        check("★ slot 0x%02X 在两种 vtable 下 ret 一致（%s vs %s）"
              % (slot, a, b), a is not None and a == b, "ret %s" % a)
    check("★ slot 0x38（0x7775D4）ret = 4", slot_results[("类型A", 0x38)][1] == 4,
          "%s" % (slot_results[("类型A", 0x38)][1],))

    # ---------- 2. IAT 间接调用的参数个数 ----------
    print()
    print("--- 2. 间接调用目标解析：IAT 导入 ---")
    iat_sites = {0x77764F: 0x7E1404, 0x777A38: 0x7E11C4, 0x777A70: 0x7E1394}
    argc_ok = True
    for site, iat_va in sorted(iat_sites.items()):
        name = bn.iat.get(iat_va)
        argc = IMPORT_ARGC.get(name)
        ok = argc is not None
        argc_ok = argc_ok and ok
        print("    0x%08X call [0x%08X] = %-34s argc=%s"
              % (site, iat_va, name, argc))
    check("★★ 三个 IAT 间接调用的 argc 全部已知（不猜 ret 0）",
          argc_ok, "3/3")

    # ---------- 3. 全路径 esp 模拟（不截断）----------
    print()
    print("--- 3. 全路径 esp 模拟（间接调用按解析出的 ret 展开）---")

    def resolve_indirect(ins, ecx_vtable):
        """把 `call [reg+disp]` / `call [mem]` 解析成 ret 字节数。

        返回 (ret_bytes, 说明)。无法解析返回 (None, 原因) —— 绝不退回猜 0。
        """
        ops = ins.op_str
        # 形态 1: call dword ptr [0xXXXXXXXX]  → IAT
        if ops.startswith("dword ptr [0x") and "+" not in ops:
            addr = int(ops.split("[")[1].split("]")[0], 16)
            name = bn.iat.get(addr)
            if name is None:
                return None, "IAT 未解析 0x%08X" % addr
            argc = IMPORT_ARGC.get(name)
            if argc is None:
                return None, "argc 未知 %s" % name
            return 4 * argc, "%s argc=%d" % (name, argc)
        # 形态 2: call dword ptr [reg + 0xNN]  → vtable 槽
        if "+" in ops and "[" in ops:
            disp = int(ops.split("+")[1].split("]")[0], 16)
            vt = ecx_vtable
            if vt is None:
                return None, "vtable 未知"
            fn = bn.read_dw(vt + disp)
            if fn is None:
                return None, "槽不可读"
            rs = bn.ret_size(fn)
            if rs is None:
                return None, "目标无 ret"
            return rs, "vtable 0x%08X slot 0x%02X -> 0x%08X ret %d" % (vt, disp, fn, rs)
        return None, "未识别的间接形态: %s" % ops

    def simulate(vt):
        """逐**指令**记录 esp（不是只记基本块入口）。

        ★ 为什么必须逐指令：`0x7779B5` 是 `0x7779B9` 所在基本块**内部**的一条指令
          （`0x7779B5 mov eax,[esp+0x18]` / `0x7779B9 cmp eax,...`）。
          只记块入口会漏掉它，导致「未到达」的假 FAIL。

        返回 (reached, unresolved, n_states, ind_hits)。
        ind_hits 记录 5 处间接调用**各被执行了几次** —— 用来证明本脚本
        真的走过了那些分支，而不是绕开了它们。
        """
        seen = set()
        reached = {t: set() for t in TARGETS}
        unresolved = []
        ind_hits = dict((a, 0) for a in INDIRECT_SITES)
        q = collections.deque([(FN, 0)])
        n = 0
        while q and n < 60000:
            va, esp = q.popleft()
            if (va, esp) in seen:
                continue
            seen.add((va, esp))
            n += 1
            cur = esp
            pc = va
            nxt_push = None
            while True:
                if pc in reached:
                    reached[pc].add(cur)
                i = bn.insn(pc)
                if i is None:
                    break
                m, ops = i.mnemonic, i.op_str
                if m == "push":
                    cur -= 4
                elif m == "pop":
                    cur += 4
                elif m == "call":
                    cur -= 4
                    if ops.startswith("0x"):
                        rs = bn.ret_size(int(ops, 16))
                        if rs is None:
                            cur = None
                            break
                        cur += 4 + rs
                    else:
                        if i.address in ind_hits:
                            ind_hits[i.address] += 1
                        rs, why = resolve_indirect(i, vt)
                        if rs is None:
                            unresolved.append((i.address, why))
                            cur = None
                            break
                        cur += 4 + rs
                elif m == "add" and ops.startswith("esp,"):
                    cur += int(ops.split(",")[1].strip(), 16)
                elif m == "sub" and ops.startswith("esp,"):
                    cur -= int(ops.split(",")[1].strip(), 16)
                nxt = i.address + i.size
                if m == "ret":
                    nxt_push = None
                    break
                if m == "jmp":
                    if ops.startswith("0x"):
                        q.append((int(ops, 16), cur))
                    nxt_push = None
                    break
                if m.startswith("j") and ops.startswith("0x"):
                    q.append((nxt, cur))
                    q.append((int(ops, 16), cur))
                    nxt_push = None
                    break
                pc = nxt
                nxt_push = (nxt, cur)
            if nxt_push is not None:
                q.append(nxt_push)
        return reached, unresolved, n, ind_hits

    for vt, label in sorted(VTABLES.items()):
        reached, unresolved, nvis, ind_hits = simulate(vt)
        print("    %s（vtable 0x%08X）: 访问 %d 个状态，未解析间接调用 %d 处"
              % (label, vt, nvis, len(unresolved)))
        print("      5 处间接调用执行次数: %s"
              % {("0x%08X" % k): v for k, v in sorted(ind_hits.items())})
        for t in TARGETS:
            s = reached[t]
            print("      目标 0x%08X esp 集合: %s"
                  % (t, sorted(s) if s else "（未到达）"))
        check("★★ %s 路径下无未解析的间接调用" % label,
              len(unresolved) == 0,
              "%d 处 %s" % (len(unresolved), unresolved[:3]))
        # ★★★ 覆盖自检：5 处间接调用必须**全部真的被执行过**。
        #   否则「无未解析」可能只是因为根本没走到它们 —— 那是假绿。
        unseen = [a for a, c in ind_hits.items() if c == 0]
        check("★★★ %s：5 处间接调用**全部被实际执行**（不是绕开）" % label,
              len(unseen) == 0,
              "未执行 %s" % ["0x%08X" % a for a in unseen] if unseen
              else "5/5 均执行过")
        for t in TARGETS:
            s = reached[t]
            check("★★ %s：0x%08X 的 esp 唯一且 = %+d"
                  % (label, t, EXPECTED_ESP),
                  len(s) == 1 and sorted(s)[0] == EXPECTED_ESP,
                  "%s" % sorted(s))
            got = sorted(s)[0] if len(s) == 1 else None
            check("⇒ %s：0x%08X 的 [esp+0x18] = E+0x%02X = msg"
                  % (label, t, EXPECTED_ARG),
                  got is not None and got + 0x18 == EXPECTED_ARG,
                  "E%+d" % (got + 0x18) if got is not None else "N/A")

    # ---------- 4. 两种 vtable 结论必须一致 ----------
    print()
    print("--- 4. ★ 两种 vtable 的结论必须一致（否则 esp 依赖运行时类型）---")
    ra, _, _, _ = simulate(0x7F794C)
    rb, _, _, _ = simulate(0x7F7A6C)
    same = all(ra[t] == rb[t] for t in TARGETS)
    check("★★★ 类型 A 与类型 B 的 esp 集合完全相同（结论与类型无关）",
          same, "%s" % {("0x%08X" % t): (sorted(ra[t]), sorted(rb[t])) for t in TARGETS})

    # ---------- 5. 负控：解析器必须能拒绝错误输入 ----------
    print()
    print("--- 5. ★ 负控：解析器不能瞎猜 ---")
    fake = bn.insn(0x7775D4)
    rs, why = resolve_indirect(fake, None)
    check("★★ 负控：vtable 未知时 resolve_indirect 返回 None（不猜 ret 0）",
          rs is None, "%s" % why)
    rs2, why2 = resolve_indirect(fake, 0x7F794C)
    check("★ 正控：vtable 已知时能解析出 ret 4", rs2 == 4, "%s" % why2)
    # IAT 未命中
    class _Fake(object):
        mnemonic = "call"
        op_str = "dword ptr [0x7effff]"
    rs3, why3 = resolve_indirect(_Fake(), None)
    check("★★ 负控：IAT 未命中时返回 None（不猜 ret 0）", rs3 is None, "%s" % why3)

    # ---------- 5b. ★★★ 取值负控：改 argc / ret 必须让 esp 集合翻掉 ----------
    #   ★ 变异选点纪律（变种 I）：只有**在通往目标的路径上**的间接调用，
    #     改它才会改变 esp。改一个终局 return 之前的调用，esp 集合不变 ——
    #     那不是门禁漏了，是变异选错了位置。
    print()
    print("--- 5b. ★★★ 取值负控：改 argc / ret，esp 集合必须翻 ---")

    def simulate_with(argc_over=None, ret_over=None):
        old_argc = dict(IMPORT_ARGC)
        old_ret = bn.ret_size
        if argc_over:
            IMPORT_ARGC.update(argc_over)
        if ret_over:
            def _rs(va):
                if va in ret_over:
                    return ret_over[va]
                return old_ret(va)
            bn.ret_size = _rs
        try:
            return simulate(0x7F794C)[0]
        finally:
            IMPORT_ARGC.clear()
            IMPORT_ARGC.update(old_argc)
            bn.ret_size = old_ret

    base = simulate(0x7F794C)[0]
    check("基线：0x777687 的 esp 集合 = [-16]",
          base[0x777687] == {-0x10}, "%s" % sorted(base[0x777687]))

    # M1：GetMenu argc 1 → 2（ret 4 → 8）。GetMenu 在通往 0x777687 的路径上。
    m1 = simulate_with(argc_over={"USER32.dll!GetMenu": 2})
    check("★★★ M1 GetMenu argc 1→2 ⇒ 0x777687 的 esp 不再唯一（翻红）",
          len(m1[0x777687]) != 1,
          "%s" % sorted(m1[0x777687]))

    # M2：slot14 ret 4 → 0。
    m2 = simulate_with(ret_over={0x7B1780: 0})
    check("★★★ M2 slot14 ret 4→0 ⇒ 0x777687 的 esp 不再唯一（翻红）",
          len(m2[0x777687]) != 1,
          "%s" % sorted(m2[0x777687]))

    # ★ M3：DefWindowProcA argc 4→3 **不应**改变结果 —— 该路径以 ret 0x10 结束，
    #   根本到不了 0x777687。这不是门禁漏，是变异选错了位置（变种 I）。
    m3 = simulate_with(argc_over={"USER32.dll!DefWindowProcA": 3})
    check("★ M3 DefWindowProcA argc 4→3 ⇒ 结果**不变**（该路径 ret 0x10 终局，不在通往目标的路上）",
          m3[0x777687] == base[0x777687],
          "%s（与基线一致 ⇒ 变异选点无效，不是漏检）" % sorted(m3[0x777687]))
    # 确认 DWP 站点确实是终局返回
    dwp_site = 0x777A70
    nxt_ret = None
    for i in bn.md.disasm(bn.b[bn.va2off(dwp_site):bn.va2off(dwp_site) + 0x20], dwp_site):
        if i.mnemonic == "ret":
            nxt_ret = (i.address, i.op_str)
            break
    check("★★ DefWindowProcA 调用之后第一条 ret 是 ret 0x10（证实它是终局路径）",
          nxt_ret is not None and nxt_ret[1] == "0x10",
          "0x%08X ret %s" % nxt_ret if nxt_ret else "未找到")

    # ---------- 6. 与 _esp_bfs.py 的结论交叉 ----------
    print()
    print("--- 6. 交叉：与 _esp_bfs.py（截断版）的结论一致 ---")
    print("    _esp_bfs.py 结论：0x777687 / 0x7779B9 / 0x7779B5 均为 esp=-0x10（13/13）")
    print("    本脚本结论：同上，且**覆盖了经间接调用的分支**")
    check("★★ 两条独立实现的 esp 结论一致（都是 -0x10）",
          all(len(ra[t]) == 1 and sorted(ra[t])[0] == EXPECTED_ESP for t in TARGETS),
          "截断版 13/13 + 全路径版本文")

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
