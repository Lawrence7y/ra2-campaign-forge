# -*- coding: utf-8 -*-
"""`[0x887368]` deref 普查 v2：修正「紧接 call」判据错误后的完整清单

v1（`_g_deref_census.py`）的方法学错误
--------------------------------------
v1 的判据是「`mov ecx,[0x887368]` 的**下一条指令**是 call」。
这条判据把 **67 处**归进了「自己处理」，只留下 7 处「直接 call」。

**但真实的崩溃点 `0x654405` 恰恰不在那 7 处里**：

    00654405  mov ecx, [0x887368]
    0065440B  mov [esp+0x18], edx      ← 寄存器 spill，不影响 ecx
    0065440F  mov [esp+0x1c], eax      ← 寄存器 spill，不影响 ecx
    00654413  call 0x724730            ← ★ 崩溃就在这里

⇒ 正确判据必须是「**从 mov 起向前走，跟踪 ecx 是否仍然存活，直到遇到 call**」，
  而不是「下一条就是 call」。v1 的 7 处清单**漏掉了实际崩溃点**。

★ 这个错误由异族核验员在复核 v3 时指出（`VERIFY_V3_VERDICT.md` 不符项 B）。

本脚本（v2）
------------
1. 字节级找出 `[0x887368]` 的全部引用点，反汇编核对为真指令操作数。
2. 对每个站点：若载入目标是 ecx，则**向前走**直到：
   - 遇到 call（此时 ecx 若仍存活 ⇒ 该 call 就是「以 [G] 为 this 的调用」）
   - 遇到 ret / jmp（该站点不以 call 收尾）
   - ecx 被别的来源覆盖（该站点不是「把 [G] 当 this」）
3. 对每个被调函数，求**首个随 this 变化的内存访问偏移**（区分 lea 与真访问）。
4. 统计每个调用点的守卫情况（flags 级）。
5. 报告间接调用站点。

只读，不写任何二进制。
"""
import collections
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G = 0x887368

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

# ★ skipdata=True：不设置时 capstone 会在 0x46F59D 停下，
#   只反汇编约 15.5 万条指令，且**不报错**（核验员实测）。
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def va2off(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + s["vsize"]:
            return s["rawptr"] + (va - s["va"])
    return None


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}"


def dec(va, n=16):
    off = va2off(va)
    if off is None:
        return []
    out = []
    for i in MD.disasm(DATA[off:off + n * 16], va):
        out.append(i)
        if len(out) >= n:
            break
    return out


def is_G_mem(op):
    return (op.type == X86_OP_MEM and op.mem.base == 0
            and op.mem.index == 0 and op.mem.disp == G)


def find_G_sites():
    """字节级找 [0x887368] 引用，再用反汇编核对为真指令操作数。"""
    pat = struct.pack("<I", G)
    body = DATA[TEXT["rawptr"]:TEXT["rawptr"] + TEXT["rawsize"]]
    byte_hits = []
    i = 0
    while True:
        i = body.find(pat, i)
        if i < 0:
            break
        byte_hits.append(TEXT["va"] + i)
        i += 1
    sites, seen = [], set()
    for h in byte_hits:
        for back in range(0, 8):
            st = h - back
            for k in dec(st, 3):
                if k.address <= h < k.address + len(k.bytes):
                    if any(is_G_mem(o) for o in k.operands) and k.address not in seen:
                        seen.add(k.address)
                        sites.append(k)
                    break
            if seen and any(s.address for s in sites if abs(s.address - h) <= 8):
                break
    return byte_hits, sorted(sites, key=lambda x: x.address)


FLAGS_OPS = {"test", "cmp", "add", "sub", "and", "or", "xor", "inc", "dec",
             "neg", "shl", "shr", "sar", "adc", "sbb", "imul"}
# 这些指令不写第一个操作数（不覆盖 ecx）
NON_DEST = {"test", "cmp", "push", "call", "jmp", "je", "jne", "jz", "jnz",
            "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "js", "jns",
            "jo", "jno", "jp", "jnp", "ret", "nop"}


def walk_to_call(ins):
    """从 `mov <dst>,[G]` 起向前走，跟踪 dst 是否仍存活，直到 call。

    返回 dict:
      kind   : 'call' / 'call-indirect' / 'dead'(dst 被覆盖) / 'exit'(ret/jmp) / 'none'
      call   : call 指令（或 None）
      target : 直接目标 VA（或 None）
      gap    : mov 与 call 之间的指令数
      guard  : 中间是否有 test/cmp（flags 级）
      dst    : 载入的寄存器名
    """
    ops = ins.operands
    if not ops or ops[0].type != X86_OP_REG:
        return dict(kind="none", call=None, target=None, gap=0, guard=False, dst=None)
    dst = MD.reg_name(ops[0].reg)
    seq = [k for k in dec(ins.address, 20) if k.address > ins.address]
    live = True
    for idx, k in enumerate(seq):
        if k.mnemonic == "call":
            if not live:
                return dict(kind="dead", call=k, target=None, gap=idx,
                            guard=False, dst=dst)
            if k.operands and k.operands[0].type == X86_OP_IMM:
                return dict(kind="call", call=k, target=k.operands[0].imm,
                            gap=idx, guard=any(x.mnemonic in ("test", "cmp")
                                               for x in seq[:idx]), dst=dst)
            return dict(kind="call-indirect", call=k, target=None, gap=idx,
                        guard=any(x.mnemonic in ("test", "cmp")
                                  for x in seq[:idx]), dst=dst)
        if k.mnemonic in ("ret", "jmp"):
            return dict(kind="exit", call=None, target=None, gap=idx,
                        guard=False, dst=dst)
        # dst 被覆盖？（排除 test/cmp/push 这类不改目的操作数的）
        if k.operands and k.operands[0].type == X86_OP_REG \
                and MD.reg_name(k.operands[0].reg) == dst \
                and k.mnemonic not in NON_DEST:
            live = False
    return dict(kind="none", call=None, target=None, gap=len(seq),
                guard=False, dst=dst)


def first_mem_access(fn_va, maxinsn=60):
    """首个**真正访问内存**的 this 偏移（区分 lea 与真访问）。

    ★ 核验员指出：`lea esi,[ebx+0x24C]` 只是地址算术，不访问内存。
      0x724580 的真访问是后续 `mov eax,[esi+4]` = +0x250。

    ★ 但 lea 必须建立**带偏移**的别名：`lea esi,[ebx+0x24C]` 之后
      esi 等于 this+0x24C，故 `[esi+4]` 应还原为 this+0x250。
      首版只允许 disp==0 的 lea 建别名 ⇒ 0x724580 假阴性。
    """
    insns = dec(fn_va, maxinsn)
    # this_regs: 寄存器名 -> 相对 this 的偏移
    this_regs = {"ecx": 0}
    first_lea = None
    for ins in insns:
        ops = ins.operands
        if ins.mnemonic != "lea":
            for op in ops:
                if op.type == X86_OP_MEM and op.mem.base:
                    b = MD.reg_name(op.mem.base)
                    if b in this_regs:
                        off = this_regs[b] + op.mem.disp
                        if 0 <= off <= 0x4000:
                            return off, ins, first_lea
        else:
            for op in ops:
                if op.type == X86_OP_MEM and op.mem.base:
                    b = MD.reg_name(op.mem.base)
                    if b in this_regs:
                        off = this_regs[b] + op.mem.disp
                        if 0 <= off <= 0x4000 and first_lea is None:
                            first_lea = (off, ins)
        # 别名传播（带偏移）
        if ins.mnemonic == "mov" and len(ops) == 2 \
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG \
                and MD.reg_name(ops[1].reg) in this_regs:
            this_regs[MD.reg_name(ops[0].reg)] = this_regs[MD.reg_name(ops[1].reg)]
        elif ins.mnemonic == "lea" and len(ops) == 2 \
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_MEM \
                and ops[1].mem.base and MD.reg_name(ops[1].mem.base) in this_regs:
            this_regs[MD.reg_name(ops[0].reg)] = \
                this_regs[MD.reg_name(ops[1].mem.base)] + ops[1].mem.disp
        elif ins.mnemonic in ("add", "sub") and len(ops) == 2 \
                and ops[0].type == X86_OP_REG \
                and MD.reg_name(ops[0].reg) in this_regs \
                and ops[1].type == X86_OP_IMM:
            d = ops[1].imm if ins.mnemonic == "add" else -ops[1].imm
            this_regs[MD.reg_name(ops[0].reg)] += d
        elif ops and ops[0].type == X86_OP_REG \
                and MD.reg_name(ops[0].reg) in this_regs \
                and ins.mnemonic not in NON_DEST \
                and ins.mnemonic not in ("lea",) \
                and not (len(ops) == 2 and ops[1].type == X86_OP_REG
                         and MD.reg_name(ops[1].reg) in this_regs):
            this_regs.pop(MD.reg_name(ops[0].reg), None)
        if ins.mnemonic == "ret":
            break
    return None, None, first_lea


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHORT), sha[:8])
    print(f"  capstone skipdata = {MD.skipdata}（★ 必须为 True，否则线性反汇编会静默截断）")
    chk("capstone skipdata 已开启", MD.skipdata is True, str(MD.skipdata))

    # --------------------------------------------------------- A
    print()
    print("=" * 78)
    print(f"== STEP A  [0x{G:X}] 引用点")
    print("=" * 78)
    byte_hits, sites = find_G_sites()
    print(f"  字节级命中 : {len(byte_hits)}")
    print(f"  指令级站点 : {len(sites)}")
    chk("指令级站点数 <= 字节命中数", len(sites) <= len(byte_hits),
        f"{len(sites)} <= {len(byte_hits)}")
    chk("指令级站点数 == 74（与账本记载一致）", len(sites) == 74, str(len(sites)))

    # --------------------------------------------------------- B
    print()
    print("=" * 78)
    print("== STEP B  ★ 修正判据：向前走到 call（不是「下一条是 call」）")
    print("=" * 78)
    print("  v1 的判据「mov 的下一条是 call」只得到 7 处，**漏掉了崩溃点 0x654405**。")
    print("  正确判据：从 mov 起向前走，跟踪目标寄存器是否仍存活，直到 call。\n")

    results = []
    for ins in sites:
        w = walk_to_call(ins)
        results.append((ins, w))

    dist = collections.Counter(w["kind"] for _, w in results)
    print("  结局分布：")
    for k, n in dist.most_common():
        print(f"    {k:<16} {n}")
    chk("分类总数 == 站点数", sum(dist.values()) == len(sites), str(len(sites)))

    calls = [(ins, w) for ins, w in results if w["kind"] == "call"]
    indirect = [(ins, w) for ins, w in results if w["kind"] == "call-indirect"]
    print(f"\n  以 [G] 为 this 的**直接** call 站点：{len(calls)}")
    print(f"  以 [G] 为 this 的**间接** call 站点：{len(indirect)}")

    print("\n  间隙分布（mov 与 call 之间隔几条指令）：")
    gaps = collections.Counter(w["gap"] for _, w in calls)
    for g in sorted(gaps):
        print(f"    gap={g:<2} {gaps[g]:>2} 处")
    chk("★ 存在 gap>0 的站点（证明 v1 判据错误）",
        any(g > 0 for g in gaps), str(sorted(g for g in gaps if g > 0)))

    crash = [w for ins, w in calls if ins.address == 0x654405]
    print(f"\n  ★ 崩溃点 0x654405 是否在清单内：{'是' if crash else '否'}")
    if crash:
        print(f"      gap={crash[0]['gap']}  target={crash[0]['target']:#x}  "
              f"guard={crash[0]['guard']}")
    chk("★★ 崩溃点 0x654405 在直接 call 清单内", bool(crash),
        f"gap={crash[0]['gap']}" if crash else "missing")

    # --------------------------------------------------------- C
    print()
    print("=" * 78)
    print("== STEP C  被调函数 → 首个真内存访问偏移")
    print("=" * 78)
    by_t = collections.Counter(w["target"] for _, w in calls)
    print(f"  不同的被调函数：{len(by_t)} 个\n")
    rows = []
    for t in sorted(by_t, key=lambda x: (x is None, x)):
        n = by_t[t]
        off, ins, lea = first_mem_access(t)
        rows.append((t, n, off, ins, lea))
        print(f"  {t:#010x}  站点 {n:2d}")
        print(f"      首个真内存访问偏移 : {('0x%X' % off) if off is not None else '—'}")
        if ins is not None:
            print(f"        {fmt(ins)}")
        if lea is not None:
            print(f"      （此前有 lea 0x{lea[0]:X}: {fmt(lea[1])}）")

    print()
    print("  按首个真内存访问偏移分组：")
    grp = collections.defaultdict(list)
    for t, n, off, ins, lea in rows:
        grp[off].append((t, n))
    for off in sorted(grp, key=lambda x: (x is None, x)):
        members = grp[off]
        label = f"0x{off:X}" if off is not None else "无 this 内存访问"
        tot = sum(n for _, n in members)
        print(f"    {label:<16} 函数 {len(members):2d} / 站点 {tot:3d}  "
              f"{[hex(t) for t, _ in members]}")
    chk("★ 偏移 0x250 组（崩溃现场 Access）恰好覆盖崩溃函数",
        0x250 in grp and any(t == 0x724730 for t, _ in grp[0x250]),
        str([hex(t) for t, _ in grp.get(0x250, [])]))

    # --------------------------------------------------------- D
    print()
    print("=" * 78)
    print("== STEP D  67 个调用点的守卫情况")
    print("=" * 78)
    gd = sum(1 for _, w in calls if w["guard"])
    ug = len(calls) - gd
    print(f"  有守卫 {gd} / 无守卫 {ug}（共 {len(calls)}）")
    print("\n  按被调函数统计：")
    per = collections.defaultdict(lambda: [0, 0])
    for _, w in calls:
        per[w["target"]][0 if w["guard"] else 1] += 1
    for t in sorted(per, key=lambda x: (x is None, x)):
        g, u = per[t]
        print(f"    {t:#010x}  有守卫 {g:2d} / 无守卫 {u:2d}")
    chk("★ 存在无守卫站点", ug > 0, str(ug))

    print("\n  无守卫站点全清单：")
    for ins, w in calls:
        if not w["guard"]:
            print(f"    mov@{ins.address:#010x} → call@{w['call'].address:#010x} "
                  f"{w['target']:#x}  gap={w['gap']}")

    # --------------------------------------------------------- E
    print()
    print("=" * 78)
    print("== STEP E  间接 call 站点")
    print("=" * 78)
    for ins, w in indirect:
        print(f"  mov@{ins.address:#010x} → {fmt(w['call'])}  gap={w['gap']}")
    if not indirect:
        print("  无")
    print(f"\n  共 {len(indirect)} 处。")

    # --------------------------------------------------------- F
    print()
    print("=" * 78)
    print("== STEP F  结论")
    print("=" * 78)
    print(f"  以 [G] 为 this 的直接调用：{len(calls)} 个站点，"
          f"分布在 {len(by_t)} 个函数上")
    print(f"  其中无守卫：{ug} 个站点")
    print()
    print("  ⇒ 修复若只守「v3 的 4 个函数」，覆盖率 =")
    covered = sum(n for t, n, _, _, _ in rows if t in (0x724730, 0x724580, 0x724530, 0x724540))
    print(f"      {covered}/{len(calls)} = {100*covered/len(calls):.1f}%")
    chk("★ v3 四守卫的覆盖率 < 100%（故不充分）", covered < len(calls),
        f"{covered}/{len(calls)}")

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


WANT_SHORT = WANT_SHA8

if __name__ == "__main__":
    sys.exit(main())
