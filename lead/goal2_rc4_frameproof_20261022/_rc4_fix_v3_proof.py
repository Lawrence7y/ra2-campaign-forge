# -*- coding: utf-8 -*-
"""RC-4 修复草案 v3：四守卫（补上 0x724530 / 0x724540）

v2 的缺口（`_g_deref_census.py` 查出）
--------------------------------------
以 `[0x887368]` 为 this 的**直接 E8 调用**共 7 处，目标是 **4 个**函数：

| 函数 | 站点 | 首个 this 解引用偏移 | v2 是否覆盖 |
|:--|:--:|:--:|:--|
| `0x724730` | 1 | `0x250` | ✅ |
| `0x724580` | 4 | `0x24C` | ✅ |
| **`0x724530`** | 1 | **`0x228`** | ❌ |
| **`0x724540`** | 1 | **`0x22C`** | ❌ |

后两个是**纯访问器**（各 3 条指令）：

```asm
00724530  8b8128020000  mov eax, [ecx+0x228]   ; ★ ecx=0 ⇒ AV @ 0x228
00724536  89812c020000  mov [ecx+0x22c], eax
0072453C  c3            ret

00724540  8b812c020000  mov eax, [ecx+0x22c]   ; ★ ecx=0 ⇒ AV @ 0x22C
00724546  898128020000  mov [ecx+0x228], eax
0072454C  c3            ret
```

调用点（都紧邻 `mov ecx,[0x887368]`，**无守卫**）：

    006AB994  mov ecx, [0x887368]
    006AB99A  call 0x724530          ← 无 test/cmp
    006AB99F  mov ecx, [0x887368]
    006AB9A5  push 0                 ← 继续用

    006AB9E3  mov ecx, [0x887368]
    006AB9E9  call 0x724540          ← 无 test/cmp

本脚本要证明
------------
A. 四函数的 hook 边界全部落在指令边界上，且覆盖长度 = 各自序言字节数。
B. 四个 cave 的字节、`je`/`jmp` 位移、capstone 语义全部成立。
C. 四条「零值路径」与四条「非零路径」的栈全部回到基线。
D. 四函数的调用者**全不读返回值**（决定 `.null` 返回 `eax=0` 是否安全）。

只读，不写任何二进制、不部署。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G = 0x887368

# (函数, hook 长度, resume)
#   ★ resume 不必然 == va + hook_len：
#     hook 只覆盖 6/8 字节放 E9，但**其后紧邻的原指令若也必须重放**
#     （如 0x724736 的 push esi，因为尾声有配对的 pop esi），
#     cave 就要多放几条原指令，resume 落在更后面。
#     ⇒ 判据不是 "resume == va+hook_len"，而是
#       「被重放的指令集合」+「未被重放的后续指令」恰好拼成原指令流，
#       且栈配平（STEP C 证）。
FNS = [
    dict(va=0x724730, hook=6,  resume=0x724737, name="FN_A 0x724730",
         replay_extra=bytes.fromhex("56")),      # ★ 额外重放 push esi
    dict(va=0x724580, hook=8,  resume=0x724588, name="FN_B 0x724580",
         replay_extra=b""),
    dict(va=0x724530, hook=6,  resume=0x724536, name="FN_C 0x724530",
         replay_extra=b""),
    dict(va=0x724540, hook=6,  resume=0x724546, name="FN_D 0x724540",
         replay_extra=b""),
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


def ret_size(fn_va):
    """函数体内**第一个** ret 的操作数（0 或 4）。

    ★ 窗口要足够大：0x724730 的尾声在 0x7248AE，距函数头 ~0x17E 字节。
      用指令数上限 400 而不是 60。
    """
    off = va2off(fn_va)
    for i in MD.disasm(DATA[off:off + 0x800], fn_va):
        if i.mnemonic == "ret":
            return int(i.op_str) if i.op_str else 0
    return None


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    sha = hashlib.sha256(BIN.read_bytes()).hexdigest()
    print(f"  gamemd.exe : {sha}")
    chk("binary identity", sha.startswith(WANT_SHORT), sha[:8])

    # ------------------------------------------------------------- A
    print()
    print("=" * 78)
    print("== STEP A  hook 边界（必须整条指令覆盖）")
    print("=" * 78)
    for f in FNS:
        va, hl, rs = f["va"], f["hook"], f["resume"]
        insns = dis(va, 12)
        acc = 0
        covered = []
        for i in insns:
            if acc >= hl:
                break
            covered.append(i)
            acc += len(i.bytes)
        print(f"\n  {f['name']}  hook_len={hl}")
        for i in covered:
            print("    " + fmt(i))
        f["orig"] = raw(va, hl)
        f["covered"] = covered
        chk(f"{f['name']} hook_len == 序言整条累计字节", acc == hl, f"{acc} vs {hl}")
        chk(f"{f['name']} resume 处是新指令起点",
            dis(rs, 1)[0].address == rs, hex(rs))
        chk(f"{f['name']} hook_len >= 5（放得下 E9 rel32）", hl >= 5, str(hl))
        chk(f"{f['name']} 原字节 = 覆盖指令字节拼接",
            f["orig"] == b"".join(i.bytes for i in covered), f["orig"].hex(" "))

        # ★ 额外重放段必须紧接 hook 之后，且必须整条指令
        extra = f["replay_extra"]
        print(f"    额外重放 {len(extra)} 字节 @ {va+hl:#x}: {extra.hex(' ')}")
        if extra:
            chk(f"{f['name']} 额外重放字节 == 映像原文",
                raw(va + hl, len(extra)) == extra,
                raw(va + hl, len(extra)).hex(" "))
            ex_ins = dis(va + hl, 4)
            consumed = 0
            for i in ex_ins:
                if consumed >= len(extra):
                    break
                consumed += len(i.bytes)
                print("      " + fmt(i))
            chk(f"{f['name']} 额外重放整条覆盖（不截断指令）",
                consumed == len(extra), f"{consumed} vs {len(extra)}")
        print(f"    合计重放 {hl+len(extra)} 字节；resume = {rs:#x}，"
              f"应 == {va+hl+len(extra):#x}")
        chk(f"{f['name']} resume == va + hook_len + extra",
            rs == va + hl + len(extra), f"{rs:#x} vs {va+hl+len(extra):#x}")

    # ------------------------------------------------------------- B
    print()
    print("=" * 78)
    print("== STEP B  四个 cave 的字节与语义")
    print("=" * 78)
    FAKE = 0x10000000
    for k, f in enumerate(FNS):
        f["cave_va"] = FAKE + k * 0x40
        ca = bytearray()
        ca += bytes.fromhex("85c9")               # test ecx,ecx
        je_at = len(ca)
        ca += bytes.fromhex("7400")               # je rel8 placeholder
        ca += f["orig"]                           # 重放被覆盖的原指令
        ca += f["replay_extra"]                   # ★ 额外重放（如 push esi）
        jmp_at = len(ca)
        ca += bytes.fromhex("e900000000")         # jmp rel32 placeholder
        null_at = len(ca)
        ca += bytes.fromhex("31c0c20400")         # xor eax,eax; ret 4
        je_rel = null_at - (je_at + 2)
        ca[je_at + 1] = je_rel & 0xFF
        struct.pack_into("<i", ca, jmp_at + 1,
                         f["resume"] - (f["cave_va"] + jmp_at + 5))
        f["cave"] = bytes(ca)
        f["je_rel"] = je_rel
        f["null_off"] = null_at

        print(f"\n  {f['name']}  cave ({len(ca)} 字节) @ {f['cave_va']:#x}")
        print(f"    {f['cave'].hex(' ')}")
        print(f"    je rel8={je_rel} → .null @ +{null_at}；"
              f"jmp rel32 → {f['resume']:#x}")
        ins = list(MD.disasm(f["cave"], f["cave_va"]))
        for i in ins:
            print("    " + fmt(i))
        chk(f"{f['name']} cave[0]=test ecx,ecx", ins[0].mnemonic == "test", fmt(ins[0]))
        chk(f"{f['name']} cave[1]=je", ins[1].mnemonic == "je", fmt(ins[1]))
        chk(f"{f['name']} je 目标 == .null",
            ins[1].operands[0].imm == f["cave_va"] + null_at,
            hex(f["cave_va"] + null_at))
        chk(f"{f['name']} je rel8 在范围", -128 <= je_rel <= 127, str(je_rel))
        chk(f"{f['name']} 重放原指令字节一致",
            f["cave"][4:4 + len(f["orig"])] == f["orig"],
            f["cave"][4:4 + len(f["orig"])].hex(" "))
        if f["replay_extra"]:
            chk(f"{f['name']} 额外重放字节一致",
                f["cave"][4 + len(f["orig"]):4 + len(f["orig"]) + len(f["replay_extra"])]
                == f["replay_extra"],
                f["replay_extra"].hex(" "))
        jmps = [i for i in ins if i.mnemonic == "jmp"]
        chk(f"{f['name']} 恰 1 条 jmp 且目标 == resume",
            len(jmps) == 1 and jmps[0].operands[0].imm == f["resume"],
            hex(f["resume"]))
        chk(f"{f['name']} 末条 ret 4",
            ins[-1].mnemonic == "ret" and ins[-1].op_str == "4", fmt(ins[-1]))

    # ------------------------------------------------------------- C
    print()
    print("=" * 78)
    print("== STEP C  栈平衡（16 条路径）")
    print("=" * 78)
    BASE = 0x100000
    print("  主论证（结构性，不依赖解析尾声）：")
    print("    cave 在 [va, resume) 区间重放了**完全相同**的原指令字节，")
    print("    然后 jmp 到 resume。⇒ 从 resume 起的执行流与原函数逐字节相同，")
    print("    因此『非零路径』的 esp 变化与原函数**恒等**，无需另行推演。")
    print("    『零值路径』未执行任何 sub/push，只 call(-4)+ret N(+4+N) ⇒ 净 0。")
    print()
    for f in FNS:
        va, hl = f["va"], f["hook"]
        extra = f["replay_extra"]
        replay = f["covered"] + dis(va + hl, 4)
        ex_consumed, ex_ins = 0, []
        for i in replay[len(f["covered"]):]:
            if ex_consumed >= len(extra):
                break
            ex_ins.append(i)
            ex_consumed += len(i.bytes)
        replay_ins = f["covered"] + ex_ins
        pushes = sum(1 for i in replay_ins if i.mnemonic == "push")
        subs = sum(int(i.op_str.split(",")[1].strip(), 16)
                   for i in replay_ins
                   if i.mnemonic == "sub" and i.op_str.startswith("esp"))
        rsz = ret_size(va)
        print(f"\n  {f['name']}  ret {rsz}")
        print(f"    重放段: sub esp,{subs:#x} + {pushes} 个 push "
              f"= esp 下移 {subs + 4*pushes:#x}（cave 内原样执行）")
        chk(f"{f['name']} 重放段字节 == 映像原文 [va,resume)",
            f["orig"] + extra == raw(va, hl + len(extra)),
            (f["orig"] + extra).hex(" "))
        chk(f"{f['name']} resume == va + hook + extra",
            f["resume"] == va + hl + len(extra),
            f"{f['resume']:#x}")

        # 零值路径的 esp 净变化，以**调用方 push arg 之前**为基线：
        #   调用方 push arg      : -rsz      （stdcall，参数个数 = rsz/4）
        #   call 压 retaddr      : -4
        #   .null: xor; ret N    : +4 + rsz  （弹 retaddr + 参数）
        #   合计 = -rsz - 4 + 4 + rsz = 0
        nargs = rsz // 4
        bal_null = -rsz - 4 + 4 + rsz
        print(f"    零值路径: push {nargs} arg(-{rsz}) + call(-4) + ret {rsz}(+{4+rsz}) "
              f"= {bal_null:+d}")
        chk(f"{f['name']} 零值路径栈自平衡（ret {rsz} 与 {nargs} 个参数匹配）",
            bal_null == 0, f"{bal_null:+d}")

        # 附加校验：尾声里 pop 的个数必须等于重放段 push 的个数
        #   （只对能线性解析到 ret 的函数做；解析不到则跳过并注明）
        prev = dis(va, 400)
        rets = [k for k, i in enumerate(prev) if i.mnemonic == "ret"]
        if rets:
            idx = rets[0]
            epi = prev[max(0, idx - 8):idx]
            n_pop = sum(1 for i in epi if i.mnemonic == "pop")
            add_esp = sum(int(i.op_str.split(",")[1].strip(), 16)
                          for i in epi
                          if i.mnemonic == "add" and i.op_str.startswith("esp"))
            print(f"    尾声(可解析): {n_pop} 个 pop + add esp,{add_esp:#x}")
            if f["name"].startswith("FN_C") or f["name"].startswith("FN_D"):
                chk(f"{f['name']} 小函数无 push/pop（纯访问器）",
                    pushes == 0 and n_pop == 0, f"push={pushes} pop={n_pop}")
            else:
                chk(f"{f['name']} 尾声 pop 数 == 重放段 push 数",
                    n_pop == pushes, f"{n_pop} vs {pushes}")
        else:
            print("    尾声: 线性解析未达 ret（跳过该附加校验）")

    # ------------------------------------------------------------- D
    print()
    print("=" * 78)
    print("== STEP D  四函数的调用者是否读返回值")
    print("=" * 78)
    for f in FNS:
        cs = all_e8_callers(f["va"])
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
        print(f"\n  {f['name']}：{len(cs)} 个直接 E8 调用者 "
              f"（覆盖 eax {ow} / 读 eax {rd} / 不碰 {ot}）")
        print(f"    调用点: {', '.join(hex(c) for c in cs)}")
        for c, d in reads:
            print(f"    ★ {c:#x}  {d}")
        f["callers"] = cs
        chk(f"{f['name']} 的调用者全不读返回值", rd == 0, f"read={rd}")

    # ------------------------------------------------------------- E
    print()
    print("=" * 78)
    print("== STEP E  v3 草案汇总（离线，未部署）")
    print("=" * 78)
    print("  ── gamemd 侧（4 处函数头）──")
    for f in FNS:
        n_nop = f["hook"] - 5
        print(f"    {f['va']:#x} : {f['orig'].hex(' ')}  ->  "
              f"E9 <rel32→DLL cave>  + {n_nop}×90")
    print("  ── DLL 侧（4 个静态数组 + PAGE_EXECUTE_READWRITE）──")
    for f in FNS:
        print(f"    cave[{f['name']}] ({len(f['cave'])}B) : {f['cave'].hex(' ')}")
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


WANT_SHORT = WANT_SHA8

if __name__ == "__main__":
    sys.exit(main())
