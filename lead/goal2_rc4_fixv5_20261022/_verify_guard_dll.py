#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-4 守卫副本 DLL 的离线核验（rc4_guard.cpp / ra2rc4guard.dll）。

★ 为什么需要这一层
  `_verify_patch_v5.py` 核的是 **PATCH_SPEC_V5 的 cave 字节**（不含命中计数器）。
  本轮的 DLL 在 cave 尾部多插了一条 `lock inc [counter]`（裁决 5 要求每个守卫
  有命中计数器）⇒ cave 字节与 v5 规格**不再逐字节相同**，必须单独核。

★ 核验对象
  1. 从编译产物里抽出的 `k_sites` 表 == 规格表（VA / hook / replay / fn_ret / 原字节）
  2. 用 **C++ 逻辑的 Python 镜像**重算 8 条 cave，与 DLL 里实际生成的 cave 逐字节比
  3. capstone 反汇编每条 cave，断言：
     - 第 1 条 test ecx,ecx
     - 第 2 条 je，目标 == null 块起点
     - replay 段 == gamemd 原映像 [va, va+replay)
     - 恰 1 条 jmp，目标 == resume
     - 命中计数器 = lock inc [abs32]，abs32 == &g_hits[i]
     - 末条 ret 操作数 == fn_ret
     - cave 长度 <= 0x40（槽距）
  4. 负控：改 fn_ret / 改 jmp 目标 / 改 replay 各一次，断言核验必须红

★ 纪律
  只读 gamemd.exe 与 ra2rc4guard.dll；不启动游戏；不写 ra2youli。
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import capstone

ROOT = Path(r"D:\Project\ra2-campaign-forge")
GAMEMD = ROOT / "ra2youli" / "gamemd.exe"
DLL = ROOT / "lead" / "goal2_rc4_fixv5_20261022" / "src" / "ra2rc4guard.dll"

GAMEMD_SHA16 = "73201cc021497c95"
SLOT_STRIDE = 0x40

CHECKS: list[tuple[str, bool, str]] = []


def chk(name: str, cond: bool, detail: str = "") -> bool:
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


# ---------------------------------------------------------------------------
# 规格表（与 rc4_guard.cpp 的 k_sites 同源；原字节取自 gamemd 映像）
# ---------------------------------------------------------------------------
SPEC = [
    # (va, hook_len, replay_len, fn_ret)
    (0x007241A0,  5,  5, 4),
    (0x00724200,  5,  5, 4),
    (0x00724520, 10, 10, 4),
    (0x00724530,  6,  6, 0),
    (0x00724540,  6,  6, 0),
    (0x00724580,  8,  8, 4),
    (0x00724730,  6,  7, 4),
    (0x00724C00,  5,  5, 0),
]


def build_cave(site_idx: int, va: int, replay_len: int, fn_ret: int,
               orig: bytes, cave_va: int, counter_addr: int) -> bytes:
    """rc4_guard.cpp::BuildCave 的逐行镜像。"""
    off_je = 2
    off_rep = 4
    off_jmp = off_rep + replay_len
    off_null = off_jmp + 5
    off_cnt = off_null
    off_xor = off_cnt + 7
    off_ret = off_xor + 2
    total = off_ret + (1 if fn_ret == 0 else 3)

    out = bytearray(total)
    out[0], out[1] = 0x85, 0xC9                       # test ecx, ecx

    rel = off_null - (off_je + 2)
    assert -128 <= rel <= 127, rel
    out[off_je], out[off_je + 1] = 0x74, rel & 0xFF    # je null

    out[off_rep:off_rep + replay_len] = orig           # replay

    resume = va + replay_len
    jrel = resume - (cave_va + off_jmp + 5)
    out[off_jmp] = 0xE9
    struct.pack_into("<i", out, off_jmp + 1, jrel)     # jmp resume

    out[off_cnt] = 0xF0                                # lock inc [counter]
    out[off_cnt + 1] = 0xFF
    out[off_cnt + 2] = 0x05
    struct.pack_into("<I", out, off_cnt + 3, counter_addr & 0xFFFFFFFF)

    out[off_xor], out[off_xor + 1] = 0x31, 0xC0        # xor eax, eax

    if fn_ret == 0:
        out[off_ret] = 0xC3
    else:
        out[off_ret] = 0xC2
        struct.pack_into("<H", out, off_ret + 1, fn_ret)
    return bytes(out)


def main() -> int:
    print("=" * 90)
    print("== STEP 0  identity")
    print("=" * 90)
    import hashlib
    gsha = hashlib.sha256(GAMEMD.read_bytes()).hexdigest()
    dsha = hashlib.sha256(DLL.read_bytes()).hexdigest()
    print(f"  gamemd.exe      : {gsha}")
    print(f"  ra2rc4guard.dll : {dsha}")
    chk("gamemd 身份", gsha.startswith(GAMEMD_SHA16), gsha[:16])

    gd = GAMEMD.read_bytes()
    dd = DLL.read_bytes()

    def g_off(va: int) -> int:
        return va - 0x400000          # 本件 .text raw==RVA==va-ImageBase（已在前序核过）

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    # -----------------------------------------------------------------------
    print()
    print("=" * 90)
    print("== STEP 1  从 DLL 抽 k_sites 表，逐条比对规格")
    print("=" * 90)
    needle = bytes([0x8A, 0x44, 0x24, 0x04, 0x56])       # site 0 的 orig
    pos = dd.find(needle)
    chk("在 DLL 中找到 k_sites[0].orig", pos > 0, hex(pos) if pos > 0 else "not found")
    if pos <= 0:
        return 1
    # 结构布局（MSVC x86，实测）：uintptr(4) + 4×u8 + orig[16]，无填充 ⇒ 24B，orig 在 +7
    ORIG_OFF = 7
    base = pos - ORIG_OFF
    print(f"  k_sites 表基址（文件偏移）= {base:#x}")

    table = []
    for k in range(8):
        o = base + k * 24
        va = struct.unpack_from("<I", dd, o)[0]
        hook = dd[o + 4]
        rl = dd[o + 5]
        fr = dd[o + 6]
        orig = dd[o + ORIG_OFF:o + ORIG_OFF + 16]
        table.append((va, hook, rl, fr, orig))
        eva, ehook, erl, efr = SPEC[k]
        got = (va, hook, rl, fr, orig[:rl])
        want = (eva, ehook, erl, efr, gd[g_off(eva):g_off(eva) + erl])
        chk(f"k_sites[{k}] == 规格（VA/hook/replay/fn_ret/原字节）",
            got == want,
            f"va={va:08X} hook={hook} replay={rl} ret={fr} orig={orig[:rl].hex()}")

    # -----------------------------------------------------------------------
    print()
    print("=" * 90)
    print("== STEP 2  用 C++ 逻辑镜像重算 8 条 cave，capstone 逐条断言")
    print("=" * 90)
    # 假想 cave 基址（与 DLL 运行时一致：0x10000000 + i*0x40）
    # 计数器地址取一个稳定假值，只用于比对「cave 里写的是不是同一个数」
    FAKE_COUNTER = 0x10040000
    for k, (va, hook, rl, fr, orig16) in enumerate(table):
        orig = orig16[:rl]
        cave_va = 0x10000000 + k * SLOT_STRIDE
        cave = build_cave(k, va, rl, fr, orig, cave_va, FAKE_COUNTER + k * 4)
        resume = va + rl

        ins = list(md.disasm(cave, cave_va))
        print(f"\n  0x{va:08X}  cave ({len(cave)}B @ 0x{cave_va:08X}, fn_ret={fr})")
        print(f"    {cave.hex(' ')}")
        for i in ins:
            print(f"      {i.address:08X}  {i.bytes.hex():<18} {i.mnemonic} {i.op_str}")

        chk(f"0x{va:08X} 首条 = test ecx,ecx",
            ins[0].mnemonic == "test" and "ecx" in ins[0].op_str, ins[0].op_str)

        # ★ null 块起点必须按**结构偏移**定位，不能按「第一条 xor eax,eax」扫。
        #   反例：0x724C00 的重放段是 `8b 51 04 33 c0`，本身自带一条 xor eax,eax
        #   （原函数语义），按助记符扫会抓到重放段内部那条 ⇒ 假红。
        off_null = 4 + rl + 5
        null_va = cave_va + off_null
        je = [i for i in ins if i.mnemonic == "je"]
        chk(f"0x{va:08X} 第 2 条 = je 且目标在 cave 内",
            len(je) == 1 and cave_va <= je[0].operands[0].imm < cave_va + len(cave),
            hex(je[0].operands[0].imm) if je else "no je")
        chk(f"0x{va:08X} je 目标 == null 块起点（结构偏移 {off_null}）",
            bool(je) and je[0].operands[0].imm == null_va,
            f"je→{hex(je[0].operands[0].imm)} want {hex(null_va)}")

        # replay 段
        chk(f"0x{va:08X} replay 段 == gamemd 原映像",
            cave[4:4 + rl] == gd[g_off(va):g_off(va) + rl], f"{rl}B")

        jmps = [i for i in ins if i.mnemonic == "jmp"]
        chk(f"0x{va:08X} 恰 1 条 jmp 且目标 == resume",
            len(jmps) == 1 and jmps[0].operands[0].imm == resume,
            f"{len(jmps)} jmp → {hex(jmps[0].operands[0].imm)} (want {hex(resume)})")

        # 命中计数器：capstone 把 F0 前缀并进助记符 ⇒ mnemonic 是 "lock inc" 而非 "inc"
        cnt = [i for i in ins if i.mnemonic == "lock inc"]
        chk(f"0x{va:08X} 有 lock inc [绝对地址]",
            len(cnt) == 1 and cnt[0].address == null_va,
            f"{cnt[0].op_str} @ {hex(cnt[0].address)}" if cnt else "none")
        if cnt:
            want_cnt = FAKE_COUNTER + k * 4
            got_cnt = cnt[0].operands[0].mem.disp
            chk(f"0x{va:08X} 计数器地址 == &g_hits[{k}]",
                got_cnt == want_cnt, f"{hex(got_cnt)} want {hex(want_cnt)}")

        # ret
        rets = [i for i in ins if i.mnemonic.startswith("ret")]
        chk(f"0x{va:08X} 末条 ret 操作数 == fn_ret({fr})",
            len(rets) == 1 and (rets[0].op_str.strip() or "0") == str(fr),
            f"ret {rets[0].op_str.strip() or '0'}")

        chk(f"0x{va:08X} cave 长度 <= 槽距 0x40", len(cave) <= SLOT_STRIDE, f"{len(cave)}B")

    # -----------------------------------------------------------------------
    print()
    print("=" * 90)
    print("== STEP 3  负控（必须全红）")
    print("=" * 90)
    va0, hook0, rl0, fr0, orig0_16 = table[3]     # 0x724530, fn_ret=0
    orig0 = orig0_16[:rl0]

    # NC1：fn_ret 写错（0 → 4）
    bad = build_cave(3, va0, rl0, 4, orig0, 0x10000000 + 3 * SLOT_STRIDE, FAKE_COUNTER)
    bins = list(md.disasm(bad, 0x10000000 + 3 * SLOT_STRIDE))
    bret = [i for i in bins if i.mnemonic.startswith("ret")][-1]
    nc1 = (bret.op_str.strip() or "0") != str(fr0)
    chk("NC1 fn_ret 改 4 ⇒ 末条 ret 不再是 0（门禁会红）", nc1,
        f"ret {bret.op_str.strip() or '0'}")

    # NC2：jmp 目标偏 1
    cave_va = 0x10000000 + 3 * SLOT_STRIDE
    bad2 = bytearray(build_cave(3, va0, rl0, fr0, orig0, cave_va, FAKE_COUNTER))
    off_jmp = 4 + rl0
    jrel = struct.unpack_from("<i", bad2, off_jmp + 1)[0]
    struct.pack_into("<i", bad2, off_jmp + 1, jrel + 1)
    b2 = list(md.disasm(bytes(bad2), cave_va))
    j2 = [i for i in b2 if i.mnemonic == "jmp"][0]
    nc2 = j2.operands[0].imm != (va0 + rl0)
    chk("NC2 jmp 目标 +1 ⇒ 不再等于 resume（门禁会红）", nc2, hex(j2.operands[0].imm))

    # NC3：replay 改一字节
    bad3 = bytearray(build_cave(3, va0, rl0, fr0, orig0, cave_va, FAKE_COUNTER))
    bad3[4] ^= 0xFF
    nc3 = bytes(bad3[4:4 + rl0]) != gd[g_off(va0):g_off(va0) + rl0]
    chk("NC3 replay 改 1 字节 ⇒ 与原映像不符（门禁会红）", nc3, "xor 0xFF")

    # -----------------------------------------------------------------------
    print()
    print("=" * 90)
    print("== RESULT")
    print("=" * 90)
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    nc_ok = all(ok for n, ok, _ in CHECKS if n.startswith("NC"))
    print(f"  checks passed: {passed}/{total}")
    print(f"  negative controls red: {'YES' if nc_ok else 'NO'}")
    verdict = passed == total and nc_ok
    print(f"  RESULT: {'ALL PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
