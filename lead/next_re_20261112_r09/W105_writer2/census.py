# -*- coding: utf-8 -*-
r"""
W105_writer2 census —— CellClass 链头 (+0xE4 / +0xE8) 读写点普查
================================================================
修正 W99 的两个方法缺陷:
  (1) W99 在原始字节流里搜 "SIB 形式 + disp32==0xE4" 的字节模式, 命中的几乎全是
      [esp+0xE4] 栈访问 (栈偏移与 CellClass+0xE4 无关), 整批假阳性。
      => 本脚本用 capstone 线性扫描按真实指令边界解码, 在【解码出的操作数文本】
         上匹配 disp, 而不是在原始字节里搜模式。
  (2) W99 只扫了 SIB 形式编码。=> 本脚本对每条命中手工解 modrm/SIB 位,
      同时覆盖 modrm-disp32 (例 89 B1 E4 00 00 00 = mov [ecx+0xE4], esi) 与
      SIB (例 89 A4 24 E4 00 00 00 = mov [esp+0xE4], esi) 两种形式并分别计数。
      disp8 形式 (0xE4 => -0x1C, 0xE8 => -0x18, 符号扩展为负偏移) 语义上不是
      +0xE4/+0xE8, 不会被匹配。

判定口径:
  A 类(真目标·写): mem 操作数 disp==0xE4/0xE8, base 非空且非 ESP/EBP, 该操作数为写。
  B 类(读):        同口径但为读 (含 lea, 标注"取址")。
  C 类(假阳性计数): disp==0xE4/0xE8 且 base∈{esp,ebp} 的写/读命中数;
                   另计 base 为空 (disp32 绝对地址 0xE4/0xE8) 的命中数。

函数边界: 线性扫描收集全部解码指令; 函数起点 = .text 起点 + 每个 ret/retf 之后
  (其间字节全为 0x90/0xCC 填充, 允许 0 字节) 的下一条已解码指令地址。
  命中向上找最近函数起点; 若 [函数起点, 命中) 区间内有解码 gap (无效编码逐字节
  跳过产生), 函数归属标 "边界未定" (不静默跳过)。

环境: capstone 5.0.7 (lite 绑定, 无 insn.detail, 故用 op_str 解析操作数 +
  regs_access 交叉验证 + 手工解 modrm/SIB)。输出 EVIDENCE\census.txt (UTF-8)。
只读 gamemd.exe; 不启动游戏 / 不注入 / 不附加调试器 / 不写 ra2youli\ 任何文件。
"""

import bisect
import re
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = (r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09"
       r"\W105_writer2\EVIDENCE\census.txt")

IMAGE_BASE = 0x400000
TARGET_DISPS = (0xE4, 0xE8)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# ---- 指令方向表 (mem 操作数在 op_str 逗号前 => dst; 在后 => src) ----
WRITE_DST = {"mov", "add", "sub", "and", "or", "xor", "adc", "sbb", "inc",
             "dec", "neg", "not", "shl", "shr", "sar", "rol", "ror", "rcl",
             "rcr", "pop", "xadd", "cmpxchg", "bswap", "setne", "sete",
             "seta", "setb", "setg", "setl", "setle", "setge", "sets",
             "setns", "movzx", "movsx",
             # FPU/状态寄存器存储类: 向内存写
             "fstp", "fst", "fistp", "fist", "fisttp",
             "fnstcw", "fnstsw", "fnstenv", "fnsave"}
READ_BOTH = {"cmp", "test"}
READ_ONLY = {"push", "call", "jmp", "lea",   # lea 特殊: 取址, 非内存读
             "fld", "fild", "fldcw", "fldenv", "frstor"}
PURE_WRITE = {"mov", "pop"}                  # dst 纯写 (非 RMW)
RMW = {"add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec", "neg",
       "not", "shl", "shr", "sar", "rol", "ror", "rcl", "rcr", "xadd",
       "cmpxchg"}

PREFIXES = {0x66, 0x67, 0xF2, 0xF3, 0xF0, 0x2E, 0x3E, 0x26, 0x36, 0x64, 0x65}

MEM_RE = re.compile(r"\[([^\]]*)\]")
HEX_RE = re.compile(r"^0x[0-9a-fA-F]+$")


def parse_mem(content):
    """解析 capstone Intel 语法括号内容 -> (base, index, scale, disp)。
    返回 disp 为有符号 int; 解析失败返回 None。"""
    base = index = None
    scale = 1
    disp = 0
    content = re.sub(r"\s*-\s*", " + -", content)  # capstone 负偏移写作 " - 0x14"
    for tok in re.split(r"\s*\+\s*", content.strip()):
        tok = tok.strip()
        neg = False
        if tok.startswith("-"):
            neg = True
            tok = tok[1:].strip()
        if "*" in tok:
            r, s = tok.split("*")
            index = r.strip()
            scale = int(s.strip(), 0)
        elif HEX_RE.match(tok):
            v = int(tok, 16)
            disp += -v if neg else v
        else:
            if base is None:
                base = tok
            else:
                index = tok
    return base, index, scale, disp


def opcode_modrm_pos(raw):
    """返回 modrm 字节在指令内的下标; 无 modrm 返回 None。"""
    i = 0
    while i < len(raw) and raw[i] in PREFIXES:
        i += 1
    if i >= len(raw):
        return None
    if raw[i] == 0x0F:
        i += 2
    else:
        i += 1
    return i if i < len(raw) else None


def sib_present(raw):
    p = opcode_modrm_pos(raw)
    if p is None:
        return False
    modrm = raw[p]
    return (modrm & 0x07) == 0x04 and (modrm >> 6) != 3   # rm==100 且 mod!=11


def load_text():
    pe = pefile.PE(EXE, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    assert ib == IMAGE_BASE, "ImageBase 与底座不符: 0x%X" % ib
    for s in pe.sections:
        if s.Name.rstrip(b"\x00") == b".text":
            return s.get_data(), ib + s.VirtualAddress
    raise RuntimeError(".text 未找到")


def sweep(data, base_va):
    """线性扫描: 逐条解码, 无效编码则前进 1 字节并记 gap。"""
    insns, gaps = [], []
    i, n, va, gap_start = 0, len(data), base_va, None
    while i < n:
        try:
            insn = next(md.disasm(data[i:i + 16], va, count=1))
        except StopIteration:
            if gap_start is None:
                gap_start = va
            i += 1
            va += 1
            continue
        if gap_start is not None:
            gaps.append((gap_start, va))
            gap_start = None
        insns.append((va, insn.size, bytes(insn.bytes), insn.mnemonic,
                      insn.op_str))
        i += insn.size
        va += insn.size
    if gap_start is not None:
        gaps.append((gap_start, va))
    return insns, gaps


def find_function_starts(insns, base_va, data, va0):
    starts = [base_va]
    for idx in range(len(insns) - 1):
        va, size, raw, mnem, ops = insns[idx]
        if mnem not in ("ret", "retf"):
            continue
        nxt = insns[idx + 1]
        if nxt[0] == va + size:
            starts.append(nxt[0])
        else:
            off = va + size - va0
            pad = data[off:off + (nxt[0] - (va + size))]
            if all(b in (0x90, 0xCC) for b in pad):
                starts.append(nxt[0])
    return sorted(set(starts))


def gaps_bytes(gaps, lo, hi):
    total = 0
    for g0, g1 in gaps:
        a, b = max(g0, lo), min(g1, hi)
        if b > a:
            total += b - a
    return total


def fb(raw):
    return " ".join("%02x" % b for b in raw)


def main():
    data, va0 = load_text()
    L = []
    out = L.append

    out("=== W105 census: gamemd.exe .text 中 disp==0xE4/0xE8 内存操作数普查 ===")
    out("产出命令: python census.py   (本文件即其完整 stdout)")
    out("输入: %s  (.text @ 0x%08X, %d 字节)" % (EXE, va0, len(data)))
    out("口径: 按指令边界解码后匹配 mem.disp∈{0xE4,0xE8}; base∈{esp,ebp} 计入 C 类;")
    out("      base 空 (disp32 绝对地址) 单独计数; disp8 负偏移不匹配。")

    insns, gaps = sweep(data, va0)
    out("")
    out("== 扫描统计 ==")
    out("解码指令总数: %d" % len(insns))
    out("无效编码 gap 区段数: %d, 覆盖字节: %d"
        % (len(gaps), sum(g1 - g0 for g0, g1 in gaps)))

    fstarts = find_function_starts(insns, va0, data, va0)
    out("函数起点锚 (ret/retf + 0x90/0xCC 填充切分): %d 个" % len(fstarts))

    def func_of(va):
        k = bisect.bisect_right(fstarts, va) - 1
        return fstarts[k] if k >= 0 else None

    # ---- 自检 (对照 LEAD_FINDINGS_R09 L1) ----
    out("")
    out("== 自检 (对照 LEAD_FINDINGS_R09 L1) ==")
    by_va = {t[0]: t for t in insns}
    for va, expect in ((0x47C52A, "mov esi, [ecx+0xE4]"),
                       (0x47C4E3, "mov esi, [ecx+0xE8]"),
                       (0x47C538, "call [eax+0x2C]")):
        t = by_va.get(va)
        if t is None:
            out("自检 0x%08X: 未解码出指令 -> FAIL" % va)
        else:
            ok = expect.split()[0] == t[3] and ("0xe4" in t[4] or "0x2c" in t[4]
                                                or "0xe8" in t[4])
            out("自检 0x%08X: %-6s %-24s [%s] -> %s"
                % (va, t[3], t[4], fb(t[2]), "PASS" if ok else "FAIL"))

    A, B = [], []
    Cw = Cr = Cabs = 0
    idx_of = {t[0]: i for i, t in enumerate(insns)}

    for i, (va, size, raw, mnem, ops) in enumerate(insns):
        for m in MEM_RE.finditer(ops):
            base, index, scale, disp = parse_mem(m.group(1))
            if disp not in TARGET_DISPS:
                continue
            # 写/读判定: mem 在逗号前 => dst
            before_comma = ops.find(",") == -1 or m.start() < ops.find(",")
            if mnem in READ_BOTH:
                is_write = False          # cmp/test 两读
            elif mnem in READ_ONLY:
                is_write = False          # push/call/jmp/lea 读
            elif mnem in WRITE_DST and before_comma:
                is_write = True
            else:
                is_write = False
            if base in ("esp", "ebp"):
                if is_write:
                    Cw += 1
                else:
                    Cr += 1
                continue
            if base is None:
                Cabs += 1
                continue
            rec = dict(va=va, raw=raw, mnem=mnem, ops=ops, base=base,
                       index=index or "-", scale=scale,
                       form="SIB" if sib_present(raw) else "modrm-disp32",
                       is_write=is_write, is_lea=(mnem == "lea"),
                       before_comma=before_comma)
            f = func_of(va)
            if f is None:
                rec["func"], rec["quality"] = "无锚", "LOW"
            else:
                gb = gaps_bytes(gaps, f, va)
                rec["func"] = f
                rec["quality"] = "HIGH" if gb == 0 else \
                    "边界未定(gap %dB in [func,hit))" % gb
            if is_write:
                # 写值种类
                if mnem in ("fstp", "fst", "fistp", "fist", "fisttp"):
                    rec["store"] = "FPU存储(浮点值)"
                elif mnem.startswith("fnst") or mnem == "fnsave":
                    rec["store"] = "状态寄存器存储"
                elif mnem in RMW:
                    rec["store"] = "RMW"
                elif "," in ops:
                    src = ops.split(",", 1)[1].strip()
                    if src.startswith("["):
                        rec["store"] = "内存拷贝"
                    else:
                        try:
                            v = int(src, 0)
                        except ValueError:
                            v = None
                        if v is None:
                            rec["store"] = "寄存器值"
                        else:
                            if v < 0:
                                v &= 0xFFFFFFFF
                            rec["store"] = ("置零(imm=0)" if v == 0
                                            else "立即数(0x%X)" % v)
                else:
                    rec["store"] = "RMW"
                if ops.startswith("byte ptr"):
                    rec["width"] = "byte"
                elif ops.startswith("word ptr"):
                    rec["width"] = "word"
                else:
                    rec["width"] = "dword"
                A.append(rec)
            else:
                B.append(rec)

    def zeroed_by_xor(rec):
        """mov [b+disp], reg 且 reg 由最近 3 条内 xor r,r 置零"""
        if rec["store"] != "寄存器值":
            return False
        i = idx_of[rec["va"]]
        src = rec["ops"].split(",", 1)[1].strip()
        for j in range(max(0, i - 3), i):
            pva, ps, praw, pm, po = insns[j]
            if pm == "xor" and po == "%s, %s" % (src, src):
                return True
        return False

    # ---- Lead 补丁判据 (不改方法, 只加判读) ----
    RD_LO, RD_HI = 0x7E1000, 0x812000   # Lead L2 的 .rdata 游程范围

    def vptr_install_near(i, base):
        """±20 条内出现 mov dword [同base+0], imm32∈.rdata => 正在装虚表"""
        for j in range(max(0, i - 20), min(len(insns), i + 21)):
            pva, ps, praw, pm, po = insns[j]
            if pm != "mov" or "," not in po or not po.startswith("dword ptr ["):
                continue
            dst, src = po.split(",", 1)
            src = src.strip()
            if not HEX_RE.match(src):
                continue
            m2 = MEM_RE.search(dst)
            if not m2:
                continue
            b2, _ix, _sc, d2 = parse_mem(m2.group(1))
            if b2 == base and d2 == 0 and RD_LO <= int(src, 16) <= RD_HI:
                return (pva, po)
        return None

    def guarded_by_cmp(i, base, disp):
        """前 2 条内 cmp [同base+同disp], X => 条件写 (仅当字段==X 才落 store)"""
        for j in range(max(0, i - 2), i):
            pva, ps, praw, pm, po = insns[j]
            if pm != "cmp":
                continue
            for m2 in MEM_RE.finditer(po):
                b2, _ix, _sc, d2 = parse_mem(m2.group(1))
                if b2 == base and d2 == disp:
                    return (pva, po)
        return None

    def loads_from_next(i, srcreg):
        """前 3 条内 mov <srcreg>, [x+0x30] => 链头←next 摘头形态"""
        for j in range(max(0, i - 3), i):
            pva, ps, praw, pm, po = insns[j]
            if pm != "mov" or "," not in po:
                continue
            dst, src = po.split(",", 1)
            if dst.strip() != srcreg:
                continue
            m2 = MEM_RE.search(src)
            if m2:
                b2, _ix, _sc, d2 = parse_mem(m2.group(1))
                if b2 and d2 == 0x30:
                    return (pva, po)
        return None

    AEX = []
    for r in A:
        i = idx_of[r["va"]]
        src = r["ops"].split(",", 1)[1].strip() if "," in r["ops"] else ""
        r["vptr"] = vptr_install_near(i, r["base"])
        r["guard"] = guarded_by_cmp(i, r["base"],
                                    0xE4 if "0xe4" in r["ops"] else 0xE8)
        r["next"] = loads_from_next(i, src) if src and not HEX_RE.match(src) \
            else None
        if r["vptr"]:
            AEX.append(r)

    def judge_of(r):
        if r["vptr"]:
            j = "A-excluded: 他类构造/初始化 (±20条内 mov [同base+0], .rdata imm32 @0x%08X)" % r["vptr"][0]
            return j
        s = r["store"]
        if r["next"]:
            return "unlink-head候选: 链头←自身next(+0x30), 不比较this [%s <- %s @0x%08X]" \
                % (r["ops"].split(",", 1)[1].strip(), r["next"][1], r["next"][0])
        if s == "置零(imm=0)":
            if r["guard"]:
                return "条件置空: imm=0, 前有cmp[同字段]守卫 (@0x%08X)" % r["guard"][0]
            return "置空: imm=0, 指令级无条件 (上下文分支另见±2条)"
        if zeroed_by_xor(r):
            if r["guard"]:
                return "条件置空: xor置零后写入, 前有cmp[同字段]守卫 (@0x%08X)" % r["guard"][0]
            return "置空: xor置零后写入, 指令级无条件 (上下文分支另见±2条)"
        if s == "FPU存储(浮点值)":
            return "其它: 浮点字段写 (非指针形态)"
        if s == "状态寄存器存储":
            return "其它: 状态寄存器存储 (非指针形态)"
        if r["guard"]:
            return "条件写: 前有cmp[同字段]守卫 (@0x%08X); %s" % (r["guard"][0], s)
        if s == "寄存器值":
            return "link候选: 寄存器(指针)写入链头字段 (守卫未见cmp[同字段])"
        if s.startswith("立即数"):
            return "其它: 非零立即数写入 (非指针形态)"
        if s == "内存拷贝":
            return "其它: 链头被另一内存值替换"
        return "其它: 读改写 (%s)" % r["mnem"]

    out("")
    out("== 汇总 ==")
    out("A 类 (写 [base+0xE4/0xE8], base 非 esp/ebp): %d 条" % len(A))
    a_sib = sum(1 for r in A if r["form"] == "SIB")
    out("    编码形式: SIB=%d, modrm-disp32=%d" % (a_sib, len(A) - a_sib))
    a_high = sum(1 for r in A if r["quality"] == "HIGH")
    out("    函数边界可信: HIGH=%d, 边界未定=%d" % (a_high, len(A) - a_high))
    out("B 类 (读 [base+0xE4/0xE8], base 非 esp/ebp): %d 条" % len(B))
    b_sib = sum(1 for r in B if r["form"] == "SIB")
    out("    编码形式: SIB=%d, modrm-disp32=%d" % (b_sib, len(B) - b_sib))
    out("C 类 (假阳性, base=esp/ebp): 写命中=%d, 读命中=%d" % (Cw, Cr))
    out("    另: base 空 (disp32 绝对地址 0xE4/0xE8): %d" % Cabs)

    out("")
    out("== A 类明细 (VA | 字节 | 反汇编 | func | 编码 | 宽 | 写值 | 判读; 附±2条上下文) ==")
    for r in A:
        judge = judge_of(r)
        if r["index"] != "-":
            judge += "; 注意:变址[%s*%d], 可能不是对象字段" % (r["index"], r["scale"])
        out("0x%08X  %-20s %s %s | func=0x%08X(%s) | %s | 宽=%s | 写值=%s | %s"
            % (r["va"], fb(r["raw"]), r["mnem"], r["ops"], r["func"],
               r["quality"], r["form"], r["width"], r["store"], judge))
        i = idx_of[r["va"]]
        for j in range(max(0, i - 2), min(len(insns), i + 3)):
            pva, ps, praw, pm, po = insns[j]
            out("    %s 0x%08X  %-16s %s %s"
                % (">>" if pva == r["va"] else "  ", pva, fb(praw), pm, po))

    out("")
    out("== A-excluded 节 (±20 条内出现 mov [同base+0], .rdata imm32 => 他类构造/初始化) ==")
    out("计数: %d 条 (这些写点的 base 对象在装虚表, 是普通类的构造, 非 cell 链头操作)" % len(AEX))
    for r in AEX:
        out("0x%08X  %-20s %s %s | func=0x%08X | 依据: 0x%08X: %s"
            % (r["va"], fb(r["raw"]), r["mnem"], r["ops"], r["func"],
               r["vptr"][0], r["vptr"][1]))
    out("A 类剔除后真候选 (可能为 cell 链头写的): %d 条" % (len(A) - len(AEX)))

    out("")
    out("== B 类明细 ==")
    for r in B:
        tag = "取址(非内存读)" if r["is_lea"] else "读"
        out("0x%08X  %-20s %s %s | func=0x%08X(%s) | %s | base=%s | %s"
            % (r["va"], fb(r["raw"]), r["mnem"], r["ops"], r["func"],
               r["quality"], r["form"], r["base"], tag))

    out("")
    out("== C 类 (esp/ebp 基址 = 栈访问, 与 CellClass 字段无关; 前 20 条示例) ==")
    shown = 0
    for va, size, raw, mnem, ops in insns:
        if shown >= 20:
            break
        for m in MEM_RE.finditer(ops):
            base, _i, _s, disp = parse_mem(m.group(1))
            if disp in TARGET_DISPS and base in ("esp", "ebp"):
                out("例: 0x%08X  %-18s %s %s" % (va, fb(raw), mnem, ops))
                shown += 1
                break
    out("(仅示例, 计数见汇总)")

    out("")
    out("== 补充 (仅服务 UAF 判定): 写 [base+0x30] (节点 next 指针) ==")
    out("口径: dword 写, base 非 esp/ebp, disp==0x30。中间节点摘链必然要写")
    out("某个节点的 +0x30; 若这类写点在链族函数附近缺席, 支持 '摧毁后未摘链'。")
    out("+0x30 是常见偏移, 全 .text 的命中含大量无关结构, 故仅列出:")
    out("  (a) 计数; (b) 落在已知链族邻域 func∈[0x47B000,0x480000) 的;")
    out("  (c) 落在含 A 类命中函数里的。")
    sup_all, sup_chain, sup_afunc = 0, [], []
    a_funcs = set(r["func"] for r in A if isinstance(r["func"], int))
    for i, (va, size, raw, mnem, ops) in enumerate(insns):
        if not ops.startswith("dword") or mnem not in WRITE_DST or mnem in READ_BOTH:
            continue
        for m in MEM_RE.finditer(ops):
            base, _ix, _sc, disp = parse_mem(m.group(1))
            if disp != 0x30 or base in ("esp", "ebp", None):
                continue
            if ops.find(",") != -1 and m.start() > ops.find(","):
                continue                       # src 侧, 非写
            sup_all += 1
            f = func_of(va)
            if f is not None and 0x47B000 <= f < 0x480000:
                sup_chain.append((va, raw, mnem, ops, f))
            if f in a_funcs:
                sup_afunc.append((va, raw, mnem, ops, f))
            break
    out("写 [base+0x30] (dword, base 非 esp/ebp) 全 .text 计数: %d" % sup_all)
    out("  其中 func∈[0x47B000,0x480000) (链族邻域): %d 条:" % len(sup_chain))
    for va, raw, mnem, ops, f in sup_chain:
        out("    0x%08X  %-18s %s %s | func=0x%08X" % (va, fb(raw), mnem, ops, f))
    out("  其中 func 含 A 类命中: %d 条:" % len(sup_afunc))
    for va, raw, mnem, ops, f in sup_afunc:
        out("    0x%08X  %-18s %s %s | func=0x%08X" % (va, fb(raw), mnem, ops, f))

    out("")
    out("== gap / 边界未定说明 ==")
    out("gap = 线性扫描遇到无效编码时逐字节跳过的区间, gap 内字节未被解码。")
    out("某命中的 [func, hit) 区间含 gap 时, 其函数归属标 边界未定; 该命中本身的")
    out("指令边界仍有效 (它是一次成功解码)。gap 区间清单位于 gap_addr_list 节。")

    out("")
    out("== gap 区间清单 (前 60 条) ==")
    for g0, g1 in gaps[:60]:
        out("0x%08X - 0x%08X (%d B)" % (g0, g1, g1 - g0))
    if len(gaps) > 60:
        out("... 其余 %d 条见汇总计数" % (len(gaps) - 60))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("written:", OUT)
    print("A=%d B=%d Cw=%d Cr=%d Cabs=%d insns=%d gaps=%d fstarts=%d AEX=%d"
          % (len(A), len(B), Cw, Cr, Cabs, len(insns), len(gaps), len(fstarts),
             len(AEX)))
    for r in A:
        print("A 0x%08X [%s] %s %s | func=0x%08X | %s | %s | %s"
              % (r["va"], fb(r["raw"]), r["mnem"], r["ops"], r["func"],
                 r["form"], r["width"], r["store"]))
    for r in B:
        print("B 0x%08X [%s] %s %s | func=0x%08X | %s | base=%s%s"
              % (r["va"], fb(r["raw"]), r["mnem"], r["ops"], r["func"],
                 r["form"], r["base"],
                 " LEA" if r["is_lea"] else ""))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
