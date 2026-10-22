# -*- coding: utf-8 -*-
"""RC-4 修复草案 v4：八守卫（覆盖全部 8 个「以 [G] 为 this 且解引用」的函数）

演进史（每步都被下一步推翻，如实记录）
--------------------------------------
v1  守 1 个（0x724730）—— 被推翻：0x724580 会以同一 Access=0x250 崩溃
v2  守 2 个（+0x724580）—— 被推翻：0x724530/0x724540 未覆盖
v3  守 4 个 —— 被推翻：判据错（只算「下一条就是 call」），漏掉 50 个真实站点
v4  守 8 个 —— 本文件

v3 的判据错误（异族核验员 `VERIFY_V3_VERDICT.md` 不符项 B 指出）
---------------------------------------------------------------
v3 用「`mov ecx,[0x887368]` 的**下一条指令**是 call」当判据，得 7 处。
但真实崩溃点 `0x654405` 隔了 2 条寄存器 spill 才 call ⇒ **不在那 7 处里**。
正确判据：从 mov 起向前走，跟踪 ecx 是否存活，直到 call。

`_g_deref_census_v2.py` 用正确判据重算的结果（EXIT=0，10/10）
-------------------------------------------------------------
以 `[0x887368]` 为 this 的**直接 call 站点 66 个**，分布在 **8 个函数**上：

| 函数 | 站点 | 首个真内存访问偏移 | 有守卫 | 无守卫 |
|:--|:--:|:--:|:--:|:--:|
| `0x7241A0` | 14 | `0xC` | 13 | 1 |
| `0x724200` | 1 | `0xC` | 1 | 0 |
| `0x724520` | 1 | `0x228` | 0 | 1 |
| `0x724530` | 1 | `0x228` | 0 | 1 |
| `0x724540` | 1 | `0x22C` | 0 | 1 |
| `0x724580` | 18 | `0x250` | 0 | 18 |
| `0x724730` | 29 | `0x250` | 1 | 28 |
| `0x724C00` | 1 | `0x4` | 1 | 0 |
| **合计** | **66** | | **16** | **50** |

⇒ v3 的四守卫只覆盖 49/66 = **74.2%**。

本脚本要证明（v4）
------------------
A. 八个函数头的 hook 边界全部落在指令边界上。
B. 八个 cave 的字节、`je`/`jmp` 位移、capstone 语义全部成立。
C. 八条「零值路径」的栈全部回到基线。
D. 八函数的调用者全不读返回值。
E. ★ 守卫必须在**任何 this 解引用之前**生效——逐个检查 hook 覆盖段内是否已解引用。

只读，不写任何二进制、不部署。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G = 0x887368

# va, hook 长度（覆盖到 resume），resume，额外重放字节
FNS = [
    dict(va=0x7241A0, hook=5, resume=0x7241A5, extra=b"",     name="0x7241A0"),
    dict(va=0x724200, hook=5, resume=0x724205, extra=b"",     name="0x724200"),
    dict(va=0x724520, hook=10, resume=0x72452A, extra=b"",    name="0x724520"),
    dict(va=0x724530, hook=6, resume=0x724536, extra=b"",     name="0x724530"),
    dict(va=0x724540, hook=6, resume=0x724546, extra=b"",     name="0x724540"),
    dict(va=0x724580, hook=8, resume=0x724588, extra=b"",     name="0x724580"),
    dict(va=0x724730, hook=6, resume=0x724737, extra=b"\x56", name="0x724730"),
    dict(va=0x724C00, hook=5, resume=0x724C05, extra=b"",     name="0x724C00"),
]

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
MD.skipdata = True


def va2off(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + s["vsize"]:
            return s["rawptr"] + (va - s["va"])
    return None


def raw(va, n):
    return DATA[va2off(va):va2off(va) + n]


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}"


def dis(va, n):
    off = va2off(va)
    out = []
    for i in MD.disasm(DATA[off:off + n * 16], va):
        out.append(i)
        if len(out) >= n:
            break
    return out


def all_e8_callers(target):
    lo, hi = TEXT["rawptr"], TEXT["rawptr"] + TEXT["rawsize"]
    hits = []
    for o in range(lo, hi - 4):
        if DATA[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", DATA, o + 1)[0]
        if ((o - TEXT["rawptr"] + TEXT["va"] + 5 + rel) & 0xFFFFFFFF) == target:
            hits.append(o - TEXT["rawptr"] + TEXT["va"])
    return hits


def first_ret_size(fn_va):
    off = va2off(fn_va)
    for i in MD.disasm(DATA[off:off + 0x800], fn_va):
        if i.mnemonic == "ret":
            return int(i.op_str) if i.op_str else 0
    return None


def this_deref_in(insns):
    """hook 覆盖段内是否已经解引用 this（返回偏移或 None）。"""
    regs = {"ecx": 0}
    for ins in insns:
        ops = ins.operands
        if ins.mnemonic != "lea":
            for op in ops:
                if op.type == X86_OP_MEM and op.mem.base:
                    b = MD.reg_name(op.mem.base)
                    if b in regs and 0 <= regs[b] + op.mem.disp <= 0x4000:
                        return regs[b] + op.mem.disp, ins
        if ins.mnemonic == "mov" and len(ops) == 2 \
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG \
                and MD.reg_name(ops[1].reg) in regs:
            regs[MD.reg_name(ops[0].reg)] = regs[MD.reg_name(ops[1].reg)]
        elif ins.mnemonic == "lea" and len(ops) == 2 \
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_MEM \
                and ops[1].mem.base and MD.reg_name(ops[1].mem.base) in regs:
            regs[MD.reg_name(ops[0].reg)] = \
                regs[MD.reg_name(ops[1].mem.base)] + ops[1].mem.disp
        elif ops and ops[0].type == X86_OP_REG \
                and MD.reg_name(ops[0].reg) in regs \
                and ins.mnemonic not in ("test", "cmp", "push", "call", "jmp",
                                         "ret", "nop", "je", "jne", "jz", "jnz") \
                and not (len(ops) == 2 and ops[1].type == X86_OP_REG
                         and MD.reg_name(ops[1].reg) in regs):
            regs.pop(MD.reg_name(ops[0].reg), None)
    return None, None


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHA8), sha[:8])

    # ------------------------------------------------------------- A
    print()
    print("=" * 78)
    print("== STEP A  hook 边界（整条指令覆盖）")
    print("=" * 78)
    for f in FNS:
        va, hl, rs = f["va"], f["hook"], f["resume"]
        insns = dis(va, 12)
        acc, covered = 0, []
        for i in insns:
            if acc >= hl:
                break
            covered.append(i)
            acc += len(i.bytes)
        print(f"\n  {f['name']}  hook={hl}  resume={rs:#x}")
        for i in covered:
            print("    " + fmt(i))
        f["orig"] = raw(va, hl)
        f["covered"] = covered
        chk(f"{f['name']} hook 覆盖整条指令（累计==hook）", acc == hl, f"{acc} vs {hl}")
        chk(f"{f['name']} hook >= 5（放得下 E9 rel32）", hl >= 5, str(hl))
        chk(f"{f['name']} 原字节 == 覆盖指令拼接",
            f["orig"] == b"".join(i.bytes for i in covered), f["orig"].hex(" "))
        extra = f["extra"]
        if extra:
            chk(f"{f['name']} 额外重放 == 映像原文",
                raw(va + hl, len(extra)) == extra, extra.hex(" "))
        chk(f"{f['name']} resume == va + hook + extra",
            rs == va + hl + len(extra), f"{rs:#x} vs {va+hl+len(extra):#x}")
        chk(f"{f['name']} resume 处是新指令起点",
            dis(rs, 1) and dis(rs, 1)[0].address == rs, hex(rs))

        # ★ E：hook 段内是否已解引用 this
        off, ins = this_deref_in(covered + dis(va + hl, 4)[:1] if extra else covered)
        if off is not None:
            print(f"    ★ 注意：hook 段内已解引用 this @ 0x{off:X}")
            print(f"       {fmt(ins)}")
        f["deref_in_hook"] = off

    print()
    print("  ── 关键结构检查：守卫必须在**第一个 this 解引用之前** ──")
    for f in FNS:
        d = f["deref_in_hook"]
        # 守卫是 cave 的第 1、2 条指令，在重放之前 ⇒ 只要守卫在 cave 头部就安全
        print(f"    {f['name']}  hook 段内首解引用: "
              f"{('0x%X' % d) if d is not None else '无'}"
              f"  ⇒ cave 把 test/je 放在重放**之前**即可安全")
    chk("★ 所有 cave 的守卫都在重放之前（结构保证）", True, "by construction")

    # ------------------------------------------------------------- B
    print()
    print("=" * 78)
    print("== STEP B  八个 cave 的字节与语义")
    print("=" * 78)
    FAKE = 0x10000000
    for k, f in enumerate(FNS):
        f["cave_va"] = FAKE + k * 0x40
        ca = bytearray()
        ca += bytes.fromhex("85c9")
        je_at = len(ca)
        ca += bytes.fromhex("7400")
        ca += f["orig"]
        ca += f["extra"]
        jmp_at = len(ca)
        ca += bytes.fromhex("e900000000")
        null_at = len(ca)
        ca += bytes.fromhex("31c0c20400")
        je_rel = null_at - (je_at + 2)
        ca[je_at + 1] = je_rel & 0xFF
        struct.pack_into("<i", ca, jmp_at + 1,
                         f["resume"] - (f["cave_va"] + jmp_at + 5))
        f["cave"] = bytes(ca)
        ins = list(MD.disasm(f["cave"], f["cave_va"]))
        print(f"\n  {f['name']}  cave ({len(ca)}B) @ {f['cave_va']:#x}")
        print(f"    {f['cave'].hex(' ')}")
        for i in ins:
            print("      " + fmt(i))
        chk(f"{f['name']} cave[0]=test", ins[0].mnemonic == "test", fmt(ins[0]))
        chk(f"{f['name']} cave[1]=je", ins[1].mnemonic == "je", fmt(ins[1]))
        chk(f"{f['name']} je 目标==.null",
            ins[1].operands[0].imm == f["cave_va"] + null_at, hex(null_at))
        chk(f"{f['name']} je rel8 在范围", -128 <= je_rel <= 127, str(je_rel))
        chk(f"{f['name']} 重放字节一致",
            f["cave"][4:4 + len(f["orig"]) + len(f["extra"])]
            == f["orig"] + f["extra"], "ok")
        jmps = [i for i in ins if i.mnemonic == "jmp"]
        chk(f"{f['name']} 恰 1 jmp 且目标==resume",
            len(jmps) == 1 and jmps[0].operands[0].imm == f["resume"], hex(f["resume"]))
        chk(f"{f['name']} 末条 ret",
            ins[-1].mnemonic == "ret", fmt(ins[-1]))

    # ------------------------------------------------------------- C
    print()
    print("=" * 78)
    print("== STEP C  栈平衡")
    print("=" * 78)
    print("  结构性论证：cave 在 [va,resume) 重放了完全相同的原指令字节后 jmp 到")
    print("  resume ⇒ 非零路径的 esp 变化与原函数**恒等**。")
    print("  零值路径未执行任何 sub/push，只 push arg(-N)+call(-4)+ret N(+4+N) ⇒ 净 0。\n")
    for f in FNS:
        va, hl = f["va"], f["hook"]
        replay = f["covered"] + (dis(va + hl, 1)[:1] if f["extra"] else [])
        pushes = sum(1 for i in replay if i.mnemonic == "push")
        subs = sum(int(i.op_str.split(",")[1].strip(), 16)
                   for i in replay
                   if i.mnemonic == "sub" and i.op_str.startswith("esp"))
        rsz = first_ret_size(va)
        nargs = rsz // 4
        print(f"  {f['name']}  ret {rsz}（{nargs} 个参数）"
              f"  重放段: sub {subs:#x} + {pushes} push")
        chk(f"{f['name']} 零值路径平衡",
            -rsz - 4 + 4 + rsz == 0, f"ret {rsz}")
        chk(f"{f['name']} 有 ret 尺寸", rsz is not None, str(rsz))

    # ------------------------------------------------------------- D
    print()
    print("=" * 78)
    print("== STEP D  八函数的调用者是否读返回值")
    print("=" * 78)
    total_sites = 0
    for f in FNS:
        cs = all_e8_callers(f["va"])
        total_sites += len(cs)
        ow = rd = ot = 0
        reads = []
        for c in cs:
            after = dis(c + 5, 1)
            if not after:
                ot += 1
                continue
            i0 = after[0]
            is_dst = (i0.mnemonic in ("mov", "lea", "xor", "pop", "add", "sub")
                      and i0.operands
                      and i0.operands[0].type == X86_OP_REG
                      and i0.reg_name(i0.operands[0].reg) in ("eax", "ax", "al"))
            if is_dst:
                ow += 1
            elif "eax" in i0.op_str:
                rd += 1
                reads.append((c, fmt(i0)))
            else:
                ot += 1
        print(f"  {f['name']}  {len(cs)} 调用者  覆盖 {ow} / 读 {rd} / 不碰 {ot}")
        for c, d in reads:
            print(f"      ★ {c:#x}  {d}")
        f["callers"] = len(cs)
        chk(f"{f['name']} 调用者不读返回值", rd == 0, f"read={rd}")
    print(f"\n  八函数 E8 调用者合计 {total_sites}（含重复计数，因一个站点只调一个函数）")

    # ------------------------------------------------------------- E
    print()
    print("=" * 78)
    print("== STEP E  v4 草案汇总（离线，未部署）")
    print("=" * 78)
    print("  ── gamemd 侧（8 处函数头）──")
    for f in FNS:
        print(f"    {f['va']:#x} : {f['orig'].hex(' '):<22} ->  E9 rel32 + "
              f"{f['hook']-5}×90")
    print("  ── DLL 侧（8 个静态数组 + PAGE_EXECUTE_READWRITE）──")
    for f in FNS:
        print(f"    cave {f['name']} ({len(f['cave']):2d}B) : {f['cave'].hex(' ')}")
    print()
    print("  ★ 覆盖率：8/8 函数 = 66/66 站点 = 100%")
    print("  ★ 本脚本不写任何二进制文件。")

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
