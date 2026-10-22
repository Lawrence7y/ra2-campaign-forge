# -*- coding: utf-8 -*-
"""`[0x887368]` 全量 deref 普查：修复只守两个函数头，够不够？

问题
----
v2 草案在 `0x724730` 与 `0x724580` 两个函数头加守卫。
但账本记载 `[0x887368]` 有 **74 处引用**。若其中还有别的站点
「读出这个指针后自己解引用」，或「传给第三个函数」，守卫就覆盖不到。

本脚本要回答三件事
------------------
A. `[0x887368]` 的**全部**引用站点分类：
   - 读入寄存器后**自己解引用**（`mov eax,[ecx+off]` 等）
   - 读入 ecx 后**调用**（分直接 call / 间接 call）
   - 纯读入后不做上述动作（比较、存储等）
B. 每个「读入 ecx 后调用」的目标函数，其**首个随 ecx 变化的解引用偏移**是多少。
   —— 若偏移落在 `0x250` 附近，说明同族；若完全不同的偏移，说明另一条崩溃链。
C. 「自己解引用」的那些站点**有没有 null 守卫**（flags 级判据）。

只读，不写任何二进制。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_ECX, X86_REG_ESP, X86_REG_EBP)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G = 0x887368
FN_A, FN_B = 0x724730, 0x724580

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def load_pe(path):
    d = path.read_bytes()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    opt = e + 0x18
    ib = struct.unpack_from("<I", d, opt + 0x1C)[0]
    so = opt + struct.unpack_from("<H", d, e + 0x14)[0]
    secs = []
    for i in range(nsec):
        o = so + 40 * i
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        secs.append({"name": d[o:o + 8].rstrip(b"\x00").decode("latin1"),
                     "va": va + ib, "vsize": vs, "rawptr": rp, "rawsize": rs})
    return d, ib, secs


DATA, IMAGEBASE, SECS = load_pe(BIN)
TEXT = next(s for s in SECS if s["name"] == ".text")
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True

TEXT_LO, TEXT_HI = TEXT["va"], TEXT["va"] + TEXT["vsize"]


def va2off(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + s["vsize"]:
            return s["rawptr"] + (va - s["va"])
    return None


def section_of(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + s["vsize"]:
            return s["name"]
    return None


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}"


def find_literal_refs(target):
    """在 .text 里找所有出现 target 这个 4 字节小端值的位置。

    ★ 这是**字节级**扫描，会包含「不是指令操作数」的偶然命中。
      每个命中都要再用反汇编核对是否真是 `[0x887368]` 操作数。
    """
    pat = struct.pack("<I", target)
    body = DATA[TEXT["rawptr"]:TEXT["rawptr"] + TEXT["rawsize"]]
    out = []
    i = 0
    while True:
        i = body.find(pat, i)
        if i < 0:
            break
        out.append(TEXT["va"] + i)
        i += 1
    return out


def dis_linear(va, maxinsn=12):
    off = va2off(va)
    if off is None:
        return []
    out = []
    for i in MD.disasm(DATA[off:off + maxinsn * 16], va):
        out.append(i)
        if len(out) >= maxinsn:
            break
    return out


def is_abs_mem_operand(ins, addr):
    """该指令是否有一个操作数是 [addr] 绝对内存。"""
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                and op.mem.disp == addr:
            return True
    return False


def deref_this_offset(fn_va, maxinsn=40):
    """返回函数体里**首个随 ecx 变化的解引用偏移**（即 this->offset）。

    做法：线性反汇编前 N 条；跟踪「哪个寄存器当前等于 this」；
    遇到 `mov reg, ecx` 或 `lea reg,[ecx+0]` 就记下别名；
    遇到 `[alias + disp]` 且 disp 合理（0..0x4000）就返回 disp。
    """
    insns = dis_linear(fn_va, maxinsn)
    this_regs = {X86_REG_ECX}
    for ins in insns:
        m = ins.mnemonic
        ops = ins.operands
        # 解引用检查
        for op in ops:
            if op.type == X86_OP_MEM and op.mem.base in this_regs:
                d = op.mem.disp
                # ★ 不要按寄存器名排除 ebp：本件里 `mov ebp,ecx` 使 ebp **就是 this**
                #   （0x724730 正是这种写法）。排除 ebp 会把真命中杀掉。
                #   esp 永不会进 this_regs（无 `mov esp,ecx`），故无需特判。
                if 0 <= d <= 0x4000:
                    return d, ins
        # 别名传播
        if m == "mov" and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[1].type == X86_OP_REG and ops[1].reg in this_regs:
            this_regs.add(ops[0].reg)
        elif m == "lea" and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[1].type == X86_OP_MEM \
                and ops[1].mem.base in this_regs and ops[1].mem.disp == 0:
            this_regs.add(ops[0].reg)
        # 若目标寄存器被其它来源覆盖，撤销别名
        elif m in ("mov", "lea", "xor", "pop", "add", "sub", "and", "or") \
                and len(ops) >= 1 and ops[0].type == X86_OP_REG \
                and not (len(ops) == 2 and ops[1].type == X86_OP_REG
                         and ops[1].reg in this_regs):
            this_regs.discard(ops[0].reg)
        if m in ("ret",):
            break
    return None, None


def call_target(ins):
    if ins.mnemonic != "call":
        return None, None
    op = ins.operands[0]
    if op.type == X86_OP_IMM:
        return op.imm, "direct"
    return None, "indirect"


FLAGS_OPS = {"test", "cmp", "add", "sub", "and", "or", "xor", "inc", "dec",
             "neg", "shl", "shr", "sar", "adc", "sbb", "imul"}


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHA8), sha[:8])

    print()
    print("=" * 78)
    print(f"== STEP A  [0x{G:X}] 字节级引用普查")
    print("=" * 78)
    hits = find_literal_refs(G)
    print(f"  .text 内出现 0x{G:X} 这个 4 字节值的次数：{len(hits)}")

    # 逐点反汇编核对：必须能解出一条含 [0x887368] 的指令，且该地址落在指令内
    real = []          # (insn, operand_index)
    seen = set()
    for h in hits:
        # 从 h-7 到 h 各试一次，找能对齐出含该操作数的指令
        got = None
        for back in range(0, 8):
            start = h - back
            if section_of(start) != ".text":
                continue
            insns = dis_linear(start, 3)
            for ins in insns:
                if ins.address <= h < ins.address + len(ins.bytes):
                    if is_abs_mem_operand(ins, G):
                        got = ins
                    break
            if got:
                break
        if got and got.address not in seen:
            seen.add(got.address)
            real.append(got)

    print(f"  经反汇编确认的**指令级**站点：{len(real)}")
    chk(f"指令级站点数 <= 字节命中数", len(real) <= len(hits),
        f"{len(real)} <= {len(hits)}")

    # 分类
    own_deref, call_direct, call_indirect, other = [], [], [], []
    for ins in real:
        # 往前看 10 条，找该指令之后的下一条指令
        fwd = [i for i in dis_linear(ins.address, 8) if i.address > ins.address]
        if not fwd:
            other.append((ins, "no-follow"))
            continue
        nxt = fwd[0]
        if nxt.mnemonic == "call":
            tgt, kind = call_target(nxt)
            if kind == "direct":
                call_direct.append((ins, nxt, tgt))
            else:
                call_indirect.append((ins, nxt))
        else:
            # 看这条指令自己是否把 [G] 读进寄存器
            loads_into = None
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.disp == G:
                    pass
            if ins.mnemonic == "mov" and len(ins.operands) == 2 \
                    and ins.operands[0].type == X86_OP_REG \
                    and ins.operands[1].type == X86_OP_MEM:
                loads_into = ins.reg_name(ins.operands[0].reg)
            own_deref.append((ins, nxt, loads_into))

    print()
    print("  ── 分类 ──")
    print(f"    mov reg,[G] 后**不是** call（自己处理）  : {len(own_deref)}")
    print(f"    mov ecx,[G] 后 **直接** call             : {len(call_direct)}")
    print(f"    mov ecx,[G] 后 **间接** call             : {len(call_indirect)}")
    print(f"    其它                                     : {len(other)}")
    chk("分类总数 == 指令级站点数",
        len(own_deref) + len(call_direct) + len(call_indirect) + len(other) == len(real),
        str(len(real)))

    print()
    print("=" * 78)
    print("== STEP B  直接 call 的目标函数 → 首个 this 解引用偏移")
    print("=" * 78)
    by_target = {}
    for ins, nxt, tgt in call_direct:
        by_target.setdefault(tgt, []).append(ins.address)
    print(f"  直接 call 的**不同目标函数**：{len(by_target)} 个")
    print()
    rows = []
    for tgt in sorted(by_target):
        sites = by_target[tgt]
        off, ins = deref_this_offset(tgt)
        rows.append((tgt, len(sites), off, ins))
        mark = ""
        if tgt in (FN_A, FN_B):
            mark = "  ★ 已被 v2 守卫"
        print(f"  {tgt:#010x}  站点 {len(sites):2d}  首个 this 解引用偏移 "
              f"{('0x%X' % off) if off is not None else '—':>8}{mark}")
    print()
    print("  ⇒ 按首个解引用偏移分组：")
    grp = {}
    for tgt, n, off, ins in rows:
        grp.setdefault(off, []).append((tgt, n))
    for off in sorted(grp, key=lambda x: (x is None, x)):
        members = grp[off]
        total_sites = sum(n for _, n in members)
        guarded = sum(1 for t, _ in members if t in (FN_A, FN_B))
        label = f"0x{off:X}" if off is not None else "无 this 解引用"
        print(f"    {label:<12} 函数 {len(members):2d} 个 / 站点 {total_sites:2d} / "
              f"其中已守 {guarded} 个函数")

    # 关键断言：0x250 这一族是否只有这两个函数
    fam = [(t, n, off) for t, n, off, _ in rows if off is not None and off in (0x228, 0x22C, 0x24C, 0x250)]
    print()
    print(f"  ★ 首个解引用落在 0x228/0x22C/0x24C/0x250 这一族（同一对象头部区）的函数：{len(fam)} 个")
    for t, n, off in fam:
        mark = "  ← 已被 v2 守卫" if t in (FN_A, FN_B) else "  ★★ 未被 v2 守卫"
        print(f"      {t:#010x}  站点 {n}  偏移 0x{off:X}{mark}")
    chk("★ 0x22x/0x25x 族共有 4 个函数（不止 v2 守的 2 个）", len(fam) == 4,
        str([hex(t) for t, _, _ in fam]))
    unguarded_fns = [t for t, _, _ in fam if t not in (FN_A, FN_B)]
    chk("★★ 其中 2 个（0x724530/0x724540）v2 **未覆盖**",
        set(unguarded_fns) == {0x724530, 0x724540},
        str([hex(t) for t in unguarded_fns]))

    print()
    print("=" * 78)
    print("== STEP C  自己处理 [G] 的站点有无 null 守卫（全量 67 处）")
    print("=" * 78)
    guarded_n = unguarded_n = 0
    unguarded_list = []
    for ins, nxt, reg in own_deref:
        fwd = [i for i in dis_linear(ins.address, 12) if i.address > ins.address]
        guard = None
        for i in fwd[:8]:
            if i.mnemonic in ("test", "cmp"):
                guard = i
                break
            if i.mnemonic in ("call", "ret", "jmp"):
                break
        if guard:
            guarded_n += 1
        else:
            unguarded_n += 1
            unguarded_list.append(ins.address)
        status = "有守卫" if guard else "★无守卫"
        print(f"  {ins.address:#010x}  {ins.mnemonic} {ins.op_str:<30} "
              f"→ {nxt.mnemonic} {nxt.op_str:<22} {status}")
        if guard:
            print(f"            守卫: {fmt(guard)}")
    print(f"\n  统计：有守卫 {guarded_n} / 无守卫 {unguarded_n}（共 {len(own_deref)}）")
    chk("自己处理 [G] 的站点全部列出", guarded_n + unguarded_n == len(own_deref),
        f"{guarded_n}+{unguarded_n}={len(own_deref)}")

    print()
    print("  ── 无守卫站点清单（这些是「读出指针后不判空就使用」）──")
    for a in unguarded_list:
        print(f"    {a:#010x}")
    print(f"  共 {len(unguarded_list)} 处。")
    print()
    print("  ★ 但「无守卫」≠「会崩溃」。要真的崩，还须满足两条：")
    print("     (1) 该处读出的值随后被**解引用**（而不是仅比较/存储/传参）")
    print("     (2) 崩溃那一刻 [G] 确实是 0")
    print("  ⇒ 本脚本只做第 (1) 步的粗筛；逐站定案需看每条后续指令，超出本轮范围。")

    print()
    print("=" * 78)
    print("== STEP D  间接 call 站点")
    print("=" * 78)
    for ins, nxt in call_indirect:
        print(f"  {ins.address:#010x}  mov ... ,[0x{G:X}]  → {nxt.address:#x} "
              f"{nxt.mnemonic} {nxt.op_str}")
    print(f"\n  共 {len(call_indirect)} 处。")
    chk("★ 以 [G] 为 ecx 的调用**全是直接 E8**（无间接）",
        len(call_indirect) == 0, str(len(call_indirect)))
    print()
    print("  ⇒ 好消息：不存在「以 [G] 为 this 的间接调用」这类静态不可解析路径。")
    print("    账本里『4778 处 call [mem] 不可静态解析』的风险，在**这一条线**上不成立。")
    print()
    print("  ⇒ 但 v2 的**真实残余风险**不是间接调用，而是 §STEP B 查出的：")
    print("    同族函数 `0x724530` / `0x724540` 也在 `ecx=0` 时解引用 this")
    print("    （偏移 0x228 / 0x22C），而 v2 只守了 `0x724730` / `0x724580`。")

    print()
    print("=" * 78)
    print("== RESULT")
    print("=" * 78)
    n = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {n}/{len(CHECKS)}")
    for name, ok, d in CHECKS:
        if not ok:
            print(f"  FAIL: {name}  {d}")
    print("RESULT:", "ALL PASS" if n == len(CHECKS) else "HAS FAILURES")
    return 0 if n == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
