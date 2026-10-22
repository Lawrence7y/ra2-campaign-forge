# -*- coding: utf-8 -*-
"""RC-4 修复 v5 门禁：cave 的 ret 操作数必须从**实际字节**读出并与函数自身 ret 等值。

为什么要有 v5（v4 门禁的缺陷）
------------------------------
v4 的 `_rc4_fix_v4_proof.py` STEP C 用这条断言判「零值路径栈平衡」：

    chk(..., -rsz - 4 + 4 + rsz == 0, f"ret {rsz}")

`rsz` 是函数自己的 ret 尺寸，表达式恒等于 0 ⇒ **恒真式**。它从未读取 cave 里
实际写下的 ret 操作数。于是 v4 草案把 8 条 cave 的尾部统一硬编码成 `c2 04 00`
（ret 4），而 0x724530 / 0x724540 / 0x724C00 三条实际是 `c3`（ret 0），
门禁依然 123/123 全绿 —— 部署后这三处会多弹 4 字节栈。

v5 的判据：反汇编 cave，从 capstone 指令对象里读末条 ret 的立即数 `cave_ret`，
断言 `cave_ret == fn_ret`（fn_ret 从 gamemd 原映像线性解码得到）。
另加三个负控，保证这个断言**不是恒真**：人为改坏 ret / jmp / replay 后必须变红。

栈平衡模型（实测数字，不是恒真式）
---------------------------------
零值路径（caller 已 push fn_ret 字节参数并 call）：
    净变化 = -fn_ret(参数) - 4(call 压返回地址) + 4 + cave_ret(ret 弹)
           = cave_ret - fn_ret        ⇒ 必须 == 0
注意：只有 fn_ret == 4 时它才退化成 `+fn_ret - 4`。对 c3（ret 0）函数，
`+fn_ret-4 = -4 ≠ 0`，所以那个写法本身是错的；一般式是 cave_ret - fn_ret。
非零路径（test/je 不跳 + 重放 + jmp）：
    cave 段 esp 变化必须与原映像 [va,resume) 段的 esp 变化**逐值相等** ⇒ 相对净变化 0。

纪律：只读 gamemd.exe，不写任何二进制，不启动游戏/loader，不跑 trip。
所有数字由本脚本从二进制算出，不 import 原脚本。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r"D:\Project\ra2-campaign-forge")
BIN = ROOT / "ra2youli" / "gamemd.exe"
WANT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

FAKE_BASE = 0x10000000      # cave 假想基址
CAVE_STRIDE = 0x40          # DLL 侧按 0x40 排布
CAVE_MAX = 32               # 单条 cave 上限

# va / hook（gamemd 侧被 E9+90 覆盖的字节数）/ resume（cave 末尾 jmp 的目标）
FNS = [
    dict(name="0x7241A0", va=0x7241A0, hook=5,  resume=0x7241A5),
    dict(name="0x724200", va=0x724200, hook=5,  resume=0x724205),
    dict(name="0x724520", va=0x724520, hook=10, resume=0x72452A),
    dict(name="0x724530", va=0x724530, hook=6,  resume=0x724536),
    dict(name="0x724540", va=0x724540, hook=6,  resume=0x724546),
    dict(name="0x724580", va=0x724580, hook=8,  resume=0x724588),
    dict(name="0x724730", va=0x724730, hook=6,  resume=0x724737),
    dict(name="0x724C00", va=0x724C00, hook=5,  resume=0x724C05),
]

CHECKS = []


def chk(tag, name, cond, detail=""):
    ok = bool(cond)
    CHECKS.append((tag, name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {tag:<4} {name}  {detail}")
    return ok


def info(msg):
    print(f"[INFO] {msg}")


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


# ---------------------------------------------------------------- PE / va2off
class PE:
    """自己解析节表；va2off 带完整校验（不硬编码 0x1000+(va-0x401000)）。"""

    def __init__(self, path):
        self.data = path.read_bytes()
        d = self.data
        assert d[:2] == b"MZ", "not MZ"
        e = u32(d, 0x3C)
        assert d[e:e + 4] == b"PE\x00\x00", "not PE"
        coff = e + 4
        self.nsec = u16(d, coff + 2)
        optsz = u16(d, coff + 16)
        opt = coff + 20
        self.magic = u16(d, opt)
        self.image_base = u32(d, opt + 0x1C)
        self.section_align = u32(d, opt + 0x20)
        self.file_align = u32(d, opt + 0x24)
        self.entry = u32(d, opt + 0x10)
        self.size_image = u32(d, opt + 0x38)
        self.size_headers = u32(d, opt + 0x3C)
        so = opt + optsz
        self.secs = []
        for i in range(self.nsec):
            o = so + 40 * i
            self.secs.append(dict(
                name=d[o:o + 8].rstrip(b"\x00").decode("latin1"),
                vsize=u32(d, o + 8),
                va=u32(d, o + 12) + self.image_base,
                rawsize=u32(d, o + 16),
                rawptr=u32(d, o + 20),
                chars=u32(d, o + 36),
            ))

    def sec_of(self, va):
        for s in self.secs:
            if s["va"] <= va < s["va"] + s["vsize"]:
                return s
        return None

    def va2off(self, va, n=1):
        """VA -> 文件偏移；越界/无文件支撑则抛错（校验，不静默）。"""
        s = self.sec_of(va)
        if s is None:
            raise ValueError(f"VA {va:#x} 不在任何节内")
        delta = va - s["va"]
        if delta + n > s["rawsize"]:
            raise ValueError(f"VA {va:#x} 无文件支撑（delta={delta:#x} raw={s['rawsize']:#x}）")
        off = s["rawptr"] + delta
        if off + n > len(self.data):
            raise ValueError(f"VA {va:#x} 偏移 {off:#x} 超出文件")
        return off

    def read(self, va, n):
        o = self.va2off(va, n)
        return self.data[o:o + n]

    def fmt_sections(self):
        out = []
        for s in self.secs:
            out.append(f"    {s['name']:<8} va={s['va']:#010x} vsize={s['vsize']:#09x} "
                       f"rawptr={s['rawptr']:#09x} rawsize={s['rawsize']:#09x} "
                       f"chars={s['chars']:#010x}")
        return "\n".join(out)


PEIMG = PE(BIN)
DATA = PEIMG.data
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = False


def dis(va, nbytes, limit=None):
    buf = PEIMG.read(va, nbytes)
    out = []
    for i in MD.disasm(buf, va):
        out.append(i)
        if limit is not None and len(out) >= limit:
            break
    return out


def fmt(i):
    return f"{i.address:08X}  {i.bytes.hex(' '):<26} {i.mnemonic} {i.op_str}"


def _is_reg(op, name):
    return op.type == X86_OP_REG and MD.reg_name(op.reg) == name


def esp_delta(ins):
    """单条指令对 esp 的位移；None = 无法静态确定。call 记 0（返回地址进又出）。

    只有**写** esp 的指令才影响栈；`mov eax,[esp+4]` 这类读不算。
    """
    m = ins.mnemonic
    ops = ins.operands
    if m == "push":
        return -4
    if m == "pop":
        return 4
    if m == "call":
        return 0
    if m == "ret":
        return 4 + (ops[0].imm if ops else 0)
    if m in ("pushad", "pusha"):
        return -32
    if m in ("popad", "popa"):
        return 32
    if m == "leave":
        return None
    if m in ("sub", "add") and ops and _is_reg(ops[0], "esp") and len(ops) > 1 \
            and ops[1].type == X86_OP_IMM:
        v = ops[1].imm
        return -v if m == "sub" else v
    if m == "lea" and len(ops) == 2 and _is_reg(ops[0], "esp") \
            and ops[1].type == X86_OP_MEM and ops[1].mem.base \
            and MD.reg_name(ops[1].mem.base) == "esp" and not ops[1].mem.index:
        return ops[1].mem.disp
    if m in ("mov", "xchg") and ops:
        writes_esp = _is_reg(ops[0], "esp") or (m == "xchg" and _is_reg(ops[1], "esp"))
        if writes_esp:
            return None
        return 0
    return 0


def delta_sum(insns):
    tot = 0
    for i in insns:
        d = esp_delta(i)
        if d is None:
            return None
        tot += d
    return tot


# ---------------------------------------------------------------- cave 构造
def build_cave(f, cave_va, fn_ret):
    """按 fn_ret 构造 cave：test/je + 重放 [va,resume) + jmp + null(xor/ret fn_ret)。"""
    replay = PEIMG.read(f["va"], f["resume"] - f["va"])
    ca = bytearray(b"\x85\xc9")                 # test ecx, ecx
    ca += b"\x74\x00"                           # je rel8（占位）
    ca += replay
    jmp_off = len(ca)
    ca += b"\xe9\x00\x00\x00\x00"               # jmp resume（占位）
    null_off = len(ca)
    ca += b"\x31\xc0"                           # xor eax, eax
    ca += b"\xc3" if fn_ret == 0 else b"\xc2" + struct.pack("<H", fn_ret)
    je_rel = null_off - 4
    assert -128 <= je_rel <= 127, je_rel
    ca[3] = je_rel & 0xFF
    rel = f["resume"] - (cave_va + jmp_off + 5)
    assert -0x80000000 <= rel < 0x80000000, rel
    struct.pack_into("<i", ca, jmp_off + 1, rel)
    return bytes(ca), null_off, jmp_off


# ---------------------------------------------------------------- cave 判据
def eval_cave(cave, f, fn_ret, cave_va):
    """从 cave 字节本身反推全部事实（ret 操作数、je/jmp 目标、重放段、栈变化）。"""
    r = dict(cave_va=cave_va, insns=[], parsed=False)
    ins = list(MD.disasm(bytes(cave), cave_va))
    r["insns"] = ins
    if not ins or sum(len(i.bytes) for i in ins) != len(cave):
        r.update(c7=False, c8=False, c9=False, c10=False, c11=False,
                 cave_ret=None, jmp_off=None, null_off=None, je_target=None,
                 jmp_target=None, null_net=None, nz_net=None,
                 nz_cave=None, nz_orig=None, why="cave 反汇编不完整/有尾字节")
        return r

    # --- 定位 null 块：jmp 之后的第一条指令（不借助 je 自己的目标）
    jmps = [i for i in ins if i.mnemonic == "jmp"]
    jmp_ins = jmps[0] if len(jmps) == 1 else None
    jmp_off = (jmp_ins.address - cave_va) if jmp_ins else None
    idx = ins.index(jmp_ins) if jmp_ins else -1
    null_ins = ins[idx + 1] if 0 <= idx < len(ins) - 1 else None
    null_off = (null_ins.address - cave_va) if null_ins else None

    # --- #7 ret：从指令对象读立即数，再用字节编码交叉验证
    rets = [i for i in ins if i.mnemonic == "ret"]
    cave_ret = None
    ret_bytes_ok = False
    if len(rets) == 1 and rets[0] is ins[-1]:
        ri = rets[0]
        cave_ret = ri.operands[0].imm if ri.operands else 0
        b = ri.bytes
        if b[0] == 0xC3 and len(b) == 1:
            ret_bytes_ok = (cave_ret == 0)
        elif b[0] == 0xC2 and len(b) == 3:
            ret_bytes_ok = (struct.unpack("<H", b[1:3])[0] == cave_ret)
    c7 = (cave_ret is not None and ret_bytes_ok and cave_ret == fn_ret
          and null_off is not None and rets[0].address - cave_va >= null_off)

    # --- #8 头部结构
    t = ins[0]
    test_ok = (t.mnemonic == "test" and t.bytes == b"\x85\xc9" and len(t.operands) == 2
               and all(o.type == X86_OP_REG for o in t.operands)
               and MD.reg_name(t.operands[0].reg) == "ecx"
               and MD.reg_name(t.operands[1].reg) == "ecx")
    je = ins[1] if len(ins) > 1 else None
    je_ok = (je is not None and je.mnemonic in ("je", "jz") and je.size == 2
             and len(je.operands) == 1 and je.operands[0].type == X86_OP_IMM)
    je_target = je.operands[0].imm if je_ok else None
    je_tgt_ok = (je_ok and null_off is not None and je_target == cave_va + null_off)
    je_rel = struct.unpack("<b", bytes([cave[3]]))[0] if len(cave) > 3 else 999
    je_rel_ok = (je_ok and -128 <= je_rel <= 127
                 and je_target == je.address + 2 + je_rel)
    xor_ok = (null_ins is not None and null_ins.mnemonic == "xor"
              and len(null_ins.operands) == 2
              and all(o.type == X86_OP_REG for o in null_ins.operands)
              and MD.reg_name(null_ins.operands[0].reg) == "eax"
              and MD.reg_name(null_ins.operands[1].reg) == "eax")
    c8 = bool(test_ok and je_ok and je_tgt_ok and je_rel_ok and xor_ok)

    # --- #9 恰 1 条 jmp，目标 == resume
    jmp_target = None
    if jmp_ins is not None and len(jmp_ins.operands) == 1 \
            and jmp_ins.operands[0].type == X86_OP_IMM:
        jmp_target = jmp_ins.operands[0].imm
    c9 = (jmp_ins is not None and jmp_target == f["resume"])

    # --- #10 重放段 == 原映像 [va, resume)
    replay = cave[4:jmp_off] if jmp_off is not None else None
    orig = PEIMG.read(f["va"], f["resume"] - f["va"])
    c10 = (replay is not None and replay == orig)

    # --- #11 栈平衡（两个实测数）
    null_net = nz_net = nz_cave = nz_orig = None
    if null_off is not None:
        null_d = delta_sum([i for i in ins if i.address - cave_va >= null_off])
        if null_d is not None:
            null_net = -fn_ret - 4 + null_d      # 参数(-fn_ret) + call(-4) + null 路径
    if jmp_off is not None:
        nz_cave = delta_sum([i for i in ins if i.address - cave_va < null_off])
        nz_orig = delta_sum(dis(f["va"], f["resume"] - f["va"]))
        if nz_cave is not None and nz_orig is not None:
            nz_net = nz_cave - nz_orig
    c11 = (null_net == 0 and nz_net == 0)

    r.update(parsed=True, c7=c7, c8=c8, c9=c9, c10=c10, c11=c11,
             cave_ret=cave_ret, ret_bytes_ok=ret_bytes_ok,
             test_ok=test_ok, je_ok=je_ok, je_tgt_ok=je_tgt_ok, je_rel_ok=je_rel_ok,
             xor_ok=xor_ok, je_rel=je_rel, je_target=je_target,
             jmp_off=jmp_off, null_off=null_off, jmp_target=jmp_target,
             null_net=null_net, nz_net=nz_net, nz_cave=nz_cave, nz_orig=nz_orig,
             replay=replay, why="")
    return r


def force_ret(cave, bad_ret):
    """把 cave 尾部的 ret 强制改成 bad_ret 编码（不假设当前尾部是 c3 还是 c2）。"""
    b = bytearray(cave)
    if b[-1] == 0xC3:
        b = b[:-1]
    elif b[-3] == 0xC2:
        b = b[:-3]
    else:
        raise AssertionError(f"尾部不是 ret: {bytes(b[-4:]).hex(' ')}")
    b += b"\xc3" if bad_ret == 0 else b"\xc2" + struct.pack("<H", bad_ret)
    return bytes(b)


def build_v4_style(f, cave_va):
    """原样复刻 v4 草案的 cave：尾部一律 `31 c0 c2 04 00`（ret 4）。"""
    replay = PEIMG.read(f["va"], f["resume"] - f["va"])
    ca = bytearray(b"\x85\xc9\x74\x00")
    ca += replay
    jmp_off = len(ca)
    ca += b"\xe9\x00\x00\x00\x00"
    null_off = len(ca)
    ca += b"\x31\xc0\xc2\x04\x00"
    ca[3] = (null_off - 4) & 0xFF
    struct.pack_into("<i", ca, jmp_off + 1, f["resume"] - (cave_va + jmp_off + 5))
    return bytes(ca)


def first_ret(va):
    """从函数头线性解码，返回（首条 ret 指令, 立即数, 该段全部指令）。"""
    sec = PEIMG.sec_of(va)
    end = min(sec["va"] + sec["vsize"], sec["va"] + sec["rawsize"], va + 0x800)
    ins = dis(va, end - va)
    for i in ins:
        if i.mnemonic == "ret":
            return i, (i.operands[0].imm if i.operands else 0), ins
    return None, None, ins


def main():
    print("=" * 100)
    print("== STEP 0  身份 / PE 节表 / va2off 校验")
    print("=" * 100)
    sha = hashlib.sha256(DATA).hexdigest()
    print(f"  file     : {BIN}")
    print(f"  size     : {len(DATA):#x}")
    print(f"  sha256   : {sha}")
    print(f"  MZ/PE    : {DATA[:2]!r} / {DATA[u32(DATA, 0x3C):u32(DATA, 0x3C) + 4]!r}")
    print(f"  magic    : {PEIMG.magic:#x} (PE32=0x10b)   image_base={PEIMG.image_base:#x}")
    print(f"  align    : section={PEIMG.section_align:#x} file={PEIMG.file_align:#x}")
    print(f"  entry    : {PEIMG.image_base + 0:#x} + RVA {PEIMG.entry:#x} = "
          f"{PEIMG.image_base + PEIMG.entry:#x}  ({PEIMG.sec_of(PEIMG.image_base + PEIMG.entry)['name']})")
    print(f"  sections : {PEIMG.nsec}")
    print(PEIMG.fmt_sections())

    chk("G0", "PE32 magic", PEIMG.magic == 0x10B, f"{PEIMG.magic:#x}")
    chk("G0", "image_base == 0x400000", PEIMG.image_base == 0x400000, f"{PEIMG.image_base:#x}")
    # 本映像 FileAlignment 实测为 0x1000（不是常见的 0x200），断言用实测值而不是想当然的常量
    chk("G0", "SectionAlignment == 0x1000 且 FileAlignment 为 2 的幂且 ∈ [0x200,0x1000]",
        PEIMG.section_align == 0x1000
        and PEIMG.file_align >= 0x200 and PEIMG.file_align <= 0x1000
        and (PEIMG.file_align & (PEIMG.file_align - 1)) == 0,
        f"section={PEIMG.section_align:#x} file={PEIMG.file_align:#x}")
    chk("G0", "节表项数与遍历一致", len(PEIMG.secs) == PEIMG.nsec, str(len(PEIMG.secs)))
    # 节表自洽：VA 4K 对齐、rawptr 文件对齐、不越文件、VA 区间不重叠
    ok_align = all(s["va"] % PEIMG.section_align == 0 for s in PEIMG.secs)
    ok_file = all(s["rawptr"] % PEIMG.file_align == 0
                  and s["rawptr"] + s["rawsize"] <= len(DATA)
                  for s in PEIMG.secs)
    order = sorted(PEIMG.secs, key=lambda s: s["va"])
    ok_ovl = all(order[i]["va"] + order[i]["vsize"] <= order[i + 1]["va"]
                 for i in range(len(order) - 1))
    chk("G0", "节 VA 4K 对齐", ok_align)
    chk("G0", "节 rawptr 文件对齐且不越界", ok_file)
    chk("G0", "节 VA 区间不重叠", ok_ovl)
    # va2off 自校验：节首 VA 必须映射回节首 rawptr；所有函数 VA 必须落在 .text 且有文件支撑
    ok_rt = all(PEIMG.va2off(s["va"]) == s["rawptr"] for s in PEIMG.secs)
    chk("G0", "va2off(节首) == rawptr（节表→文件偏移自洽）", ok_rt)
    text = next(s for s in PEIMG.secs if s["name"] == ".text")
    print(f"  .text    : va={text['va']:#x} .. {text['va'] + text['vsize']:#x}  "
          f"raw={text['rawptr']:#x} .. {text['rawptr'] + text['rawsize']:#x}")
    ok_text = all(PEIMG.sec_of(f["va"]) is text for f in FNS)
    chk("G0", "8 个 VA 全部落在 .text", ok_text)
    ok_back = True
    for f in FNS:
        try:
            PEIMG.va2off(f["va"], f["resume"] - f["va"])
        except ValueError as e:
            ok_back = False
            print(f"       {e}")
    chk("G0", "8 个 VA 的 [va,resume) 均有文件支撑", ok_back)
    chk("G0", "8 个 VA 互不相同", len({f["va"] for f in FNS}) == 8)
    chk("G0", "sha256 前缀 == 73201cc0", sha.startswith("73201cc0"), sha[:8])

    # ------------------------------------------------------------ A: hook
    print()
    print("=" * 100)
    print("== STEP A  hook 段：指令边界 / resume 边界")
    print("=" * 100)
    for f in FNS:
        va, hook, resume = f["va"], f["hook"], f["resume"]
        print(f"\n  ── {f['name']}  hook={hook}  resume={resume:#x} ──")
        covered, acc = [], 0
        for i in dis(va, hook + 0x10):
            if acc >= hook:
                break
            covered.append(i)
            acc += len(i.bytes)
        for i in covered:
            print("    " + fmt(i))
        f["covered"] = covered
        f["orig_hook"] = PEIMG.read(va, hook)
        f["extra"] = resume - va - hook
        print(f"    覆盖 {acc}B / hook {hook}B   resume-va={resume - va}B   "
              f"extra(重放但保留在映像里的整指令)={f['extra']}B")

        chk(f["name"], "hook 段恰由整指令拼成（累计 == hook）", acc == hook, f"{acc} vs {hook}")
        chk(f["name"], "hook 段字节 == 覆盖指令拼接",
            f["orig_hook"] == b"".join(i.bytes for i in covered), f["orig_hook"].hex(" "))
        chk(f["name"], "hook >= 5（放得下 E9 rel32）", hook >= 5, str(hook))
        chk(f["name"], "resume >= va+hook（跳板不被截断）", resume >= va + hook,
            f"{resume:#x} >= {va + hook:#x}")
        # resume 必须是线性解码下的指令起点
        starts, a = set(), 0
        for i in dis(va, max(resume - va, hook) + 0x10):
            starts.add(i.address)
            a += len(i.bytes)
            if a > resume - va + 0x10:
                break
        chk(f["name"], "resume 是线性解码的指令起点", resume in starts, f"{resume:#x}")
        # 独立再验一次：从 resume 直接起解码，必须成功且 address == resume
        r_dec = dis(resume, 16, limit=1)
        print(f"    resume 起解码: "
              + (fmt(r_dec[0]) if r_dec else "<解码失败>"))
        chk(f["name"], "resume 处 capstone 解码成功且 address == resume",
            bool(r_dec) and r_dec[0].address == resume,
            f"{r_dec[0].address:#x}" if r_dec else "no insn")
        # extra 段（[va+hook, resume)）必须是完整指令
        ex_ok = True
        if f["extra"] > 0:
            ex, acc2 = [], 0
            for i in dis(va + hook, f["extra"] + 0x8):
                if acc2 >= f["extra"]:
                    break
                ex.append(i)
                acc2 += len(i.bytes)
            ex_ok = (acc2 == f["extra"])
            print(f"    extra 段: " + " ; ".join(f"{i.mnemonic} {i.op_str}" for i in ex))
            info(f"{f['name']} 表值 hook={hook}，但 resume-va={resume - va} ⇒ "
                 f"多 {f['extra']}B 在 cave 里重放，映像中该字节保留为死字节")
        chk(f["name"], "resume-va == hook + extra（extra 为完整指令）", ex_ok,
            f"{resume - va} == {hook} + {f['extra']}")

    # 任务书给的 (va, hook, resume) 表里，7 条满足 resume == va+hook；
    # 0x724730 的 resume 比 va+hook 多 1 字节。这不是笔误：0x724736 的 `56 push esi`
    # 是完整指令，必须一起重放进 cave，否则非零路径会丢掉 esi 的保存。
    # 这里把这个唯一例外钉成显式断言，防止「悄悄放宽」变成新的恒真门禁。
    exact = [f for f in FNS if f["resume"] == f["va"] + f["hook"]]
    inexact = [f for f in FNS if f["resume"] != f["va"] + f["hook"]]
    print(f"\n  resume == va + hook 的函数: {len(exact)}/8")
    for f in inexact:
        ex = PEIMG.read(f["va"] + f["hook"], f["extra"])
        exi = dis(f["va"] + f["hook"], f["extra"] + 0x8, limit=1)
        print(f"  ★ 例外 {f['name']}: resume-va={f['resume'] - f['va']}B, hook={f['hook']}B, "
              f"多 {f['extra']}B = {ex.hex(' ')} ({exi[0].mnemonic} {exi[0].op_str})")
    chk("RESUME", "resume != va+hook 的函数恰为 1 个且是 0x724730（已显式建模）",
        len(inexact) == 1 and inexact[0]["name"] == "0x724730",
        ", ".join(f["name"] for f in inexact) or "none")
    chk("RESUME", "该例外的 extra 字节是完整指令且长度 == extra",
        len(inexact) == 1 and inexact[0]["extra"] == 1
        and len(dis(inexact[0]["va"] + inexact[0]["hook"], 8, limit=1)[0].bytes) == 1,
        f"extra={inexact[0]['extra'] if inexact else '-'}B")

    # ------------------------------------------------------------ B: fn_ret
    print()
    print("=" * 100)
    print("== STEP B  函数自身 ret（原映像实测）")
    print("=" * 100)
    for f in FNS:
        r, n, seg = first_ret(f["va"])
        f["fn_ret"] = n
        f["fn_ret_insn"] = r
        f["head_seg"] = seg
        print(f"\n  {f['name']}: 首条 ret @ {r.address:#x}  bytes={r.bytes.hex(' ')}  "
              f"op_str={r.op_str!r}  ⇒ fn_ret = {n}")
        # 全函数范围（到下一个函数头）内的 ret 分布，仅供参考
        nxt = next((g["va"] for g in FNS if g["va"] > f["va"]), f["va"] + 0x800)
        allr = [i for i in dis(f["va"], nxt - f["va"]) if i.mnemonic == "ret"]
        dist = {}
        for i in allr:
            v = i.operands[0].imm if i.operands else 0
            dist[v] = dist.get(v, 0) + 1
        print(f"    [va, {nxt:#x}) 内 ret {len(allr)} 条，立即数分布 {dict(sorted(dist.items()))}"
              f"（守卫用函数头所在路径的首条 ret）")
        chk(f["name"], "找到主终止 ret", r is not None, f"{r.address:#x}" if r else "none")
        chk(f["name"], "ret 编码合法（c3 或 c2 imm16）",
            r.bytes[0] == 0xC3 or (r.bytes[0] == 0xC2 and len(r.bytes) == 3), r.bytes.hex(" "))

    # ------------------------------------------------------------ C: cave
    print()
    print("=" * 100)
    print("== STEP C  cave 构造 + 从实际字节读 ret（核心断言）")
    print("=" * 100)
    for k, f in enumerate(FNS):
        cave_va = FAKE_BASE + k * CAVE_STRIDE
        f["cave_va"] = cave_va
        cave, null_off, jmp_off = build_cave(f, cave_va, f["fn_ret"])
        f["cave"], f["null_off"], f["jmp_off"] = cave, null_off, jmp_off
        print(f"\n  ── {f['name']}  cave {len(cave)}B @ {cave_va:#x}  (fn_ret={f['fn_ret']}) ──")
        print(f"    {cave.hex(' ')}")
        for i in MD.disasm(cave, cave_va):
            print("      " + fmt(i))
        ev = eval_cave(cave, f, f["fn_ret"], cave_va)
        f["ev"] = ev

        chk(f["name"], "sha256 前缀 == 73201cc0", sha.startswith("73201cc0"), sha[:8])
        chk(f["name"], "cave 可完整反汇编（无尾字节）", ev["parsed"], str(len(cave)))
        chk(f["name"], "cave 头部第 1 条 == test ecx,ecx", ev["test_ok"], fmt(ev["insns"][0]))
        chk(f["name"], "cave 第 2 条 == je 且目标 == null 块起点",
            ev["je_ok"] and ev["je_tgt_ok"],
            f"je→{ev['je_target']:#x}  null@{cave_va + ev['null_off']:#x}")
        chk(f["name"], "je rel8 ∈ [-128,127]", ev["je_rel_ok"],
            f"rel8={ev['je_rel']} 目标={ev['je_target']:#x}")
        chk(f["name"], "null 块首条 == xor eax,eax", ev["xor_ok"])
        # ★ 核心：cave_ret 从指令对象读出，等值断言
        chk(f["name"], "★ cave_ret(实测) == fn_ret", ev["c7"],
            f"cave_ret={ev['cave_ret']}  fn_ret={f['fn_ret']}")
        chk(f["name"], "cave 恰 1 条 jmp 且目标 == resume", ev["c9"],
            f"jmp→{ev['jmp_target']:#x}  resume={f['resume']:#x}"
            + ("" if ev["c9"] else f"  (jmp 数={len([i for i in ev['insns'] if i.mnemonic == 'jmp'])})"))
        chk(f["name"], "重放段 == 原映像 [va,resume)", ev["c10"],
            f"cave[{4}:{ev['jmp_off']}] = {ev['replay'].hex(' ')}")
        chk(f["name"], "cave 长度 <= 32B", len(cave) <= CAVE_MAX, f"{len(cave)}B")
        chk(f["name"], "cave 长度 <= 0x40 槽位", len(cave) <= CAVE_STRIDE, f"{len(cave)}B")

    # 槽位互不重叠（DLL 侧按 0x40 排布，任何一条溢出都会压到下一条）
    ok_slot = all(FNS[i]["cave_va"] + len(FNS[i]["cave"]) <= FNS[i + 1]["cave_va"]
                  for i in range(len(FNS) - 1))
    chk("SLOT", "8 个 cave 槽位互不重叠", ok_slot,
        f"最大长度 {max(len(f['cave']) for f in FNS)}B vs 槽距 {CAVE_STRIDE:#x}B")

    # ------------------------------------------------------------ D: 栈
    print()
    print("=" * 100)
    print("== STEP D  栈平衡（实测数字，非恒真式）")
    print("=" * 100)
    print("  零值路径: 净 = -fn_ret(调用者已压的参数) - 4(call 压返回地址)")
    print("                  + 4(ret 弹返回地址) + cave_ret(ret 弹参数)")
    print("            = cave_ret - fn_ret   ⇒ 必须 == 0")
    print("  注：任务书里写的 '+fn_ret - 4' 只是 fn_ret==4 时的巧合形式；")
    print("      对 c3（fn_ret=0）函数它给出 -4，会误判。故本脚本用一般式并从字节实测 cave_ret。")
    print("  非零路径: cave 段 esp 变化 与 原映像 [va,resume) 段 esp 变化 必须逐值相等\n")
    for f in FNS:
        ev = f["ev"]
        lit = f["fn_ret"] - 4          # 任务书里的字面式 +fn_ret-4
        print(f"  {f['name']}  fn_ret={f['fn_ret']}  cave_ret={ev['cave_ret']}")
        print(f"    零值(一般式): -{f['fn_ret']}(参数) - 4(call) + 4(ret 弹返回地址)"
              f" + {ev['cave_ret']}(ret 弹参数) = {ev['null_net']}")
        print(f"    零值(任务书字面式 +fn_ret-4) = {lit}"
              + ("   [与一般式一致]" if lit == ev["null_net"] else
                 "   [★与一般式不一致：字面式仅在 fn_ret==4 时成立]"))
        print(f"    非零: cave 段 = {ev['nz_cave']}   原映像段 = {ev['nz_orig']}"
              f"   相对净变化 = {ev['nz_net']}")
        chk(f["name"], "零值路径净变化 == 0（实测 cave_ret 参与）", ev["null_net"] == 0,
            f"{ev['null_net']}")
        chk(f["name"], "非零路径净变化 == 0（cave 段 vs 原映像段）", ev["nz_net"] == 0,
            f"{ev['nz_cave']} - {ev['nz_orig']} = {ev['nz_net']}")
        # 任务书给的字面式 `+fn_ret-4` 其实等价于 fn_ret-4，只在 fn_ret==4 时为 0。
        # 这里断言「字面式与一般式的一致性 ⟺ fn_ret==4」，把这个前提钉死。
        chk(f["name"], "字面式 +fn_ret-4 与一般式一致 ⟺ fn_ret==4",
            (lit == ev["null_net"]) == (f["fn_ret"] == 4),
            f"literal={lit} general={ev['null_net']} fn_ret={f['fn_ret']}")

    # ------------------------------------------------------------ E: 负控
    print()
    print("=" * 100)
    print("== STEP E  负控（门禁必须变红，否则门禁失效）")
    print("=" * 100)
    f0, f1, f3, f5 = FNS[0], FNS[1], FNS[3], FNS[5]
    NC = []

    # 负控 1a：ret 4 -> ret 8（0x7241A0）
    c = force_ret(f0["cave"], f0["fn_ret"] + 4)
    ev = eval_cave(c, f0, f0["fn_ret"], f0["cave_va"])
    print(f"\n  NC1a {f0['name']}: ret 操作数 {f0['fn_ret']} -> {f0['fn_ret'] + 4}")
    print(f"    {c.hex(' ')}")
    print(f"    cave_ret 实测 = {ev['cave_ret']}   c7={'PASS' if ev['c7'] else 'FAIL'}   "
          f"零值净变化 = {ev['null_net']}")
    chk("NC1a", "改坏 ret 后 ★核心断言必须 FAIL", ev["c7"] is False,
        f"cave_ret={ev['cave_ret']} vs fn_ret={f0['fn_ret']}")
    chk("NC1a", "改坏 ret 后栈平衡也必须 FAIL", ev["c11"] is False, f"net={ev['null_net']}")
    NC.append(("NC1a", ev["c7"] is False and ev["c11"] is False))

    # 负控 1b：ret 0 -> ret 4（0x724530，v4 草案真实错误）
    c = force_ret(f3["cave"], 4)
    ev = eval_cave(c, f3, f3["fn_ret"], f3["cave_va"])
    print(f"\n  NC1b {f3['name']}: c3(ret 0) -> c2 04 00(ret 4)  ← v4 草案的真实错误")
    print(f"    {c.hex(' ')}")
    print(f"    cave_ret 实测 = {ev['cave_ret']}   c7={'PASS' if ev['c7'] else 'FAIL'}   "
          f"零值净变化 = {ev['null_net']}")
    chk("NC1b", "c3→ret4 后 ★核心断言必须 FAIL", ev["c7"] is False,
        f"cave_ret={ev['cave_ret']} vs fn_ret={f3['fn_ret']}")
    chk("NC1b", "c3→ret4 后栈平衡也必须 FAIL", ev["c11"] is False, f"net={ev['null_net']}")
    NC.append(("NC1b", ev["c7"] is False and ev["c11"] is False))

    # 负控 1c：ret 4 -> ret 0（反向，0x7241A0），确认双向都能抓
    c = force_ret(f0["cave"], 0)
    ev = eval_cave(c, f0, f0["fn_ret"], f0["cave_va"])
    print(f"\n  NC1c {f0['name']}: c2 04 00(ret 4) -> c3(ret 0)  ← 反向")
    print(f"    {c.hex(' ')}")
    print(f"    cave_ret 实测 = {ev['cave_ret']}   c7={'PASS' if ev['c7'] else 'FAIL'}   "
          f"零值净变化 = {ev['null_net']}")
    chk("NC1c", "ret4→c3 后 ★核心断言必须 FAIL", ev["c7"] is False,
        f"cave_ret={ev['cave_ret']} vs fn_ret={f0['fn_ret']}")
    NC.append(("NC1c", ev["c7"] is False))

    # 负控 2：jmp 目标 resume+1（0x724200）
    c = bytearray(f1["cave"])
    jo = f1["jmp_off"]
    struct.pack_into("<i", c, jo + 1, (f1["resume"] + 1) - (f1["cave_va"] + jo + 5))
    ev = eval_cave(bytes(c), f1, f1["fn_ret"], f1["cave_va"])
    print(f"\n  NC2 {f1['name']}: jmp 目标 {f1['resume']:#x} -> {f1['resume'] + 1:#x}")
    print(f"    {bytes(c).hex(' ')}")
    print(f"    jmp 实测目标 = {ev['jmp_target']:#x}   c9={'PASS' if ev['c9'] else 'FAIL'}")
    chk("NC2", "改偏 jmp 目标后第 9 条必须 FAIL", ev["c9"] is False,
        f"jmp→{ev['jmp_target']:#x}")
    NC.append(("NC2", ev["c9"] is False))

    # 负控 3：replay 末字节翻转（0x724580）
    c = bytearray(f5["cave"])
    jo = f5["jmp_off"]
    old = c[jo - 1]
    c[jo - 1] ^= 0x01
    ev = eval_cave(bytes(c), f5, f5["fn_ret"], f5["cave_va"])
    print(f"\n  NC3 {f5['name']}: replay 末字节 {old:#04x} -> {c[jo - 1]:#04x}")
    print(f"    {bytes(c).hex(' ')}")
    print(f"    重放段 = {ev['replay'].hex(' ')}   原映像 = {PEIMG.read(f5['va'], f5['resume'] - f5['va']).hex(' ')}")
    print(f"    c10={'PASS' if ev['c10'] else 'FAIL'}  （jmp_off 仍为 {ev['jmp_off']}，结构未破坏）")
    chk("NC3", "改坏 replay 后第 10 条必须 FAIL", ev["c10"] is False, "replay != image")
    chk("NC3", "负控 3 未破坏 cave 结构（jmp 仍被唯一识别）", ev["jmp_off"] == jo, str(ev["jmp_off"]))
    NC.append(("NC3", ev["c10"] is False))

    # 负控 4：把 v4 草案的原始错误整体注入（3 条 c3 函数全改成 ret 4），
    # 断言「v4 草案」在 v5 判据下必须整体不通过 —— 证明 v5 能抓住历史缺陷。
    print("\n  NC4  v4 草案原样注入：用 build_v4_style 重建 3 条 c3 函数的 cave（尾部 ret 4）")
    v4_bad = 0
    for f in FNS:
        if f["fn_ret"] != 0:
            continue
        c = build_v4_style(f, f["cave_va"])
        ev = eval_cave(c, f, f["fn_ret"], f["cave_va"])
        print(f"    {f['name']}: v4 cave {c.hex(' ')}")
        print(f"      cave_ret 实测={ev['cave_ret']}  fn_ret={f['fn_ret']}  "
              f"c7={'PASS' if ev['c7'] else 'FAIL'}  零值净={ev['null_net']}")
        if ev["c7"] is False:
            v4_bad += 1
    chk("NC4", "v4 草案的 3 处 ret 错误在 v5 判据下全部被抓住", v4_bad == 3, f"{v4_bad}/3")
    NC.append(("NC4", v4_bad == 3))

    print()
    for tag, red in NC:
        print(f"  负控 {tag}: {'RED（门禁有效）' if red else 'GREEN（★门禁失效）'}")
    chk("NC*", "全部负控都变红（门禁非恒真）", all(red for _, red in NC),
        f"{sum(1 for _, r in NC if r)}/{len(NC)} 红")

    # ------------------------------------------------------------ F: 表 + 素材
    print()
    print("=" * 100)
    print("== STEP F  主表")
    print("=" * 100)
    print(f"  {'VA':<10}{'hook':>5}{'replay':>7}{'fn_ret':>7}{'cave_ret':>9}  "
          f"{'verdict':<8}{'len':>4}  cave hex")
    for f in FNS:
        ev = f["ev"]
        per = [c for c in CHECKS if c[0] == f["name"]]
        bad = [c[1] for c in per if not c[2]]
        verdict = "PASS" if not bad else "FAIL"
        print(f"  {f['name']:<10}{f['hook']:>5}{f['resume'] - f['va']:>7}"
              f"{f['fn_ret']:>7}{ev['cave_ret']:>9}  {verdict:<8}{len(f['cave']):>4}  "
              f"{f['cave'].hex(' ')}")

    print()
    print("=" * 100)
    print("== STEP G  交付素材（hook 字节 / cave 反汇编）")
    print("=" * 100)
    for f in FNS:
        rel = f["cave_va"] - (f["va"] + 5)
        hook_bytes = b"\xE9" + struct.pack("<i", rel) + b"\x90" * (f["hook"] - 5)
        f["hook_bytes"] = hook_bytes
        print(f"\n  {f['name']}  fn_ret={f['fn_ret']}  cave_va={f['cave_va']:#x}  "
              f"cave_len={len(f['cave'])}")
        print(f"    hook({f['hook']}B) : {hook_bytes.hex(' ')}")
        print(f"    cave({len(f['cave'])}B) : {f['cave'].hex(' ')}")
        for i in MD.disasm(f["cave"], f["cave_va"]):
            print("      " + fmt(i))
        if f["extra"]:
            print(f"    note: 映像 {f['va'] + f['hook']:#x} 起的 {f['extra']}B "
                  f"({PEIMG.read(f['va'] + f['hook'], f['extra']).hex(' ')}) 被 jmp 跳过，"
                  f"cave 内重放")

    # hook 跳板自检：hook 字节必须反汇编成 1 条 jmp→cave_va + 纯 nop 填充
    print()
    print("  ── hook 跳板自检（从 hook 字节本身解码，不信构造公式）──")
    for f in FNS:
        hb = f["hook_bytes"]
        hi = list(MD.disasm(hb, f["va"]))
        tgt = hi[0].operands[0].imm if hi and hi[0].operands else None
        nops = all(i.mnemonic == "nop" for i in hi[1:])
        total = sum(len(i.bytes) for i in hi)
        print(f"    {f['name']}: {' ; '.join(f'{i.mnemonic} {i.op_str}' for i in hi)}"
              f"   → {tgt:#x}")
        chk(f["name"], "hook 解码为 jmp→本 cave + 纯 nop 填充",
            hi and hi[0].mnemonic == "jmp" and tgt == f["cave_va"] and nops
            and total == f["hook"], f"{tgt:#x} vs {f['cave_va']:#x}")
        chk(f["name"], "hook 长度 == 表中 hook", len(hb) == f["hook"],
            f"{len(hb)} vs {f['hook']}")

    print()
    print("=" * 100)
    print("== RESULT")
    print("=" * 100)
    n = sum(1 for _, _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    print(f"checks passed: {n}/{total}")
    for tag, name, ok, d in CHECKS:
        if not ok:
            print(f"  FAIL: [{tag}] {name}  {d}")
    nc_all_red = all(red for _, red in NC)
    print(f"negative controls red: {sum(1 for _, r in NC if r)}/{len(NC)}"
          f"  ({', '.join(t for t, r in NC if r)})")
    all_pass = (n == total) and nc_all_red
    if not nc_all_red:
        print("RESULT: FAIL  ← 门禁失效：有负控未变红，断言可能是恒真式")
    else:
        print("RESULT:", "ALL PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
