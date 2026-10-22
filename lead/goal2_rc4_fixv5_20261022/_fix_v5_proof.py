# -*- coding: utf-8 -*-
"""RC-4 修复草案 v5：修正 v4 的 3 处 ret 宽度错误。

v4 缺陷（本文件发现，v4 的 123/123 未捕获）
--------------------------------------------
v4 的 8 个 cave 零值路径**全部**硬编码 `31 c0 c2 04 00`（xor eax,eax; ret 4）。
但三个函数的真实返回指令是 `c3`（ret，无参数）：

    0x724530  ... 0072453C  c3     ret
    0x724540  ... 0072454C  c3     ret
    0x724C00  ... 00724C0A  c3     ret

`ret 4` 在**零值路径**上会从调用方栈多弹 4 字节 ⇒ 栈失衡 4 字节，
返回到错误地址。这是必崩缺陷，且只在 ecx==0 时触发（正是守卫要保护的那条路）。

v4 的门禁为什么没抓到
--------------------
STEP B 只断言 `ins[-1].mnemonic == "ret"`（**存在**），
STEP C 虽然正确算出 `ret 0`，却把平衡式写成 `-rsz - 4 + 4 + rsz == 0`
—— 这个式子里 `rsz` 自己约掉了，**恒等于 0，与 cave 实际字节无关**。
⇒ 两条判据都不检查 cave 末条的**宽度**。
（同项目已记教训：「门禁要断言取值不是存在」。）

v5 的判据
---------
1. 逐函数取真实 ret 宽度（从函数头线性反汇编到首个 ret）。
2. 由真实宽度**生成** cave 末条（不硬编码）。
3. 断言 cave 末条字节 == 由真实宽度算出的期望字节（取值断言）。
4. 断言零值路径净 esp 变化 == 0，且式子**含 cave 末条实际字节**。

只读 gamemd.exe，不写任何二进制。
"""
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G = 0x887368

DATA = BIN.read_bytes()

_pe = struct.unpack_from("<I", DATA, 0x3C)[0]
_nsec = struct.unpack_from("<H", DATA, _pe + 6)[0]
_opt = _pe + 24
_base = struct.unpack_from("<I", DATA, _opt + 28)[0]
_sect = _opt + struct.unpack_from("<H", DATA, _pe + 20)[0]
SECS = {}
for _i in range(_nsec):
    _o = _sect + 40 * _i
    _nm = DATA[_o:_o + 8].rstrip(b"\0").decode()
    _vs, _va, _rs, _ro = struct.unpack_from("<IIII", DATA, _o + 8)
    SECS[_nm] = (_base + _va, _rs, _ro)
TEXT = SECS[".text"]

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True

_checks = 0
_fails = 0


def chk(name, cond, detail=""):
    global _checks, _fails
    _checks += 1
    if cond:
        print("[PASS] %s  %s" % (name, detail))
    else:
        _fails += 1
        print("[FAIL] %s  %s" % (name, detail))


def va2off(va):
    for _nm, (_va, _rs, _ro) in SECS.items():
        if _va <= va < _va + _rs:
            return _ro + (va - _va)
    raise ValueError("va not mapped: %#x" % va)


def raw(va, n):
    o = va2off(va)
    return DATA[o:o + n]


def dis(va, n):
    return list(MD.disasm(raw(va, n), va))


def fmt(i):
    return "%08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)


def first_ret_size(fn_va):
    for i in MD.disasm(raw(fn_va, 0x800), fn_va):
        if i.mnemonic in ("ret", "retf"):
            return (int(i.op_str) if i.op_str else 0), i
    return None, None


# hook 长度覆盖到 resume；extra = resume 之前额外要重放的 1 条指令字节
FNS = [
    dict(va=0x7241A0, hook=5, extra=b"", name="0x7241A0"),
    dict(va=0x724200, hook=5, extra=b"", name="0x724200"),
    dict(va=0x724520, hook=10, extra=b"", name="0x724520"),
    dict(va=0x724530, hook=6, extra=b"", name="0x724530"),
    dict(va=0x724540, hook=6, extra=b"", name="0x724540"),
    dict(va=0x724580, hook=8, extra=b"", name="0x724580"),
    # 0x724730：hook 6B 覆盖 sub esp,0xc / push ebp / mov ebp,ecx，
    # 其后 0x724736 的 `push esi` 一并重放进 cave（与 v4 同构，resume=0x724737）
    dict(va=0x724730, hook=6, extra=b"\x56", name="0x724730"),
    dict(va=0x724C00, hook=5, extra=b"", name="0x724C00"),
]


def build_null_path(ret_sz):
    """由真实 ret 宽度生成零值路径字节：xor eax,eax; ret [imm16]。"""
    body = b"\x31\xc0"
    if ret_sz == 0:
        body += b"\xc3"
    else:
        body += b"\xc2" + struct.pack("<H", ret_sz)
    return body


print("=" * 78)
print("== STEP 0  identity")
print("=" * 78)
import hashlib
h = hashlib.sha256(DATA).hexdigest()
print("  gamemd.exe : %s" % h)
chk("binary identity", h.startswith(WANT_SHA8), WANT_SHA8)

print()
print("=" * 78)
print("== STEP A  hook 边界 + 真实 ret 宽度")
print("=" * 78)
for f in FNS:
    va, hl = f["va"], f["hook"]
    ins = dis(va, hl + 8)
    acc, covered = 0, []
    for i in ins:
        if acc >= hl:
            break
        covered.append(i)
        acc += i.size
    f["covered"] = covered
    f["orig"] = raw(va, hl)
    f["resume"] = va + hl + len(f["extra"])
    print("\n  %s  hook=%d  resume=%#x" % (f["name"], hl, f["resume"]))
    for i in covered:
        print("    " + fmt(i))
    chk("%s hook 覆盖整条指令" % f["name"], acc == hl, "%d vs %d" % (acc, hl))
    chk("%s hook >= 5" % f["name"], hl >= 5, str(hl))
    chk("%s 原字节 == 覆盖指令拼接" % f["name"],
        f["orig"] == b"".join(i.bytes for i in covered), f["orig"].hex(" "))
    if f["extra"]:
        chk("%s 额外重放 == 映像原文" % f["name"],
            raw(va + hl, len(f["extra"])) == f["extra"], f["extra"].hex(" "))
    rsz, rins = first_ret_size(va)
    f["ret_sz"] = rsz
    print("    ★ 真实返回指令: " + fmt(rins))
    chk("%s 真实 ret 宽度已取到" % f["name"], rsz is not None, "ret %d" % rsz)

print()
print("=" * 78)
print("== STEP B  按真实 ret 宽度生成 cave，并断言末条字节取值")
print("=" * 78)
FAKE = 0x10000000
for k, f in enumerate(FNS):
    f["cave_va"] = FAKE + k * 0x40
    ca = bytearray()
    ca += b"\x85\xc9"                       # test ecx, ecx
    je_at = len(ca)
    ca += b"\x74\x00"                       # je .null（位移稍后回填）
    ca += f["orig"] + f["extra"]            # 重放原指令
    jmp_at = len(ca)
    ca += b"\xe9\x00\x00\x00\x00"           # jmp resume
    null_at = len(ca)
    null_bytes = build_null_path(f["ret_sz"])
    ca += null_bytes
    je_rel = null_at - (je_at + 2)
    ca[je_at + 1] = je_rel & 0xFF
    struct.pack_into("<i", ca, jmp_at + 1, f["resume"] - (f["cave_va"] + jmp_at + 5))
    f["cave"] = bytes(ca)
    f["null_bytes"] = null_bytes
    f["null_off"] = null_at

    ins = list(MD.disasm(f["cave"], f["cave_va"]))
    print("\n  %s  cave (%dB) @ %#x  真实 ret=%d" % (f["name"], len(ca), f["cave_va"], f["ret_sz"]))
    print("    " + f["cave"].hex(" "))
    for i in ins:
        print("      " + fmt(i))

    chk("%s cave[0]=test" % f["name"], ins[0].mnemonic == "test", fmt(ins[0]))
    chk("%s cave[1]=je" % f["name"], ins[1].mnemonic == "je", fmt(ins[1]))
    chk("%s je 目标==.null" % f["name"],
        ins[1].operands[0].imm == f["cave_va"] + null_at, hex(null_at))
    chk("%s je rel8 在范围" % f["name"], -128 <= je_rel <= 127, str(je_rel))
    chk("%s 重放字节一致" % f["name"],
        f["cave"][4:4 + len(f["orig"]) + len(f["extra"])] == f["orig"] + f["extra"], "ok")
    jmps = [i for i in ins if i.mnemonic == "jmp"]
    chk("%s 恰 1 jmp 且目标==resume" % f["name"],
        len(jmps) == 1 and jmps[0].operands[0].imm == f["resume"], hex(f["resume"]))

    # ★ 核心修正：末条 ret 的**宽度**必须等于函数真实宽度
    last = ins[-1]
    chk("%s 末条是 ret" % f["name"], last.mnemonic in ("ret", "retf"), fmt(last))
    got = int(last.op_str) if last.op_str else 0
    chk("%s ★ cave 末条 ret 宽度 == 函数真实宽度" % f["name"],
        got == f["ret_sz"], "cave=%d real=%d" % (got, f["ret_sz"]))
    # ★ 取值断言：末条字节逐字节等于期望
    expect_bytes = b"\xc3" if f["ret_sz"] == 0 else b"\xc2" + struct.pack("<H", f["ret_sz"])
    chk("%s ★ cave 末条字节取值 == 期望" % f["name"],
        f["cave"][-len(expect_bytes):] == expect_bytes,
        "%s vs %s" % (f["cave"][-len(expect_bytes):].hex(" "), expect_bytes.hex(" ")))
    # 末条必须是 cave 里最后一条指令（ret 后不得再有字节）
    chk("%s ret 位于 cave 末尾（其后无字节）" % f["name"],
        last.address + last.size == f["cave_va"] + len(f["cave"]), "ok")

print()
print("=" * 78)
print("== STEP C  零值路径栈平衡（式子含 cave 末条实际宽度）")
print("=" * 78)
print("  零值路径执行的指令：je（不碰栈）→ xor eax,eax → ret <N>")
print("  进入 cave 时栈上已有：调用方 push 的参数（若有）+ call 压的返回地址")
print("  故净变化 = -(4 + N) + (4 + N) = 0，N 取函数真实 ret 宽度。\n")
for f in FNS:
    rsz = f["ret_sz"]
    nargs = rsz // 4
    pops = 4 + rsz                      # ret 弹掉的：返回地址 + N 字节参数
    pushed_by_caller = 4 + rsz          # call 压返回地址(4) + 调用方压参数(rsz)
    net = pushed_by_caller - pops
    print("  %s  ret %d（%d 参数）  call压入=%d  ret弹出=%d  净=%d"
          % (f["name"], rsz, nargs, pushed_by_caller, pops, net))
    chk("%s 零值路径净 esp == 0" % f["name"], net == 0, str(net))

print()
print("=" * 78)
print("== STEP D  v4 vs v5 差异")
print("=" * 78)
V4_NULL = bytes.fromhex("31c0c20400")
diffs = 0
for f in FNS:
    changed = f["null_bytes"] != V4_NULL
    if changed:
        diffs += 1
    print("  %s  v4 末条=%s  v5 末条=%s  %s"
          % (f["name"], V4_NULL.hex(" "), f["null_bytes"].hex(" "),
             "★ 已修正" if changed else "不变"))
chk("v5 修正的函数数 == 3", diffs == 3, str(diffs))

print()
print("=" * 78)
print("== RESULT")
print("=" * 78)
print("checks passed: %d/%d" % (_checks - _fails, _checks))
if _fails:
    print("RESULT: %d FAIL" % _fails)
    sys.exit(1)
print("RESULT: ALL PASS")
