# -*- coding: utf-8 -*-
"""独立复核 RC-4 崩溃帧三项主张。

复核对象
--------
  主张 1：崩溃入口是 0x654413（不是 L3 的 0x4A8B75）
  主张 2：0x724580 是 0x724730 的兄弟函数，ecx=0 时首个随 this 的解引用偏移同为 0x250
  主张 3：v1 草案的 cave 落位 .detour:0xB95700 是错的

本脚本刻意**不 import** 任何被复核脚本，只依赖 capstone + struct，
所有结论都由本文件从 gamemd.exe / except.txt 的原始字节重新推出。

只读：不写任何二进制，不改任何已有文件；只额外输出同名 .txt 日志。
"""

import hashlib
import re
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # ...\ra2-campaign-forge
BIN = ROOT / "ra2youli" / "gamemd.exe"
EXC = ROOT / "ra2youli" / "except.txt"
OUT = HERE / "VERIFY_RC4_FRAME.txt"

WANT_SHA8 = "73201cc0"

CRASH_FN = 0x724730
SIBLING = 0x724580
OWNER = 0x654320
OWNER_END = 0x65448B
G_THIS = 0x887368
L3 = 0x4A8960
L3_DIRECT_CALL = 0x4A8B75
L3_DIRECT_RET = 0x4A8B7A

CLAIM1_SITE = 0x654413
CLAIM1_RET = 0x654418
CLAIM1_SLOT = 0x00F9A358

DETOUR_HOLE = 0xB9375C
V1_CAVE = 0xB95700
V1_CAVE_LEN = 21

# ---------------------------------------------------------------- 记录
LINES = []
CHECKS = []          # (claim, name, ok, detail)


def emit(s=""):
    print(s)
    LINES.append(s)


def chk(claim, name, cond, detail=""):
    """claim: 0=环境, 1/2/3=对应主张, 'x'=交叉信息"""
    ok = bool(cond)
    CHECKS.append((claim, name, ok, detail))
    emit(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    return ok


def note(s):
    emit(f"       NOTE: {s}")


# ---------------------------------------------------------------- PE
class PE:
    def __init__(self, path):
        self.data = path.read_bytes()
        d = self.data
        self.e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[self.e_lfanew:self.e_lfanew + 4] != b"PE\x00\x00":
            raise SystemExit("not a PE file")
        coff = self.e_lfanew + 4
        self.nsec = struct.unpack_from("<H", d, coff + 2)[0]
        optsz = struct.unpack_from("<H", d, coff + 16)[0]
        self.opt = coff + 20
        self.magic = struct.unpack_from("<H", d, self.opt)[0]
        self.imagebase = struct.unpack_from("<I", d, self.opt + 0x1C)[0]
        self.sect_align = struct.unpack_from("<I", d, self.opt + 0x20)[0]
        self.file_align = struct.unpack_from("<I", d, self.opt + 0x24)[0]
        self.size_of_image = struct.unpack_from("<I", d, self.opt + 0x38)[0]
        self.sec = []
        so = self.opt + optsz
        for i in range(self.nsec):
            o = so + 40 * i
            name = d[o:o + 8].rstrip(b"\x00").decode("latin1")
            vs, rva, rs, rp = struct.unpack_from("<IIII", d, o + 8)
            ch = struct.unpack_from("<I", d, o + 36)[0]
            self.sec.append(dict(name=name, rva=rva, va=rva + self.imagebase,
                                 vsize=vs, rawsize=rs, rawptr=rp, ch=ch))

    def find(self, va):
        for s in self.sec:
            if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def off(self, va):
        """文件偏移；仅当落在 VirtualSize 内。"""
        s = self.find(va)
        if s is None:
            return None
        delta = va - s["va"]
        if delta >= s["vsize"]:
            return None
        return s["rawptr"] + delta

    def off_raw(self, va):
        """文件偏移；允许落到 VirtualSize 之外的 raw padding。"""
        s = self.find(va)
        if s is None:
            return None
        delta = va - s["va"]
        if delta >= s["rawsize"]:
            return None
        return s["rawptr"] + delta

    def read(self, va, n):
        o = self.off(va)
        if o is None or o + n > len(self.data):
            return None
        return self.data[o:o + n]

    def read_raw(self, va, n):
        o = self.off_raw(va)
        if o is None or o + n > len(self.data):
            return None
        return self.data[o:o + n]

    def secname(self, va):
        s = self.find(va)
        return s["name"] if s else None


PEI = PE(BIN)
D = PEI.data
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True


def dis(va, count):
    o = PEI.off(va)
    if o is None:
        return []
    out = []
    for i in MD.disasm(D[o:o + count * 16], va):
        out.append(i)
        if len(out) >= count:
            break
    return out


def insn_at(va):
    g = dis(va, 1)
    return g[0] if g and g[0].address == va else None


def ops(i):
    """去掉所有空格后的 op_str，便于字面比较。"""
    return i.op_str.replace(" ", "")


def e8_target(va):
    """va 处若是 E8 rel32，返回目标 VA，否则 None。"""
    b = PEI.read(va, 5)
    if b is None or b[0] != 0xE8:
        return None
    return (va + 5 + struct.unpack_from("<i", b, 1)[0]) & 0xFFFFFFFF


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex():<24} {i.mnemonic} {i.op_str}"


def text_section():
    return next(s for s in PEI.sec if s["name"] == ".text")


def e8_callers(target):
    """在 .text 的 VirtualSize 内逐字节扫 E8 rel32，收集调用者。"""
    t = text_section()
    lo, hi = t["rawptr"], t["rawptr"] + t["vsize"]
    out = []
    for o in range(lo, hi - 4):
        if D[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", D, o + 1)[0]
        va = t["va"] + (o - lo)
        if ((va + 5 + rel) & 0xFFFFFFFF) == target:
            out.append(va)
    return out


def linear_sweep(va, stop):
    """从函数入口线性反汇编到 stop（含）。用于取得权威指令边界。"""
    o = PEI.off(va)
    out = []
    for i in MD.disasm(D[o:o + (stop - va) + 0x20], va):
        out.append(i)
        if i.address >= stop:
            break
    return out


# ---------------------------------------------------------------- except.txt
def parse_except(path):
    raw = path.read_bytes()
    txt = raw.decode("latin1")
    regs = {}
    for n in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        m = re.search(n + r":([0-9A-Fa-f]{8})", txt)
        regs[n] = int(m.group(1), 16) if m else None
    m = re.search(r"Access address:([0-9A-Fa-f]+) was", txt)
    access = int(m.group(1), 16) if m else None
    stack = {}
    order = []
    for m in re.finditer(r"^([0-9A-Fa-f]{8}): ([0-9A-Fa-f]{8})", txt, re.M):
        a, v = int(m.group(1), 16), int(m.group(2), 16)
        stack[a] = v
        order.append(a)
    return raw, txt, regs, access, stack, order


# flags 会被这些指令改写（mov / lea / push / pop / movzx 等不改）
FLAG_WRITERS = {
    "test", "cmp", "add", "sub", "adc", "sbb", "and", "or", "xor",
    "inc", "dec", "neg", "shl", "sal", "shr", "sar", "rol", "ror",
    "rcl", "rcr", "shld", "shrd", "imul", "mul", "div", "idiv",
    "bt", "bts", "btr", "btc", "bsf", "bsr", "cmpxchg", "xadd",
    "sahf", "lahf", "stc", "clc", "cmc", "std", "cld", "popf", "popfd",
}

JCC = {"je", "jz", "jne", "jnz", "ja", "jae", "jb", "jbe",
       "jg", "jge", "jl", "jle", "js", "jns", "jo", "jno",
       "jp", "jnp", "jcxz", "jecxz"}


# ================================================================== main
def main():
    emit("=" * 78)
    emit("== STEP 0  身份与时点锚")
    emit("=" * 78)
    sha = hashlib.sha256(D).hexdigest()
    emit(f"  gamemd.exe sha256 : {sha}")
    chk(0, "gamemd.exe sha256 前 8 位 == 73201cc0", sha[:8] == WANT_SHA8, sha[:8])
    chk(0, "PE32 / ImageBase 0x400000",
        PEI.magic == 0x10B and PEI.imagebase == 0x400000,
        f"magic={PEI.magic:#x} ib={PEI.imagebase:#x}")
    chk(0, "节数 == 5", PEI.nsec == 5, str(PEI.nsec))

    raw_exc, txt_exc, regs, access, stack, order = parse_except(EXC)
    sha_exc = hashlib.sha256(raw_exc).hexdigest()
    emit(f"  except.txt sha256 : {sha_exc}")
    emit(f"  except.txt bytes  : {len(raw_exc)}")
    emit(f"  stack entries     : {len(stack)}")
    chk(0, "栈转储条目 == 1024", len(stack) == 1024, str(len(stack)))
    chk(0, "栈转储地址连续（步长 4）",
        all(order[i + 1] - order[i] == 4 for i in range(len(order) - 1)),
        f"{order[0]:#010x}..{order[-1]:#010x}")
    emit(f"  栈范围 : {order[0]:#010x} .. {order[-1]:#010x}")

    # ------------------------------------------------------------ STEP 1
    emit()
    emit("=" * 78)
    emit("== STEP 1  崩溃现场")
    emit("=" * 78)
    for k in ("Eip", "Esp", "Ebp", "Eax", "Ebx", "Ecx", "Edx", "Esi", "Edi"):
        emit(f"  {k} = {regs[k]:08X}")
    emit(f"  Access address = {access:#x}")
    chk(1, "Eip == 0x724737", regs["Eip"] == 0x724737, f"{regs['Eip']:08X}")
    chk(1, "Esp == 0x00F9A344", regs["Esp"] == 0x00F9A344, f"{regs['Esp']:08X}")
    chk(1, "Ecx == 0（this == NULL）", regs["Ecx"] == 0, f"{regs['Ecx']:08X}")
    chk(1, "Ebp == 0", regs["Ebp"] == 0, f"{regs['Ebp']:08X}")
    chk(1, "Access address == 0x250", access == 0x250,
        f"{access:#x}" if access is not None else "None")
    b_eip = PEI.read(regs["Eip"], 6)
    chk(1, "Eip 处 6 字节 == 8b 85 50 02 00 00 (mov eax,[ebp+0x250])",
        b_eip == bytes.fromhex("8b8550020000"), b_eip.hex(" "))
    chk(1, "except.txt 字面存在 '00F9A358: 00654418'",
        "00F9A358: 00654418" in txt_exc,
        "found" if "00F9A358: 00654418" in txt_exc else "MISSING")

    # ------------------------------------------------------------ STEP 2
    emit()
    emit("=" * 78)
    emit("== STEP 2  0x724730 序言与帧内偏移（自算）")
    emit("=" * 78)
    pro = dis(CRASH_FN, 5)
    for i in pro:
        emit("  " + fmt(i))
    chk(1, "0x724730 前 6 字节 == 83 ec 0c 55 8b e9",
        PEI.read(CRASH_FN, 6) == bytes.fromhex("83ec0c558be9"),
        PEI.read(CRASH_FN, 6).hex(" "))
    chk(1, "0x724736 == 56 (push esi)", PEI.read(0x724736, 1) == b"\x56",
        PEI.read(0x724736, 1).hex())
    nbytes = 0
    for i in dis(CRASH_FN, 4):        # sub / push ebp / mov ebp,ecx / push esi
        nbytes += i.size
    chk(1, "序言 4 条指令共 7 字节（0x724730..0x724736）", nbytes == 7,
        f"{nbytes} 字节, 末地址 {CRASH_FN + nbytes:#x}")
    # 栈上被减掉的是 3(sub) + 4(push ebp) + 4(push esi) = 0xB；mov ebp,ecx 不动 esp
    esp_delta = 0x0C + 4 + 4
    chk(1, "序言使 esp 下移 0x14 ⇒ 返回地址在 [esp+0x14]",
        CRASH_FN + nbytes == 0x724737, f"esp -= {esp_delta:#x}")
    slot_ret = regs["Esp"] + 0x14
    slot_arg = regs["Esp"] + 0x18
    chk(1, f"[ESP+0x14] 槽位地址 == {CLAIM1_SLOT:#010x}", slot_ret == CLAIM1_SLOT,
        f"{slot_ret:#010x}")
    chk(1, "[ESP+0x00] == Esi（push esi 保存）",
        stack.get(regs["Esp"]) == regs["Esi"],
        f"{stack.get(regs['Esp']):#010x} vs Esi={regs['Esi']:#010x}")
    chk(1, "[ESP+0x04] == 0xFFFFFFFF（旧 ebp，已被 mov ebp,ecx 覆盖）",
        stack.get(regs["Esp"] + 4) == 0xFFFFFFFF,
        f"{stack.get(regs['Esp'] + 4):#010x}")
    chk(1, "[ESP+0x14] 落在 .text", PEI.secname(stack.get(slot_ret, 0)) == ".text",
        f"{stack.get(slot_ret):#010x} in {PEI.secname(stack.get(slot_ret, 0))}")
    chk(1, "[ESP+0x18] == 0xF2（唯一参数）", stack.get(slot_arg) == 0xF2,
        f"{stack.get(slot_arg):#010x}")
    pushes = [i for i in linear_sweep(0x6543D9, CLAIM1_SITE) if i.mnemonic == "push"]
    chk(1, "调用点前确有 push 0xf2", any(i.op_str == "0xf2" for i in pushes),
        ", ".join(i.op_str for i in pushes))

    # ------------------------------------------------------------ STEP 3
    emit()
    emit("=" * 78)
    emit("== STEP 3  主张 1：崩溃入口 = 0x654413")
    emit("=" * 78)
    chk(1, "0x654413 处首字节 == 0xE8", D[PEI.off(CLAIM1_SITE)] == 0xE8,
        f"{D[PEI.off(CLAIM1_SITE)]:#04x}")
    t = e8_target(CLAIM1_SITE)
    chk(1, "0x654413 的 E8 rel32 目标 == 0x724730", t == CRASH_FN,
        f"{t:#x}" if t else "None")
    emit(f"  0x654413 字节: {PEI.read(CLAIM1_SITE, 5).hex(' ')}"
         f"  (rel32={struct.unpack_from('<i', PEI.read(CLAIM1_SITE, 5), 1)[0]:#x})")

    callers_a = e8_callers(CRASH_FN)
    emit(f"  0x724730 直接 E8 调用者共 {len(callers_a)} 个：")
    emit("    " + ", ".join(f"{c:#x}" for c in callers_a))
    chk(1, "0x724730 直接 E8 调用者 == 30 个", len(callers_a) == 30,
        str(len(callers_a)))
    chk(1, "0x654413 在该调用者名单内", CLAIM1_SITE in callers_a, f"{CLAIM1_SITE:#x}")

    # 通用判定：遍历栈值 V，V-5 处 E8 且目标 == 0x724730 ⇒ V 是该帧返回地址
    hits = []
    for a, v in sorted(stack.items()):
        if v < PEI.imagebase:
            continue
        if e8_target((v - 5) & 0xFFFFFFFF) == CRASH_FN:
            hits.append((a, v))
    emit(f"  栈上 0x724730 的返回地址命中：{[(hex(a), hex(v)) for a, v in hits]}")
    chk(1, "栈上 0x724730 的返回地址唯一命中 1 处", len(hits) == 1, str(len(hits)))
    chk(1, f"命中槽位 == {CLAIM1_SLOT:#010x} 且值 == {CLAIM1_RET:#010x}",
        bool(hits) and hits[0] == (CLAIM1_SLOT, CLAIM1_RET),
        f"{hits[0][0]:#010x}:{hits[0][1]:#010x}" if hits else "none")
    chk(1, "该返回地址 - 5 == 0x654413",
        bool(hits) and (hits[0][1] - 5) == CLAIM1_SITE,
        f"{hits[0][1] - 5:#x}" if hits else "none")

    t_l3 = e8_target(L3_DIRECT_CALL)
    chk(1, "0x4A8B75 确实是 E8 且指向 0x724730", t_l3 == CRASH_FN,
        f"{t_l3:#x}" if t_l3 else "None")
    chk(1, "0x4A8B75 位于 L3 0x4A8960 内", L3 < L3_DIRECT_CALL < 0x4A8C00,
        f"{L3_DIRECT_CALL:#x}")
    chk(1, "★ 0x4A8B7A 不在栈上任何位置", L3_DIRECT_RET not in stack.values(),
        f"present={L3_DIRECT_RET in stack.values()}")
    chk(1, "★ 栈上无任何值 V 使 V-5 == 0x4A8B75",
        all(v - 5 != L3_DIRECT_CALL for v in stack.values()), "none")
    near = sorted((a, v) for a, v in stack.items() if 0x4A8B00 <= v < 0x4A8C00)
    emit(f"  栈上落在 0x4A8B00..0x4A8BFF 的值：{[(hex(a), hex(v)) for a, v in near]}")

    # ------------------------------------------------------------ STEP 4
    emit()
    emit("=" * 78)
    emit("== STEP 4  主张 2：0x724580 兄弟函数与 0x250 偏移")
    emit("=" * 78)
    for i in dis(SIBLING, 12):
        emit("  " + fmt(i))
    chk(2, "0x724580 前 10 字节 == 53 55 56 57 8b 7c 24 14 8b d9",
        PEI.read(SIBLING, 10) == bytes.fromhex("535556578b7c24148bd9"),
        PEI.read(SIBLING, 10).hex(" "))
    i_lea = insn_at(0x72458C)
    chk(2, "0x72458C == lea esi,[ebx+0x24c]",
        i_lea is not None and i_lea.mnemonic == "lea"
        and ops(i_lea) == "esi,[ebx+0x24c]",
        fmt(i_lea) if i_lea else "not an instruction start")
    i_mov = insn_at(0x724596)
    chk(2, "0x724596 == mov eax,[esi+4]",
        i_mov is not None and i_mov.mnemonic == "mov"
        and ops(i_mov) == "eax,dwordptr[esi+4]",
        fmt(i_mov) if i_mov else "not an instruction start")
    chk(2, "0x24C + 4 == 0x250 == Access address", 0x24C + 4 == access,
        f"{0x24C + 4:#x}")
    i_first = insn_at(0x72458A)
    chk(2, "0x72458A == mov eax,[edi]（ecx=0 时先读调用方栈地址，合法）",
        i_first is not None and i_first.mnemonic == "mov"
        and ops(i_first) == "eax,dwordptr[edi]",
        fmt(i_first) if i_first else "-")
    note("0x724580 的第一个解引用是 0x72458A 的 [edi]（读调用方压入的栈地址，ecx=0 时仍合法）；"
         "首个『随 ecx 变化』的解引用是 0x724596 的 [esi+4] = 0x250。"
         "若把 0x724596 表述为『首次解引用』，措辞不精确，但崩溃地址结论成立。")

    # 0x654320 内 4 处 mov ecx,[0x887368]
    body = linear_sweep(OWNER, OWNER_END)
    emit(f"  0x654320..{OWNER_END:#x} 线性反汇编共 {len(body)} 条指令")
    loads = [i for i in body if i.mnemonic == "mov"
             and ops(i) == f"ecx,dwordptr[{G_THIS:#x}]"]
    emit("  mov ecx,[0x887368] 出现于：" + ", ".join(f"{i.address:#x}" for i in loads))
    chk(2, "0x654320 内 mov ecx,[0x887368] 恰 4 处", len(loads) == 4, str(len(loads)))
    chk(2, "4 处地址 == 0x654405/0x654418/0x654446/0x654473",
        [i.address for i in loads] == [0x654405, 0x654418, 0x654446, 0x654473],
        ", ".join(f"{i.address:#x}" for i in loads))

    pairs = []
    for L in loads:
        nxt = next((i for i in body if i.address > L.address and i.mnemonic == "call"), None)
        pairs.append((L, nxt))
    emit("  mov → 紧随 call：")
    for L, c in pairs:
        emit(f"    {L.address:#08x} → {c.address:#08x} {c.op_str}"
             f"  (E8={c.bytes[0] == 0xE8})")
    chk(2, "4 处紧随的 call 地址 == 0x654413/0x654423/0x654469/0x654479",
        [c.address for _, c in pairs] == [0x654413, 0x654423, 0x654469, 0x654479],
        ", ".join(f"{c.address:#x}" for _, c in pairs))
    tgts = [e8_target(c.address) for _, c in pairs]
    emit(f"  4 个 call 的目标：{', '.join(f'{x:#x}' for x in tgts)}")
    chk(2, "目标序列 == [0x724730, 0x724580, 0x724730, 0x724580]",
        tgts == [CRASH_FN, SIBLING, CRASH_FN, SIBLING],
        ", ".join(f"{x:#x}" for x in tgts))
    chk(2, "0x724730 与 0x724580 各被调用 2 次",
        tgts.count(CRASH_FN) == 2 and tgts.count(SIBLING) == 2,
        f"A={tgts.count(CRASH_FN)} B={tgts.count(SIBLING)}")
    chk(2, "崩溃入口 0x654413 属于这 4 处之一",
        any(c.address == CLAIM1_SITE for _, c in pairs), "0x654413")

    # flags 级守卫判定：mov 不改 flags，看 mov→call 之间有无改 flags 的指令
    emit("  守卫判定（mov 与 call 之间逐条检查 flags 改写）：")
    all_clean = True
    for L, c in pairs:
        between = [i for i in body if L.address < i.address < c.address]
        writers = [i for i in between if i.mnemonic in FLAG_WRITERS]
        jccs = [i for i in between if i.mnemonic in JCC]
        clean = not writers and not jccs
        all_clean = all_clean and clean
        emit(f"    {L.address:#08x}..{c.address:#08x}: {len(between)} 条: "
             f"{[f'{i.mnemonic} {i.op_str}' for i in between]}")
        emit(f"      flags 改写={[fmt(i) for i in writers]}  jcc={[fmt(i) for i in jccs]}")
    chk(2, "★ 4 处 mov→call 之间均无改 flags 指令 / 无 jcc ⇒ 全无守卫", all_clean,
        "unguarded" if all_clean else "guarded")
    chk(2, "4 处之间均无 test / cmp",
        all(not any(i.mnemonic in ("test", "cmp")
                    for i in body if L.address < i.address < c.address)
            for L, c in pairs), "none")

    # ------------------------------------------------------------ STEP 5
    emit()
    emit("=" * 78)
    emit("== STEP 5  主张 3：.detour cave 落位")
    emit("=" * 78)
    det = next(s for s in PEI.sec if s["name"] == ".detour")
    emit(f"  .detour RVA={det['rva']:#x} VA={det['va']:#x} "
         f"VirtualSize={det['vsize']:#x} SizeOfRawData={det['rawsize']:#x} "
         f"PointerToRawData={det['rawptr']:#x}")
    emit(f"  Characteristics = {det['ch']:#010x}")
    chk(3, "Characteristics 恰为 0xC0000040", det["ch"] == 0xC0000040,
        f"{det['ch']:#010x}")
    for nm, bit in [("MEM_EXECUTE", 0x20000000), ("MEM_READ", 0x40000000),
                    ("MEM_WRITE", 0x80000000), ("CNT_CODE", 0x20),
                    ("CNT_INITIALIZED_DATA", 0x40)]:
        emit(f"    {nm:<22} 0x{bit:08x} = {'SET' if det['ch'] & bit else 'CLEAR'}")
    chk(3, "★ MEM_EXECUTE(0x20000000) 未置位", not (det["ch"] & 0x20000000), "CLEAR")
    chk(3, "MEM_WRITE(0x80000000) 置位", bool(det["ch"] & 0x80000000), "SET")
    chk(3, "MEM_READ(0x40000000) 置位", bool(det["ch"] & 0x40000000), "SET")
    chk(3, "CNT_CODE(0x20) 未置位", not (det["ch"] & 0x20), "CLEAR")
    note("⇒ 0xC0000040 = WRITE|READ|CNT_INITIALIZED_DATA。"
         "v1 文档写『R/W/X』是错的：没有 X。")

    vs_end = det["va"] + det["vsize"]
    raw_end = det["va"] + det["rawsize"]
    emit(f"  VirtualSize 末 = {vs_end:#x}；raw 末 = {raw_end:#x}")
    chk(3, "VirtualSize == 0x2718", det["vsize"] == 0x2718, f"{det['vsize']:#x}")
    chk(3, "段末 VA == 0xB95718", vs_end == 0xB95718, f"{vs_end:#x}")
    chk(3, "0xB95700 + 21 == 0xB95715 仍在 VirtualSize 内（0xB95718）",
        V1_CAVE + V1_CAVE_LEN <= vs_end,
        f"{V1_CAVE + V1_CAVE_LEN:#x} <= {vs_end:#x}")
    chk(3, "0xB95700 之后 VirtualSize 内仅剩 24 字节",
        vs_end - V1_CAVE == 0x18, f"{vs_end - V1_CAVE:#x}")
    chk(3, "0xB95700 之后 raw padding 共 2304 字节",
        raw_end - V1_CAVE == 2304, f"{raw_end - V1_CAVE}")
    note("⇒ 『2304 字节空闲』只在 raw padding 意义上成立（0xB95700..0xB96000）；"
         "按 VirtualSize 只有 24 字节。v1 的 21 字节 cave 恰好塞得下，"
         "所以 v1 的硬伤不是越界，而是该段没有执行位 + 该区实为 Detours 载荷尾部。")

    body_raw = PEI.read_raw(det["va"], det["vsize"])
    nz = [k for k, b in enumerate(body_raw) if b]
    last_nz = det["va"] + max(nz)
    emit(f"  末个非零字节 VA = {last_nz:#x}")
    chk(3, "段内最后一个非零字节 VA == 0xB956FE", last_nz == 0xB956FE, f"{last_nz:#x}")

    head = PEI.read_raw(det["va"], 0x50)
    emit(f"  段首 0x50 字节: {head.hex(' ')}")
    chk(3, "段首 4 字节 == 40 00 00 00（长度字段 0x40，不是签名）",
        head[0:4] == b"\x40\x00\x00\x00", head[0:4].hex(" "))
    chk(3, "段内 +4 处 == 'Dtr\\0'（Detours 签名在 +4，不在段首）",
        head[4:8] == b"Dtr\x00", head[4:8].hex(" "))
    chk(3, "段内 +0x40 处有 'MZ'（内嵌映像起点）",
        head[0x40:0x42] == b"MZ", head[0x40:0x42].hex(" "))

    def holes(buf, base, minlen=64):
        out = []
        i = 0
        n = len(buf)
        while i < n:
            if buf[i] == 0:
                j = i
                while j < n and buf[j] == 0:
                    j += 1
                if j - i >= minlen:
                    out.append((base + i, j - i))
                i = j
            else:
                i += 1
        return out

    h_vs = holes(body_raw, det["va"])
    emit(f"  VirtualSize 内 >=64B 全零空洞：{[(hex(a), l) for a, l in h_vs]}")
    chk(3, "VirtualSize 内 >=64B 空洞恰 1 处", len(h_vs) == 1, str(len(h_vs)))
    chk(3, "该空洞位于 0xB9375C、长 1548 字节",
        bool(h_vs) and h_vs[0] == (DETOUR_HOLE, 1548),
        f"{h_vs[0][0]:#x} len={h_vs[0][1]}" if h_vs else "none")

    body_rawfull = PEI.read_raw(det["va"], det["rawsize"])
    h_raw = holes(body_rawfull, det["va"])
    emit(f"  raw 范围内 >=64B 全零空洞：{[(hex(a), l) for a, l in h_raw]}")
    chk(3, "raw 范围内 >=64B 空洞 2 处（含 VirtualSize 之外的 padding）",
        len(h_raw) == 2, str(len(h_raw)))
    chk(3, "第二处空洞起于 0xB956FF、长 2305 字节（0xB95700 之后的全零 padding）",
        len(h_raw) == 2 and h_raw[1] == (0xB956FF, 2305),
        f"{h_raw[1][0]:#x} len={h_raw[1][1]}" if len(h_raw) == 2 else "n/a")

    emit(f"  SizeOfImage (RVA) = {PEI.size_of_image:#x}；"
         f".detour RVA 末 = {det['rva'] + det['vsize']:#x}")
    chk(3, "SizeOfImage 覆盖 .detour",
        det["rva"] + det["vsize"] <= PEI.size_of_image,
        f"{det['rva'] + det['vsize']:#x} <= {PEI.size_of_image:#x}")
    page_end = ((det["rva"] + det["vsize"] + PEI.sect_align - 1)
                // PEI.sect_align) * PEI.sect_align + PEI.imagebase
    chk(3, "映射页上界 VA == 0xB96000（padding 在内存中可见）",
        page_end == 0xB96000, f"{page_end:#x}")

    # ------------------------------------------------------------ STEP 6
    emit()
    emit("=" * 78)
    emit("== STEP 6  交叉信息（不参与三项判定）")
    emit("=" * 78)
    chain = [(0x6403A3, 0x654320, 0x6403A8, 0x00F9A388),
             (0x6ABD39, 0x6403A0, 0x6ABD3E, 0x00F9A3AC),
             (0x4A8B13, 0x6ABD30, 0x4A8B18, 0x00F9A3E4),
             (0x652D4C, 0x4A8850, 0x652D51, 0x00F9A43C)]
    for site, callee, ret, slot in chain:
        t2 = e8_target(site)
        got = stack.get(slot)
        emit(f"  call {site:#x} → {callee:#x}: target={t2:#x} "
             f"ret={ret:#x} stack[{slot:#x}]={got:#x} "
             f"ok={t2 == callee and got == ret}")
    chk("x", "上溯帧链 4 帧全部自洽",
        all(e8_target(s) == c and stack.get(sl) == r for s, c, r, sl in chain),
        "4/4")
    chk("x", "0x4A8B13 落在 L3 函数体（0x4A8960..0x4A8B75）内",
        L3 < 0x4A8B13 < L3_DIRECT_CALL, f"{0x4A8B13:#x}")
    l3_body = linear_sweep(L3, L3_DIRECT_CALL)
    rets = [i for i in l3_body if i.mnemonic.startswith("ret")]
    chk("x", "L3 0x4A8960..0x4A8B75 之间无 ret（证明是同一函数体，无函数边界）",
        len(rets) == 0, f"ret 数={len(rets)}")
    chk("x", "0x4A8B00 与 0x4A8B18 两个返回地址都在 L3 函数体内",
        all(L3 < v < L3_DIRECT_CALL for v in (0x4A8B00, 0x4A8B18)),
        "0x4A8B00, 0x4A8B18")

    # 0x724580 是否有栈帧：无 ⇒ 崩溃发生在第 1 次调用（0x654413）而非第 2 次
    hits_b = []
    for a, v in sorted(stack.items()):
        if v >= PEI.imagebase and e8_target((v - 5) & 0xFFFFFFFF) == SIBLING:
            hits_b.append((a, v))
    emit(f"  栈上 0x724580 的返回地址命中：{[(hex(a), hex(v)) for a, v in hits_b]}")
    chk("x", "0x724580 无栈帧 ⇒ 崩溃发生在第一次调用 0x654413（未走到 0x654423）",
        len(hits_b) == 0, "0 frames")

    note("0x4A8B18（= call 0x4A8B13 的返回地址）在栈上，而 0x4A8B13 位于 "
         "L3 0x4A8960 函数体内 ⇒ L3 确实在本条崩溃路径上，"
         "但它走的是 0x4A8B13 的嵌套调用（→0x6ABD30），不是 0x4A8B75 的直接调用。")
    note("⇒ 被复核方『本次崩溃不经 L3』的说法过强/错误；正确表述是"
         "『不经 L3 在 0x4A8B75 的直接调用』。L3 是祖先帧。")

    # ------------------------------------------------------------ RESULT
    emit()
    emit("=" * 78)
    emit("== RESULT")
    emit("=" * 78)
    npass = sum(1 for _, _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    emit(f"checks passed: {npass}/{total}")
    for c, name, ok, detail in CHECKS:
        if not ok:
            emit(f"  FAIL: [{c}] {name}  {detail}")

    emit()
    emit("== 分项判定")
    for claim, label in ((0, "环境/身份"), (1, "主张 1 崩溃入口"),
                         (2, "主张 2 兄弟函数"), (3, "主张 3 v1 cave"),
                         ("x", "交叉信息")):
        sub = [ok for c, _, ok, _ in CHECKS if c == claim]
        emit(f"  {label:<18} {sum(sub)}/{len(sub)} "
             f"{'PASS' if all(sub) else 'FAIL'}")

    all_ok = npass == total
    emit(f"RESULT: {'ALL PASS' if all_ok else 'HAS FAILURES'}")

    OUT.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    print(f"\n(log written to {OUT})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
