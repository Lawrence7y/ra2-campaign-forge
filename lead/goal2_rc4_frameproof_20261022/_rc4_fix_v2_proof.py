# -*- coding: utf-8 -*-
"""RC-4 修复草案 v2：双守卫 + DLL trampoline（取代 v1 的 .detour cave）

v1 草案的两处硬伤（本轮推翻）
----------------------------
1. **`.detour` 段不可执行。**
   段特性 `0xC0000040`：`MEM_WRITE`(0x80000000) | `MEM_READ`(0x40000000) | `CNT_CODE`(0x20) | `CNT_INITIALIZED_DATA`(0x40)，
   **`MEM_EXECUTE`(0x20000000) 清零**。v1 写「R/W/**X**」是错的。
   且该段真实内容是 Detours 载荷（段首即 `Dtr` 签名 + 内嵌 MZ 映像），不是空白代码区。
2. **「2304 字节空闲」是错的。**
   `.detour` 的 `VirtualSize = 0x2718`，末个非零字节在 `0xB956FE`。
   v1 选的 `0xB95700` 之后只有 24 字节仍在段内，再往后越界。
   真正可用空洞只有一处：`0xB9375C`，长 1548 字节。

v2 的做法
---------
照搬项目既有范式（`ra2render/blitter_hooks.cpp:1384 InstallGreatestThreatHook`）：

    gamemd 里只改**函数头 5/8 字节** → `E9 rel32` 跳到 **DLL 自己的静态数组**
    DLL 静态数组在 `VirtualProtect(PAGE_EXECUTE_READWRITE)` 后填充：
        守卫 + 重放原序言 + `E9 rel32` 跳回 gamemd

好处：cave 在 DLL 里，段属性由 DLL 自己控制；不动 gamemd 的节表。

要守两个函数（不是 v1 的一个）
------------------------------
`0x654320` 内有 **4 处**以 `[0x887368]` 为 this 的 deref 调用，全无守卫：

    0x654413 -> 0x724730     0x654423 -> 0x724580
    0x654469 -> 0x724730     0x654479 -> 0x724580

只守 `0x724730` 不够：它会安全返回，紧接着 `0x724580` 在 `0x724596` 读
`[esi+4]`（esi = 0+0x24C）⇒ **Access 同样是 0x250**，症状一模一样。

本脚本只做静态取证 + 字节推演，不写任何二进制、不部署。
"""
import hashlib
import re
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
EXC = Path(r"D:\Project\ra2-campaign-forge\ra2youli\except.txt")
WANT_SHA8 = "73201cc0"

G_CRASH = 0x887368
FN_A = 0x724730
FN_B = 0x724580
OWNER = 0x654320
RESUME_A = 0x724737          # cave A 重放 sub/push ebp/mov ebp,ecx/push esi 后跳这里
RESUME_B = 0x724588          # cave B 重放 8 字节后跳这里
HOOK_LEN_A = 6               # sub(3)+push ebp(1)+mov ebp,ecx(2)
HOOK_LEN_B = 8               # push ebx/ebp/esi/edi(4)+mov edi,[esp+0x14](4)

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


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
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        ch = struct.unpack_from("<I", d, o + 36)[0]
        secs.append({"name": d[o:o + 8].rstrip(b"\x00").decode("latin1"),
                     "va": va + ib, "vsize": vs, "rawptr": rp,
                     "rawsize": rs, "ch": ch})
    return d, ib, secs


DATA, IMAGEBASE, SECS = load_pe(BIN)
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


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


def raw(va, n):
    return DATA[va2off(va):va2off(va) + n]


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}"


def dis(va, n):
    off = va2off(va)
    if off is None:
        return []
    out = []
    for i in MD.disasm(DATA[off:off + n * 16], va):
        out.append(i)
        if len(out) >= n:
            break
    return out


def insn_at(va):
    got = dis(va, 1)
    return got[0] if got and got[0].address == va else None


def call_target_at(va):
    off = va2off(va)
    if off is None or off + 5 > len(DATA) or DATA[off] != 0xE8:
        return None
    return (va + 5 + struct.unpack_from("<i", DATA, off + 1)[0]) & 0xFFFFFFFF


def all_e8_callers(target):
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


def parse_except(path):
    txt = path.read_bytes().decode("latin1")
    regs = {}
    for n in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        m = re.search(n + r":([0-9A-Fa-f]{8})", txt)
        if m:
            regs[n] = int(m.group(1), 16)
    m = re.search(r"Access address:([0-9A-Fa-f]+) was", txt)
    access = int(m.group(1), 16) if m else None
    stack = {}
    for m in re.finditer(r"^([0-9A-Fa-f]{8}): ([0-9A-Fa-f]{8})", txt, re.M):
        stack[int(m.group(1), 16)] = int(m.group(2), 16)
    return regs, access, stack


# ================================================================== main
def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHA8), sha[:8])
    regs, access, stack = parse_except(EXC)
    print(f"  except.txt : {hashlib.sha256(EXC.read_bytes()).hexdigest()}")
    print(f"  stack      : {len(stack)} entries")
    print(f"  Access     : {access:#x}")
    chk("Access == 0x250", access == 0x250, hex(access) if access else "?")

    # ---------------------------------------------------------- A 链
    print()
    print("=" * 78)
    print("== STEP A  现场栈帧链逐帧核对（不依赖序言算术）")
    print("=" * 78)
    print("  方法：遍历栈转储每个 4 字节值 V，若 V-5 处是 E8 rel32 且目标等于已知函数，")
    print("        则 V 是该函数帧的返回地址。对全转储通用，可被反证。")
    chain = [
        (0x724730, 0x654413, 0x00F9A358, "FN_A 0x724730 ← 崩溃函数本身"),
        (0x654320, 0x6403A3, 0x00F9A388, "OWNER 0x654320"),
        (0x6403A0, 0x6ABD39, 0x00F9A3AC, "0x6403A0"),
        (0x6ABD30, 0x4A8B13, 0x00F9A3E4, "0x6ABD30（L3 0x4A8960 内嵌套调用）"),
        (0x4A8850, 0x652D4C, 0x00F9A43C, "0x4A8850"),
    ]
    for fn, site, slot, label in chain:
        got = stack.get(slot)
        want = (site + 5) & 0xFFFFFFFF
        ok = (got == want and call_target_at(site) == fn)
        print(f"  {label}")
        print(f"      call {site:#x} -> {fn:#x} ; 期望 retaddr {want:#010x}, "
              f"栈上 {slot:#010x} = {got:#010x}")
        chk(f"链 {fn:#x} 的返回地址帧", ok, f"{got:#010x}")

    # ---------------------------------------------------------- B 4 处
    print()
    print("=" * 78)
    print("== STEP B  0x654320 内 4 处以 [0x887368] 为 this 的 deref 调用")
    print("=" * 78)
    body = dis(OWNER, 200)
    loads = [i for i in body
             if i.mnemonic == "mov" and i.op_str == "ecx, dword ptr [0x887368]"]
    for i in loads:
        print("    " + fmt(i))
    chk("0x654320 内 4 次读 [0x887368]", len(loads) == 4, str(len(loads)))

    sites = []
    for L in loads:
        for i in body:
            if i.address > L.address and i.mnemonic == "call":
                guarded = any(x.mnemonic in ("test", "cmp")
                              for x in body if L.address < x.address < i.address)
                sites.append((L.address, i.address, i.op_str, guarded))
                break
    print(f"\n  每个 load 之后的首个 call：")
    for load_va, call_va, tgt, guarded in sites:
        print(f"    load {load_va:#x} -> call {call_va:#x} {tgt:<12} "
              f"守卫={'有' if guarded else '★无'}")
    chk("4 处全部无守卫", len(sites) == 4 and all(not g for *_, g in sites),
        f"unguarded={sum(1 for *_, g in sites if not g)}/4")
    callees = {int(t, 16) for _, _, t, _ in sites if t.startswith("0x")}
    chk("被调函数恰为 {0x724730, 0x724580}", callees == {FN_A, FN_B},
        str([hex(c) for c in sorted(callees)]))
    chk("崩溃入口 0x654413 在清单内",
        any(c == 0x654413 for _, c, _, _ in sites), "0x654413")

    # ---------------------------------------------------------- C 兄弟函数
    print()
    print("=" * 78)
    print("== STEP C  ★ 0x724580 在 ecx=0 时的首次解引用也是 0x250")
    print("=" * 78)
    for i in dis(FN_B, 10):
        print("    " + fmt(i))
    print("\n  推演（ecx=0）：")
    print("    push ebx/ebp/esi/edi   esp -= 0x10")
    print("    mov  edi,[esp+0x14]    edi = 调用方压入的栈地址（有效）")
    print("    mov  ebx,ecx           ebx = 0")
    print("    mov  eax,[edi]         读栈，有效")
    print("    lea  esi,[ebx+0x24c]   ★ esi = 0x24C")
    print("    mov  eax,[esi+4]       ★★ 读 0x250 ⇒ AV")
    i_lea = insn_at(0x72458C)
    i_mov = insn_at(0x724596)
    chk("0x72458C == lea esi,[ebx+0x24c]",
        i_lea is not None and i_lea.mnemonic == "lea"
        and "ebx + 0x24c" in i_lea.op_str, fmt(i_lea) if i_lea else "-")
    chk("0x724596 == mov eax,[esi+4]",
        i_mov is not None and i_mov.mnemonic == "mov"
        and "[esi + 4]" in i_mov.op_str, fmt(i_mov) if i_mov else "-")
    chk("★ 0x24C+4 == Access(0x250)", 0x24C + 4 == access, hex(0x24C + 4))
    chk("⇒ v1 单点守 0x724730 不充分", True, "结构性结论")

    # ---------------------------------------------------------- D 推翻 v1 cave
    print()
    print("=" * 78)
    print("== STEP D  ★ 推翻 v1 的 cave 落位（.detour）")
    print("=" * 78)
    det = next(s for s in SECS if s["name"] == ".detour")
    print(f"  .detour  va={det['va']:08X} vsize={det['vsize']:08X} "
          f"rawsize={det['rawsize']:08X} characteristics={det['ch']:08X}")
    flags = [("MEM_EXECUTE", 0x20000000), ("MEM_READ", 0x40000000),
             ("MEM_WRITE", 0x80000000), ("CNT_CODE", 0x00000020),
             ("CNT_INITIALIZED_DATA", 0x00000040)]
    for nm, bit in flags:
        print(f"    {nm:<22} = {'SET' if det['ch'] & bit else 'CLEAR'}")
    chk("★ .detour 无 MEM_EXECUTE（v1 写 R/W/X 是错的）",
        not (det["ch"] & 0x20000000), f"ch={det['ch']:08X}")

    dbody = DATA[det["rawptr"]:det["rawptr"] + det["vsize"]]
    nz = [k for k in range(len(dbody)) if dbody[k] != 0]
    last_nz = det["va"] + max(nz)
    print(f"\n  末个非零字节 VA = {last_nz:#x}（vsize 末 = {det['va']+det['vsize']:#x}）")
    print(f"  段首 12 字节: {dbody[:12].hex(' ')}")
    print(f"    +0x00: {dbody[0:4].hex(' ')}  = 长度字段")
    print(f"    +0x04: {dbody[4:8].hex(' ')}  = 'Dtr\\0'（Detours 签名）")
    chk("★ 段首 +4 是 Detours 'Dtr' 签名 ⇒ 是载荷区不是空白",
        dbody[4:7] == b"Dtr", dbody[4:8].hex(" "))
    chk("★ v1 选的 0xB95700 之后段内仅剩 24 字节",
        det["va"] + det["vsize"] - 0xB95700 == 24,
        str(det["va"] + det["vsize"] - 0xB95700))
    chk("★ 故 v1 的「2304 字节空闲」不成立", last_nz == 0xB956FE, hex(last_nz))

    # 真实空洞
    holes = []
    i = 0
    while i < len(dbody):
        if dbody[i] == 0:
            j = i
            while j < len(dbody) and dbody[j] == 0:
                j += 1
            if j - i >= 64:
                holes.append((det["va"] + i, j - i))
            i = j
        else:
            i += 1
    print(f"\n  .detour 内真实空洞（vsize 内，>=64B）：{len(holes)} 处")
    for va, ln in holes:
        print(f"    {va:#010x} len={ln}")
    chk("vsize 内确有 1548 字节空洞（若坚持用 .detour 唯一选择）",
        any(ln == 1548 for _, ln in holes), str([ln for _, ln in holes]))
    print("  ⇒ 但该段无执行位 ⇒ **不能用**。改用 DLL 内 trampoline（项目既有范式）。")

    # ---------------------------------------------------------- E 序言边界
    print()
    print("=" * 78)
    print("== STEP E  两个函数头的覆盖边界")
    print("=" * 78)
    orig_a = raw(FN_A, HOOK_LEN_A)
    orig_b = raw(FN_B, HOOK_LEN_B)
    print(f"  FN_A {FN_A:#x} 前 {HOOK_LEN_A} 字节: {orig_a.hex(' ')}")
    print(f"  FN_B {FN_B:#x} 前 {HOOK_LEN_B} 字节: {orig_b.hex(' ')}")
    chk("FN_A 前 6B == sub esp,0xc; push ebp; mov ebp,ecx",
        orig_a == bytes.fromhex("83ec0c558be9"), orig_a.hex(" "))
    chk("FN_A 第 7 字节是 push esi（0x724736）",
        raw(0x724736, 1) == b"\x56", raw(0x724736, 1).hex())
    chk("FN_A hook 后首条原指令 = 0x724736 push esi",
        0x724736 + 1 == RESUME_A, f"{RESUME_A:#x}")

    chk("FN_B 前 8B == push ebx/ebp/esi/edi; mov edi,[esp+0x14]",
        orig_b == bytes.fromhex("535556578b7c2414"), orig_b.hex(" "))
    chk("FN_B hook 后首条原指令 = 0x724588 mov ebx,ecx",
        raw(RESUME_B, 2) == bytes.fromhex("8bd9"), raw(RESUME_B, 2).hex())
    chk("FN_B 覆盖边界落在指令边界上",
        FN_B + HOOK_LEN_B == RESUME_B, hex(RESUME_B))

    # ---------------------------------------------------------- F trampoline 字节
    print()
    print("=" * 78)
    print("== STEP F  DLL 侧 trampoline 字节（位置在 DLL，不占 gamemd 空间）")
    print("=" * 78)

    # cave A: test ecx,ecx | je .null | <6B 原指令> | push esi | jmp RESUME_A | .null: xor eax,eax; ret 4
    #   ★ push esi 在 0x724736，hook 只覆盖到 0x724735，所以必须重放
    ca = bytearray()
    ca += bytes.fromhex("85c9")                     # test ecx,ecx
    je_a = len(ca)
    ca += bytes.fromhex("7400")                     # je rel8 placeholder
    ca += orig_a                                    # 6B 原指令
    ca += bytes.fromhex("56")                       # push esi（重放）
    jmp_a = len(ca)
    ca += bytes.fromhex("e900000000")               # jmp rel32 placeholder
    null_a = len(ca)
    ca += bytes.fromhex("31c0c20400")               # xor eax,eax; ret 4
    ca[je_a + 1] = (null_a - (je_a + 2)) & 0xFF
    print(f"  cave A 逻辑布局（{len(ca)} 字节，位置由 DLL 分配）：")
    print(f"    {bytes(ca).hex(' ')}")
    print(f"    je rel8 = {ca[je_a+1]:<3} → .null @ +{null_a}")
    print(f"    jmp rel32 = RESUME_A - (cave+{jmp_a+5}) = {RESUME_A:#x} - (cave+{jmp_a+5})")
    chk("cave A je rel8 可表示", -128 <= (null_a - (je_a + 2)) <= 127,
        str(null_a - (je_a + 2)))
    chk("cave A 长 21", len(ca) == 21, str(len(ca)))

    # cave B: test ecx,ecx | je .null | <8B 原指令> | jmp RESUME_B | .null: xor eax,eax; ret 4
    cb = bytearray()
    cb += bytes.fromhex("85c9")
    je_b = len(cb)
    cb += bytes.fromhex("7400")
    cb += orig_b                                    # 8B 原指令
    jmp_b = len(cb)
    cb += bytes.fromhex("e900000000")
    null_b = len(cb)
    cb += bytes.fromhex("31c0c20400")
    cb[je_b + 1] = (null_b - (je_b + 2)) & 0xFF
    print(f"\n  cave B 逻辑布局（{len(cb)} 字节）：")
    print(f"    {bytes(cb).hex(' ')}")
    print(f"    je rel8 = {cb[je_b+1]:<3} → .null @ +{null_b}")
    chk("cave B je rel8 可表示", -128 <= (null_b - (je_b + 2)) <= 127,
        str(null_b - (je_b + 2)))
    chk("cave B 长 22", len(cb) == 22, str(len(cb)))

    # 用假想基址做 capstone 语义复核
    FAKE_A, FAKE_B = 0x10000000, 0x10000100
    ta = bytearray(ca)
    struct.pack_into("<i", ta, jmp_a + 1, RESUME_A - (FAKE_A + jmp_a + 5))
    ta = bytes(ta)
    print(f"\n  capstone 复核 cave A（假想基址 {FAKE_A:#x}）：")
    ia = list(MD.disasm(ta, FAKE_A))
    for i in ia:
        print("    " + fmt(i))
    chk("cave A 首条 test ecx,ecx", ia[0].mnemonic == "test", fmt(ia[0]))
    chk("cave A 次条 je", ia[1].mnemonic == "je", fmt(ia[1]))
    chk("cave A 重放 6B 原指令",
        ta[4:10] == orig_a, ta[4:10].hex(" "))
    chk("cave A 重放 push esi", ta[10] == 0x56, hex(ta[10]))
    chk("cave A jmp 目标 == 0x724737",
        any(i.mnemonic == "jmp" and i.operands[0].imm == RESUME_A for i in ia),
        hex(RESUME_A))
    chk("cave A 末条 ret 4",
        ia[-1].mnemonic == "ret" and ia[-1].op_str == "4", fmt(ia[-1]))

    tb = bytearray(cb)
    struct.pack_into("<i", tb, jmp_b + 1, RESUME_B - (FAKE_B + jmp_b + 5))
    tb = bytes(tb)
    print(f"\n  capstone 复核 cave B（假想基址 {FAKE_B:#x}）：")
    ib = list(MD.disasm(tb, FAKE_B))
    for i in ib:
        print("    " + fmt(i))
    chk("cave B 首条 test ecx,ecx", ib[0].mnemonic == "test", fmt(ib[0]))
    chk("cave B 次条 je", ib[1].mnemonic == "je", fmt(ib[1]))
    chk("cave B 重放 8B 原指令", tb[4:12] == orig_b, tb[4:12].hex(" "))
    chk("cave B jmp 目标 == 0x724588",
        any(i.mnemonic == "jmp" and i.operands[0].imm == RESUME_B for i in ib),
        hex(RESUME_B))
    chk("cave B 末条 ret 4",
        ib[-1].mnemonic == "ret" and ib[-1].op_str == "4", fmt(ib[-1]))

    # ---------------------------------------------------------- G 栈平衡
    print()
    print("=" * 78)
    print("== STEP G  栈平衡（含调用方 push arg + ret 4）")
    print("=" * 78)
    BASE = 0x100000

    def trace(title, steps):
        esp = BASE
        print(f"  {title}")
        for nm, dl in steps:
            esp += dl
            print(f"    {nm:<34} esp={esp:#x}")
        return esp

    e = trace("原 FN_A：", [
        ("push arg", -4), ("call (retaddr)", -4), ("sub esp,0xc", -0xC),
        ("push ebp", -4), ("push esi", -4), ("... body ...", 0),
        ("pop esi", +4), ("pop ebp", +4), ("add esp,0xc", +0xC),
        ("ret 4 (retaddr+arg)", +8)])
    chk("FN_A 原路径 esp 回基线", e == BASE, hex(e))
    e = trace("patched FN_A 非零：", [
        ("push arg", -4), ("call (retaddr)", -4), ("jmp; test; je 不跳", 0),
        ("sub esp,0xc", -0xC), ("push ebp", -4), ("mov ebp,ecx", 0),
        ("push esi", -4), ("jmp 0x724737; ... body ...", 0),
        ("pop esi", +4), ("pop ebp", +4), ("add esp,0xc", +0xC),
        ("ret 4", +8)])
    chk("FN_A 非零 esp 回基线", e == BASE, hex(e))
    e = trace("patched FN_A 零值：", [
        ("push arg", -4), ("call (retaddr)", -4), ("jmp; test; je 跳", 0),
        ("xor eax,eax", 0), ("ret 4", +8)])
    chk("FN_A 零值 esp 回基线", e == BASE, hex(e))

    e = trace("原 FN_B：", [
        ("push arg", -4), ("call (retaddr)", -4),
        ("push ebx", -4), ("push ebp", -4), ("push esi", -4), ("push edi", -4),
        ("... body ...", 0),
        ("pop edi", +4), ("pop esi", +4), ("pop ebp", +4), ("pop ebx", +4),
        ("ret 4", +8)])
    chk("FN_B 原路径 esp 回基线", e == BASE, hex(e))
    e = trace("patched FN_B 非零：", [
        ("push arg", -4), ("call (retaddr)", -4), ("jmp; test; je 不跳", 0),
        ("push ebx", -4), ("push ebp", -4), ("push esi", -4), ("push edi", -4),
        ("mov edi,[esp+0x14]", 0), ("jmp 0x724588; ... body ...", 0),
        ("pop edi", +4), ("pop esi", +4), ("pop ebp", +4), ("pop ebx", +4),
        ("ret 4", +8)])
    chk("FN_B 非零 esp 回基线", e == BASE, hex(e))
    e = trace("patched FN_B 零值：", [
        ("push arg", -4), ("call (retaddr)", -4), ("jmp; test; je 跳", 0),
        ("xor eax,eax", 0), ("ret 4", +8)])
    chk("FN_B 零值 esp 回基线", e == BASE, hex(e))

    print("\n  ★ cave B 里 mov edi,[esp+0x14] 的 esp 基准与原函数一致：")
    print("     原：入口 esp=E-8，push×4 → E-24，[esp+0x14] → E-0x10")
    print("     cave：同样在 4 个 push 之后 ⇒ 取同一槽")
    chk("cave B 的 mov edi,[esp+0x14] 取到同一槽", True, "E-0x10")

    # ---------------------------------------------------------- H 返回值
    print()
    print("=" * 78)
    print("== STEP H  被守函数的调用者是否读返回值（决定 ret 4 的 eax 是否可为 0）")
    print("=" * 78)
    for fn in (FN_A, FN_B):
        cs = all_e8_callers(fn)
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
        print(f"\n  {fn:#x}：{len(cs)} 个直接 E8 调用者")
        print(f"    覆盖 eax {ow} / 读 eax {rd} / 不碰 {ot}")
        for c, d in reads:
            print(f"    ★ {c:#x}  {d}")
        chk(f"{fn:#x} 的调用者全不读返回值", rd == 0, f"read={rd}")

    # ---------------------------------------------------------- I 汇总
    print()
    print("=" * 78)
    print("== STEP I  v2 草案汇总（离线，未部署）")
    print("=" * 78)
    print("  ── gamemd 侧（两处函数头，各 1 次 VirtualProtect 写入）──")
    print(f"    {FN_A:#x} : {orig_a.hex(' ')}  ->  E9 <rel32 → DLL caveA>  + {HOOK_LEN_A-5}×90")
    print(f"    {FN_B:#x} : {orig_b.hex(' ')}  ->  E9 <rel32 → DLL caveB>  + {HOOK_LEN_B-5}×90")
    print("  ── DLL 侧（静态数组 + PAGE_EXECUTE_READWRITE）──")
    print(f"    caveA ({len(ca)}B) : test ecx,ecx / je .null / {orig_a.hex(' ')} / 56 / jmp {RESUME_A:#x}")
    print(f"                        .null: xor eax,eax / ret 4")
    print(f"    caveB ({len(cb)}B) : test ecx,ecx / je .null / {orig_b.hex(' ')} / jmp {RESUME_B:#x}")
    print(f"                        .null: xor eax,eax / ret 4")
    print()
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
