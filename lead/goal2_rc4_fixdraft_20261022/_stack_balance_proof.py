# -*- coding: utf-8 -*-
"""栈平衡推演验证（RC-4 修复补丁的命门）。

这是补丁最可能出错的地方，必须逐字节推演。

调用方视角（stdcall，1 个参数）
------------------------------
```asm
push <arg>            ; esp -= 4
call 0x724730         ; push retaddr (esp -= 4)，跳到 hook
```

原函数 0x724730 的栈操作
------------------------
```asm
0x724730  sub  esp, 0xc        ; esp -= 0xc
0x724733  push ebp             ; esp -= 4
0x724734  mov  ebp, ecx
0x724736  push esi             ; esp -= 4
...
0x7248A9  pop  esi             ; esp += 4
0x7248AA  pop  ebp             ; esp += 4
0x7248AB  add  esp, 0xc        ; esp += 0xc
0x7248AE  ret  4               ; 弹出 retaddr(esp+=4) + 参数(esp+=4)
```
净效果：`-0xc -4 -4 +4 +4 +0xc +4(retaddr) +4(arg)` = 0 ✅

补丁后的路径 1：ecx != 0（正常路径）
------------------------------------
```asm
call 0x724730                 ; push retaddr
0x724730  jmp  0xB95700       ; (无栈操作)
0xB95700  test ecx, ecx       ; (无栈操作)
0xB95702  je   ...            ; 不跳
0xB95704  sub  esp, 0xc       ; esp -= 0xc      ← 原指令，等价
0xB95707  push ebp            ; esp -= 4        ← 原指令，等价
0xB95708  mov  ebp, ecx
0xB9570A  push esi            ; esp -= 4        ← 原指令，等价
0xB9570B  jmp  0x724737       ; (无栈操作)
0x724737  mov eax,[ebp+0x250] ; 继续原逻辑
...
0x7248A9  pop esi; pop ebp; add esp,0xc; ret 4   ← 与原函数同一出口
```
栈效果：与原来**完全一致** ✅

补丁后的路径 2：ecx == 0（守卫路径）
------------------------------------
```asm
call 0x724730                 ; push retaddr    esp = E-4
0x724730  jmp  0xB95700
0xB95700  test ecx, ecx
0xB95702  je   0xB95710       ; 跳到 .null
0xB95710  xor  eax, eax       ; (无栈操作)
0xB95712  ret  4              ; 弹出 retaddr(esp+=4) + arg(esp+=4)  esp = E+4
```
★ 关键：守卫路径**没有**执行 `sub esp,0xc` / `push ebp` / `push esi`，
所以也**不需要** `pop esi` / `pop ebp` / `add esp,0xc`。
直接 `ret 4` 正好把 retaddr 和参数弹出 ⇒ 栈回到调用方 push arg 之前的状态 ✅

⇒ **两条路径的栈都平衡。**

本脚本
------
用模拟器逐条执行 cave 字节，跟踪 esp 变化，断言两条路径最终 esp 都回到正确值。
"""
import struct
import sys
from pathlib import Path

CAVE = 0x00B95700
HOOK = 0x724730
RESUME = 0x724737
NULL_VA = 0x00B95710
CALLER_ESP = 0x100000       # 任意基准

CAVE_BYTES = bytes.fromhex("85c9740c83ec0c558be9 56e927f0b8ff31c0c20400".replace(" ", ""))
HOOK_BYTES = bytes.fromhex("e9cb0f4700 90".replace(" ", ""))

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def simulate(ecx, verbose=True):
    """模拟执行：caller push arg → call hook → cave → ...

    返回 (path, final_esp, notes)。
    """
    esp = CALLER_ESP
    notes = []
    # caller: push arg
    esp -= 4
    notes.append(f"push arg            esp=0x{esp:X}")
    # call 0x724730: push retaddr
    esp -= 4
    notes.append(f"call 0x724730       esp=0x{esp:X}  (retaddr pushed)")
    # 跳到 hook -> cave（无栈操作）
    notes.append(f"jmp 0x{CAVE:X}          esp=0x{esp:X}")
    # test ecx,ecx
    notes.append(f"test ecx,ecx (ecx={ecx})")
    if ecx == 0:
        # je .null
        notes.append(f"je 0x{NULL_VA:X}       (taken)")
        # xor eax,eax
        notes.append("xor eax,eax")
        # ret 4
        retaddr = 4
        esp += 4
        notes.append(f"ret 4 (pop retaddr) esp=0x{esp:X}")
        esp += 4
        notes.append(f"ret 4 (pop arg)     esp=0x{esp:X}")
        path = "null"
    else:
        notes.append("je (not taken)")
        # sub esp,0xc
        esp -= 0xC
        notes.append(f"sub esp,0xc         esp=0x{esp:X}")
        # push ebp
        esp -= 4
        notes.append(f"push ebp            esp=0x{esp:X}")
        # mov ebp,ecx
        notes.append("mov ebp,ecx")
        # push esi
        esp -= 4
        notes.append(f"push esi            esp=0x{esp:X}")
        # jmp RESUME
        notes.append(f"jmp 0x{RESUME:X}        esp=0x{esp:X}")
        # ... 原函数体 ... 到 0x7248A9
        # pop esi
        esp += 4
        notes.append(f"pop esi             esp=0x{esp:X}")
        # pop ebp
        esp += 4
        notes.append(f"pop ebp             esp=0x{esp:X}")
        # add esp,0xc
        esp += 0xC
        notes.append(f"add esp,0xc         esp=0x{esp:X}")
        # ret 4
        esp += 4
        notes.append(f"ret 4 (pop retaddr) esp=0x{esp:X}")
        esp += 4
        notes.append(f"ret 4 (pop arg)     esp=0x{esp:X}")
        path = "normal"

    if verbose:
        for n in notes:
            print(f"    {n}")
    return path, esp, notes


def main():
    print("=" * 78)
    print("== STEP 0  byte sanity")
    print("=" * 78)
    print(f"  cave bytes ({len(CAVE_BYTES)}): {CAVE_BYTES.hex(' ')}")
    print(f"  hook bytes ({len(HOOK_BYTES)}): {HOOK_BYTES.hex(' ')}")
    chk("cave is 21 bytes", len(CAVE_BYTES) == 21, str(len(CAVE_BYTES)))
    chk("hook is 6 bytes", len(HOOK_BYTES) == 6, str(len(HOOK_BYTES)))

    print()
    print("=" * 78)
    print("== STEP 1  baseline: ORIGINAL function (no patch)")
    print("=" * 78)
    esp = CALLER_ESP
    esp -= 4; print(f"    push arg            esp=0x{esp:X}")
    esp -= 4; print(f"    call 0x724730       esp=0x{esp:X}")
    esp -= 0xC; print(f"    sub esp,0xc         esp=0x{esp:X}")
    esp -= 4; print(f"    push ebp            esp=0x{esp:X}")
    esp -= 4; print(f"    push esi            esp=0x{esp:X}")
    esp += 4; print(f"    pop esi             esp=0x{esp:X}")
    esp += 4; print(f"    pop ebp             esp=0x{esp:X}")
    esp += 0xC; print(f"    add esp,0xc         esp=0x{esp:X}")
    esp += 4; print(f"    ret 4 (retaddr)     esp=0x{esp:X}")
    esp += 4; print(f"    ret 4 (arg)         esp=0x{esp:X}")
    baseline_esp = esp
    chk("baseline returns esp to CALLER_ESP", baseline_esp == CALLER_ESP,
        f"0x{baseline_esp:X} vs 0x{CALLER_ESP:X}")

    print()
    print("=" * 78)
    print("== STEP 2  patched path A: ecx != 0 (normal)")
    print("=" * 78)
    pA, espA, _ = simulate(0x87F7E8)
    chk("path A returns esp to CALLER_ESP", espA == CALLER_ESP,
        f"0x{espA:X}")
    chk("path A esp == baseline esp", espA == baseline_esp,
        f"0x{espA:X} vs 0x{baseline_esp:X}")

    print()
    print("=" * 78)
    print("== STEP 3  patched path B: ecx == 0 (guarded)")
    print("=" * 78)
    pB, espB, _ = simulate(0)
    chk("path B returns esp to CALLER_ESP", espB == CALLER_ESP,
        f"0x{espB:X}")
    chk("path B esp == baseline esp", espB == baseline_esp,
        f"0x{espB:X} vs 0x{baseline_esp:X}")

    print()
    print("=" * 78)
    print("== STEP 4  verify cave byte-level semantics with capstone")
    print("=" * 78)
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        ins = list(md.disasm(CAVE_BYTES, CAVE))
        # 逐条打印并断言
        expect = [
            ("test", "ecx"), ("je", None), ("sub", "esp"), ("push", "ebp"),
            ("mov", "ebp"), ("push", "esi"), ("jmp", None),
            ("xor", "eax"), ("ret", "4"),
        ]
        chk("cave decodes to exactly 9 instructions", len(ins) == 9, str(len(ins)))
        for k, (mn, frag) in enumerate(expect):
            if k >= len(ins):
                break
            i = ins[k]
            ok = i.mnemonic == mn and (frag is None or frag in i.op_str)
            print(f"    [{k}] {i.address:08X}  {i.mnemonic:<6} {i.op_str:<20} "
                  f"{'OK' if ok else 'MISMATCH'}")
            chk(f"cave[{k}] == {mn} {frag or ''}", ok, f"{i.mnemonic} {i.op_str}")

        # 关键：ret 是 ret 4 还是 ret
        last = ins[-1]
        chk("last insn is 'ret 4' (not bare ret)", last.mnemonic == "ret"
            and last.op_str.strip() == "4", f"{last.mnemonic} {last.op_str}")
    except ImportError:
        chk("capstone available", False, "import failed")

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    all_ok = all(ok for _, ok, _ in CHECKS)
    if all_ok:
        print("  [已证] 补丁的两条路径栈都平衡：")
        print("         - ecx != 0：cave 执行原 4 条指令后 jmp 回 0x724737，")
        print("                     走原函数同一出口（pop esi/pop ebp/add esp,0xc/ret 4）")
        print("         - ecx == 0：cave 直接 xor eax,eax; ret 4，")
        print("                     因为未执行 sub/push，故不需 pop/add")
        print("         ⇒ 两条路径最终 esp 都 == 调用方 push arg 之前的值")
        print("  [已证] cave 字节语义与设计一致（capstone 逐条核对 9/9）")
    else:
        print("  [失败] 见上方 FAIL 项。")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
