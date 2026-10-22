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
    """返回 (写入的寄存器名 or None, 源操作数字符串 or None)。"""
    m = ins.mnemonic
    if m not in WRITE_MNEM:
        return None, None
    parts = [p.strip() for p in ins.op_str.split(",")]
    if not parts:
        return None, None
    dst = parts[0]
    if dst not in GPR:
        return None, None
    src = parts[1] if len(parts) > 1 else None
    return dst, src


def classify_source(ins, src):
    """把一次写入的源定性。返回 ('GLOBAL',None) / ('ZERO',None) /
    ('REG',reg) / ('UNKNOWN',reason)。"""
    m = ins.mnemonic
    if src is None:
        # pop / inc / dec / neg 之类：读旧值
        return "UNKNOWN", "read-modify-write"
    s = src.strip()
    # ★ 条件写（cmov）：条件不成立时 ecx 保留旧值 ⇒ 不能当作无条件赋值，
    #   必须回到更上游继续追。判 GLOBAL 会让「ecx==[0x887368]」变成错误命题。
    if m.startswith("cmov"):
        return "UNKNOWN", "conditional-write"
    if m in ("xor", "sub") and s == ins.op_str.split(",")[0].strip():
        return "ZERO", None
    if m == "and" and s == "0":
        return "ZERO", None
    if m == "mov" and s in GPR:
        return "REG", s
    # ★ lea 取的是**地址**不是内容 —— `lea ecx,[0x887368]` 得到的是非零地址，
    #   绝不能算作 GLOBAL（算作 GLOBAL 会让「ecx==0 时守卫命中」的推论失效）。
    if m == "lea":
        return "UNKNOWN", "lea-address-not-load"
    if "[0x%x]" % SINGLETON in s.lower() or "[0x%08x]" % SINGLETON in s.lower():
        return "GLOBAL", None
    if s in GPR:
        return "REG", s
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
            # 字符串指令隐含读写 ecx（rep 前缀的计数寄存器）
            if m.split()[0] in ("rep", "repe", "repne") or \
               m in ("movs", "stos", "lods", "scas", "cmps") or \
               m.split(" ")[0] in ("movsd", "stosd", "lodsd", "scasd", "cmpsd"):
                ends["strop"] += 1
                sources.add(("UNKNOWN", "string-op-clobbers-ecx@0x%X" % p))
                seen.add((p, reg))
                continue
            dst, src = operand_write(pi)
            if dst == reg:
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
