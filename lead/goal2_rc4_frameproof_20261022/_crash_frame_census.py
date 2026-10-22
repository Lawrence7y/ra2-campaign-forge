# -*- coding: utf-8 -*-
"""RC-4 崩溃帧普查：用 except.txt 现场栈反推 0x724730 的真实调用者。

要回答的唯一问题
----------------
`0x724730` 有 30 个直接 E8 调用者。崩溃那一次，**到底是哪一个**调进来的？

为什么现场栈能定案
------------------
崩溃帧的返回地址是**可算的**：

    0x724730  83 ec 0c   sub  esp, 0xc      (3)
    0x724733  55         push ebp           (1)
    0x724734  8b e9      mov  ebp, ecx      (2)
    0x724736  56         push esi           (1)

⇒ 崩溃时 ESP = 函数入口 ESP − 20
⇒ 返回地址在 ESP+0x14，唯一参数在 ESP+0x18

于是下面四条**都可证伪**：

    [ESP+0x00] == 崩溃时 Esi        （被 push 保存）
    [ESP+0x04] == 崩溃时的**旧** ebp（≠ 当前 ebp，因为 mov ebp,ecx 已覆盖）
    [ESP+0x14] == 返回地址 ⇒ 减 5 得到 call 指令地址
    [ESP+0x18] == 唯一参数

再往上：**不靠序言算术**，而是直接遍历栈转储里的每个 4 字节值 V，
若 V−5 处是一条 `E8 rel32` 且目标等于某已知被调函数，则 V 就是那个函数帧的返回地址。
这对整个转储通用，且可被反证。

★ 若 `0x724730` 的返回地址**唯一命中**某个调用点，则「崩溃从哪条路进来」定案。
★ 同时检查 L3（`0x4A8960`）在 `0x4A8B75` 的返回地址 `0x4A8B7A` 是否在栈上
  ——不在 ⇒ **本次崩溃不经 L3**（这是本轮最关键的一条否定证据）。

只读，不写任何二进制。
"""
import hashlib
import re
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
EXC = Path(r"D:\Project\ra2-campaign-forge\ra2youli\except.txt")
WANT_SHA8 = "73201cc0"

CRASH_FN = 0x724730
L3 = 0x4A8960
L3_CALL_SITE = 0x4A8B75
G_CRASH = 0x887368

# 栈上值得反查的被调函数（已知链成员 + 本轮候选）
WATCH = {
    0x724730: "CRASH_FN 0x724730",
    0x654320: "0x654320 (直调崩溃函数的上层)",
    0x6403A0: "0x6403A0",
    0x6ABD30: "0x6ABD30",
    0x4A8960: "L3 0x4A8960",
    0x4A8850: "0x4A8850",
    0x652CF0: "One_Time 0x652CF0",
    0x5BDF70: "0x5BDF70 (表A slot 0x78)",
    0x67E730: "0x67E730 (视口变更候选)",
    0x533FD0: "0x533FD0",
    0x7241A0: "0x7241A0",
}

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


# ---------------------------------------------------------------- PE
def load_pe(path):
    d = path.read_bytes()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    if d[e:e + 4] != b"PE\x00\x00":
        raise SystemExit("not PE")
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    opt = e + 0x18
    ib = struct.unpack_from("<I", d, opt + 0x1C)[0]
    so = opt + struct.unpack_from("<H", d, e + 0x14)[0]
    secs = []
    for i in range(nsec):
        o = so + 40 * i
        name = d[o:o + 8].rstrip(b"\x00").decode("latin1")
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        secs.append({"name": name, "va": va + ib, "vsize": vs,
                     "rawptr": rp, "rawsize": rs})
    return d, ib, secs


DATA, IMAGEBASE, SECS = load_pe(BIN)


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


MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


def dis(va, n):
    off = va2off(va)
    out = []
    for i in MD.disasm(DATA[off:off + n * 16], va):
        out.append(i)
        if len(out) >= n:
            break
    return out


def fmt(ins):
    return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}"


def call_target_at(va):
    """若 va 处是一条 E8 rel32，返回目标 VA；否则 None。"""
    off = va2off(va)
    if off is None or off + 5 > len(DATA):
        return None
    if DATA[off] != 0xE8:
        return None
    rel = struct.unpack_from("<i", DATA, off + 1)[0]
    return (va + 5 + rel) & 0xFFFFFFFF


def find_e8_callers(target):
    """扫描 .text 里所有 E8 rel32 指向 target 的位置（naive 扫描，逐点复核）。"""
    text = next(s for s in SECS if s["name"] == ".text")
    lo, hi = text["rawptr"], text["rawptr"] + text["rawsize"]
    hits = []
    for o in range(lo, hi - 4):
        if DATA[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", DATA, o + 1)[0]
        if ((o - text["rawptr"] + text["va"] + 5 + rel) & 0xFFFFFFFF) == target:
            hits.append(o - text["rawptr"] + text["va"])
    return hits


# ---------------------------------------------------------------- except.txt
def parse_except(path):
    raw = path.read_bytes()
    txt = raw.decode("latin1")
    regs = {}
    for name in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        m = re.search(name + r":([0-9A-Fa-f]{8})", txt)
        if m:
            regs[name] = int(m.group(1), 16)
    m = re.search(r"Access address:([0-9A-Fa-f]+) was", txt)
    access = int(m.group(1), 16) if m else None
    stack = {}
    for m in re.finditer(r"^([0-9A-Fa-f]{8}): ([0-9A-Fa-f]{8})", txt, re.M):
        stack[int(m.group(1), 16)] = int(m.group(2), 16)
    return raw, regs, access, stack


def main():
    print("=" * 78)
    print("== STEP 0  时点锚（except.txt 会被游戏覆盖，必须钉住）")
    print("=" * 78)
    raw_bin = BIN.read_bytes()
    sha_bin = hashlib.sha256(raw_bin).hexdigest()
    print(f"  gamemd.exe sha256 : {sha_bin}")
    chk("gamemd.exe 身份", sha_bin.startswith(WANT_SHA8), sha_bin[:8])
    raw_exc, regs, access, stack = parse_except(EXC)
    print(f"  except.txt  sha256 : {hashlib.sha256(raw_exc).hexdigest()}")
    print(f"  except.txt  bytes  : {len(raw_exc)}")
    print(f"  stack entries      : {len(stack)}")

    print()
    print("=" * 78)
    print("== STEP 1  崩溃现场与四元组")
    print("=" * 78)
    for k in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        print(f"  {k} = {regs.get(k, -1):08X}")
    print(f"  Access = {access:#x}" if access is not None else "  Access = ?")
    chk("Eip == 0x724737", regs.get("Eip") == 0x724737, f"{regs.get('Eip'):08X}")
    chk("Access == 0x250", access == 0x250, f"{access:#x}" if access else "?")
    chk("Ebp == 0", regs.get("Ebp") == 0, f"{regs.get('Ebp'):08X}")
    chk("Ecx == 0", regs.get("Ecx") == 0, f"{regs.get('Ecx'):08X}")
    chk("Eip 处字节 == mov eax,[ebp+0x250]",
        DATA[va2off(0x724737):va2off(0x724737) + 6] == bytes.fromhex("8b8550020000"),
        DATA[va2off(0x724737):va2off(0x724737) + 6].hex(" "))

    esp = regs["Esp"]

    print()
    print("=" * 78)
    print("== STEP 2  0x724730 序言 → 帧内偏移")
    print("=" * 78)
    pro = dis(0x724730, 4)
    for i in pro:
        print("  " + fmt(i))
    total = 0
    total_insn_bytes = 0
    for i in pro:
        total_insn_bytes += len(i.bytes)
        if i.mnemonic == "sub" and i.op_str.startswith("esp"):
            total += int(i.op_str.split(",")[1].strip(), 16)
        elif i.mnemonic == "push":
            total += 4
        elif i.mnemonic == "mov" and i.op_str.startswith("ebp, ecx"):
            continue          # 不调 esp，但仍在序言内
        else:
            break
    print(f"  序言 4 条指令共 {total_insn_bytes} 字节（0x724730..0x724736）")
    print(f"  序言使 esp 下移 {total} 字节 ⇒ 返回地址在 [esp+{total:#x}]")
    chk("序言使 esp 下移 0x14", total == 0x14, hex(total))
    chk("序言 4 条指令共 7 字节", total_insn_bytes == 7, str(total_insn_bytes))
    chk("0x724734 == mov ebp,ecx",
        DATA[va2off(0x724734):va2off(0x724734) + 2] == bytes.fromhex("8be9"),
        DATA[va2off(0x724734):va2off(0x724734) + 2].hex(" "))
    chk("0x724736 == push esi",
        DATA[va2off(0x724736):va2off(0x724736) + 1] == bytes.fromhex("56"),
        DATA[va2off(0x724736):va2off(0x724736) + 1].hex(" "))

    slot_esi = esp + 0x00
    slot_ebp = esp + 0x04
    slot_ret = esp + 0x14
    slot_arg = esp + 0x18
    print(f"  [ESP+0x00]={slot_esi:08X}  ← 保存的 esi")
    print(f"  [ESP+0x04]={slot_ebp:08X}  ← 保存的旧 ebp")
    print(f"  [ESP+0x14]={slot_ret:08X}  ← 返回地址")
    print(f"  [ESP+0x18]={slot_arg:08X}  ← 唯一参数")

    print()
    print("=" * 78)
    print("== STEP 3  帧内三条一致性断言（全部可证伪）")
    print("=" * 78)
    v_esi = stack.get(slot_esi)
    v_ebp = stack.get(slot_ebp)
    v_ret = stack.get(slot_ret)
    v_arg = stack.get(slot_arg)
    chk("[ESP+0x00] == Esi（push esi 保存）",
        v_esi == regs["Esi"], f"{v_esi:#010x} vs Esi={regs['Esi']:#010x}")
    chk("[ESP+0x04] != 当前 ebp（旧 ebp 被留在栈上）",
        v_ebp is not None and v_ebp != regs["Ebp"],
        f"{v_ebp:#010x} vs Ebp={regs['Ebp']:#010x}")
    chk("[ESP+0x14] 落在 .text", section_of(v_ret) == ".text" if v_ret else False,
        f"{v_ret:#010x}")

    print()
    print("=" * 78)
    print("== STEP 4  ★ 返回地址 → 调用点（定案的唯一一问）")
    print("=" * 78)
    callers = find_e8_callers(CRASH_FN)
    print(f"  0x{CRASH_FN:X} 的直接 E8 调用者：{len(callers)} 个")
    print("    " + ", ".join(f"{c:#x}" for c in callers))
    site = (v_ret - 5) & 0xFFFFFFFF
    chk("返回地址-5 是一条 E8 且指向 0x724730",
        call_target_at(site) == CRASH_FN,
        f"{site:#x} -> {call_target_at(site)}")
    chk("该调用点在 30 个调用者名单内", site in callers, f"{site:#x}")
    print(f"  ★ 调用指令：{site:#x}")
    for i in dis(site - 0x10, 8):
        mark = "  <<<< CALL" if i.address == site else ""
        print("    " + fmt(i) + mark)

    print()
    print("=" * 78)
    print("== STEP 5  该调用点有无 null 守卫（flags 级判据）")
    print("=" * 78)
    # 从 mov ecx,[0x887368] 开始扫到 call 为止
    pre = [i for i in dis(site - 0x40, 20) if i.address < site]
    guard = None
    flags_ops = {"test", "cmp", "add", "sub", "and", "or", "xor", "inc", "dec",
                 "neg", "shl", "shr", "sar", "adc", "sbb", "imul"}
    for i in pre:
        if i.mnemonic in flags_ops:
            guard = i
    tail = [i for i in pre if i.address >= (site - 0x0E)]
    print("  调用点前 0x0E 字节窗口：")
    for i in tail:
        print("    " + fmt(i))
    mov_ecx = [i for i in pre if i.mnemonic == "mov"
               and i.op_str.startswith("ecx, dword ptr [0x887368]")]
    chk("调用前确实用 mov ecx,[0x887368] 取 this",
        bool(mov_ecx), f"{mov_ecx[-1].address:#x}" if mov_ecx else "none")
    if mov_ecx:
        m = mov_ecx[-1].address
        between = [i for i in pre if m < i.address < site]
        print(f"  mov 在 {m:#x}；到 call 之间 {len(between)} 条指令：")
        for i in between:
            print("    " + fmt(i))
        chk("mov 与 call 之间无 test/cmp（⇒ 无守卫）",
            not any(i.mnemonic in ("test", "cmp") for i in between),
            "guarded" if any(i.mnemonic in ("test", "cmp") for i in between) else "unguarded")

    print()
    print("=" * 78)
    print("== STEP 6  唯一参数 = 0xF2 的独立核对")
    print("=" * 78)
    push_src = [i for i in pre if i.mnemonic == "push"]
    print(f"  [ESP+0x18] = {v_arg:#010x}")
    for i in push_src:
        print("    " + fmt(i))
    chk("参数值 == 0xF2", v_arg == 0xF2, f"{v_arg:#010x}")
    chk("调用点上方存在 push 0xf2（压参指令）",
        any(i.mnemonic == "push" and i.op_str == "0xf2" for i in push_src),
        "found" if any(i.mnemonic == "push" and i.op_str == "0xf2" for i in push_src) else "none")

    print()
    print("=" * 78)
    print("== STEP 7  向上反查整条链（通用：遍历栈值 V，看 V-5 是否 call 到被调者）")
    print("=" * 78)
    chain_found = {}
    for callee, label in WATCH.items():
        hits = []
        for addr, v in sorted(stack.items()):
            if v < IMAGEBASE:
                continue
            t = call_target_at((v - 5) & 0xFFFFFFFF)
            if t == callee:
                hits.append((addr, v))
        chain_found[callee] = hits
        if hits:
            for addr, v in hits:
                print(f"  {label:<34} retaddr {v:08X} @ stack {addr:08X}  (call {v-5:#x})")
        else:
            print(f"  {label:<34} — 不在栈上")

    print()
    print("=" * 78)
    print("== STEP 8  ★ L3 与本次崩溃的关系（精确表述）")
    print("=" * 78)
    l3_ret = (L3_CALL_SITE + 5) & 0xFFFFFFFF
    print(f"  L3 内 call 0x724730 的调用点是 {L3_CALL_SITE:#x}，其返回地址应为 {l3_ret:#x}")
    t = call_target_at(L3_CALL_SITE)
    print(f"  call_target_at({L3_CALL_SITE:#x}) = {t}")
    chk("0x4A8B75 确实是 call 0x724730", t == CRASH_FN, str(t))
    chk("0x4A8B7A 不在崩溃栈上 ⇒ 本帧不由 L3 在 0x4A8B75 直接调用产生",
        l3_ret not in stack.values(), f"{l3_ret:#x}")

    # ★ 但 L3 是祖先帧：0x4A8B13 在其函数体内，其返回地址 0x4A8B18 在栈上
    l3_ancestor_ret = 0x4A8B18
    on_stack = l3_ancestor_ret in stack.values()
    print(f"\n  ★ 0x4A8B18（= L3 内 call 0x6ABD30 的返回地址）在栈上: {on_stack}")
    chk("★ L3 确实是祖先帧（0x4A8B18 在栈上）", on_stack, hex(l3_ancestor_ret))
    # L3 函数体范围 0x4A8960..0x4A8B75 之间无 ret ⇒ 0x4A8B13 与 0x4A8B75 同属一个函数
    body_insns = []
    for i in MD.disasm(DATA[va2off(L3):va2off(L3) + (L3_CALL_SITE - L3) + 16], L3):
        body_insns.append(i)
        if i.address >= L3_CALL_SITE:
            break
    rets = [i for i in body_insns if i.mnemonic == "ret"]
    print(f"  L3 0x{L3:X}..0x{L3_CALL_SITE:X} 之间 ret 数 = {len(rets)}")
    chk("L3 函数体内（到 0x4A8B75 为止）无 ret ⇒ 两处调用同属一个函数",
        len(rets) == 0, str(len(rets)))
    print()
    print("  ⇒ 精确表述：**L3 在崩溃路径上（祖先帧），但本帧的直接调用者是")
    print("    0x654413，不是 L3 自己的 0x4A8B75。**")
    print("    旧账本『本次崩溃不经 L3』过强，应更正为『不经 L3 在 0x4A8B75 的直接调用』。")

    print()
    print("=" * 78)
    print("== STEP 9  5 个「紧邻 mov ecx,[0x887368]」候选逐个判定")
    print("=" * 78)
    cands = [0x654413, 0x654469, 0x6AC03E, 0x6D0634, 0x6D0664]
    for c in cands:
        is_call = call_target_at(c) == CRASH_FN
        ret = (c + 5) & 0xFFFFFFFF
        on_stack = ret in stack.values()
        verdict = "★ 命中（本次崩溃入口）" if on_stack else "不在本次栈上"
        print(f"  {c:#x}  call→0x724730:{'是' if is_call else '否':<2}  "
              f"retaddr {ret:#x} 在栈上:{'是' if on_stack else '否'}   {verdict}")
        chk(f"候选 {c:#x} 的判定", (not is_call) or (on_stack == (c == site)),
            verdict)

    print()
    print("=" * 78)
    print("== STEP 10  栈上所有 .text 值（人工复核用）")
    print("=" * 78)
    for addr, v in sorted(stack.items()):
        if section_of(v) == ".text":
            t = call_target_at((v - 5) & 0xFFFFFFFF)
            tag = f"retaddr of call {v-5:#x} -> {t:#x}" if t else ""
            print(f"  {addr:08X}: {v:08X}   {tag}")

    print()
    print("=" * 78)
    print("== RESULT")
    print("=" * 78)
    npass = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {npass}/{len(CHECKS)}")
    for name, ok, detail in CHECKS:
        if not ok:
            print(f"  FAIL: {name}  {detail}")
    print("RESULT:", "ALL PASS" if npass == len(CHECKS) else "HAS FAILURES")
    return 0 if npass == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
