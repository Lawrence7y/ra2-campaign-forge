#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§394：v5 补丁覆盖的**取值证明** —— 用 CFG 后向数据流，取代 §393 的形态启发式。

§393 的门禁判的是「回溯窗口里**存在**一条 `[0x887368]` 装载」，
那是存在性判据，抓不住「装载换全局」（P23/P23b）。本节改成**取值证明**。

要证的命题（唯一一条）：
    对 8 个补丁目标函数的**每一个**直接调用点，
    调用瞬间 `ecx` 的值 = `[0x887368]` 的一次装载（可经寄存器中转）。

一旦这条成立，补丁的覆盖问题就闭合了：
    函数头的 `test ecx,ecx / je` 读的正是 ecx，
    ecx == [0x887368] ⇒ 全局为 0 时守卫必命中，与调用者自带什么守卫无关。
    （§393 的 C 类「调用者前置守卫」因此是**多余的分类**，本节不再需要。）

方法：真后向数据流
  - 前驱图来自**分支目标解析**（jmp/jcc 的目标入边 + 顺序 fall-through），
    不是线性相邻 —— 这是 §393 抓不住 P23 的根因（16 个站点的 ecx 来自分支路径）。
  - 追踪寄存器集合随 `mov ecx, <reg>` 切换（实测 0x4E1FA9 经 esi 中转）。
  - 遇 `call` ⇒ 被追踪寄存器被调用者破坏 ⇒ UNKNOWN（保守，不猜）。
  - 走到函数入口（无前驱）⇒ UNKNOWN（保守）。

★ 负控必须能把它打红：P23 换全局、P23b 换另一站点、P27 拆守卫。
  若负控不红，本门禁同样作废 —— 判据是「它能拒绝什么」。
"""
import collections
import re as _re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "ra2bench" / "gamemd.exe"
RESULTS = []

TARGETS = [0x7241A0, 0x724200, 0x724520, 0x724530,
           0x724540, 0x724580, 0x724730, 0x724C00]

EXPECTED_COUNTS = {
    0x7241A0: 14, 0x724200: 1, 0x724520: 1, 0x724530: 1,
    0x724540: 1, 0x724580: 18, 0x724730: 30, 0x724C00: 1,
}

SINGLETON = 0x887368

# 会写第一个操作数（目标）的助记符
WRITE_MNEM = {
    "mov", "movzx", "movsx", "movsxd", "lea", "pop", "xchg", "xadd",
    "add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec",
    "neg", "not", "imul", "shl", "shr", "sar", "rol", "ror",
    "cmovz", "cmovnz", "cmove", "cmovne", "cmova", "cmovb",
    "cmovg", "cmovl", "cmovge", "cmovle", "cmovae", "cmovbe",
}

GPR = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"}

# 部分寄存器：写 cx/cl/ch 等于改写 ecx 的低位 ⇒ 追踪 ecx 时必须判 UNKNOWN
PARTIAL = {
    "ax": "eax", "al": "eax", "ah": "eax",
    "bx": "ebx", "bl": "ebx", "bh": "ebx",
    "cx": "ecx", "cl": "ecx", "ch": "ecx",
    "dx": "edx", "dl": "edx", "dh": "edx",
    "si": "esi", "di": "edi", "bp": "ebp", "sp": "esp",
}

# ★ 这些指令会写寄存器，但**写的不是第一个操作数**（或写的范围不确定）。
#   漏掉它们会让「该寄存器未被改写」的推断变假 —— 属于变种 G-2 的潜在口子。
#   实测 67 条链上命中 0 次（295 条不同指令），但保留判定以防将来改动。
CLOBBER_MULTI = {
    "mul": {"eax", "edx"}, "imul1": {"eax", "edx"},
    "div": {"eax", "edx"}, "idiv": {"eax", "edx"},
    "cwd": {"edx"}, "cdq": {"edx"},
    "cpuid": {"eax", "ebx", "ecx", "edx"},
    "rdtsc": {"eax", "edx"},
    "popa": GPR, "popad": GPR,
    "enter": {"esp", "ebp"}, "leave": {"esp", "ebp"},
    "xlat": {"eax"},
}

# 写第一个操作数、但不在 WRITE_MNEM 里的指令（补全）
EXTRA_WRITE = {"shld", "shrd", "bts", "btr", "btc", "bswap", "cmpxchg"}


def check(tag, cond, ev=""):
    RESULTS.append((tag, bool(cond), ev))
    print("  %-70s %s  %s" % (tag, "PASS" if cond else "FAIL", ev))
    return bool(cond)


class Bin(object):
    def __init__(self, path, data=None):
        import capstone
        self.b = data if data is not None else Path(path).read_bytes()
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
        self._map_text()

    def va2off(self, va):
        rva = va - self.ib
        for nm, v, vs, ra, rs in self.secs:
            if v <= rva < v + max(vs, rs):
                off = ra + (rva - v)
                if 0 <= off < len(self.b):
                    return off
        return None

    def _map_text(self):
        d = {n: (v, vs, ra, rs) for n, v, vs, ra, rs in self.secs}
        self.text_va = d[".text"][0] + self.ib
        self.text_end = self.text_va + d[".text"][1]
        self.code = {}
        pc = self.text_va
        while pc < self.text_end:
            o = self.va2off(pc)
            if o is None:
                break
            ch = min(0x1000, self.text_end - pc)
            ins = list(self.md.disasm(self.b[o:o + ch], pc))
            if not ins:
                pc += 1
                continue
            for i in ins:
                self.code[i.address] = i
            pc = ins[-1].address + ins[-1].size
        # 前驱图：分支目标 + fall-through（★ 非线性相邻）
        self.prev = collections.defaultdict(set)
        for a, i in self.code.items():
            ft = a + i.size
            m = i.mnemonic
            if m == "ret":
                continue
            if m == "jmp":
                t = self._target(i)
                if t is not None:
                    self.prev[t].add(a)
                continue
            if m.startswith("j") and m != "jmp":
                t = self._target(i)
                if t is not None:
                    self.prev[t].add(a)
                if ft in self.code:
                    self.prev[ft].add(a)
                continue
            if ft in self.code:
                self.prev[ft].add(a)

    @staticmethod
    def _target(ins):
        try:
            return int(ins.op_str, 16)
        except ValueError:
            return None

    def callers_of(self, tgt):
        out = []
        for a, i in self.code.items():
            if i.mnemonic == "call" and i.op_str.startswith("0x"):
                if self._target(i) == tgt:
                    out.append(a)
        return sorted(out)


def operand_write(ins):
    """返回 (写入的寄存器名 or None, 源操作数字符串 or None)。

    ★ 覆盖三类写入，缺一类就会把「未改写」判错：
      1. WRITE_MNEM ∪ EXTRA_WRITE：写第一个操作数
      2. PARTIAL：写 8/16 位子寄存器 —— 归到**宿主** 32 位寄存器
         （`mov cl,1` 改写 ecx；`mov dl,1` 只改写 edx，与 ecx 无关）
      3. CLOBBER_MULTI / 字符串指令：隐含写，写的不只第一个操作数
         ⇒ 返回 ("__IMPLICIT__", 原因)，由调用方判 UNKNOWN
    """
    if not ins.mnemonic:
        return None, None
    # rep/repne 前缀：字符串指令隐含读写 ecx（计数）与 esi/edi
    if ins.mnemonic.startswith("rep"):
        return "__IMPLICIT__", "string-op"
    if ins.mnemonic in ("movsd", "stosd", "lodsd", "scasd", "cmpsd",
                        "movsb", "stosb", "lodsb", "scasb", "cmpsb",
                        "movsw", "stosw", "lodsw", "scasw", "cmpsw"):
        return "__IMPLICIT__", "string-op"
    if ins.mnemonic in CLOBBER_MULTI:
        return "__IMPLICIT__", ins.mnemonic
    if ins.mnemonic not in WRITE_MNEM and ins.mnemonic not in EXTRA_WRITE:
        return None, None
    parts = [p.strip() for p in ins.op_str.split(",")]
    if not parts:
        return None, None
    dst = parts[0]
    src = parts[1] if len(parts) > 1 else None
    if dst in PARTIAL:
        # 子寄存器 ⇒ 归到宿主。是否影响被追踪寄存器由调用方按名字比对决定。
        return PARTIAL[dst], ("__PARTIAL__" + (src or ""))
    if dst not in GPR:
        return None, None
    return dst, src


def _is_full_width_load(s):
    """判断操作数是否是 [0x887368] 的 **32 位整字** 装载。

    ★ 「dword ptr」包含子串「word ptr」，用 `in` 判断会把 dword 误判成 16 位。
      用 `\\bword ptr` 避开（dword 是一个词，\\b 不在其中间匹配）。
    """
    low = s.lower()
    if "[0x%x]" % SINGLETON not in low and "[0x%08x]" % SINGLETON not in low:
        return False
    if "dword ptr" in low:
        return True
    if "byte ptr" in low or _re.search(r"\bword ptr", low):
        return False
    return True   # 裸 [0x887368]，capstone 对 32 位 mov 默认整字


def classify_source(ins, src):
    """把一次写入的源定性。返回 ('GLOBAL',None) / ('ZERO',None) /
    ('REG',reg) / ('UNKNOWN',reason)。

    ★★★ 核心约束：**只有 `mov` 是纯赋值**。
      其它任何写 ecx 的指令都不是「把源值原样搬进 ecx」：

        and  ecx,[0x887368]   → ecx = 旧ecx & [..]   ≠ [..]
        add  ecx,[0x887368]   → ecx = 旧ecx + [..]   ≠ [..]
        shld ecx,esi,cl       → ecx 是拼接结果      ≠ esi
        bts  ecx,eax          → 只置一位            ≠ eax
        xadd ecx,esi          → 交换后相加          ≠ esi
        movzx ecx,word ptr[…] → 只取低 16 位，高位清零 ≠ [..] 的 32 位值

      早期版本只要操作数字符串里出现 `[0x887368]` 就判 GLOBAL，
      于是上面第一、二、六行全部被判成「ecx == [0x887368]」—— 假绿。
      （由异族探针 probe_c 发现，我自己复现确认。）
    """
    if src is not None and src.startswith("__PARTIAL__"):
        return "UNKNOWN", "partial-write"
    if src is None:
        return "UNKNOWN", "read-modify-write"
    s = src.strip()
    dst = ins.op_str.split(",")[0].strip()
    if ins.mnemonic in ("xor", "sub") and s == dst:
        return "ZERO", None
    if ins.mnemonic == "lea":
        return "UNKNOWN", "lea-address-not-load"
    if ins.mnemonic.startswith("cmov"):
        return "UNKNOWN", "conditional-write"
    if ins.mnemonic != "mov":
        return "UNKNOWN", "not-pure-assignment(%s)" % ins.mnemonic
    if s in GPR:
        return "REG", s
    if _is_full_width_load(s):
        return "GLOBAL", None
    return "UNKNOWN", s


def backward_sources(bin_, call_va, max_nodes=40000, override=None):
    """从 call_va 后向追踪 ecx 的来源集合。

    返回 (sources, meta)。sources 是 ('GLOBAL',None)/('ZERO',None)/('UNKNOWN',reason)
    的去重集合。经寄存器中转时切换追踪对象（(地址, reg) 为工作项）。

    override: {指令地址: 伪造源操作数字符串} —— 仅供负控使用，
              用来模拟「把该处的装载换成别的全局」（P23/P23b 的形态）。

    ★ meta["ends"] 记账每一条工作链**怎么结束的**：
        writer   命中一个写该寄存器的指令（已定性）
        entry    走到函数入口（无前驱）
        call     被 call 破坏
        strop    字符串指令（rep movs 等隐含改写 ecx）
        unmapped 前驱不在已解码集合
        merged   所有前驱都已访问过（重复收敛，不丢信息）
        trunc    超节点上限
      任何一条链都不能「无声消失」—— 否则 67/67 会是记账假绿。
    """
    override = override or {}
    seen = set()
    work = [(call_va, "ecx")]
    sources = set()
    ends = collections.Counter()
    while work:
        node, reg = work.pop()
        key = (node, reg)
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > max_nodes:
            ends["trunc"] += 1
            sources.add(("UNKNOWN", "truncated"))
            break
        preds = bin_.prev.get(node)
        if not preds:
            ends["entry"] += 1
            sources.add(("UNKNOWN", "function-entry"))
            continue
        progressed = False
        for p in preds:
            if (p, reg) in seen:
                continue
            pi = bin_.code.get(p)
            if pi is None:
                ends["unmapped"] += 1
                sources.add(("UNKNOWN", "unmapped-pred"))
                continue
            progressed = True
            m = pi.mnemonic
            dst, src = operand_write(pi)
            # ★ 隐含写：字符串指令/部分寄存器/mul-div-cpuid 等
            #   它们改写 ecx（或无法确定改写哪个），一律判 UNKNOWN，绝不猜。
            if dst == "__IMPLICIT__":
                ends["strop"] += 1
                sources.add(("UNKNOWN", "implicit-write:%s@0x%X" % (src, p)))
                seen.add((p, reg))
                continue
            if dst == reg:
                # ★ 部分写（mov cl,1 / add cx,eax）：只改低位，ecx 高位保留旧值
                #   ⇒ 无法断言「ecx == [0x887368]」，必须判 UNKNOWN。
                if src is not None and src.startswith("__PARTIAL__"):
                    ends["strop"] += 1
                    sources.add(("UNKNOWN", "partial-write@0x%X" % p))
                    seen.add((p, reg))
                    continue
                eff_src = override.get(p, src)
                kind, val = classify_source(pi, eff_src)
                ends["writer"] += 1
                seen.add((p, reg))
                if kind == "REG":
                    work.append((p, val))
                else:
                    sources.add((kind, val))
                continue
            if m == "call":
                ends["call"] += 1
                sources.add(("UNKNOWN", "clobbered-by-call@0x%X" % p))
                seen.add((p, reg))
                continue
            work.append((p, reg))
        if not progressed:
            # 所有前驱都已访问过：该链的信息已由其它路径记录，不丢数据
            ends["merged"] += 1
    return sources, dict(ends=dict(ends), nodes=len(seen),
                         trunc=ends["trunc"] > 0)


def main():
    bn = Bin(EXE)
    print("=" * 100)
    print("§394 v5 补丁覆盖的取值证明：ecx == [0x%X] 于全部调用点" % SINGLETON)
    print("=" * 100)

    # ---------- 0. 建图自检 ----------
    print()
    print("--- 0. 前驱图自检（防「图没建起来」型假绿）---")
    check("指令总数 > 1,300,000（线性扫描覆盖全 .text）",
          len(bn.code) > 1300000, "%d 条" % len(bn.code))
    n_branch_edges = sum(len(v) for v in bn.prev.values())
    check("前驱边数 > 指令数（分支目标确实入图，非线性相邻）",
          n_branch_edges > len(bn.code), "%d 条边" % n_branch_edges)
    # 取一个已知分支目标，确认它的前驱不止 fall-through
    p48 = bn.prev.get(0x48CE62, set())
    check("0x48CE62 的前驱集合非空且含分支来源",
          len(p48) > 0, "%s" % sorted("0x%X" % x for x in p48))

    # ---------- 1. 调用点普查 ----------
    print()
    print("--- 1. 调用点普查（逐目标基线）---")
    calls = {t: bn.callers_of(t) for t in TARGETS}
    for t in TARGETS:
        print("    0x%08X : %2d 个调用者" % (t, len(calls[t])))
    for t in TARGETS:
        check("0x%08X 调用点数 == %d" % (t, EXPECTED_COUNTS[t]),
              len(calls[t]) == EXPECTED_COUNTS[t], "实测 %d" % len(calls[t]))
    total = sum(len(v) for v in calls.values())
    check("合计 67 个直接调用点", total == 67, "%d 处" % total)

    # ---------- 2. ★ 逐站点后向数据流 ----------
    print()
    print("--- 2. ★ 逐站点后向数据流：ecx 的实际来源 ---")
    verdict = {}
    for t in TARGETS:
        for s in calls[t]:
            srcs, meta = backward_sources(bn, s)
            verdict[s] = (t, srcs, meta)

    n_global = 0
    n_zero = 0
    bad = []
    agg_ends = collections.Counter()
    for s, (t, srcs, meta) in sorted(verdict.items()):
        agg_ends.update(meta["ends"])
        kinds = set(k for k, _ in srcs)
        if meta["trunc"]:
            bad.append((s, t, "TRUNCATED", srcs))
            continue
        if kinds == {"GLOBAL"}:
            n_global += 1
        elif kinds == {"ZERO"}:
            n_zero += 1
        else:
            bad.append((s, t, "+".join(sorted(kinds)), srcs))

    print("    ecx 来源 = [0x%X] 装载          : %d 处" % (SINGLETON, n_global))
    print("    ecx 来源 = 常量 0（xor/sub 自清零）: %d 处" % n_zero)
    print("    未闭合（UNKNOWN / 混合 / 截断）    : %d 处" % len(bad))
    for s, t, k, srcs in bad:
        print("      0x%08X -> 0x%08X  %s  %s"
              % (s, t, k, sorted(srcs)[:3]))

    # ★★★ 记账自检：每个站点的链必须终止于「命中写点」，不能走到未知来源。
    #   若出现 entry/call/unmapped/strop/trunc，说明有链走到未知来源，
    #   而 GLOBAL 判定只是碰巧由另一条链提供 —— 那就是记账假绿。
    #   merged（所有前驱已访问）是**收敛**，不是丢数据，允许。
    #   注：writer 总数可以 > 67 —— 一个站点经多路径到达多个写点属正常
    #   （实测 0x4E1FA9 经 esi 中转有 2 条链，0x640427 有 1 条链 + 1 次收敛）。
    print("    链终止记账：%s" % dict(agg_ends))
    bad_term = [s for s, (t, srcs, meta) in verdict.items()
                if meta["ends"].get("entry", 0) or meta["ends"].get("call", 0)
                or meta["ends"].get("unmapped", 0) or meta["ends"].get("strop", 0)
                or meta["ends"].get("trunc", 0)
                or meta["ends"].get("writer", 0) == 0]
    check("★★ 67 个站点每条链都终止于 ecx 写点（无 entry/call/unmapped/strop/trunc）",
          len(bad_term) == 0,
          "writer=%d merged=%d 异常站点=%d"
          % (agg_ends["writer"], agg_ends["merged"], len(bad_term)))
    if bad_term:
        for s in bad_term[:6]:
            print("      异常 0x%08X ends=%s" % (s, verdict[s][2]["ends"]))

    check("★★★ 全部 67 个调用点的 ecx 都装载自 [0x%X]（取值证明）"
          % SINGLETON,
          n_global == 67 and len(bad) == 0,
          "GLOBAL=%d ZERO=%d 未闭合=%d" % (n_global, n_zero, len(bad)))

    # 中转站点必须存在（否则说明 REG 切换分支没被走到）
    relay = []
    for s, (t, srcs, meta) in verdict.items():
        for p in bn.prev.get(s, ()):
            pi = bn.code.get(p)
            if pi is not None:
                d, src = operand_write(pi)
                if d == "ecx" and src in GPR:
                    relay.append((s, src))
    check("存在经寄存器中转的站点（REG 切换分支被实际走到，非死代码）",
          len(relay) > 0,
          "%s" % ["0x%X via %s" % (a, r) for a, r in relay][:4])

    # ---------- 3. 补丁守卫形态（P27 的正面断言）----------
    print()
    print("--- 3. 8 个目标函数头是否具备 test ecx,ecx / je 的插入位置 ---")
    # 补丁在函数头前插入，这里验证每个目标的第一条指令是**可识别的函数边界**
    # （不是指令中段），否则 trampoline 会劈开一条指令。
    ok_bounds = []
    for t in TARGETS:
        ins = bn.code.get(t)
        ok_bounds.append((t, ins is not None))
        print("    0x%08X : %s" % (t, ("%s %s" % (ins.mnemonic, ins.op_str))
                                   if ins else "NOT-AN-INSTRUCTION-BOUNDARY"))
    check("8 个补丁目标地址都是指令边界（trampoline 不会劈开指令）",
          all(ok for _, ok in ok_bounds),
          "%d/8" % sum(1 for _, ok in ok_bounds if ok))

    # ---------- 4. ★ 负控：变异必须打红 ----------
    print()
    print("--- 4. ★ 负控：把装载换成别的全局，整条分析必须改判 ---")
    # 先找出每个测试站点真正被分析命中的那个 ecx 写点（不是「附近随便一个」）
    def ecx_writer_reached(site):
        found = []
        seen = set()
        work = [(site, "ecx")]
        while work:
            node, reg = work.pop()
            if (node, reg) in seen:
                continue
            seen.add((node, reg))
            for p in bn.prev.get(node, ()):
                if (p, reg) in seen:
                    continue
                pi = bn.code.get(p)
                if pi is None:
                    continue
                d, src = operand_write(pi)
                if d == reg:
                    kind, val = classify_source(pi, src)
                    if kind == "GLOBAL":
                        found.append(p)
                    elif kind == "REG":
                        work.append((p, val))
                    seen.add((p, reg))
                elif pi.mnemonic == "call":
                    seen.add((p, reg))
                else:
                    work.append((p, reg))
        return found

    MUT_SITES = [0x654413, 0x6D05AB]
    for site in MUT_SITES:
        writers = ecx_writer_reached(site)
        check("负控前置：站点 0x%08X 的装载点可定位" % site,
              len(writers) > 0, "%s" % ["0x%X" % w for w in writers])
        if not writers:
            continue
        # 把**所有**命中的装载点都改成别的全局 —— 模拟 P23/P23b
        ov = {w: "dword ptr [0x887640]" for w in writers}
        srcs_mut, meta_mut = backward_sources(bn, site, override=ov)
        kinds_mut = set(k for k, _ in srcs_mut)
        check("★★ 负控 0x%08X 装载换全局 ⇒ 结论翻为非 GLOBAL（门禁会红）"
              % site,
              "GLOBAL" not in kinds_mut,
              "变异后 %s" % sorted(kinds_mut))

    # P27 形态：拆掉守卫 —— 由 §392 的 guard_premise 门禁负责；
    # 本门禁证明的是「ecx 的取值」，守卫形态不在其证明范围，故不重复。
    k_bad = classify_source(bn.code[0x654405], "[0x887640]")
    k_good = classify_source(bn.code[0x654405], "dword ptr [0x887368]")
    check("★ classify_source 对源地址敏感：0x887640 ⇒ %s，0x887368 ⇒ %s"
          % (k_bad[0], k_good[0]),
          k_bad[0] != "GLOBAL" and k_good[0] == "GLOBAL")
    # lea 陷阱：取地址 ≠ 取内容。用真实的 lea 指令验证分类器不误判。
    lea_ins = next((i for i in bn.code.values()
                    if i.mnemonic == "lea" and "ecx," in i.op_str), None)
    if lea_ins is not None:
        k_lea, v_lea = classify_source(lea_ins, lea_ins.op_str.split(",")[1].strip())
        check("★ lea 语义守卫：lea 取地址不判 GLOBAL（样例 0x%08X）"
              % lea_ins.address,
              k_lea != "GLOBAL", "判为 %s（%s）" % (k_lea, v_lea))
    check("★ 0x654405 是 mov 装载而非 lea（GLOBAL 判定的前提）",
          bn.code[0x654405].mnemonic == "mov",
          "实际 %s" % bn.code[0x654405].mnemonic)

    # ---------- 4b. ★★★ 字节级变异：真的改二进制，端到端重跑 ----------
    #   上面 4 节的 override 只测了分类器对字符串的敏感性。
    #   这里把**磁盘镜像**里 0x654405 的 `[0x887368]` 改成 `[0x887640]`，
    #   重建整个 Bin（重新线性扫描 + 重建前驱图），走完整条分析链。
    #   这才是 P23 的真实形态：若门禁仍全绿，它就是假绿。
    print()
    print("--- 4b. ★★★ 字节级变异（真改镜像 + 重建全图，端到端）---")
    mut_off = bn.va2off(0x654405)
    orig = bytes(bn.b[mut_off:mut_off + 6])
    check("0x654405 原始字节 = 8B 0D 68 73 88 00（mov ecx,[0x887368]）",
          orig == b"\x8b\x0d\x68\x73\x88\x00", orig.hex(" "))
    mut = bytearray(bn.b)
    # [0x887368] 的 disp32 位于偏移 +2..+6；改成 0x887640
    struct.pack_into("<I", mut, mut_off + 2, 0x887640)
    bn_mut = Bin(EXE, data=bytes(mut))
    check("变异后 0x654405 解码为 [0x887640]（装载已换全局）",
          "0x887640" in bn_mut.code[0x654405].op_str,
          bn_mut.code[0x654405].op_str)
    srcs_m, meta_m = backward_sources(bn_mut, 0x654413)
    check("★★★ 字节级负控：装载换全局后，0x654413 的来源不再是 GLOBAL"
          "（门禁会红）",
          "GLOBAL" not in set(k for k, _ in srcs_m),
          "变异后 %s（ends=%s）"
          % (sorted(set(k for k, _ in srcs_m)), meta_m["ends"]))
    # 正控：未变异的镜像上同一站点必须仍是 GLOBAL（证明上一条不是恒真）
    srcs_o, _ = backward_sources(bn, 0x654413)
    check("★★ 正控：未变异镜像上同一站点仍判 GLOBAL（负控非恒真）",
          set(k for k, _ in srcs_o) == {"GLOBAL"},
          "%s" % sorted(set(k for k, _ in srcs_o)))

    # ---------- 4c. ★★★ 全量重跑：变异后 67 → 66，证明门禁整体敏感 ----------
    #   单站点改判只能证明「那一条链被分析到了」。
    #   全量重跑证明「整套普查的计数会随二进制变化而变化」——
    #   即 67/67 这个数字不是写死的、也不是恒真。
    print()
    print("--- 4c. ★★★ 变异后全量重跑（67 → 66）---")

    def census(bin_):
        n = 0
        fails = []
        for t in TARGETS:
            for s in bin_.callers_of(t):
                srcs, meta = backward_sources(bin_, s)
                if set(k for k, _ in srcs) == {"GLOBAL"} and not meta["trunc"]:
                    n += 1
                else:
                    fails.append((s, t, sorted(set(k for k, _ in srcs))))
        return n, fails

    n_mut, fails_mut = census(bn_mut)
    check("★★★ 变异镜像的全量普查 = 66/67（不是 67，门禁整体敏感）",
          n_mut == 66, "实测 %d/67" % n_mut)
    check("★★ 变异镜像的失败站点恰为 0x654413（唯一受影响者）",
          [f[0] for f in fails_mut] == [0x654413],
          "%s" % ["0x%08X" % f[0] for f in fails_mut])
    check("★★★ 未变异镜像的全量普查 = 67/67（正控）",
          n_global == 67, "实测 %d/67" % n_global)

    # ---------- 4d. ★★★ P23b：换另一个站点，同样必须掉到 66 ----------
    #   只测一个站点可能是「恰好那个站点被特殊处理」。
    #   换一个不同目标函数（0x6D05A0 → 0x724730）的装载点重跑，结论必须同构。
    print()
    print("--- 4d. ★★★ P23b：换另一个装载点（0x6D05A0）重跑全量 ---")
    off2 = bn.va2off(0x6D05A0)
    check("0x6D05A0 原始字节 = 8B 0D 68 73 88 00",
          bytes(bn.b[off2:off2 + 6]) == b"\x8b\x0d\x68\x73\x88\x00",
          bn.b[off2:off2 + 6].hex(" "))
    mut2 = bytearray(bn.b)
    struct.pack_into("<I", mut2, off2 + 2, 0x887640)
    bn_mut2 = Bin(EXE, data=bytes(mut2))
    n_mut2, fails_mut2 = census(bn_mut2)
    check("★★★ P23b 变异后全量普查 = 66/67", n_mut2 == 66,
          "实测 %d/67" % n_mut2)
    check("★★ P23b 的失败站点恰为 0x6D05AB", [f[0] for f in fails_mut2] == [0x6D05AB],
          "%s" % ["0x%08X" % f[0] for f in fails_mut2])

    # ---------- 4e. ★★ P27 形态：拆掉 ecx 装载（改成 nop），必须掉数 ----------
    #   §393 登记「P27 拆守卫抓不住」。本门禁证明的是 ecx 取值，
    #   所以它抓的是「装载被拆」而不是「守卫被拆」—— 两者都让覆盖失效，
    #   但只有前者在本门禁的证明范围内。这里明确区分，不含糊过去。
    print()
    print("--- 4e. ★★ P27 形态：把装载整条改成 nop（等价于拆掉来源）---")
    off3 = bn.va2off(0x654405)
    mut3 = bytearray(bn.b)
    mut3[off3:off3 + 6] = b"\x90" * 6
    bn_mut3 = Bin(EXE, data=bytes(mut3))
    srcs_m3, meta_m3 = backward_sources(bn_mut3, 0x654413)
    check("★★ 装载改成 nop 后，0x654413 的来源不再是 GLOBAL",
          "GLOBAL" not in set(k for k, _ in srcs_m3),
          "变异后 %s" % sorted(set(k for k, _ in srcs_m3)))
    print("    注：本门禁证明 ecx 的**取值**；「守卫被拆」（test/je 移除）")
    print("        不属本门禁范围，由 §392 _verify_guard_premise.py 负责。")
    print("        §393 登记的 P27 盲区在本门禁下仍未闭合，但归属已明确。")

    # ---------- 4f. 确定性：同输入两次跑结论必须一致 ----------
    srcs_r1, _ = backward_sources(bn, 0x6D05AB)
    srcs_r2, _ = backward_sources(bn, 0x6D05AB)
    check("★ 确定性：同一站点两次分析结果一致（无遍历顺序依赖）",
          srcs_r1 == srcs_r2, "%s == %s" % (sorted(srcs_r1), sorted(srcs_r2)))

    # ---------- 4g. ★ 写入分类覆盖自检（防止将来漏类）----------
    #   这些指令都会写 ecx（或其宿主），但写的不是「第一个操作数」的常规形态。
    #   实测 67 条链上命中 0 次，所以下面用合成指令验证判定逻辑本身在工作。
    print()
    print("--- 4g. ★ 写入分类覆盖自检（合成指令，非二进制）---")

    class _FakeIns(object):
        def __init__(self, mn, ops):
            self.mnemonic = mn
            self.op_str = ops

    cases = [
        ("mov", "ecx, dword ptr [0x887368]", "ecx", "GLOBAL-eligible"),
        ("mov", "cl, 1", "ecx", "partial→UNKNOWN"),
        ("mov", "dl, 1", "edx", "partial 归宿主 edx，与 ecx 无关"),
        ("add", "cx, ax", "ecx", "partial→UNKNOWN"),
        ("shld", "ecx, edx, 4", "ecx", "EXTRA_WRITE 覆盖"),
        ("bts", "ecx, 3", "ecx", "EXTRA_WRITE 覆盖"),
        ("mul", "ecx", "__IMPLICIT__", "隐含写 eax/edx"),
        ("cdq", "", "__IMPLICIT__", "隐含写 edx"),
        ("cpuid", "", "__IMPLICIT__", "隐含写全部"),
        ("rep movsd", "dword ptr es:[edi], dword ptr [esi]", "__IMPLICIT__",
         "字符串指令隐含写 ecx"),
        ("cmp", "ecx, 0", None, "cmp 不写"),
        ("test", "ecx, ecx", None, "test 不写"),
    ]
    for mn, ops, want, why in cases:
        got, _ = operand_write(_FakeIns(mn, ops))
        check("  写入分类 %-10s %-38s → %s（%s）"
              % (mn, ops[:38], got, why), got == want, "实测 %s" % got)

    # 关键：partial 写**不**应把无关寄存器的站点判红（这正是我第一版犯的错）
    check("★ 回归：mov dl,1 不得导致 ecx 被判定为 partial 写",
          operand_write(_FakeIns("mov", "dl, 1"))[0] == "edx",
          "第一版误判成 __IMPLICIT__ ⇒ 7 个站点假红")

    # ---------- 4h. ★★★ classify_source 的假绿形态（异族 probe_c 发现）----------
    #   旧版判据：只要源操作数字符串里出现 `[0x887368]` 就判 GLOBAL。
    #   于是下面这些**根本不是纯赋值**的指令全被判成「ecx == [0x887368]」。
    #   我用真实的 capstone 解码这些字节，再走一遍 classify_source。
    print()
    print("--- 4h. ★★★ classify_source 假绿形态（真实字节解码）---")
    FAKE_GREEN = [
        ("23 0d 68 73 88 00", "and", "ecx = 旧ecx & [..] ≠ [..]"),
        ("0b 0d 68 73 88 00", "or", "ecx = 旧ecx | [..] ≠ [..]"),
        ("03 0d 68 73 88 00", "add", "ecx = 旧ecx + [..] ≠ [..]"),
        ("2b 0d 68 73 88 00", "sub", "ecx = 旧ecx - [..] ≠ [..]"),
        ("0f af 0d 68 73 88 00", "imul", "ecx = 旧ecx × [..] ≠ [..]"),
        ("0f a5 f1", "shld", "ecx 是拼接结果 ≠ esi"),
        ("0f ab c1", "bts", "只置一位 ≠ eax"),
        ("0f c1 f1", "xadd", "交换后相加 ≠ esi"),
        ("0f b7 0d 68 73 88 00", "movzx", "只取低 16 位 ≠ [..] 的 32 位值"),
        ("66 0f b6 0d 68 73 88 00", "movzx", "只取低 8 位 ≠ [..]"),
        ("66 0f be 0d 68 73 88 00", "movsx", "符号扩展 16 位 ≠ [..]"),
    ]
    leaked = []
    for hexb, want_mn, why in FAKE_GREEN:
        raw = bytes.fromhex(hexb)
        ins = next(bn.md.disasm(raw, 0x1000), None)
        if ins is None or ins.mnemonic != want_mn:
            check("  解码 %-22s → %s" % (hexb, want_mn), False,
                  "实际解码 %s" % (ins.mnemonic if ins else "失败"))
            continue
        d, s = operand_write(ins)
        kind, val = classify_source(ins, s) if d == "ecx" else (None, None)
        if kind == "GLOBAL":
            leaked.append((ins.mnemonic, ins.op_str, why))
        print("    %-8s %-32s → %-18s %s"
              % (ins.mnemonic, ins.op_str, "%s/%s" % (kind, val), why))
    check("★★★ 上述 11 种非纯赋值指令**无一**被判为 GLOBAL（否则假绿）",
          len(leaked) == 0,
          "%d 处泄漏 %s" % (len(leaked), leaked[:3]) if leaked else "全部正确拒绝")

    # 正控：真正的纯赋值必须判 GLOBAL（证明上面不是「一律拒绝」的恒真）
    real_ins = next(bn.md.disasm(bytes.fromhex("8b 0d 68 73 88 00"), 0x1000), None)
    d0, s0 = operand_write(real_ins)
    k0, _ = classify_source(real_ins, s0)
    check("★ 正控：mov ecx,[0x887368] 仍判 GLOBAL（拒绝不是恒真）",
          k0 == "GLOBAL", "判为 %s" % k0)

    # ---------- 5. 结论 ----------
    print()
    print("--- 5. 结论 ---")
    print("    命题：每个调用点 ecx == [0x%X]" % SINGLETON)
    print("    证明手段：CFG 后向数据流（分支目标解析 + 寄存器中转追踪）")
    print("    推论：函数头 test ecx,ecx / je 在全局为 0 时于所有调用路径命中")
    print("    ⇒ §393 的 C 类（调用者前置守卫）为多余分类，已弃用")

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
